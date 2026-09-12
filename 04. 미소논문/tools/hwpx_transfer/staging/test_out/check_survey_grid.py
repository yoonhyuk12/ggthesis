# -*- coding: utf-8 -*-
"""설문 표 격자 정합 검사 — 모든 행의 cellSz 폭 합 = 표 폭, colAddr/colSpan이 격자와 일치.

어긋나면 한글이 행을 재배치한다(과거 사고). 표준 라이브러리만 쓴다.
"""
import re, sys, zipfile, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from blocks_to_hwpx import tbl_spans, tr_spans, tc_spans, cell_addr, para_plain_text

# 설문 틀만 고른다 — 본문 표가 섞이지 않도록 양식 고유 문구로 판정한다.
TARGETS = ("안녕하십니까", "2. 사전 설문 (", "전혀그렇지않다", "매우미흡")

path = sys.argv[1]
s2 = zipfile.ZipFile(path).read("Contents/section2.xml").decode("utf-8")
ok = bad = 0
for a, b in tbl_spans(s2):
    tbl = s2[a:b]
    full = para_plain_text(tbl)
    if not any(t in full for t in TARGETS):
        continue
    text = full[:40]
    head = re.match(r"<hp:tbl[^>]*>", tbl).group(0)
    row_cnt = int(re.search(r'rowCnt="(\d+)"', head).group(1))
    col_cnt = int(re.search(r'colCnt="(\d+)"', head).group(1))
    tbl_w = int(re.search(r'<hp:sz width="(\d+)"', tbl).group(1))
    grid = {}
    col_w, problems = {}, []
    rows = tr_spans(tbl)
    for ri, (ra, rb) in enumerate(rows):
        tr = tbl[ra:rb]
        cells = [tr[ca:cb] for ca, cb in tc_spans(tr)]
        for tc in cells:
            col, row, cs, rs, w, h = cell_addr(tc)
            if row != ri:
                problems.append("r%d 셀의 rowAddr=%d" % (ri, row))
            for dr in range(rs):
                for dc in range(cs):
                    key = (ri + dr, col + dc)
                    if key in grid:
                        problems.append("격자 중복 %s" % (key,))
                    grid[key] = w if cs == 1 else None
            if cs == 1:
                if col in col_w and col_w[col] != w:
                    problems.append("열 %d 폭 불일치 %d vs %d" % (col, col_w[col], w))
                col_w[col] = w
        # 이 행이 그리드 전 열을 덮으면 폭 합이 표 폭과 같아야 한다
        covered = sum(cell_addr(tc)[2] for tc in cells)
        wsum = sum(cell_addr(tc)[4] for tc in cells)
        if covered == col_cnt and wsum != tbl_w:
            problems.append("r%d 폭 합 %d != 표 폭 %d" % (ri, wsum, tbl_w))
    for r in range(row_cnt):
        for c in range(col_cnt):
            if (r, c) not in grid:
                problems.append("격자 구멍 (%d,%d)" % (r, c))
    span_w = sum(col_w.get(c, 0) for c in range(col_cnt))
    label = text.replace("\n", " ")[:28]
    if problems:
        bad += 1
        print("FAIL %-30s %dx%d w=%d : %s" % (label, row_cnt, col_cnt, tbl_w,
                                              "; ".join(problems[:4])))
    else:
        ok += 1
        note = "열폭합=%d" % span_w if span_w else "단일 셀"
        print("OK   %-30s %dx%d 표폭=%-6d %s%s" % (
            label, row_cnt, col_cnt, tbl_w, note,
            "" if (not span_w or span_w == tbl_w) else "  (!! 표 폭과 다름)"))
print("설문 표 %d개 — OK %d / FAIL %d" % (ok + bad, ok, bad))
sys.exit(1 if bad else 0)
