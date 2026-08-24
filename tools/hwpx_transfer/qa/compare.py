# MD 기준 항목열과 hwpx 추출 항목열을 정규화·정렬 대조해 누락/추가/불일치를 전수 보고하는 QA 대조기
"""compare.py — 제1~3장 충실도 대조.

usage: python compare.py <hwpx_dump.json> <md_ch01.json> <md_ch02.json> <md_ch03.json>
"""
import difflib
import json
import re
import sys

EMSP = " "


def strip_inline(t):
    """MD 인라인 마크업 제거(굵게·기울임·코드·링크). hwpx는 서식으로 표현되므로 문자열에서 뺀다."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", t)
    t = t.replace("`", "")
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t


def norm(t):
    t = strip_inline(t)
    t = t.replace("&emsp;", " ").replace(EMSP, " ").replace(" ", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def md_linear(items):
    """MD 항목열 → (태그, 정규화텍스트, 원문, 줄번호) 선형열. 표는 셀 단위로 펼친다."""
    out = []
    for it in items:
        k = it["kind"]
        if k == "excluded":
            continue
        if k in ("h1", "h2", "h3", "h4"):
            out.append((k, norm(it["text"]), it["text"], it["line"]))
        elif k == "para":
            out.append((it.get("sub", "p"), norm(it["text"]), it["text"], it["line"]))
        elif k == "table":
            for r, row in enumerate(it["rows"]):
                for c, cell in enumerate(row):
                    for line in cell.split("<br>"):
                        if norm(line):
                            out.append(("cell[%d,%d]" % (r, c), norm(line),
                                        line, it["line"]))
    return out


def hwpx_linear(units):
    out = []
    for u in units:
        if u["kind"] == "para":
            if norm(u["text"]):
                out.append(("para", norm(u["text"]), u["text"], u["i"]))
        elif u["kind"] == "table":
            for r, row in enumerate(u["rows"]):
                for c, cell in enumerate(row):
                    for line in cell.split("\n"):
                        if norm(line):
                            out.append(("cell[%d,%d]" % (r, c), norm(line),
                                        line, u["i"]))
    return out


def main():
    dump = json.load(open(sys.argv[1], encoding="utf-8"))
    s2 = [x for x in dump if x["sec"] == "section2.xml"]
    # 제1~3장 = 처음부터 '제4장 연구설계' 문단 직전까지
    end = next(n for n, x in enumerate(s2)
               if x["kind"] == "para" and x["text"].strip() == "제4장 연구설계")
    body = s2[:end]

    md = []
    for p in sys.argv[2:]:
        md += md_linear(json.load(open(p, encoding="utf-8")))

    hx = hwpx_linear(body)
    a = [t for _, t, _, _ in md]
    b = [t for _, t, _, _ in hx]

    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    report = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        report.append({
            "op": tag,
            "md": [{"tag": md[i][0], "line": md[i][3], "text": md[i][2]}
                   for i in range(i1, i2)],
            "hwpx": [{"tag": hx[j][0], "para_idx": hx[j][3], "text": hx[j][2]}
                     for j in range(j1, j2)],
        })

    print("MD 항목 %d, hwpx 항목 %d, 차이 블록 %d" % (len(a), len(b), len(report)))
    json.dump(report, open("diff_ch1-3.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for r in report:
        print("--- %s" % r["op"])
        for m in r["md"]:
            print("  MD  L%s %s: %s" % (m["line"], m["tag"], m["text"][:160]))
        for h in r["hwpx"]:
            print("  HWP p%s %s: %s" % (h["para_idx"], h["tag"], h["text"][:160]))


if __name__ == "__main__":
    main()
