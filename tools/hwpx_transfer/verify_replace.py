# 기존 hwpx에 타깃 치환을 적용한 결과가 원본을 의도한 만큼만 바꿨는지 대조하는 검증기
"""verify_replace.py — hwpx 타깃 치환 결과 검증 (검증 1~8).

사용 예:
    python tools/hwpx_transfer/verify_replace.py base.hwpx out.hwpx 3

`fill_hwpx.py replace --map` 으로 부분 치환한 산출물을 원본과 대조해 8가지를 본다.
전부 통과하면 exit 0, 하나라도 어긋나면 exit 1이다. 인자·파일 오류는 exit 2.

    1. ZIP 엔트리 목록·순서·압축 방식이 같은가
    2. 섹션 XML 외 모든 엔트리의 SHA256이 같은가
    3. 문단 개수가 같은가
    4. 달라진 문단 수가 기대치와 정확히 같은가 (초과분 = 오치환)
    5. 달라진 문단의 linesegarray가 제거됐거나 textpos가 새 길이 이내인가
    6. 전체 run·t 개수가 같은가
    7. 빨간 charPr별 run 개수가 같은가
    8. 가이드 마커 접두사가 빨간 run 안에 들어 있는 횟수가 같은가

8번이 이 검증기의 존재 이유다. 치환 키가 run 경계를 가로지르면 매칭 범위 전체가
첫 run의 글자모양을 따라가므로, 빨간 마커의 앞부분이 검정으로 바뀐다. 이때 run 개수도
t 개수도 빨간 run 개수도 그대로라 1~7로는 잡히지 않고, fill_hwpx.py는 exit 0을
반환하며 check --strict·validate.py도 통과한다.

빨간 charPr id는 하드코딩하지 않고 header.xml의 textColor="#FF0000"에서 끌어온다.
마커 접두사 5종은 blocks_to_hwpx.py의 GUIDE_MARKER_RE와 같은 목록이다.

zipfile + re(표준 라이브러리)만 쓴다.
"""

import hashlib
import re
import sys
import zipfile

# blocks_to_hwpx.py의 GUIDE_MARKER_RE와 동일한 다섯 접두사와 대괄호 없는 `실험전`.
# 본문이 아닌 것(미확정 자리·인용·그림 지시)만 빨간 글자로 나가야 한다.
MARKER_PREFIXES = (
    "[DATA PENDING",
    "[확정 필요",
    "[CITE_TODO",
    "[그림 삽입 예정",
    "[UNVERIFIED",
    "실험전",
)

RED_COLOR = "#FF0000"

SECTION_RE = re.compile(r"^Contents/section\d+\.xml$")
P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
T_TAG_RE = re.compile(r"<(?:\w+:)?t(?![\w:])")
RUN_TAG_RE = re.compile(r"<(?:\w+:)?run(?![\w:])")
# 자기닫힘 run(<hp:run charPrIDRef="7"/>)을 먼저 잡는다. 열림 태그 대안을 앞에 두면
# `[^>]*?>`가 `…"7"/>`까지 삼킨 뒤 `.*?</run>`이 다음 run으로 넘어가 빈 run이 이웃
# run의 텍스트를 가로챈다 — 2026-09-12 운영본에서 빨간 마커 1건을 검정으로 오판한 원인.
RUN_BLOCK_RE = re.compile(
    r"<(?:\w+:)?run\b[^>]*?/>|<(?:\w+:)?run\b[^>]*?(?<!/)>.*?</(?:\w+:)?run>", re.S)
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')
CHARPR_TAG_RE = re.compile(r"<(?:\w+:)?charPr\b[^>]*?>")
ATTR_ID_RE = re.compile(r'\bid="(\d+)"')
ATTR_COLOR_RE = re.compile(r'\btextColor="([^"]*)"')
LINESEG_RE = re.compile(r"<(?:\w+:)?linesegarray[\s>]")
TEXTPOS_RE = re.compile(r'textpos="(\d+)"')


# ── hwpx 읽기 ────────────────────────────────────────────────────────────────
def section_names(zf):
    """문서 순서를 유지한 본문 섹션 엔트리 목록."""
    return [i.filename for i in zf.infolist() if SECTION_RE.match(i.filename)]


def red_charpr_ids(zf):
    """header.xml에서 textColor가 빨강인 charPr id 집합 — 하드코딩하지 않는다."""
    try:
        header = zf.read("Contents/header.xml").decode("utf-8")
    except KeyError:
        return set()
    ids = set()
    for tag in CHARPR_TAG_RE.findall(header):
        color = ATTR_COLOR_RE.search(tag)
        ident = ATTR_ID_RE.search(tag)
        if color and ident and color.group(1).upper() == RED_COLOR:
            ids.add(ident.group(1))
    return ids


def paragraph_spans(xml):
    """(여는태그 시작, 여는태그 끝, 닫는태그 시작, 닫는태그 끝) 목록 — 중첩 포함."""
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
    """이 문단이 직접 소유한 XML — 중첩 표 셀 문단은 잘라낸다.

    표를 감싼 바깥 문단이 셀 텍스트까지 끌어안으면 같은 내용이 두 번 집계돼
    '유일한 구절'과 '달라진 문단 수' 판정이 전부 어긋난다.
    """
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


def own_paragraphs(zf):
    """모든 섹션의 자기 소유 문단 XML을 문서 순서대로."""
    out = []
    for name in section_names(zf):
        xml = zf.read(name).decode("utf-8")
        spans = paragraph_spans(xml)
        for span in spans:
            out.append((name, own_segment(xml, span, spans)))
    return out


def body_xml(zf):
    """전 섹션 XML을 이어붙인 것 — 전역 개수 세기용."""
    return "".join(zf.read(n).decode("utf-8") for n in section_names(zf))


def run_texts(xml):
    """(charPrIDRef, 텍스트) 목록. charPrIDRef가 없는 run은 None."""
    out = []
    for m in RUN_BLOCK_RE.finditer(xml):
        block = m.group(0)
        ref = CHARPR_REF_RE.search(block[:block.find(">") + 1])
        text = "".join(T_TEXT_RE.findall(block))
        out.append((ref.group(1) if ref else None, text))
    return out


def marker_census(xml, red_ids):
    """마커 접두사가 (본문 전체 run, 빨간 run)에 각각 몇 번 나오는가.

    run 단위로 세어 합산한다. 전체 텍스트를 이어붙여 세면 run 경계에서
    없던 접두사가 생겨날 수 있다.
    """
    census = {}
    runs = run_texts(xml)
    for prefix in MARKER_PREFIXES:
        total = sum(text.count(prefix) for _, text in runs)
        red = sum(text.count(prefix) for ref, text in runs if ref in red_ids)
        census[prefix] = (total, red)
    return census


def para_text(seg):
    return "".join(T_TEXT_RE.findall(seg))


# ── 검증 ─────────────────────────────────────────────────────────────────────
def verify(base_path, out_path, expected_changed):
    failures = []

    def check(no, title, ok, detail=""):
        print(f"[{no}] {title}: {'OK' if ok else 'NG'}{'  ' + detail if detail else ''}")
        if not ok:
            failures.append(f"{no}. {title}")
        return ok

    with zipfile.ZipFile(base_path) as za, zipfile.ZipFile(out_path) as zb:
        ia, ib = za.infolist(), zb.infolist()

        names_ok = [e.filename for e in ia] == [e.filename for e in ib]
        method_ok = [e.compress_type for e in ia] == [e.compress_type for e in ib]
        check(1, "ZIP 엔트리 목록·순서·압축 방식 동일", names_ok and method_ok,
              f"엔트리 {len(ia)}개 / {len(ib)}개")
        if not names_ok:
            print("    목록이 다르면 이후 대조는 의미가 없다 — 치환기가 ZIP을 재작성했다.")
            print("\n결과: FAIL — " + ", ".join(failures))
            return 1

        sections = set(section_names(za))
        differing, non_section_diff = [], []
        for entry in ia:
            name = entry.filename
            ha = hashlib.sha256(za.read(name)).hexdigest()
            hb = hashlib.sha256(zb.read(name)).hexdigest()
            if ha != hb:
                differing.append(name)
                if name not in sections:
                    non_section_diff.append(name)
        check(2, "섹션 XML 외 엔트리 SHA256 동일", not non_section_diff,
              f"달라진 엔트리 {differing or '없음'}"
              + (f" / 섹션 아닌 것 {non_section_diff}" if non_section_diff else ""))

        pa, pb = own_paragraphs(za), own_paragraphs(zb)
        count_ok = len(pa) == len(pb)
        check(3, "문단 개수 동일", count_ok, f"{len(pa)} / {len(pb)}")

        if count_ok:
            changed = [i for i, (a, b) in enumerate(zip(pa, pb)) if a[1] != b[1]]
            check(4, "달라진 문단 수가 기대치와 일치",
                  len(changed) == expected_changed,
                  f"기대 {expected_changed} / 실제 {len(changed)} {changed[:20]}"
                  + (" …" if len(changed) > 20 else ""))

            stale = []
            for i in changed:
                seg = pb[i][1]
                if not LINESEG_RE.search(seg):
                    continue  # 캐시가 제거됐다 = 한글이 다시 조판한다
                positions = [int(v) for v in TEXTPOS_RE.findall(seg)]
                if not positions or max(positions) > len(para_text(seg)):
                    stale.append(i)
            check(5, "달라진 문단의 lineseg 제거 또는 textpos 이내", not stale,
                  f"문제 문단 {stale or '없음'}")
        else:
            check(4, "달라진 문단 수가 기대치와 일치", False, "문단 개수가 달라 대조 불가")
            check(5, "달라진 문단의 lineseg 제거 또는 textpos 이내", False, "대조 불가")

        xa, xb = body_xml(za), body_xml(zb)
        run_a, run_b = len(RUN_TAG_RE.findall(xa)), len(RUN_TAG_RE.findall(xb))
        t_a, t_b = len(T_TAG_RE.findall(xa)), len(T_TAG_RE.findall(xb))
        check(6, "전체 run·t 개수 동일", run_a == run_b and t_a == t_b,
              f"run {run_a}/{run_b}, t {t_a}/{t_b}")

        red_ids = red_charpr_ids(za)
        ca = {r: len(re.findall(r'charPrIDRef="%s"' % r, xa)) for r in sorted(red_ids)}
        cb = {r: len(re.findall(r'charPrIDRef="%s"' % r, xb)) for r in sorted(red_ids)}
        used = {r: v for r, v in ca.items() if v}
        check(7, "빨간 charPr별 run 개수 동일", ca == cb,
              f"빨간 charPr id {sorted(red_ids) or '없음'} / 사용 중 {used or '없음'}")
        if ca != cb:
            for r in sorted(red_ids):
                if ca[r] != cb[r]:
                    print(f"    NG charPr {r}: {ca[r]} -> {cb[r]}")

        ma, mb = marker_census(xa, red_ids), marker_census(xb, red_ids)
        check(8, "마커 접두사의 빨간 run 소속 횟수 동일", ma == mb,
              "(전체, 빨강) " + ", ".join(
                  f"{p}={ma[p]}" for p in MARKER_PREFIXES if ma[p][0]))
        if ma != mb:
            for prefix in MARKER_PREFIXES:
                if ma[prefix] != mb[prefix]:
                    print(f"    NG {prefix}: base(전체,빨강)={ma[prefix]}"
                          f" -> out={mb[prefix]}")
            print("    치환 키가 run 경계를 가로질러 마커 글자색이 검정으로 넘어갔다."
                  " 키를 마커 안쪽이나 바깥쪽 한쪽으로 좁혀 다시 치환하라.")

    if failures:
        print("\n결과: FAIL — " + ", ".join(failures))
        return 1
    print("\n결과: PASS — 검증 1~8 전부 통과")
    return 0


def main(argv):
    # Windows 콘솔 기본 코드페이지(cp949)에서 줄표·한글이 깨지므로 둘 다 utf-8로 고정한다.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(argv) != 4:
        print("사용법: python tools/hwpx_transfer/verify_replace.py "
              "<base.hwpx> <out.hwpx> <기대 변경 문단 수>", file=sys.stderr)
        return 2
    base_path, out_path, expected = argv[1], argv[2], argv[3]
    if not expected.isdigit():
        print(f"오류: 기대 변경 문단 수는 0 이상의 정수여야 한다 — {expected!r}",
              file=sys.stderr)
        return 2
    try:
        return verify(base_path, out_path, int(expected))
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"오류: hwpx를 열 수 없다 — {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
