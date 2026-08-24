# 정규화 없이 문자 단위로 MD↔hwpx 텍스트를 대조하고, 전각공백·줄바꿈 변환을 표본 검사한다
"""t5b_exact.py — 문자 단위 정밀 대조.

t5b_compare.py는 공백을 정규화해 정렬한다. 이 스크립트는 정렬 결과를 다시
문자 단위로 비교해 (a) 들여쓰기 이외의 공백 차이, (b) &emsp;→전각공백,
(c) <br>→줄바꿈 변환이 실제로 이루어졌는지 확인한다.
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

FW = "　"     # 전각 공백
NBSP = " "

md_all = json.load(open("tools/hwpx_transfer/qa/t5b_md_items.json", encoding="utf-8"))
hw = json.load(open("tools/hwpx_transfer/qa/t5b_final.json", encoding="utf-8"))["section2"]
ranges = json.load(open("tools/hwpx_transfer/qa/t5b_ranges.json", encoding="utf-8"))


def md_units(items):
    out = []
    for it in items:
        if it["kind"] == "table":
            for r, row in enumerate(it["rows"]):
                for c, cell in enumerate(row):
                    out.append(("cell", cell, "L%s r%d c%d" % (it["line"], r, c)))
        else:
            out.append((it["kind"], it["text"], "L%s" % it["line"]))
    return out


def hw_units(items, base):
    out = []
    for k, it in enumerate(items):
        if it["kind"] == "table":
            for r, row in enumerate(it["rows"]):
                for c, cell in enumerate(row):
                    out.append(("cell", cell, "idx%d r%d c%d" % (base + k, r, c)))
        else:
            out.append(("para", it["text"], "idx%d" % (base + k)))
    return out


def canon(s, is_cell):
    """비교용 표준화: 조립 계약상 허용된 변환만 되돌린다."""
    s = s.replace("`", "")                 # 인라인 백틱 제거(계약)
    s = s.replace("&emsp;", FW)            # &emsp; → 전각공백(계약)
    if is_cell:
        s = s.replace("<br>", "\n")        # 셀 내 <br> → 줄바꿈(계약)
    s = s.replace(NBSP, " ")
    return s


problems = []
emsp_checked = []
br_checked = []

for name, (mdkey, lo, hi) in ranges.items():
    m = md_units(md_all[mdkey])
    h = hw_units(hw[lo:hi], lo)
    # 캡션-첫행 병합 설계 때문에 셀 좌표는 어긋난다. 텍스트 단위 순서로 짝을 만든다.
    def flat(units, cellsplit):
        out = []
        for kind, text, loc in units:
            t = canon(text, kind == "cell")
            if not t.strip():
                continue
            out.append((kind, t, loc))
        return out
    fm, fh = flat(m, True), flat(h, False)
    if len(fm) != len(fh):
        problems.append("%s: 단위 수 불일치 MD %d vs HWPX %d" % (name, len(fm), len(fh)))
        continue
    for (mk, mt, ml), (hk, ht, hl) in zip(fm, fh):
        hs = ht
        # hwpx 본문 문단은 첫 글자 앞에 들여쓰기용 공백/전각공백이 붙을 수 있다
        stripped = hs.lstrip(" " + FW + NBSP)
        if mt == hs or mt == stripped or mt.strip() == hs.strip():
            pass
        else:
            problems.append("%s | MD %s: %r\n            HWPX %s: %r"
                            % (name, ml, mt[:160], hl, hs[:160]))
        if FW in mt:
            emsp_checked.append((name, ml, hl, FW in hs, hs[:80]))
        if "\n" in mt:
            br_checked.append((name, ml, hl, "\n" in hs, hs.replace("\n", "\\n")[:100]))

print("== 문자 단위 불일치: %d건" % len(problems))
for p in problems:
    print("  - " + p)
print()
print("== 전각공백(&emsp; 변환) 대상 단위: %d, 그중 hwpx에 전각공백 존재: %d"
      % (len(emsp_checked), sum(1 for x in emsp_checked if x[3])))
for x in emsp_checked:
    print("   %s MD %s -> HWPX %s  전각공백=%s  %r" % (x[0], x[1], x[2], x[3], x[4]))
print()
print("== 셀 내 줄바꿈(<br> 변환) 대상 단위: %d, 그중 hwpx에 줄바꿈 존재: %d"
      % (len(br_checked), sum(1 for x in br_checked if x[3])))
for x in br_checked:
    print("   %s MD %s -> HWPX %s  줄바꿈=%s  %r" % (x[0], x[1], x[2], x[3], x[4]))
