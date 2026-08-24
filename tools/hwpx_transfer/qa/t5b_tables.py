# MD 표와 hwpx 표를 순서대로 짝지어 행·열 수와 모든 셀(빈 셀 포함)을 전수 대조한다
"""t5b_tables.py — 표 구조 전수 대조.

캡션은 조립기가 표 첫 행(가로 병합 셀)으로 넣었다. 따라서 hwpx 표의 행 수는
MD 표 행 수 + (캡션 있으면 1)이어야 한다. colSpan을 펼쳐 열 수를 맞춘 뒤
빈 셀까지 포함해 모든 셀을 비교한다.
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

FW = "　"
EMSPACE = " "
NBSP = " "

md_all = json.load(open("tools/hwpx_transfer/qa/t5b_md_items.json", encoding="utf-8"))
hw = json.load(open("tools/hwpx_transfer/qa/t5b_final.json", encoding="utf-8"))["section2"]
ranges = json.load(open("tools/hwpx_transfer/qa/t5b_ranges.json", encoding="utf-8"))


def canon(s):
    s = s.replace("`", "").replace("&emsp;", FW).replace("<br>", "\n")
    s = s.replace(EMSPACE, FW).replace(NBSP, " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def expand(rows, spans):
    """colSpan을 펼쳐 논리 격자로 만든다(rowSpan은 세로 병합이라 행 길이만 영향)."""
    out = []
    for row, srow in zip(rows, spans):
        cells = []
        for cell, (cs, rs) in zip(row, srow):
            cells.append(cell)
            for _ in range(cs - 1):
                cells.append(None)          # 가로 병합으로 흡수된 자리
        out.append(cells)
    return out


fails = []
summary = []

for name, (mdkey, lo, hi) in ranges.items():
    md_tables = [it for it in md_all[mdkey] if it["kind"] == "table"]
    md_caps = []
    # MD에서 표 바로 앞의 table_caption을 찾아둔다
    items = md_all[mdkey]
    for i, it in enumerate(items):
        if it["kind"] != "table":
            continue
        cap = None
        for j in range(i - 1, max(-1, i - 3), -1):
            if items[j]["kind"] == "table_caption":
                cap = items[j]["text"]
                break
            if items[j]["kind"] != "p":
                break
        md_caps.append(cap)
    hw_tables = [(lo + k, it) for k, it in enumerate(hw[lo:hi]) if it["kind"] == "table"]

    print("### %s — MD 표 %d개, hwpx 표 %d개" % (name, len(md_tables), len(hw_tables)))
    if len(md_tables) != len(hw_tables):
        fails.append("%s: 표 개수 불일치 MD %d vs HWPX %d" % (name, len(md_tables), len(hw_tables)))
        continue
    for n, (mt, (idx, ht), cap) in enumerate(zip(md_tables, hw_tables, md_caps), 1):
        grid = expand(ht["rows"], ht["spans"])
        exp_rows = len(mt["rows"]) + (1 if cap else 0)
        exp_cols = max(len(r) for r in mt["rows"])
        got_rows = len(grid)
        got_cols = max(len(r) for r in grid)
        ok_dim = (exp_rows == got_rows == ht["rowCnt"]) and (exp_cols == got_cols == ht["colCnt"])
        status = "OK " if ok_dim else "DIM"
        print("  [%s] 표%d (hwpx idx %d) 기대 %dx%d / 실제 %dx%d (rowCnt=%s colCnt=%s) 캡션=%s"
              % (status, n, idx, exp_rows, exp_cols, got_rows, got_cols,
                 ht["rowCnt"], ht["colCnt"], (cap or "—")[:40]))
        if not ok_dim:
            fails.append("%s 표%d(idx %d): 기대 %dx%d, 실제 %dx%d"
                         % (name, n, idx, exp_rows, exp_cols, got_rows, got_cols))
            continue
        # 캡션 행 확인
        off = 0
        if cap:
            capcell = canon(grid[0][0] or "")
            if capcell != canon(cap):
                fails.append("%s 표%d(idx %d) 캡션행 불일치: MD %r vs HWPX %r"
                             % (name, n, idx, cap, grid[0][0]))
            off = 1
        # 전 셀 대조 (빈 셀 포함)
        for r, mrow in enumerate(mt["rows"]):
            hrow = grid[r + off]
            for c, mcell in enumerate(mrow):
                hcell = hrow[c] if c < len(hrow) else "<없음>"
                if hcell is None:
                    hcell = ""              # 가로 병합 흡수 = 원본이 빈 셀이어야 함
                if canon(mcell) != canon(hcell):
                    fails.append("%s 표%d(idx %d) r%d c%d: MD %r vs HWPX %r"
                                 % (name, n, idx, r, c, mcell[:80], str(hcell)[:80]))
    print()

print("== 표 대조 실패: %d건" % len(fails))
for f in fails:
    print("  - " + f)
