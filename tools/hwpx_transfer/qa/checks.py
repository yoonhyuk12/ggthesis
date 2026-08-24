# 제목 1:1, 표 행·열 구조, 제외 규칙 준수, 구판 오염, 인용 표기를 개별 항목으로 점검하는 QA 검사기
"""checks.py — compare.py의 선형 대조를 보완하는 항목별 검사."""
import json
import re
import sys

sys.path.insert(0, ".")
from compare import norm, strip_inline  # noqa: E402

dump = json.load(open("hwpx_dump.json", encoding="utf-8"))
s2 = [x for x in dump if x["sec"] == "section2.xml"]
end = next(n for n, x in enumerate(s2)
           if x["kind"] == "para" and x["text"].strip() == "제4장 연구설계")
body = s2[:end]
hpara = [x for x in body if x["kind"] == "para"]
htbl = [x for x in body if x["kind"] == "table"]
hall_text = "\n".join(
    [x["text"] for x in hpara] +
    ["\n".join("\t".join(r) for r in x["rows"]) for x in htbl])

MDS = [("01_서론", "md_01_서론.json"),
       ("02_이론적배경", "md_02_이론적배경.json"),
       ("03_시스템개발", "md_03_시스템개발.json")]
md = {}
for name, path in MDS:
    md[name] = json.load(open(path, encoding="utf-8"))

out = []
W = out.append

# ---------- 1. 제목 1:1 ----------
W("## 검사 1: 장·절·항 제목 1:1 대조\n")
md_heads = []
for name, _ in MDS:
    for it in md[name]:
        if it["kind"] in ("h1", "h2", "h3", "h4"):
            md_heads.append((name, it["line"], it["kind"], norm(it["text"])))
hset = [norm(p["text"]) for p in hpara]
# hwpx 본문에서 제목 문단을 순서대로 찾는다
cursor, miss, order_ok = 0, [], True
for name, line, kind, text in md_heads:
    try:
        pos = hset.index(text, cursor)
        cursor = pos + 1
    except ValueError:
        if text in hset:
            order_ok = False
            miss.append((name, line, kind, text, "순서 어긋남"))
        else:
            miss.append((name, line, kind, text, "없음"))
W("MD 헤딩 %d개 (h1 %d, h2 %d, h3 %d, h4 %d)" % (
    len(md_heads),
    sum(1 for x in md_heads if x[2] == "h1"),
    sum(1 for x in md_heads if x[2] == "h2"),
    sum(1 for x in md_heads if x[2] == "h3"),
    sum(1 for x in md_heads if x[2] == "h4")))
for name, _ in MDS:
    W("- %s: h2(절) %d개, h3(항) %d개, h4 %d개" % (
        name,
        sum(1 for it in md[name] if it["kind"] == "h2"),
        sum(1 for it in md[name] if it["kind"] == "h3"),
        sum(1 for it in md[name] if it["kind"] == "h4")))
W("")
if miss:
    W("**불일치 %d건**\n" % len(miss))
    for m in miss:
        W("- %s L%d %s `%s` — %s" % m)
else:
    W("불일치 0건 — 순서·문구 전부 일치.")
W("")

# ---------- 3. 표 구조 ----------
W("## 검사 3: 표 행·열 구조 및 셀 대조\n")
md_tables = []
for name, _ in MDS:
    for it in md[name]:
        if it["kind"] == "table":
            md_tables.append((name, it["line"], it["rows"]))
W("MD 표 %d개 (2장 %d, 3장 %d) / hwpx 표 %d개\n" % (
    len(md_tables),
    sum(1 for t in md_tables if t[0] == "02_이론적배경"),
    sum(1 for t in md_tables if t[0] == "03_시스템개발"),
    len(htbl)))
W("| # | MD 위치 | MD 행x열 | hwpx 행x열 | 구조 | 첫 행 | 표본 3셀 |")
W("|---|---|---|---|---|---|---|")
tbl_fail = []
for n, ((name, line, rows), h) in enumerate(zip(md_tables, htbl), 1):
    mr, mc = len(rows), max(len(r) for r in rows)
    hr, hc = h["nrow"], h["ncol"]
    struct = "OK" if (mr, mc) == (hr, hc) else "**불일치**"
    if struct != "OK":
        tbl_fail.append((n, name, line, (mr, mc), (hr, hc)))
    # 첫 행 전체 비교
    first_ok = True
    if hr and hc:
        for c in range(min(mc, hc)):
            mv = norm(rows[0][c]) if c < len(rows[0]) else ""
            hv = norm(h["rows"][0][c].replace("\n", " "))
            if mv != hv:
                first_ok = False
                tbl_fail.append((n, name, line, "첫행 c%d" % c, (mv, hv)))
    # 표본 3셀 (재현 가능한 결정적 선택: 대각선 위치)
    samples, sample_ok = [], True
    for k in range(3):
        r = min(1 + k * max(1, (mr - 1) // 3), mr - 1)
        c = min(k, mc - 1)
        mv = norm(rows[r][c]) if c < len(rows[r]) else ""
        hv = norm(h["rows"][r][c].replace("\n", " ")) if r < hr and c < hc else ""
        samples.append("(%d,%d)" % (r, c))
        if mv != hv:
            sample_ok = False
            tbl_fail.append((n, name, line, "셀(%d,%d)" % (r, c), (mv, hv)))
    W("| %d | %s L%d | %dx%d | %dx%d | %s | %s | %s %s |" % (
        n, name, line, mr, mc, hr, hc, struct,
        "OK" if first_ok else "**불일치**",
        " ".join(samples), "OK" if sample_ok else "**불일치**"))
W("")
if tbl_fail:
    W("**표 불일치 %d건**\n" % len(tbl_fail))
    for f in tbl_fail:
        W("- %s" % (f,))
else:
    W("표 불일치 0건.")
W("")

# ---------- 4. 제외 규칙 준수 ----------
W("## 검사 4: 제외 규칙 준수 (hwpx에 없어야 정상)\n")
W("| MD 위치 | 제외 사유 | 대표 문구 | hwpx 존재 |")
W("|---|---|---|---|")
excl_fail = []
for name, _ in MDS:
    for it in md[name]:
        if it["kind"] != "excluded":
            continue
        if it["reason"] in ("horizontal_rule", "html_tag"):
            continue
        # 제외 블록에서 검색 가능한 대표 문구(가장 긴 텍스트 행)를 뽑는다
        cands = []
        for ln in it["text"].split("\n"):
            t = strip_inline(ln.lstrip("> ").lstrip("#").strip())
            t = re.sub(r"^[\s\-\[\]x|]+", "", t)
            if len(t) >= 20 and not set(t) <= set("─│┌┐└┘├┤┬┴┼↓ "):
                cands.append(t)
        if not cands:
            continue
        probe = max(cands, key=len)[:40]
        present = norm(probe) in norm(hall_text)
        if present:
            excl_fail.append((name, it["line"], it["reason"], probe))
        W("| %s L%d | %s | %s… | %s |" % (
            name, it["line"], it["reason"], probe[:50].replace("|", "/"),
            "**있음(FAIL)**" if present else "없음(OK)"))
W("")
W("제외 규칙 위반 %d건." % len(excl_fail))
W("")

# ---------- 5. 미확정 표시 유지 ----------
W("## 검사 5: 미확정 표시 유지\n")
W("| 표시 | MD 개수 | hwpx 개수 | 판정 |")
W("|---|---|---|---|")
marks = ["[그림 삽입 예정", "[확정 필요", "[DATA PENDING", "[CITE_TODO", "[UNVERIFIED"]
mark_fail = []
for mk in marks:
    mcount = 0
    for name, _ in MDS:
        for it in md[name]:
            if it["kind"] == "excluded":
                continue
            txt = it["text"] if "text" in it else "\n".join(
                "\t".join(r) for r in it.get("rows", []))
            mcount += txt.count(mk)
    hcount = hall_text.count(mk)
    ok = mcount == hcount
    if not ok:
        mark_fail.append((mk, mcount, hcount))
    W("| `%s]` | %d | %d | %s |" % (mk, mcount, hcount,
                                    "OK" if ok else "**불일치**"))
W("")

# ---------- 6. 구판 오염 ----------
W("## 검사 6: 구판(양식) 오염 검사\n")
STALE = ["신호감지이론" , "제 3 항 절약형 혁신 이론", "YOLO-VLM", "절약형 혁신 이론",
         "제 1 절", "제 2 절", "제 1 항", "가. ", "VLM"]
W("| 탐지어 | hwpx 제1~3장 출현 | 판정 |")
W("|---|---|---|")
stale_hits = []
for kw in STALE:
    hits = [p for p in hpara if kw in p["text"]]
    W("| `%s` | %d | %s |" % (kw, len(hits), "확인 필요" if hits else "없음(OK)"))
    if hits:
        stale_hits.append((kw, [(p["i"], p["text"][:90]) for p in hits[:6]]))
W("")
for kw, hs in stale_hits:
    W("- `%s` 출현 위치:" % kw)
    for i, t in hs:
        W("  - p%d: %s" % (i, t))
W("")

# ---------- 7. 인용 표기 표본 ----------
W("## 검사 7: 내주(저자, 연도) 표기 대조\n")
CITE = re.compile(r"\(([^()]{0,60}?,\s*\d{4}[a-z]?(?:\s*;\s*[^()]{0,60}?,\s*\d{4}[a-z]?)*)\)")
md_cites, h_cites = [], []
for name, _ in MDS:
    for it in md[name]:
        if it["kind"] == "excluded":
            continue
        txt = it.get("text", "") or "\n".join("\t".join(r) for r in it.get("rows", []))
        for m in CITE.finditer(strip_inline(txt)):
            md_cites.append((name, it["line"], m.group(0)))
for p in hpara:
    for m in CITE.finditer(p["text"]):
        h_cites.append((p["i"], m.group(0)))
for t in htbl:
    for r in t["rows"]:
        for c in r:
            for m in CITE.finditer(c):
                h_cites.append((t["i"], m.group(0)))
W("MD 내주 %d개 / hwpx 내주 %d개\n" % (len(md_cites), len(h_cites)))
from collections import Counter  # noqa: E402
mc, hc2 = Counter(norm(x[2]) for x in md_cites), Counter(norm(x[1]) for x in h_cites)
cite_diff = []
for k in set(mc) | set(hc2):
    if mc[k] != hc2[k]:
        cite_diff.append((k, mc[k], hc2[k]))
# 표본 10곳 (MD 등장 순서 균등 간격 — 결정적)
W("표본 10곳 (MD 등장 순서 균등 간격):\n")
W("| # | MD 위치 | MD 내주 | hwpx 동일 문자열 개수 | 판정 |")
W("|---|---|---|---|---|")
step = max(1, len(md_cites) // 10)
for n, idx in enumerate(range(0, len(md_cites), step)[:10] if hasattr(range(0, 1), "__getitem__") else [], 1):
    pass
sel = list(range(0, len(md_cites), step))[:10]
for n, idx in enumerate(sel, 1):
    name, line, cite = md_cites[idx]
    k = norm(cite)
    W("| %d | %s L%d | `%s` | %d | %s |" % (
        n, name, line, cite.replace("|", "/"), hc2[k],
        "OK" if hc2[k] >= 1 else "**없음**"))
W("")
if cite_diff:
    W("**전수 빈도 불일치 %d종**\n" % len(cite_diff))
    for k, a, b in sorted(cite_diff):
        W("- `%s` — MD %d회 / hwpx %d회" % (k, a, b))
else:
    W("전수 빈도 대조: 내주 문자열 종류·횟수 완전 일치.")

open("checks_out.md", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
