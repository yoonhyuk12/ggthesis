# -*- coding: utf-8 -*-
"""Targeted hwpx edits: 4 red CITE_TODO markers, 이형도 sentence, 7 bib items.

Does NOT reassemble. Only Contents/section2.xml is rewritten via fill_hwpx
patch_zip_entries so other ZIP entries stay byte-identical.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# fill_hwpx.patch_zip_entries — preserves ZIP entry order/compression.
sys.path.insert(0, os.path.expanduser(r"~\.claude\skills\hwpx\scripts"))
from fill_hwpx import patch_zip_entries  # noqa: E402

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_OPEN_RE = re.compile(r"<(?:\w+:)?t\b[^>]*?>")
T_CLOSE_RE = re.compile(r"</(?:\w+:)?t>")
RUN_OPEN_RE = re.compile(r"<(?:\w+:)?run\b([^>]*?)(/?)>")
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')
P_ID_RE = re.compile(r'<(?:\w+:)?p\b[^>]*?\bid="(\d+)"')
LINESEG_BLOCK_RE = re.compile(
    r"<(?:\w+:)?linesegarray\b[^>]*?(?:/>|>.*?</(?:\w+:)?linesegarray>)", re.S
)

# Body 11pt (charPr 37 height=1100) → matching red is 70, not 71 (height=1000).
# Existing CITE_TODO in this file already uses 70.
RED_BODY = "70"

# MD source-of-truth marker strings (03_시스템개발.md).
MARKER_LABEL = "[CITE_TODO: 라벨 데이터 부재 근거 — ref54 부적합]"
MARKER_FIRE = "[CITE_TODO: 화재검출 문헌 서지]"
MARKER_HAN = "[CITE_TODO: 한소은 2026 서지 확인]"
MARKER_MOLIT = "[CITE_TODO: 국토안전관리원 2024 가이드라인 서지]"

LEE_SENTENCE = (
    "이형도(2023)는 객체탐지 알고리즘 기반의 건설현장 근로자 안전모 "
    "실시간 모니터링 모델을 구축하여, 30 FPS 이상의 실시간 검출 성능과 "
    "안전모 착용 검출 정확도를 평가하고 기술 활성화 방안을 제시하였다."
)

BIB_KIMSEOKGI = (
    "김석기, 「소규모 건설현장 사망사고의 시스템적 원인 규명을 위한 "
    "BERTopic-LLM과 AcciMap 통합 분석 프레임워크 개발」, "
    "충북대학교 박사학위논문, 2026."
)
BIB_LEEGISU = (
    "이기수, 「건설현장의 안전 확보를 위한 딥러닝 기반의 시스템비계 설치 "
    "이상감지 연구」, 명지대학교 박사학위논문, 2024."
)
BIB_LEEHYUNGDO = (
    "이형도, 「객체탐지 알고리즘을 이용한 건설현장 근로자 안전모 실시간 "
    "모니터링 기술 활성화 방안 연구」, 경기대학교 대학원 건설안전학과 "
    "박사학위논문, 2023."
)
BIB_JODOBIN = (
    "조도빈, 「국내 소규모 민간 건설프로젝트의 산업안전보건관리비 준수 "
    "실태 분석 및 개선방안 제시연구」, 울산대학교 건축학과 공학박사학위논문, "
    "2026."
)
BIB_BROWN = 'Brown et al., "Language Models are Few-Shot Learners", NeurIPS, 2020.'
BIB_WILSON = (
    'Wilson, E. B., "Probable Inference, the Law of Succession, and '
    'Statistical Inference", Journal of the American Statistical Association, '
    "Vol. 22, No. 158, 1927, pp. 209-212."
)
BIB_ULTRALYTICS = "Ultralytics, [Computer Software], 2025."


def escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paragraph_spans(xml: str):
    stack, spans = [], []
    for m in P_TOKEN_RE.finditer(xml):
        tok = m.group(0)
        if tok.startswith("</"):
            if stack:
                s0, e0 = stack.pop()
                spans.append((s0, e0, m.start(), m.end()))
        elif tok.endswith("/>"):
            spans.append((m.start(), m.end(), m.start(), m.end()))
        else:
            stack.append((m.start(), m.end()))
    spans.sort()
    return spans


def own_segment(xml, span, spans):
    s0, e0, s1, _ = span
    inner = [c for c in spans if c[0] > s0 and c[3] <= s1]
    outermost = []
    for child in inner:
        if not any(m[0] < child[0] and child[3] <= m[3] for m in outermost):
            outermost.append(child)
    parts, pos = [], e0
    for child in outermost:
        parts.append(xml[pos:child[0]])
        pos = child[3]
    parts.append(xml[pos:s1])
    return xml[s0:e0] + "".join(parts)


def para_inner_text(seg: str) -> str:
    """Concatenated <hp:t> inner XML (entities still encoded)."""
    out = []
    for m in T_OPEN_RE.finditer(seg):
        end = T_CLOSE_RE.search(seg, m.end())
        if end:
            out.append(seg[m.end():end.start()])
    return "".join(out)


def strip_lineseg(seg: str) -> str:
    return LINESEG_BLOCK_RE.sub("", seg)


def find_unique_para(xml, spans, needle: str):
    hits = []
    for i, span in enumerate(spans):
        seg = own_segment(xml, span, spans)
        text = para_inner_text(seg)
        if needle in text:
            hits.append(i)
    if len(hits) != 1:
        raise RuntimeError(f"unique para failed for {needle!r}: hits={hits}")
    return hits[0]


def insert_marker_after(seg: str, after: str, marker: str, red_id: str) -> str:
    """Split the run that owns `after` so `marker` is its own red run."""
    # Walk t nodes; locate the one that contains the insertion point.
    t_nodes = []
    for m in T_OPEN_RE.finditer(seg):
        close = T_CLOSE_RE.search(seg, m.end())
        if not close:
            continue
        t_nodes.append((m.start(), m.end(), close.start(), close.end(),
                        seg[m.end():close.start()]))
    concat = "".join(t[4] for t in t_nodes)
    pos = concat.find(after)
    if pos < 0:
        raise RuntimeError(f"anchor not in paragraph: {after!r}")
    if concat.find(after, pos + 1) >= 0:
        raise RuntimeError(f"anchor not unique in paragraph: {after!r}")
    insert_at = pos + len(after)

    acc = 0
    target_i = None
    local = None
    for i, node in enumerate(t_nodes):
        inner = node[4]
        if acc + len(inner) >= insert_at:
            target_i = i
            local = insert_at - acc
            break
        acc += len(inner)
    if target_i is None:
        raise RuntimeError("could not map insert offset to <t>")

    t_start, t_inner_start, t_inner_end, t_end, inner = t_nodes[target_i]
    left, right = inner[:local], inner[local:]

    # Find the enclosing run of this t: last <hp:run ...> that starts before t_start
    # and whose matching close is after t_end. Simple body paras: run immediately wraps t.
    run_open = None
    for m in RUN_OPEN_RE.finditer(seg):
        if m.start() > t_start:
            break
        run_open = m
    if run_open is None:
        raise RuntimeError("no enclosing run for t")
    run_attrs = run_open.group(1)
    self_close = run_open.group(2) == "/"
    if self_close:
        raise RuntimeError("target t is in a self-closing run")
    orig_pr = CHARPR_REF_RE.search(run_attrs)
    orig_id = orig_pr.group(1) if orig_pr else "37"

    # Find </hp:run> that closes this run — first close after t_end that isn't nested.
    # Body paras are <run><t>...</t></run>, so the close is right after t.
    run_close_m = re.search(r"</(?:\w+:)?run>", seg[t_end:])
    if run_close_m is None:
        raise RuntimeError("no run close after t")
    run_close_end = t_end + run_close_m.end()
    run_close_start = t_end + run_close_m.start()

    # Only split this one t. If the run contains extra siblings after t, keep them
    # on the right run.
    after_t_before_close = seg[t_end:run_close_start]

    pieces = []
    if left:
        pieces.append(f'<hp:run charPrIDRef="{orig_id}"><hp:t>{left}</hp:t></hp:run>')
    pieces.append(
        f'<hp:run charPrIDRef="{red_id}"><hp:t>{escape_text(marker)}</hp:t></hp:run>'
    )
    right_run_inner = f"<hp:t>{right}</hp:t>" if right else ""
    right_run_inner += after_t_before_close
    if right or after_t_before_close.strip():
        pieces.append(f'<hp:run charPrIDRef="{orig_id}">{right_run_inner}</hp:run>')

    new_seg = seg[:run_open.start()] + "".join(pieces) + seg[run_close_end:]
    return strip_lineseg(new_seg)


def append_black_text(seg: str, addition: str) -> str:
    """Append plain text to the last <hp:t> of the paragraph (same charPr)."""
    last = None
    for m in T_OPEN_RE.finditer(seg):
        close = T_CLOSE_RE.search(seg, m.end())
        if close:
            last = (m, close)
    if last is None:
        raise RuntimeError("no <t> to append to")
    m, close = last
    inner = seg[m.end():close.start()]
    new_inner = inner + escape_text(addition)
    new_seg = seg[:m.end()] + new_inner + seg[close.start():]
    return strip_lineseg(new_seg)


def make_bib_para(pid: int, text: str) -> str:
    return (
        f'<hp:p id="{pid}" paraPrIDRef="50" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="8"><hp:t>{escape_text(text)}</hp:t></hp:run>'
        f"</hp:p>"
    )


def next_pids(xml: str, n: int):
    ids = [int(x) for x in P_ID_RE.findall(xml)]
    start = (max(ids) + 1) if ids else 1
    return list(range(start, start + n))


def apply_xml(xml: str) -> str:
    spans = paragraph_spans(xml)

    # --- locate paragraphs by unique needles (current hwpx text) ---
    i_label = find_unique_para(xml, spans, "라벨 데이터가 사실상 존재하지 않는다(Kim, 2025)")
    i_fire = find_unique_para(xml, spans, "Kim et al.(2025)이 화재 검출에서")
    i_han = find_unique_para(xml, spans, "한소은(2026)")
    i_molit = find_unique_para(xml, spans, "국토안전관리원(2024)")
    i_leehyun = find_unique_para(
        xml, spans, "오탐과 미탐을 모두 감소시킴을 검증하였다."
    )

    i_thesis_h = find_unique_para(xml, spans, "가. 학위논문")
    i_youn = find_unique_para(
        xml, spans, "윤영석, 「중·소규모 건설현장 안전관리자 인건비"
    )
    i_leejun = find_unique_para(
        xml, spans, "이준호, 「건설현장 중대재해 감소를 위한 스마트 안전장비의 지원방법"
    )
    i_journal_h = find_unique_para(xml, spans, "나. 학술지")
    i_pods = find_unique_para(xml, spans, "Podsakoff, P. M.")
    i_jamovi = find_unique_para(xml, spans, "The jamovi project, jamovi (Version 2.7)")

    # sanity: fire and F1 Kim et al. are different paras
    i_f1 = find_unique_para(xml, spans, "Kim et al.(2025)의 F1 개선")
    if i_f1 == i_fire:
        raise RuntimeError("fire-detection Kim et al. collapsed onto F1 sentence")
    if i_han != i_f1:
        raise RuntimeError(f"한소은 expected in F1 para {i_f1}, found {i_han}")

    print("para map:")
    for name, i in [
        ("label Kim 2025", i_label),
        ("fire Kim et al", i_fire),
        ("한소은 / F1", i_han),
        ("국토안전관리원", i_molit),
        ("김현수+이형도 append", i_leehyun),
        ("가. 학위논문", i_thesis_h),
        ("윤영석", i_youn),
        ("이준호", i_leejun),
        ("나. 학술지", i_journal_h),
        ("Podsakoff", i_pods),
        ("jamovi", i_jamovi),
    ]:
        print(f"  {name}: {i}")

    pids = next_pids(xml, 7)
    print("new p ids:", pids)

    # Operations on full xml, applied high-offset → low-offset.
    # Each op is either in-place replace of span[i] or insert after span[i].end.
    ops = []

    def add_inplace(i, new_seg):
        # own_segment excludes </hp:p>; replace only through the close-tag start.
        s0, _, s1, _ = spans[i]
        ops.append((s0, s1, new_seg, f"inplace {i}"))

    def add_insert_after(i, blob, label):
        _, _, _, e1 = spans[i]
        ops.append((e1, e1, blob, f"insert-after {i} {label}"))

    # in-place body
    seg = own_segment(xml, spans[i_label], spans)
    add_inplace(
        i_label,
        insert_marker_after(
            seg,
            "라벨 데이터가 사실상 존재하지 않는다(Kim, 2025)",
            MARKER_LABEL,
            RED_BODY,
        ),
    )
    seg = own_segment(xml, spans[i_fire], spans)
    add_inplace(
        i_fire,
        insert_marker_after(seg, "Kim et al.(2025)", MARKER_FIRE, RED_BODY),
    )
    seg = own_segment(xml, spans[i_han], spans)
    add_inplace(
        i_han,
        insert_marker_after(seg, "한소은(2026)", MARKER_HAN, RED_BODY),
    )
    seg = own_segment(xml, spans[i_molit], spans)
    add_inplace(
        i_molit,
        insert_marker_after(seg, "국토안전관리원(2024)", MARKER_MOLIT, RED_BODY),
    )
    seg = own_segment(xml, spans[i_leehyun], spans)
    if "이형도(2023)는" in para_inner_text(seg):
        raise RuntimeError("이형도 sentence already present — abort to avoid dup")
    add_inplace(i_leehyun, append_black_text(seg, " " + LEE_SENTENCE))

    # bibliography inserts (no [NN] numbers — 재번호 금지, 문자열 그대로)
    add_insert_after(i_thesis_h, make_bib_para(pids[0], BIB_KIMSEOKGI), "김석기")
    add_insert_after(i_youn, make_bib_para(pids[1], BIB_LEEGISU), "이기수")
    add_insert_after(
        i_leejun,
        make_bib_para(pids[2], BIB_LEEHYUNGDO) + make_bib_para(pids[3], BIB_JODOBIN),
        "이형도+조도빈",
    )
    add_insert_after(i_journal_h, make_bib_para(pids[4], BIB_BROWN), "Brown")
    add_insert_after(i_pods, make_bib_para(pids[5], BIB_WILSON), "Wilson")
    add_insert_after(i_jamovi, make_bib_para(pids[6], BIB_ULTRALYTICS), "Ultralytics")

    # Apply from the right so earlier offsets stay valid.
    ops.sort(key=lambda o: (o[0], o[1]), reverse=True)
    # If two ops share the same start (shouldn't), still ok due to reverse.

    # Overlap check on original coordinates (inserts have start==end so they
    # don't overlap in-place ranges of other paras).
    inplace = [(a, b, lab) for a, b, _, lab in ops if a != b]
    inplace.sort()
    for (a1, b1, l1), (a2, b2, l2) in zip(inplace, inplace[1:]):
        if b1 > a2:
            raise RuntimeError(f"inplace overlap {l1} vs {l2}")

    new_xml = xml
    for start, end, repl, lab in ops:
        print(f"  apply {lab} @{start}:{end} Δ={len(repl) - (end - start)}")
        new_xml = new_xml[:start] + repl + new_xml[end:]
    return new_xml


def main():
    src = r"tools/hwpx_transfer/staging/scratch_cite/base.hwpx"
    dst = r"tools/hwpx_transfer/staging/scratch_cite/out.hwpx"
    with open(src, "rb") as f:
        buf = f.read()
    with zipfile.ZipFile(src) as zf:
        xml = zf.read("Contents/section2.xml").decode("utf-8")
        names = zf.namelist()
    print("section2 bytes", len(xml.encode("utf-8")))
    new_xml = apply_xml(xml)

    # post-checks on the new XML string
    for s in [
        MARKER_LABEL, MARKER_FIRE, MARKER_HAN, MARKER_MOLIT,
        LEE_SENTENCE, BIB_KIMSEOKGI, BIB_LEEGISU, BIB_LEEHYUNGDO,
        BIB_JODOBIN, BIB_BROWN, BIB_WILSON, BIB_ULTRALYTICS,
    ]:
        esc = escape_text(s)
        if esc not in new_xml:
            raise RuntimeError(f"missing after edit: {s[:60]!r}")
        print(f"  present: {s[:50]}")

    # F1 Kim et al. must NOT have gained a marker
    # Find the F1 sentence and ensure no CITE_TODO between Kim et al.(2025) and 의 F1
    if "Kim et al.(2025)[CITE_TODO: 화재검출 문헌 서지]의 F1" in new_xml:
        raise RuntimeError("F1 Kim et al. was wrongly marked")
    if "Kim et al.(2025)이 화재 검출에서" in new_xml.replace(MARKER_FIRE, ""):
        # after insertion the fire sentence should have marker in between
        pass
    fire_pat = "Kim et al.(2025)</hp:t></hp:run><hp:run charPrIDRef=\"70\"><hp:t>[CITE_TODO: 화재검출 문헌 서지]"
    if fire_pat not in new_xml:
        raise RuntimeError("fire marker not in red run-split form")
    print("  fire marker run-split OK")

    # existing numbered items still present
    for s in [
        "[01] 김윤헌",
        "[08] 황병복",
        "[01] Cvach",
        "[06] Yao",
        "[01] 고용노동부",
        "[03] The jamovi project",
    ]:
        if s not in new_xml:
            raise RuntimeError(f"existing numbered item missing: {s}")
    print("  existing numbered items intact")

    out = patch_zip_entries(buf, {"Contents/section2.xml": new_xml.encode("utf-8")})
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(out)
    print("wrote", dst, "bytes", len(out))
    print("base sha", hashlib.sha256(buf).hexdigest())
    print("out  sha", hashlib.sha256(out).hexdigest())


if __name__ == "__main__":
    main()
