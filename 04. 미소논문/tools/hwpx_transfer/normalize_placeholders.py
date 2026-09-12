# -*- coding: utf-8 -*-
"""MD 원고의 대괄호 자리표시자 접두사를 6종 마커로 정규화한다 (W6).

hwpx 조립기(`blocks_to_hwpx.py`)는 대괄호 자리표시자 가운데 접두사 6종
(`DATA PENDING` / `확정 필요` / `CITE_TODO` / `그림 삽입 예정` / `UNVERIFIED` /
`작성 가이드`)으로 시작하는 것만 빨간 글자로 뽑는다. 미완성 자리인데 접두사가
달라 검정으로 남는 표기를 **의미를 보존한 채 접두사만** 붙여 정규화한다.

원칙
  - 대괄호 **안** 내용만 바꾼다. 앞뒤 문맥·굵게(`**`)·백틱·이탤릭은 건드리지 않는다.
  - 실제 본문 대괄호(참조번호 `[54]`, 단계 라벨 `[1단계]`, 이미지 alt `[그림 1-1]`,
    소제목 `[정리 규칙]`)는 규칙표에 없으므로 그대로 둔다.
  - **멱등**: 이미 6종 접두사로 시작하는 자리표시자는 다시 건드리지 않는다.
    몇 번을 재실행해도 결과가 같다.

실행 (저장소 루트 기준):
    PYTHONIOENCODING=utf-8 python "04. 미소논문/tools/hwpx_transfer/normalize_placeholders.py"
    PYTHONIOENCODING=utf-8 python "04. 미소논문/tools/hwpx_transfer/normalize_placeholders.py" --dry-run
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys

# 조립기가 빨강으로 뽑는 6종 접두사 — 이걸로 시작하면 이미 정규화된 것이다.
MARKERS = (
    "DATA PENDING",
    "확정 필요",
    "CITE_TODO",
    "그림 삽입 예정",
    "UNVERIFIED",
    "작성 가이드",
)

# (1) 내용을 그대로 두고 `[DATA PENDING: …]` 접두사만 붙일 정확 일치 표기
DATA_PENDING_EXACT = {
    "분석 후 작성",
    "대응표본 t / Wilcoxon",
    "유의/비유의 표기만",
    "채택 / 기각",
    "공종 범주",
    "금액 구간",
    "단축/증가",
    "대체 적용 여부",
    "변화",
    "사용경험 구간",
    "인원 구간",
    "작성 빈도 구간",
    "컸다/작았다",
    "요인명",
    "유의하였다/유의하지 않았다",
    "이원 혼합·절대일치·평균 측정치 등 확정 후 기재",
}

# (2) `X` 또는 `X — 부연` 형태 모두 `[DATA PENDING: X …]` 로. 줄표 뒤 내용은 보존한다.
DATA_PENDING_PREFIX = (
    "실험 후 작성",
    "결과 확인 후 구체화",
)

# (3) `X` 또는 `X — 부연` 형태 모두 `[확정 필요: X …]` 로.
CONFIRM_PREFIX = ("예비조사 후 확정",)

# (4) `[확정 필요: …]` 접두사만 붙일 정확 일치 표기
CONFIRM_EXACT = {
    "O",
    "5장 분석 결과 확정 후 작성 — 실제 수치를 넣는다. 존재하지 않는 수치를 임의로 기입하지 않는다.",
    "학술적·실무적·정책적 시사점을 결과에 근거해 작성한다.",
    "제6장 연결 길잡이 — 결과 확정 후 작성",
}

# (5) 문구 끝의 '확정 필요'/'확인 필요'를 접두사로 옮기는 표기 (원문 → 접두사 뒤 내용)
CONFIRM_REWRITE = {
    "모집 경로·현장 범위 확정 필요": "모집 경로·현장 범위",
    "실험 실시 기간 확정 필요": "실험 실시 기간",
    "시행령 금액 기준 원문 확인 필요": "시행령 금액 기준 원문 확인",
}

# (6) `[작성 가이드: …]` 접두사만 붙일 정확 일치 표기 (집필 지침·서술 틀)
GUIDE_EXACT = {
    "절 안내",
    "장 전체 안내",
    "분석 자료의 구조",
    "H4 판정 서술 틀 — 분석 후 작성",
    "가설별 판정 서술 틀 — 분석 후 작성",
    "동일 형식으로 서술한다.",
    "동일 형식으로 서술하되, 품질은 4개 평정 항목별 결과도 함께 언급한다.",
    "주요 분석 결과 요약 — 실험 후 작성",
}

BRACKET_RE = re.compile(r"\[[^\[\]]*\]")

# 치환 사유 라벨 — 리포트 집계용
RULE_LABELS = {
    "citetodo": "CiteTodo → CITE_TODO (대소문자 통일)",
    "dp_exact": "DATA PENDING 접두사 부여 (정확 일치)",
    "dp_prefix": "DATA PENDING 접두사 부여 (줄표 뒤 내용 보존)",
    "cf_prefix": "확정 필요 접두사 부여 (줄표 뒤 내용 보존)",
    "cf_exact": "확정 필요 접두사 부여 (정확 일치)",
    "cf_rewrite": "확정 필요를 문구 끝에서 접두사로 이동",
    "guide": "작성 가이드 접두사 부여",
}


def classify(inner: str):
    """대괄호 안 내용을 받아 (새 내용, 규칙키)를 돌려준다. 바꿀 것이 없으면 (inner, None)."""
    # 멱등 — 이미 6종 마커면 건드리지 않는다
    for m in MARKERS:
        if inner.startswith(m):
            return inner, None

    # CiteTodo / CiteTodo: … → CITE_TODO
    if inner == "CiteTodo":
        return "CITE_TODO", "citetodo"
    if inner.startswith("CiteTodo:"):
        return "CITE_TODO:" + inner[len("CiteTodo:"):], "citetodo"

    if inner in DATA_PENDING_EXACT:
        return "DATA PENDING: " + inner, "dp_exact"

    for p in DATA_PENDING_PREFIX:
        if inner == p or inner.startswith(p + " —"):
            return "DATA PENDING: " + inner, "dp_prefix"

    for p in CONFIRM_PREFIX:
        if inner == p or inner.startswith(p + " —"):
            return "확정 필요: " + inner, "cf_prefix"

    if inner in CONFIRM_EXACT:
        return "확정 필요: " + inner, "cf_exact"

    if inner in CONFIRM_REWRITE:
        return "확정 필요: " + CONFIRM_REWRITE[inner], "cf_rewrite"

    if inner in GUIDE_EXACT:
        return "작성 가이드: " + inner, "guide"

    return inner, None


def normalize_text(text: str, stats_pattern, stats_rule):
    """문서 전체 문자열을 치환하고 통계를 누적한다."""

    def _sub(m):
        old = m.group(0)
        inner = old[1:-1]
        new_inner, rule = classify(inner)
        if rule is None:
            return old
        stats_pattern[old] += 1
        stats_rule[rule] += 1
        return "[" + new_inner + "]"

    return BRACKET_RE.sub(_sub, text)


def main(argv=None):
    ap = argparse.ArgumentParser(description="MD 자리표시자 접두사 정규화 (멱등)")
    ap.add_argument(
        "--docs",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "01.docs"),
        help="MD 원고 디렉토리 (기본: 스크립트 기준 ../../01.docs)",
    )
    ap.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 건수만 출력")
    args = ap.parse_args(argv)

    docs = os.path.normpath(args.docs)
    if not os.path.isdir(docs):
        sys.stderr.write("원고 디렉토리를 찾을 수 없다: %s\n" % docs)
        return 2

    stats_pattern = collections.Counter()
    stats_rule = collections.Counter()
    per_file = collections.Counter()
    per_file_lines = collections.Counter()

    for fn in sorted(os.listdir(docs)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(docs, fn)
        with open(path, encoding="utf-8", newline="") as f:
            src = f.read()

        before = stats_pattern.copy()
        out = normalize_text(src, stats_pattern, stats_rule)
        n = sum(stats_pattern.values()) - sum(before.values())
        per_file[fn] = n

        if n:
            # 바뀐 줄 수 (diff 줄 수 집계용)
            a = src.split("\n")
            b = out.split("\n")
            per_file_lines[fn] = sum(1 for x, y in zip(a, b) if x != y)

        if out != src and not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(out)

    total = sum(stats_pattern.values())
    print("=== 파일별 치환 건수 (바뀐 줄 수) ===")
    for fn in sorted(per_file):
        print("  %-24s %4d건  (%d줄)" % (fn, per_file[fn], per_file_lines[fn]))
    print()
    print("=== 규칙별 치환 건수 ===")
    for k in ("dp_exact", "dp_prefix", "cf_prefix", "cf_exact", "cf_rewrite", "guide", "citetodo"):
        print("  %-6s %4d건  %s" % (k, stats_rule[k], RULE_LABELS[k]))
    print()
    print("=== 표기별 치환 건수 ===")
    for s, c in sorted(stats_pattern.items(), key=lambda kv: (-kv[1], kv[0])):
        print("  %4d  %s" % (c, s))
    print()
    print("합계 %d건%s" % (total, " (dry-run, 파일 미변경)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
