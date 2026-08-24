# 완성본 hwpx를 zipfile로 직접 열어 문단·표를 문서 순서대로 JSON으로 덤프하는 QA 전용 추출기
"""dump_hwpx.py — 조립기와 독립적으로 hwpx 본문 구조를 추출한다.

산출: [{"kind":"para","sec":..,"i":..,"text":..,"style":..},
       {"kind":"table","sec":..,"i":..,"rows":[[cell,...],...],"nrow":..,"ncol":..}]
표 셀 텍스트는 셀 내 문단을 개행으로 이어 붙인다.
zipfile + ElementTree만 사용.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def runs_text(p):
    """hp:p 직속 run의 텍스트만 (중첩 표/ctrl 제외)."""
    out = []
    for run in p.findall(HP + "run"):
        for child in run:
            if child.tag in (HP + "tbl", HP + "ctrl"):
                continue
            out.append("".join(child.itertext()))
            if child.tail:
                out.append(child.tail)
    return "".join(out)


def cell_text(tc):
    sub = tc.find(HP + "subList")
    if sub is None:
        return ""
    lines = []
    for cp in sub.findall(HP + "p"):
        lines.append(runs_text(cp))
    return "\n".join(lines).strip()


def table_grid(tbl):
    """colSpan/rowSpan을 반영해 격자로 펼친 셀 텍스트 행렬을 만든다."""
    trs = tbl.findall(HP + "tr")
    grid = {}
    maxc = 0
    for r, tr in enumerate(trs):
        c = 0
        for tc in tr.findall(HP + "tc"):
            while (r, c) in grid:
                c += 1
            span = tc.find(HP + "cellSpan")
            cs = int(span.get("colSpan", "1")) if span is not None else 1
            rs = int(span.get("rowSpan", "1")) if span is not None else 1
            txt = cell_text(tc)
            for dr in range(rs):
                for dc in range(cs):
                    grid[(r + dr, c + dc)] = txt if (dr == 0 and dc == 0) else ""
            c += cs
            maxc = max(maxc, c)
    rows = []
    for r in range(len(trs)):
        rows.append([grid.get((r, c), "") for c in range(maxc)])
    return rows


def walk(p, sec, idx, out):
    txt = runs_text(p)
    style = p.get("paraPrIDRef", "")
    if txt.strip():
        out.append({"kind": "para", "sec": sec, "i": idx, "text": txt, "style": style})
    for run in p.findall(HP + "run"):
        for tbl in run.findall(HP + "tbl"):
            rows = table_grid(tbl)
            out.append({"kind": "table", "sec": sec, "i": idx,
                        "rows": rows, "nrow": len(rows),
                        "ncol": max((len(r) for r in rows), default=0)})
            # 셀 안 중첩 표는 이 논문 구조상 없으나 방어적으로 확인
            for tr in tbl.findall(HP + "tr"):
                for tc in tr.findall(HP + "tc"):
                    sub = tc.find(HP + "subList")
                    if sub is None:
                        continue
                    for cp in sub.findall(HP + "p"):
                        for r2 in cp.findall(HP + "run"):
                            for t2 in r2.findall(HP + "tbl"):
                                out.append({"kind": "nested_table", "sec": sec, "i": idx,
                                            "rows": table_grid(t2)})


def dump(path):
    out = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n)]
        names.sort(key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
        for name in names:
            root = ET.fromstring(zf.read(name))
            sec = name.split("/")[-1]
            for idx, p in enumerate(root.findall(HP + "p")):
                walk(p, sec, idx, out)
    return out


if __name__ == "__main__":
    items = dump(sys.argv[1])
    json.dump(items, open(sys.argv[2], "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("units:", len(items),
          "paras:", sum(1 for x in items if x["kind"] == "para"),
          "tables:", sum(1 for x in items if x["kind"] == "table"),
          "nested:", sum(1 for x in items if x["kind"] == "nested_table"))
