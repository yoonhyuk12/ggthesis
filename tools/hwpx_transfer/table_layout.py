# 표 셀 내용의 글리프 폭을 추정해 열폭을 설계하고, 기존 표 열폭을 병합 격자를 보존한 채 비례 재계산하는 모듈
"""table_layout.py — 내용 기반 열폭 설계(표준 라이브러리만 사용).

단위는 HWPUNIT(1pt = 100). 글리프 폭은 실제 글꼴 측정이 아니라 추정값이다
(한글·한자·전각 1em, 영문·숫자 0.55em, 공백 0.3em, 그 밖의 기호 0.5em).
추정이므로 최종 줄바꿈·쪽맞춤은 한글 재조판 PDF로 확인해야 한다(.claude/rules/hwpx-table-layout.md).
"""

import math
import re

CELL_LINEBREAK_TOKEN = "<br>"
EMSP_TOKEN = "&emsp;"

# 머리행 "라벨(단위)"의 단위 괄호 — 공백 없는 5자 이하 괄호만 단위로 본다.
# "선행연구(연구자, 연도)"처럼 쉼표·공백이 든 설명 괄호는 나누지 않는다.
HEADER_UNIT_RE = re.compile(r"^(.*\S)\s*(\([^()\s,]{1,5}\))$")

# 수치 셀 — 오른쪽 정렬 대상. 부호·소수·천 단위 쉼표·백분율·괄호 안 수치(표준편차 등)·흔한 단위를 허용한다.
NUMBER_CELL_RE = re.compile(
    r"^[\s]*[-−–+±]?\s*[\d][\d,]*(?:\.\d+)?\s*(?:%|명|개|건|회|개소|대|원|세|년|점)?"
    r"(?:\s*\(\s*[-−–+]?[\d][\d,]*(?:\.\d+)?\s*%?\s*\))?\s*$"
)


def char_em(ch):
    """문자 하나의 추정 폭(em)."""
    code = ord(ch)
    if ch == " " or ch == " ":
        return 0.3
    if ch == "　" or ch == " ":
        return 1.0
    if (0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F
            or 0x4E00 <= code <= 0x9FFF or 0x3000 <= code <= 0x303F or 0xFF00 <= code <= 0xFFEF):
        return 1.0
    if ch.isalnum():
        return 0.55
    return 0.5


def text_width(text, size_pt=10.0):
    """텍스트 한 줄의 추정 폭(HWPUNIT)."""
    text = text.replace(EMSP_TOKEN, " ")
    return int(math.ceil(sum(char_em(c) for c in text) * size_pt * 100))


def split_header_unit(text):
    """머리행 셀 "라벨(단위)" → [라벨, (단위)]. 해당 없으면 [text]."""
    if CELL_LINEBREAK_TOKEN in text:
        return [text]
    m = HEADER_UNIT_RE.match(text.strip())
    if not m:
        return [text]
    return [m.group(1), m.group(2)]


def is_number_cell(text):
    return bool(text.strip()) and bool(NUMBER_CELL_RE.match(text.replace(CELL_LINEBREAK_TOKEN, " ")))


def cell_lines(text, header=False):
    lines = text.split(CELL_LINEBREAK_TOKEN)
    if header and len(lines) == 1:
        lines = split_header_unit(text)
    return lines


HANGUL_RUN_CAP_CHARS = 4  # 한글 연속 구간은 글자 단위로 꺾이므로 최소 폭 요구를 이 글자 수로 제한한다


def _unbreakable_units(word):
    """낱말 안에서 줄바꿈이 안 되는 단위. 한글 줄나눔 기준은 한글=글자, 영문·숫자=단어이므로
    라틴·숫자·기호 연속 구간은 통째로, 한글(전각) 연속 구간은 글자 단위로 나뉘는 것으로 본다."""
    units, cur, cur_cjk = [], "", None
    for ch in word:
        cjk = char_em(ch) >= 1.0
        if cur and cjk != cur_cjk:
            units.append((cur, cur_cjk))
            cur = ""
        cur += ch
        cur_cjk = cjk
    if cur:
        units.append((cur, cur_cjk))
    return units


def _longest_word(lines, size_pt):
    """열의 최소 폭 요구(HWPUNIT): 라틴 구간은 전체 폭, 한글 구간은 HANGUL_RUN_CAP_CHARS자 폭까지만.
    '국토교통부·국토안전관리원(2025)' 같은 긴 한글 토큰 하나가 열폭 전체를 끌고 가던 문제(2026-10-08
    스모크 <표 3-2>·<표 5-1>)를 막는다."""
    best = 0
    for line in lines:
        for word in re.split(r"[\s]+", line.strip()):
            for unit, cjk in _unbreakable_units(word):
                w = text_width(unit, size_pt)
                if cjk:
                    w = min(w, int(HANGUL_RUN_CAP_CHARS * size_pt * 100))
                best = max(best, w)
    return best


def estimate_table_height(header, rows, widths, size_pt=10.0, pad=1020, line_height=1700, vpad=0):
    """표 높이 추정(HWPUNIT). 셀마다 '내용 폭 / (열폭 - pad)'로 줄 수를 어림한다(글자 단위 줄바꿈 가정).
    추정값이며 쪽맞춤 증거가 아니다 — 실제 한글 재조판 PDF로 확인한다."""
    total = 0
    for r_idx, row in enumerate([header] + list(rows)):
        is_header = r_idx == 0
        max_lines = 1
        for c, text in enumerate(row):
            avail = max(widths[c] - pad, int(size_pt * 100))
            n = 0
            for line in cell_lines(text, header=is_header):
                n += max(1, int(math.ceil(text_width(line, size_pt) / float(avail))))
            max_lines = max(max_lines, n)
        total += max_lines * line_height + vpad
    return total


def column_needs(header, rows, size_pt=10.0, pad=1020):
    """열별 (한 줄 필요 폭, 최장 낱말 폭, 평균 내용 폭) — 모두 셀 좌우 여백 pad 포함."""
    ncols = len(header)
    full = [0] * ncols
    word = [0] * ncols
    total = [0] * ncols
    count = [0] * ncols
    for r_idx, row in enumerate([header] + list(rows)):
        is_header = r_idx == 0
        for c in range(ncols):
            text = row[c] if c < len(row) else ""
            lines = cell_lines(text, header=is_header)
            line_w = max([text_width(l, size_pt) for l in lines] or [0])
            full[c] = max(full[c], line_w + pad)
            word[c] = max(word[c], _longest_word(lines, size_pt) + pad)
            if not is_header and text.strip():
                total[c] += line_w
                count[c] += 1
    mean = [(total[c] / count[c] + pad) if count[c] else float(word[c]) for c in range(ncols)]
    return full, word, mean


def _round_to_total(raw, total_width):
    """실수 열폭을 정수로 만들고 반올림 잔차를 가장 넓은 열에 몰아 합계를 total_width와 일치시킨다."""
    widths = [int(math.floor(w)) for w in raw]
    residual = total_width - sum(widths)
    widest = max(range(len(widths)), key=lambda i: widths[i])
    widths[widest] += residual
    if min(widths) <= 0:
        raise ValueError("열폭 계산 결과에 0 이하 열이 생겼다: %r" % widths)
    assert sum(widths) == total_width
    return widths


def design_column_widths(header, rows, total_width, size_pt=10.0, pad=1020,
                         equal_ratio=1.3):
    """내용 기반 열폭(정수 HWPUNIT, 합계 = total_width).

    1) 모든 열이 한 줄에 들어가면(필요 폭 합 ≤ 전체 폭) 남는 폭을 필요 폭에 비례해 나눈다.
       필요 폭이 서로 비슷하면(최대/최소 ≤ equal_ratio) 균등 분할한다.
    2) 넘치면 짧은 열(식별자·수치·구분 열: 한 줄 필요 폭이 균등 몫 이하)은 한 줄 필요 폭을
       그대로 주고, 나머지(설명·문항·근거 열)에 남은 폭을 평균 내용 폭에 비례해 배분한다.
       긴 열은 최장 낱말 폭 아래로 줄이지 않으며, 그래도 모자라면 짧은 열을 최장 낱말 폭까지 줄인다.
    """
    ncols = len(header)
    if ncols == 0:
        raise ValueError("열이 없는 표")
    if ncols == 1:
        return [total_width]
    full, word, mean = column_needs(header, rows, size_pt, pad)

    if sum(full) <= total_width:
        if max(full) <= min(full) * equal_ratio:
            return _round_to_total([total_width / ncols] * ncols, total_width)
        scale = total_width / float(sum(full))
        return _round_to_total([f * scale for f in full], total_width)

    if sum(word) >= total_width:
        # 최장 낱말조차 다 못 들어가는 밀집 표 — 낱말 폭에 비례해 나눈다(한글이 낱말 안에서 줄바꿈).
        # 이런 표는 3단계 PDF 검증에서 열폭 재배분·행 경계 나눔 대상으로 따로 본다.
        scale = total_width / float(sum(word))
        return _round_to_total([w * scale for w in word], total_width)

    share = total_width / float(ncols)
    fixed = [c for c in range(ncols) if full[c] <= share]
    flex = [c for c in range(ncols) if c not in fixed]
    if not flex:  # 이론상 sum(full) > total이면 하나 이상은 share를 넘는다
        flex, fixed = list(range(ncols)), []

    raw = [0.0] * ncols
    for c in fixed:
        raw[c] = float(full[c])
    remain = total_width - sum(raw[c] for c in fixed)
    flex_min = sum(word[c] for c in flex)
    if remain < flex_min and fixed:
        # 짧은 열을 최장 낱말 폭까지 줄여 긴 열의 최소 폭을 확보한다.
        deficit = flex_min - remain
        slack = sum(raw[c] - word[c] for c in fixed)
        take = min(deficit, max(slack, 0))
        for c in fixed:
            room = raw[c] - word[c]
            if slack > 0:
                raw[c] -= take * room / slack
        remain = total_width - sum(raw[c] for c in fixed)

    # 긴 열: 평균 내용 폭 비례, 단 최장 낱말 폭 이상. 하한에 걸린 열을 고정하고 반복한다.
    pending = list(flex)
    while pending:
        weight = sum(mean[c] for c in pending)
        budget = remain
        clipped = []
        for c in pending:
            share_c = budget * mean[c] / weight if weight else budget / len(pending)
            if share_c < word[c]:
                clipped.append(c)
        if not clipped:
            for c in pending:
                raw[c] = budget * mean[c] / weight if weight else budget / len(pending)
            break
        for c in clipped:
            raw[c] = float(word[c])
            remain -= word[c]
            pending.remove(c)
    # sum(word) < total_width이므로 짧은 열을 낱말 폭까지 줄이면 긴 열의 낱말 폭은 항상 확보된다.
    if any(raw[c] < word[c] - 1 for c in range(ncols)):
        raise AssertionError("열폭이 최장 낱말 폭보다 작다: %r < %r" % (raw, word))
    return _round_to_total(raw, total_width)


def scale_widths(widths, total_width):
    """기존 열폭 배열을 비례 축척해 합계를 total_width로 맞춘다(병합 격자는 열 단위라 보존된다)."""
    old = float(sum(widths))
    if old <= 0:
        raise ValueError("기존 열폭 합이 0 이하")
    return _round_to_total([w * total_width / old for w in widths], total_width)


def occupancy_grid(cells, row_cnt, col_cnt):
    """cells=[(row, col, rowSpan, colSpan)] → 점유 격자 검사. 중복·빈칸·범위 초과가 있으면 ValueError."""
    grid = [[None] * col_cnt for _ in range(row_cnt)]
    for idx, (r, c, rs, cs) in enumerate(cells):
        for rr in range(r, r + rs):
            for cc in range(c, c + cs):
                if rr >= row_cnt or cc >= col_cnt:
                    raise ValueError("셀 %d가 격자 범위를 벗어난다: (%d,%d)" % (idx, rr, cc))
                if grid[rr][cc] is not None:
                    raise ValueError("셀 %d와 %d가 (%d,%d)를 중복 점유한다" % (grid[rr][cc], idx, rr, cc))
                grid[rr][cc] = idx
    for rr in range(row_cnt):
        for cc in range(col_cnt):
            if grid[rr][cc] is None:
                raise ValueError("격자 (%d,%d)가 비어 있다" % (rr, cc))
    return grid
