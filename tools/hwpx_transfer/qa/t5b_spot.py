# 표별 무작위 3셀 표본과 첫 행을 원문 그대로 뽑고, &emsp; 변환 코드포인트를 확인한다
"""t5b_spot.py — 표 표본 점검 + 공백 문자 코드포인트 확인.

셸 인코딩 훼손을 피하려고 파일 스크립트로 둔다. seed 고정으로 재현 가능하다.
"""

import json
import random
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
random.seed(20260725)

FW = "　"      # IDEOGRAPHIC SPACE (전각 공백)
EMSP = " "    # EM SPACE
NBSP = " "

md = json.load(open("tools/hwpx_transfer/qa/t5b_md_items.json", encoding="utf-8"))
hw = json.load(open("tools/hwpx_transfer/qa/t5b_final.json", encoding="utf-8"))["section2"]
rg = json.load(open("tools/hwpx_transfer/qa/t5b_ranges.json", encoding="utf-8"))


def canon(s):
    s = s.replace("`", "").replace("&emsp;", FW).replace("<br>", "\n")
    s = s.replace(EMSP, FW).replace(NBSP, " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def show(s):
    return s.replace("\n", "\\n").replace(FW, "[전각]").replace(EMSP, "[EM]")


def expand(rows, spans):
    out = []
    for row, srow in zip(rows, spans):
        cells = []
        for cell, (cs, rs) in zip(row, srow):
            cells.append(cell)
            cells.extend([""] * (cs - 1))
        out.append(cells)
    return out


ok = bad = 0
for name, (k, lo, hi) in rg.items():
    items = md[k]
    mts, caps = [], []
    for i, it in enumerate(items):
        if it["kind"] != "table":
            continue
        mts.append(it)
        cap = None
        for j in range(i - 1, max(-1, i - 3), -1):
            if items[j]["kind"] == "table_caption":
                cap = items[j]["text"]
                break
            if items[j]["kind"] != "p":
                break
        caps.append(cap)
    hts = [(lo + j, x) for j, x in enumerate(hw[lo:hi]) if x["kind"] == "table"]
    if not mts:
        continue
    print("### %s" % name)
    for n, (mt, (idx, ht), cap) in enumerate(zip(mts, hts, caps), 1):
        g = expand(ht["rows"], ht["spans"])
        off = 1 if cap else 0
        print("  표%-2d (hwpx idx %d) %dx%d" % (n, idx, ht["rowCnt"], ht["colCnt"]))
        print("     첫 행(hwpx 실물): %s" % show(" | ".join(g[0]))[:170])
        coords = [(r, c) for r in range(len(mt["rows"]))
                  for c in range(len(mt["rows"][r]))]
        for r, c in random.sample(coords, min(3, len(coords))):
            m = canon(mt["rows"][r][c])
            h = canon(g[r + off][c]) if c < len(g[r + off]) else "<없음>"
            same = m == h
            ok += same
            bad += not same
            print("     r%-2d c%-2d %s MD=%r  HWPX=%r"
                  % (r, c, "일치" if same else "*불일치*",
                     show(m)[:60] or "(빈 셀)", show(h)[:60] or "(빈 셀)"))
    print()

print("무작위 셀 표본: 일치 %d / 불일치 %d" % (ok, bad))
print()
print("== &emsp; 변환 코드포인트 확인 (부록1 Part A 보기 문단)")
for i, it in enumerate(hw[425:445], 425):
    if it["kind"] != "para":
        continue
    for ch in set(it["text"]):
        if ch in (FW, EMSP, NBSP):
            print("  idx %d: %s (U+%04X) — %s | %s"
                  % (i, unicodedata.name(ch), ord(ch), show(it["text"])[:70],
                     "전각(U+3000)" if ch == FW else "EM SPACE(U+2003)"))
            break
