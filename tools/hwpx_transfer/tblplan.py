#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tblplan.py — hwpx 표 쪽맞춤 판정기.

hwpx 의 각 섹션에서 `hp:secPr/hp:pagePr` 로 본문 높이·본문 폭을 유도하고,
최상위 표(`hp:tbl`)마다 행 높이 합(`hp:cellSz@height`, 그 행에서 시작하며
`rowSpan==1` 인 셀의 최댓값)을 본문 높이와 비교해 `fits` 를 판정한다.
판정 결과에 `.claude/rules/hwpx-output-verification.md` 의 표 쪽 넘김 3단계
권고를 붙여 사람이 읽는 표와 JSON 으로 출력한다.

XML 은 표준 라이브러리 `xml.etree.ElementTree` 로만 파싱한다(정규식 파싱 금지).

사용법:
    python tools/hwpx_transfer/tblplan.py <hwpx> [--json <out.json>] [--section N]
    python tools/hwpx_transfer/tblplan.py --selftest
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import zipfile
from xml.etree import ElementTree as ET

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"

P = f"{{{HP}}}p"
TBL = f"{{{HP}}}tbl"
TR = f"{{{HP}}}tr"
TC = f"{{{HP}}}tc"
T = f"{{{HP}}}t"
SECPR = f"{{{HP}}}secPr"
PAGEPR = f"{{{HP}}}pagePr"
MARGIN = f"{{{HP}}}margin"
CELLADDR = f"{{{HP}}}cellAddr"
CELLSPAN = f"{{{HP}}}cellSpan"
CELLSZ = f"{{{HP}}}cellSz"
SZ = f"{{{HP}}}sz"

HEADER_NOTE = (
    "판정 범위: 표를 새 쪽 맨 위에 두었을 때 한 쪽에 들어가는지(단독 쪽맞춤)만 계산한다.\n"
    "           '현재 위치에서 남은 공간에 들어가는가'는 실제 조판 없이는 알 수 없으므로 판정하지 않는다.\n"
    "단위: HWPUNIT(1/7200 inch). 본문 높이 = pagePr height - margin(top+bottom+header+footer).\n"
    "      본문 폭  = pagePr width - margin(left+right+gutter)."
)

REC_OK = "OK"
REC_NOT_FITS = (
    "단독으로 한 쪽 초과: ② 열 폭·행 높이 축소 검토 → ③ pageBreak=TABLE + repeatHeader=1"
)


# ---------------------------------------------------------------- 공용 유틸


def _int_attr(elem, name, default=0):
    """정수 속성을 읽는다. 없거나 숫자가 아니면 default."""
    if elem is None:
        return default
    raw = elem.get(name)
    if raw is None:
        return default
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _cell_text(tc, limit=30):
    """셀 안의 모든 hp:t 를 이어 붙여 미리보기 문자열을 만든다."""
    if tc is None:
        return ""
    parts = [(node.text or "") for node in tc.iter(T)]
    text = " ".join("".join(parts).split())
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


# ---------------------------------------------------------------- 페이지 기하


def page_geometry(sec_root):
    """섹션 루트에서 첫 hp:pagePr 를 찾아 본문 높이·폭을 유도한다."""
    pagepr = None
    for secpr in sec_root.iter(SECPR):
        found = secpr.find(PAGEPR)
        if found is not None:
            pagepr = found
            break
    if pagepr is None:
        for cand in sec_root.iter(PAGEPR):
            pagepr = cand
            break
    if pagepr is None:
        return None

    margin = pagepr.find(MARGIN)
    geo = {
        "page_width": _int_attr(pagepr, "width"),
        "page_height": _int_attr(pagepr, "height"),
        "landscape": pagepr.get("landscape"),
        "margin_top": _int_attr(margin, "top"),
        "margin_bottom": _int_attr(margin, "bottom"),
        "margin_left": _int_attr(margin, "left"),
        "margin_right": _int_attr(margin, "right"),
        "margin_header": _int_attr(margin, "header"),
        "margin_footer": _int_attr(margin, "footer"),
        "margin_gutter": _int_attr(margin, "gutter"),
    }
    geo["body_height"] = (
        geo["page_height"]
        - geo["margin_top"]
        - geo["margin_bottom"]
        - geo["margin_header"]
        - geo["margin_footer"]
    )
    geo["body_width"] = (
        geo["page_width"]
        - geo["margin_left"]
        - geo["margin_right"]
        - geo["margin_gutter"]
    )
    return geo


# ---------------------------------------------------------------- 표 분석


def analyze_table(tbl, doc_idx, section, para_idx, geo):
    """최상위 표 하나를 판정한다."""
    rows_meta = []           # rowAddr -> {"height":…, "estimated":bool}
    row_widths = {}          # rowAddr -> 그 행에서 시작하는 셀 폭 합
    row_colspan = {}         # rowAddr -> 그 행에서 시작하는 셀 colSpan 합
    spanning = {}            # rowAddr -> [(height, rowSpan), …]  (rowSpan>1 인 셀)
    exact = {}               # rowAddr -> [height, …]             (rowSpan==1 인 셀)

    trs = tbl.findall(TR)
    for tr_pos, tr in enumerate(trs):
        for tc in tr.findall(TC):
            addr = tc.find(CELLADDR)
            span = tc.find(CELLSPAN)
            size = tc.find(CELLSZ)
            row_addr = _int_attr(addr, "rowAddr", tr_pos)
            row_span = _int_attr(span, "rowSpan", 1) or 1
            col_span = _int_attr(span, "colSpan", 1) or 1
            height = _int_attr(size, "height", 0)
            width = _int_attr(size, "width", 0)

            if row_span == 1:
                exact.setdefault(row_addr, []).append(height)
            else:
                spanning.setdefault(row_addr, []).append((height, row_span))
            row_widths[row_addr] = row_widths.get(row_addr, 0) + width
            row_colspan[row_addr] = row_colspan.get(row_addr, 0) + col_span

    row_cnt_attr = _int_attr(tbl, "rowCnt", 0)
    col_cnt_attr = _int_attr(tbl, "colCnt", 0)
    max_addr = max(
        list(exact.keys()) + list(spanning.keys()) + [len(trs) - 1, row_cnt_attr - 1]
    )
    row_cnt = max_addr + 1

    height_sum = 0
    rows_missing = []
    rows_estimated = []
    for r in range(row_cnt):
        if exact.get(r):
            h = max(exact[r])
            rows_meta.append({"row": r, "height": h, "estimated": False})
            height_sum += h
        elif spanning.get(r):
            # 그 행에서 시작하는 rowSpan==1 셀이 없다 — 병합 셀 높이를 균등 분할해 추정한다.
            h = max(math.ceil(hh / rs) for hh, rs in spanning[r])
            rows_meta.append({"row": r, "height": h, "estimated": True})
            rows_estimated.append(r)
            height_sum += h
        else:
            # 그 행에서 시작하는 셀 자체가 없다(위 행의 rowSpan 이 덮는 행).
            rows_meta.append({"row": r, "height": None, "estimated": False})
            rows_missing.append(r)

    # 열 폭 합: colSpan 합이 colCnt 와 맞는 첫 행을 쓴다(없으면 폭 합의 최댓값).
    width_sum = None
    width_row = None
    for r in range(row_cnt):
        if col_cnt_attr and row_colspan.get(r) == col_cnt_attr:
            width_sum = row_widths[r]
            width_row = r
            break
    if width_sum is None and row_widths:
        width_row, width_sum = max(row_widths.items(), key=lambda kv: kv[1])

    declared = tbl.find(SZ)
    declared_h = _int_attr(declared, "height", 0) if declared is not None else None
    declared_w = _int_attr(declared, "width", 0) if declared is not None else None

    page_break = tbl.get("pageBreak")
    repeat_header = tbl.get("repeatHeader")

    body_height = geo["body_height"] if geo else None
    body_width = geo["body_width"] if geo else None
    fits = None if body_height is None else (height_sum <= body_height)

    if fits is None:
        recommendation = "판정 불가: 섹션에서 pagePr 를 찾지 못했다"
    elif not fits:
        recommendation = REC_NOT_FITS
    elif page_break == "NONE":
        recommendation = REC_OK
    elif page_break == "CELL":
        recommendation = "pageBreak를 NONE으로 (현재 CELL — 셀 단위로 쪼개져 쪽을 넘는다)"
    else:
        recommendation = f"pageBreak를 NONE으로 (현재 {page_break!r} — 한 쪽에 들어간다)"

    notes = []
    if rows_missing:
        notes.append(f"행 {rows_missing}: 시작 셀 없음(위 행 rowSpan 이 덮음) — 높이 0 처리")
    if rows_estimated:
        notes.append(f"행 {rows_estimated}: rowSpan==1 셀 없음 — 병합 높이 균등분할로 추정")
    if body_width is not None and width_sum is not None and width_sum > body_width:
        notes.append(f"열 폭 합 {width_sum} > 본문 폭 {body_width} — 열 폭 축소 필요")

    first_tc = None
    if trs:
        tcs = trs[0].findall(TC)
        if tcs:
            first_tc = tcs[0]

    return {
        "idx": doc_idx,
        "section": section,
        "para_idx": para_idx,
        "preview": _cell_text(first_tc),
        "row_cnt_attr": row_cnt_attr,
        "col_cnt_attr": col_cnt_attr,
        "row_cnt_used": row_cnt,
        "page_break": page_break,
        "repeat_header": repeat_header,
        "rows": rows_meta,
        "height_sum": height_sum,
        "declared_height": declared_h,
        "declared_width": declared_w,
        "width_sum": width_sum,
        "width_row": width_row,
        "body_height": body_height,
        "body_width": body_width,
        "fits": fits,
        "recommendation": recommendation,
        "notes": notes,
    }


# ---------------------------------------------------------------- 섹션 순회


def analyze_section(xml_bytes, section):
    """섹션 XML 하나를 판정한다. xml_bytes 는 bytes 또는 str."""
    root = ET.fromstring(xml_bytes)
    geo = page_geometry(root)

    ctx = {"para_idx": -1, "tbl_idx": -1, "tables": [], "nested": 0}

    def walk(elem, para_stack, depth):
        for child in list(elem):
            tag = child.tag
            if tag == P:
                ctx["para_idx"] += 1
                para_stack.append(ctx["para_idx"])
                walk(child, para_stack, depth)
                para_stack.pop()
            elif tag == TBL:
                ctx["tbl_idx"] += 1
                doc_idx = ctx["tbl_idx"]
                if depth == 0:
                    ctx["tables"].append(
                        analyze_table(
                            child,
                            doc_idx,
                            section,
                            para_stack[-1] if para_stack else None,
                            geo,
                        )
                    )
                else:
                    ctx["nested"] += 1
                walk(child, para_stack, depth + 1)
            else:
                walk(child, para_stack, depth)

    walk(root, [], 0)

    return {
        "section": section,
        "geometry": geo,
        "para_cnt": ctx["para_idx"] + 1,
        "tbl_cnt_all": ctx["tbl_idx"] + 1,
        "nested_tbl_cnt": ctx["nested"],
        "tables": ctx["tables"],
    }


_SECTION_RE = re.compile(r"^Contents/section(\d+)\.xml$")


def analyze_hwpx(path, only_section=None):
    """hwpx 파일의 모든(또는 지정) 섹션을 판정한다."""
    started = time.perf_counter()
    sections = []
    with zipfile.ZipFile(path) as zf:
        names = []
        for name in zf.namelist():
            m = _SECTION_RE.match(name)
            if m:
                names.append((int(m.group(1)), name))
        names.sort()
        for num, name in names:
            if only_section is not None and num != only_section:
                continue
            sections.append(analyze_section(zf.read(name), num))
    return {
        "file": str(path),
        "sections": sections,
        "elapsed_sec": round(time.perf_counter() - started, 3),
    }


# ---------------------------------------------------------------- 출력


def _fmt(value, width, align=">"):
    text = "-" if value is None else str(value)
    return format(text, f"{align}{width}")


def render_text(result):
    out = []
    out.append(f"파일: {result['file']}")
    out.append(HEADER_NOTE)
    out.append("")

    total_top = total_nested = total_fits = total_not = 0
    pb_dist = {}
    overflow = []

    for sec in result["sections"]:
        geo = sec["geometry"]
        out.append(f"== 섹션 {sec['section']} ==")
        if geo is None:
            out.append("  pagePr 없음 — 본문 높이 유도 불가")
        else:
            out.append(
                "  용지 {w} x {h} (landscape={ls})  여백 top={t} bottom={b} "
                "header={hd} footer={ft} left={l} right={r} gutter={g}".format(
                    w=geo["page_width"], h=geo["page_height"], ls=geo["landscape"],
                    t=geo["margin_top"], b=geo["margin_bottom"],
                    hd=geo["margin_header"], ft=geo["margin_footer"],
                    l=geo["margin_left"], r=geo["margin_right"], g=geo["margin_gutter"],
                )
            )
            out.append(
                "  본문 높이 = {h} - {t} - {b} - {hd} - {ft} = {bh} HWPUNIT".format(
                    h=geo["page_height"], t=geo["margin_top"], b=geo["margin_bottom"],
                    hd=geo["margin_header"], ft=geo["margin_footer"],
                    bh=geo["body_height"],
                )
            )
            out.append(
                "  본문 폭   = {w} - {l} - {r} - {g} = {bw} HWPUNIT".format(
                    w=geo["page_width"], l=geo["margin_left"], r=geo["margin_right"],
                    g=geo["margin_gutter"], bw=geo["body_width"],
                )
            )
        out.append(
            f"  문단 {sec['para_cnt']}개 · 표 전체 {sec['tbl_cnt_all']}개 "
            f"(최상위 {len(sec['tables'])}개, 중첩 {sec['nested_tbl_cnt']}개)"
        )
        out.append("")

        if not sec["tables"]:
            out.append("  (최상위 표 없음)")
            out.append("")
            continue

        header = (
            f"  {_fmt('idx', 4)} {_fmt('para', 6)} {_fmt('행x열', 8, '<')} "
            f"{_fmt('pageBreak', 9, '<')} {_fmt('rptHdr', 6)} {_fmt('행높이합', 9)} "
            f"{_fmt('열폭합', 8)} {_fmt('fits', 5, '<')}"
        )
        out.append(header)
        out.append("  " + "-" * (len(header) - 2))

        for tb in sec["tables"]:
            total_top += 1
            pb_dist[tb["page_break"]] = pb_dist.get(tb["page_break"], 0) + 1
            if tb["fits"]:
                total_fits += 1
            else:
                total_not += 1
                overflow.append(tb)
            shape = "{}x{}".format(tb["row_cnt_attr"], tb["col_cnt_attr"])
            out.append(
                "  {} {} {} {} {} {} {} {}".format(
                    _fmt(tb["idx"], 4),
                    _fmt(tb["para_idx"], 6),
                    _fmt(shape, 8, "<"),
                    _fmt(tb["page_break"], 9, "<"),
                    _fmt(tb["repeat_header"], 6),
                    _fmt(tb["height_sum"], 9),
                    _fmt(tb["width_sum"], 8),
                    _fmt("예" if tb["fits"] else "아니오", 5, "<"),
                )
            )
            out.append(f"        · {tb['preview']}")
            out.append(f"        → {tb['recommendation']}")
            for note in tb["notes"]:
                out.append(f"        ! {note}")
        total_nested += sec["nested_tbl_cnt"]
        out.append("")

    out.append("== 요약 ==")
    out.append(f"  최상위 표 {total_top}개 · 중첩 표 {total_nested}개")
    out.append(f"  fits {total_fits}개 · not-fits {total_not}개")
    out.append(
        "  pageBreak 분포: "
        + (", ".join(f"{k}={v}" for k, v in sorted(pb_dist.items(), key=lambda x: str(x[0])))
           or "(없음)")
    )
    if overflow:
        out.append("  단독 한 쪽 초과 표:")
        for tb in overflow:
            out.append(
                f"    idx {tb['idx']} (sec {tb['section']}, para {tb['para_idx']}) "
                f"{tb['height_sum']} > {tb['body_height']} — {tb['preview']}"
            )
    else:
        out.append("  단독 한 쪽 초과 표: 없음")
    out.append(f"  실행 시간 {result['elapsed_sec']}초")
    return "\n".join(out)


# ---------------------------------------------------------------- 셀프테스트


def _synthetic_section():
    """표 2개(하나는 들어가고 하나는 넘침) + 중첩 표 1개를 담은 합성 섹션 XML."""

    def cell(col, row, width, height, col_span=1, row_span=1, text="", inner=""):
        return (
            f'<hp:tc><hp:subList><hp:p><hp:run><hp:t>{text}</hp:t></hp:run>'
            f"{inner}</hp:p></hp:subList>"
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
            f'<hp:cellSpan colSpan="{col_span}" rowSpan="{row_span}"/>'
            f'<hp:cellSz width="{width}" height="{height}"/></hp:tc>'
        )

    # 표 A: 3행 x 2열, 행 높이 1000 x 3 = 3000 <= 본문 높이 10000 → fits, pageBreak=CELL
    rows_a = "".join(
        f"<hp:tr>{cell(0, r, 2000, 1000, text=f'A{r}0')}"
        f"{cell(1, r, 2000, 1000, text=f'A{r}1')}</hp:tr>"
        for r in range(3)
    )
    tbl_a = (
        f'<hp:p><hp:run><hp:tbl pageBreak="CELL" repeatHeader="0" rowCnt="3" colCnt="2">'
        f'<hp:sz width="4000" height="3000"/>{rows_a}</hp:tbl></hp:run></hp:p>'
    )

    # 표 B: 5행 x 2열, 행 높이 3000 x 5 = 15000 > 10000 → not fits
    #       1행 왼쪽 셀에 중첩 표 1개를 넣는다.
    nested = (
        '<hp:tbl pageBreak="NONE" rowCnt="1" colCnt="1">'
        f"<hp:tr>{cell(0, 0, 1000, 500, text='N')}</hp:tr></hp:tbl>"
    )
    rows_b = []
    for r in range(5):
        inner = f"<hp:run>{nested}</hp:run>" if r == 1 else ""
        rows_b.append(
            f"<hp:tr>{cell(0, r, 2000, 3000, text=f'B{r}0', inner=inner)}"
            f"{cell(1, r, 2000, 3000, text=f'B{r}1')}</hp:tr>"
        )
    tbl_b = (
        f'<hp:p><hp:run><hp:tbl pageBreak="NONE" repeatHeader="1" rowCnt="5" colCnt="2">'
        f'<hp:sz width="4000" height="15000"/>{"".join(rows_b)}</hp:tbl></hp:run></hp:p>'
    )

    return (
        f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">'
        '<hp:p><hp:run><hp:secPr>'
        '<hp:pagePr landscape="WIDELY" width="10000" height="12000">'
        '<hp:margin header="200" footer="300" gutter="100" left="1000" '
        'right="1000" top="1000" bottom="500"/>'
        "</hp:pagePr></hp:secPr></hp:run></hp:p>"
        f"{tbl_a}{tbl_b}</hs:sec>"
    ).encode("utf-8")


def selftest():
    sec = analyze_section(_synthetic_section(), 0)
    geo = sec["geometry"]

    # 본문 높이 = 12000 - 1000(top) - 500(bottom) - 200(header) - 300(footer) = 10000
    assert geo["body_height"] == 10000, geo
    # 본문 폭 = 10000 - 1000 - 1000 - 100(gutter) = 7900
    assert geo["body_width"] == 7900, geo

    assert len(sec["tables"]) == 2, sec["tables"]
    assert sec["nested_tbl_cnt"] == 1, sec["nested_tbl_cnt"]
    assert sec["tbl_cnt_all"] == 3, sec["tbl_cnt_all"]

    a, b = sec["tables"]

    assert a["height_sum"] == 3000, a
    assert a["width_sum"] == 4000, a
    assert a["fits"] is True, a
    assert a["page_break"] == "CELL", a
    assert a["recommendation"].startswith("pageBreak를 NONE으로"), a
    assert a["preview"] == "A00", a

    assert b["height_sum"] == 15000, b
    assert b["fits"] is False, b
    assert b["page_break"] == "NONE", b
    assert b["recommendation"] == REC_NOT_FITS, b
    # 중첩 표(문서 순서 2번째)는 최상위 판정에서 빠지고 B 의 행 높이에 섞이지 않는다.
    assert b["row_cnt_used"] == 5, b
    assert all(r["height"] == 3000 for r in b["rows"]), b["rows"]

    # 문서 순서 idx: A=0, B=1, B 안의 중첩 표=2 (표는 진입 시점에 번호가 매겨진다)
    assert a["idx"] == 0 and b["idx"] == 1, (a["idx"], b["idx"])
    # 소속 문단 idx (문서 순서, 표 셀 문단 포함): secPr 문단 0 → A 는 1,
    # A 의 셀 문단 6개(2~7)가 뒤따르므로 B 는 8
    assert a["para_idx"] == 1, a["para_idx"]
    assert b["para_idx"] == 8, b["para_idx"]

    # 렌더링이 죽지 않는지도 확인한다.
    text = render_text({"file": "<selftest>", "sections": [sec], "elapsed_sec": 0.0})
    assert "단독으로 한 쪽 초과" in text
    assert "본문 높이" in text

    _selftest_rowspan()

    print("selftest: OK (표 2개 판정 + 중첩 표 1개 제외 + 기하 유도 + rowSpan 분기 확인)")
    return 0


def _selftest_rowspan():
    """rowSpan>1 만 있는 행의 추정·누락 분기를 따로 검증한다."""
    # 2행 x 2열. 0행 왼쪽 셀이 rowSpan=2 로 1행까지 덮고, 0행 오른쪽 셀은 rowSpan=1.
    # 1행에는 시작하는 셀이 없다 → 높이 None, 합계 0 처리.
    xml = (
        f'<hs:sec xmlns:hs="x" xmlns:hp="{HP}">'
        '<hp:p><hp:run><hp:secPr><hp:pagePr width="10000" height="12000">'
        '<hp:margin header="0" footer="0" gutter="0" left="0" right="0" '
        'top="0" bottom="0"/></hp:pagePr></hp:secPr></hp:run></hp:p>'
        '<hp:p><hp:run><hp:tbl pageBreak="NONE" rowCnt="2" colCnt="2">'
        '<hp:tr>'
        '<hp:tc><hp:cellAddr colAddr="0" rowAddr="0"/>'
        '<hp:cellSpan colSpan="1" rowSpan="2"/><hp:cellSz width="1000" height="4000"/></hp:tc>'
        '<hp:tc><hp:cellAddr colAddr="1" rowAddr="0"/>'
        '<hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="1000" height="1800"/></hp:tc>'
        '</hp:tr><hp:tr/></hp:tbl></hp:run></hp:p></hs:sec>'
    ).encode("utf-8")
    tb = analyze_section(xml, 0)["tables"][0]
    # 0행: rowSpan==1 셀(1800)이 있으므로 정확값. 1행: 시작 셀 없음 → None.
    assert tb["rows"][0] == {"row": 0, "height": 1800, "estimated": False}, tb["rows"]
    assert tb["rows"][1] == {"row": 1, "height": None, "estimated": False}, tb["rows"]
    assert tb["height_sum"] == 1800, tb["height_sum"]
    assert any("시작 셀 없음" in n for n in tb["notes"]), tb["notes"]

    # 0행에서 rowSpan==1 셀을 빼면 병합 높이 균등분할(4000/2=2000)로 추정한다.
    xml2 = xml.replace(
        b'<hp:tc><hp:cellAddr colAddr="1" rowAddr="0"/>'
        b'<hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="1000" height="1800"/></hp:tc>',
        b"",
    )
    tb2 = analyze_section(xml2, 0)["tables"][0]
    assert tb2["rows"][0] == {"row": 0, "height": 2000, "estimated": True}, tb2["rows"]
    assert tb2["height_sum"] == 2000, tb2["height_sum"]
    assert any("균등분할로 추정" in n for n in tb2["notes"]), tb2["notes"]
    # colSpan 합이 colCnt 와 맞는 행이 없으면 폭 합의 최댓값으로 대체한다.
    assert tb2["width_sum"] == 1000, tb2["width_sum"]


# ---------------------------------------------------------------- 진입점


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    ap = argparse.ArgumentParser(
        description="hwpx 표 쪽맞춤 판정기 (행 높이 합 vs 본문 높이)"
    )
    ap.add_argument("hwpx", nargs="?", help="판정할 hwpx 파일")
    ap.add_argument("--json", dest="json_out", help="판정 결과를 JSON 으로 저장할 경로")
    ap.add_argument("--section", type=int, default=None, help="이 섹션 번호만 판정")
    ap.add_argument("--selftest", action="store_true", help="합성 XML 로 자체 검증")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if not args.hwpx:
        ap.error("hwpx 경로가 필요하다 (또는 --selftest)")

    result = analyze_hwpx(args.hwpx, args.section)
    print(render_text(result))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(f"\nJSON 저장: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
