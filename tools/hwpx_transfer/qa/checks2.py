# 캡션 병합행 구조를 반영한 표 대조와, 제목 문단 한정 구판 오염 탐지를 수행하는 보정 검사기
"""checks2.py — checks.py의 표 검사(캡션 병합행 미반영)와 구판 탐지(본문 오탐)를 바로잡은 재검사."""
import json
import random
import re
import sys

sys.path.insert(0, ".")
from compare import norm  # noqa: E402

dump = json.load(open("hwpx_dump.json", encoding="utf-8"))
s2 = [x for x in dump if x["sec"] == "section2.xml"]
end = next(n for n, x in enumerate(s2)
           if x["kind"] == "para" and x["text"].strip() == "제4장 연구설계")
body = s2[:end]
hpara = [x for x in body if x["kind"] == "para"]
htbl = [x for x in body if x["kind"] == "table"]

MDS = [("02_이론적배경", "md_02_이론적배경.json"),
       ("03_시스템개발", "md_03_시스템개발.json")]
md_tables, md_caps = [], []
for name, path in MDS:
    items = json.load(open(path, encoding="utf-8"))
    last_cap = None
    for it in items:
        if it["kind"] == "para" and it.get("sub") == "table_caption":
            last_cap = it["text"]
        elif it["kind"] == "table":
            md_tables.append((name, it["line"], it["rows"]))
            md_caps.append(last_cap)
            last_cap = None

out = []
W = out.append

W("## 검사 3 (재검사): 표 행·열 구조 및 셀 대조\n")
W("hwpx 표는 **캡션을 병합된 첫 행으로 포함**하는 구조다"
  "(row0 = `<표 N-x> …` 병합셀, row1~ = MD 표의 헤더·데이터 행). "
  "따라서 기대 행수 = MD 행수 + 1이다. 아래는 이 구조를 반영한 대조 결과다.\n")
W("| # | 캡션 | MD 행x열 | hwpx 행x열 | 구조 | 캡션행 | 첫 행(헤더) 전체 | 무작위 3셀 |")
W("|---|---|---|---|---|---|---|---|")

rng = random.Random(20260725)   # 재현 가능한 무작위 셀 선택
fails = []
sample_log = []
for n, ((name, line, rows), cap, h) in enumerate(zip(md_tables, md_caps, htbl), 1):
    mr, mc = len(rows), max(len(r) for r in rows)
    hr, hc = h["nrow"], h["ncol"]
    struct = (mr + 1, mc) == (hr, hc)
    if not struct:
        fails.append("표%d(%s L%d) 구조: MD %dx%d(+캡션행=%dx%d) vs hwpx %dx%d"
                     % (n, name, line, mr, mc, mr + 1, mc, hr, hc))

    cap_hw = h["rows"][0][0].replace("\n", " ")
    cap_ok = norm(cap or "") == norm(cap_hw)
    if not cap_ok:
        fails.append("표%d 캡션: MD %r vs hwpx %r" % (n, cap, cap_hw))
    merged_ok = all(not c.strip() for c in h["rows"][0][1:])
    if not merged_ok:
        fails.append("표%d 캡션행이 병합되지 않음: %r" % (n, h["rows"][0]))

    # 첫 행(MD 헤더) 전체 대조 → hwpx row 1
    first_ok = True
    for c in range(mc):
        mv = norm(rows[0][c]) if c < len(rows[0]) else ""
        hv = norm(h["rows"][1][c].replace("\n", " ")) if hr > 1 and c < hc else ""
        if mv != hv:
            first_ok = False
            fails.append("표%d 헤더 c%d: MD %r vs hwpx %r" % (n, c, mv, hv))

    # 무작위 3셀 (헤더 제외 데이터 영역)
    cells = [(r, c) for r in range(1, mr) for c in range(mc) if c < len(rows[r])]
    pick = rng.sample(cells, min(3, len(cells)))
    samp_ok = True
    for (r, c) in pick:
        mv = norm(rows[r][c])
        hv = norm(h["rows"][r + 1][c].replace("\n", " ")) if r + 1 < hr and c < hc else ""
        if mv != hv:
            samp_ok = False
            fails.append("표%d 셀(%d,%d): MD %r vs hwpx %r" % (n, r, c, mv, hv))
        sample_log.append((n, r, c, mv, hv, mv == hv))
    W("| %d | %s | %dx%d | %dx%d | %s | %s | %s | %s %s |" % (
        n, (cap or "(없음)").split(">")[0] + ">", mr, mc, hr, hc,
        "OK" if struct else "**FAIL**",
        "OK" if (cap_ok and merged_ok) else "**FAIL**",
        "OK" if first_ok else "**FAIL**",
        " ".join("(%d,%d)" % p for p in pick), "OK" if samp_ok else "**FAIL**"))
W("")
W("표 검사 불일치 **%d건**." % len(fails))
for f in fails:
    W("- " + f)
W("")
W("<details><summary>무작위 3셀 표본 전체 (seed=20260725)</summary>\n")
W("| 표 | 셀(MD r,c) | MD 원문 | hwpx 실물 | 일치 |")
W("|---|---|---|---|---|")
for n, r, c, mv, hv, ok in sample_log:
    W("| %d | (%d,%d) | %s | %s | %s |" % (
        n, r, c, mv[:60].replace("|", "/"), hv[:60].replace("|", "/"),
        "O" if ok else "**X**"))
W("\n</details>\n")

# ---------- 검사 6 재검사: 제목 문단 한정 ----------
W("## 검사 6 (재검사): 구판(양식) 오염 — 제목 문단 한정\n")
md_all = ""
for p in ["md_01_서론.json"] + [x[1] for x in MDS]:
    for it in json.load(open(p, encoding="utf-8")):
        if it["kind"] == "excluded":
            continue
        md_all += (it.get("text", "") or
                   "\n".join("\t".join(r) for r in it.get("rows", []))) + "\n"

# 제목 문단 = 장(style 57) + '제N절/제N항/숫자.' 로 시작하는 문단
HEAD = re.compile(r"^\s*(제\s*\d+\s*[장절항]|[0-9]+\.\s)")
heads = [p for p in hpara if p["style"] == "57" or HEAD.match(p["text"])]
W("hwpx 제1~3장 제목 문단 %d개를 대상으로 구판 절·항 제목 텍스트를 탐지했다.\n" % len(heads))
W("| 구판 탐지어 | 제목 문단 출현 | 본문 출현 | MD에도 존재 | 판정 |")
W("|---|---|---|---|---|")
STALE = ["신호감지이론", "제 3 항 절약형 혁신 이론", "절약형 혁신 이론",
         "YOLO-VLM", "기술수용모델(TAM) 이론", "알람 피로도 이론",
         "제 1 절", "제 2 절", "제 3 절", "제 1 항", "제 2 항",
         "연구의 필요성 및 목적", "연구방법 및 범위"]
stale_fail = []
for kw in STALE:
    inhead = sum(1 for p in heads if kw in p["text"])
    inbody = sum(1 for p in hpara if kw in p["text"])
    inmd = md_all.count(kw)
    if inhead > 0:
        verdict = "**구판 제목 의심**"
        stale_fail.append(kw)
    elif inbody > 0 and inmd == 0:
        verdict = "**MD 없는 본문 텍스트**"
        stale_fail.append(kw)
    elif inbody > 0:
        verdict = "본문 정상(MD 일치)"
    else:
        verdict = "없음(OK)"
    W("| `%s` | %d | %d | %d | %s |" % (kw, inhead, inbody, inmd, verdict))
W("")
W("구판 오염 의심 **%d건**.%s" % (len(stale_fail),
                                "" if not stale_fail else " → " + ", ".join(stale_fail)))
W("")
W("hwpx 제1~3장 제목 문단 전체 목록:\n")
W("```")
for p in heads:
    W("p%-4d %s" % (p["i"], p["text"].strip()))
W("```")

open("checks2_out.md", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
