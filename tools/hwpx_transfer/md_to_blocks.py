# 논문 MD 원고를 한 글자도 바꾸지 않고 구조화 블록 JSON으로 변환하는 결정적(비-LLM) 파서 — hwpx 조립기(T3) 입력 생성용
# 사용법: python tools/hwpx_transfer/md_to_blocks.py  (저장소 루트 기준, 표준 라이브러리만 사용)
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC_DIR = REPO / "논문구조"
OUT_DIR = Path(__file__).resolve().parent / "staging"

FILES = [
    ("01_서론.md", "ch01.blocks.json"),
    ("02_이론적배경.md", "ch02.blocks.json"),
    ("03_시스템개발.md", "ch03.blocks.json"),
    ("04_연구설계.md", "ch04.blocks.json"),
    ("05_실증분석결과.md", "ch05.blocks.json"),
    ("06_결론.md", "ch06.blocks.json"),
    ("부록1_설문지_양식.md", "apx1.blocks.json"),
    ("부록2_설문항목_근거매핑.md", "apx2.blocks.json"),
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^\s*-{3,}\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>")
TABLE_LINE_RE = re.compile(r"^\s*\|")
SEP_ROW_RE = re.compile(r"^\s*\|[\s:\-|]+\|?\s*$")
BULLET_RE = re.compile(r"^\s*-\s+(.*)$")
NUMBERED_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
LIST_MARKER_RE = re.compile(r"^\s*(?:-\s+|\d+\.\s+)")
DIV_TAG_RE = re.compile(r"^\s*</?div[^>]*>\s*$")
COMMENT_ONE_RE = re.compile(r"^\s*<!--.*-->\s*$")
FENCE_RE = re.compile(r"^```")
CAPTION_TABLE_RE = re.compile(r"^<표\s")
CAPTION_FIG_RE = re.compile(r"^<그림\s")
FIG_PLACEHOLDER_RE = re.compile(r"^\[그림 삽입 예정")
# "본문 아님"·"내부 관리용" 명시 h2 섹션은 코디네이터 승인에 따라 통째로 excluded 처리한다
EDITORIAL_H_RE = re.compile(r"본문 아님|내부 관리용")

ESCAPABLE = "*`|\\"


def scan_markers(text):
    """이스케이프를 무시한 비-리터럴 ** 및 ` 마커 개수를 센다(불균형 판정용)."""
    bold = code = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
            i += 2
            continue
        if text.startswith("**", i):
            bold += 1
            i += 2
            continue
        if c == "`":
            code += 1
            i += 1
            continue
        i += 1
    return bold, code


def parse_inline(text, ln, ev):
    """한 행의 인라인 텍스트를 runs로 분해한다. **…**는 bold run, 백틱은 마커만 제거(집계), \\x는 이스케이프 해제(집계)."""
    bold_n, code_n = scan_markers(text)
    bold_ok = bold_n % 2 == 0
    code_ok = code_n % 2 == 0
    if not bold_ok:
        ev.append(("unbalanced_bold", ln, text))
    if not code_ok:
        ev.append(("unbalanced_code", ln, text))
    runs = []
    buf = ""
    bold = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
            buf += text[i + 1]
            ev.append(("escape_unescaped", ln, text[i : i + 2]))
            i += 2
            continue
        if bold_ok and text.startswith("**", i):
            if buf:
                runs.append({"text": buf, "bold": bold})
                buf = ""
            bold = not bold
            i += 2
            continue
        if code_ok and c == "`":
            ev.append(("backtick_removed", ln, text))
            i += 1
            continue
        buf += c
        i += 1
    if buf:
        runs.append({"text": buf, "bold": bold})
    if not runs:
        runs = [{"text": "", "bold": False}]
    return runs


def cell_text(raw, ln, ev):
    """표 셀: 굵게 마커는 제거하되 텍스트 보존(집계), 백틱·이스케이프도 동일 처리한 verbatim 문자열을 돌려준다."""
    runs = parse_inline(raw, ln, ev)
    if any(r["bold"] for r in runs):
        ev.append(("cell_bold_removed", ln, raw))
    return "".join(r["text"] for r in runs)


def split_row(line, ln, ev):
    s = line.strip()
    if "\\|" in s:
        ev.append(("escaped_pipe", ln, line))
        s = s.replace("\\|", "\x00")
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip().replace("\x00", "\\|") for c in s.split("|")]


NORM_STRIP = "#|*`\\->"
HEAD_MARKER_RE = re.compile(r"^#{1,6}\s+")


def norm(s):
    """커버리지 비교용 정규화: 헤딩·리스트 마커, 마커 문자(#, |, **, `, -, \\, >), 공백을 제거한다.

    헤딩 마커와 인라인 마커를 먼저 벗겨야 "#### 1. 제목"·"**1. 제목**"(원본 행)과
    "1. 제목"(블록 텍스트)이 같은 리스트 마커 제거를 거쳐 대칭으로 비교된다.
    """
    s = HEAD_MARKER_RE.sub("", s, count=1)
    for ch in NORM_STRIP:
        s = s.replace(ch, "")
    s = LIST_MARKER_RE.sub("", s, count=1)
    return "".join(s.split())


def parse_file(fname):
    lines = (SRC_DIR / fname).read_text(encoding="utf-8-sig").splitlines()
    n = len(lines)
    blocks = []
    excluded = []
    excl_meta = []  # (reason, start_ln, end_ln, text) — 리포트용 행 범위 기록
    assign = [None] * (n + 1)  # 1-based: 각 행이 어디로 갔는지
    ev = []  # (kind, ln, detail)

    def add_excl(reason, start, end, text):
        entry = {"reason": reason, "text": text}
        excluded.append(entry)
        excl_meta.append((reason, start, end, text))
        for k in range(start, end + 1):
            assign[k] = ("excluded", entry)

    i = 0
    while i < n:
        line = lines[i]
        ln = i + 1
        if FENCE_RE.match(line):
            j = i + 1
            while j < n and not FENCE_RE.match(lines[j]):
                j += 1
            if j >= n:
                ev.append(("unclosed_fence", ln, ""))
                j = n - 1
            add_excl("ascii_diagram", ln, j + 1, "\n".join(lines[i : j + 1]))
            i = j + 1
            continue
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).rstrip()
            if level == 2 and EDITORIAL_H_RE.search(text):
                j = i + 1
                while j < n:
                    m2 = HEADING_RE.match(lines[j])
                    if m2 and len(m2.group(1)) <= 2:
                        break
                    j += 1
                add_excl("editorial_section", ln, j, "\n".join(lines[i:j]))
                i = j
                continue
            if level > 4:
                ev.append(("h_level_mapped", ln, "h%d→h1: %s" % (level, text)))
                level = 1
            if "**" in text or "`" in text:
                ev.append(("marker_in_heading", ln, text))
            block = {"type": "h%d" % level, "text": text}
            blocks.append(block)
            assign[ln] = ("text", text)
            i += 1
            continue
        if BLOCKQUOTE_RE.match(line):
            j = i
            while j < n and BLOCKQUOTE_RE.match(lines[j]):
                j += 1
            add_excl("editorial_blockquote", ln, j, "\n".join(lines[i:j]))
            i = j
            continue
        if HR_RE.match(line):
            add_excl("horizontal_rule", ln, ln, line)
            i += 1
            continue
        if not line.strip():
            add_excl("blank", ln, ln, "")
            i += 1
            continue
        if COMMENT_ONE_RE.match(line) or "<!--" in line:
            add_excl("html_comment", ln, ln, line)
            if not COMMENT_ONE_RE.match(line):
                ev.append(("nonstandard_comment", ln, line))
            i += 1
            continue
        if DIV_TAG_RE.match(line):
            add_excl("html_tag", ln, ln, line)
            ev.append(("html_tag", ln, line.strip()))
            i += 1
            continue
        if TABLE_LINE_RE.match(line):
            j = i
            while j < n and TABLE_LINE_RE.match(lines[j]):
                j += 1
            tlines = lines[i:j]
            header = [cell_text(c, ln, ev) for c in split_row(tlines[0], ln, ev)]
            body_start = 1
            if len(tlines) >= 2 and SEP_ROW_RE.match(tlines[1]):
                body_start = 2
                assign[ln + 1] = ("table_separator",)
            else:
                ev.append(("table_no_separator", ln, tlines[0]))
            block = {"type": "table", "header": header, "rows": []}
            assign[ln] = ("text", "".join(header))
            for k in range(body_start, len(tlines)):
                rln = ln + k
                row = [cell_text(c, rln, ev) for c in split_row(tlines[k], rln, ev)]
                if len(row) != len(header):
                    ev.append(("row_len_mismatch", rln, "%d칸(헤더 %d칸)" % (len(row), len(header))))
                block["rows"].append(row)
                assign[rln] = ("text", "".join(row))
            blocks.append(block)
            i = j
            continue
        if CAPTION_TABLE_RE.match(line):
            text = line.rstrip()
            blocks.append({"type": "table_caption", "text": text})
            assign[ln] = ("text", text)
            i += 1
            continue
        if CAPTION_FIG_RE.match(line):
            text = line.rstrip()
            blocks.append({"type": "figure_caption", "text": text})
            assign[ln] = ("text", text)
            i += 1
            continue
        if FIG_PLACEHOLDER_RE.match(line):
            text = line.rstrip()
            blocks.append({"type": "figure_placeholder", "text": text})
            assign[ln] = ("text", text)
            i += 1
            continue
        mb = BULLET_RE.match(line)
        mn = NUMBERED_RE.match(line) if not mb else None
        if mb or mn:
            content = (mb or mn).group(1).rstrip()
            ev.append(("bullet_stripped" if mb else "numbered_stripped", ln, line.rstrip()))
            runs = parse_inline(content, ln, ev)
            blocks.append({"type": "p", "runs": runs})
            assign[ln] = ("text", "".join(r["text"] for r in runs))
            i += 1
            continue
        runs = parse_inline(line.rstrip(), ln, ev)
        blocks.append({"type": "p", "runs": runs})
        assign[ln] = ("text", "".join(r["text"] for r in runs))
        i += 1

    # 조립기 처리 대상(<br>, &emsp;) 위치 집계 — 블록에 남은 verbatim 텍스트 기준
    for ln0, line in enumerate(lines, 1):
        a = assign[ln0]
        if a and a[0] == "text":
            if "<br" in a[1]:
                ev.append(("br_kept", ln0, a[1][:80]))
            if "&emsp;" in a[1]:
                ev.append(("emsp_kept", ln0, a[1][:80]))

    # 커버리지 자기검증: 모든 비어있지 않은 행이 블록 텍스트 또는 excluded에 존재해야 한다
    missing = []
    stats_cov = {"total": n, "nonempty": 0, "auto": 0, "checked": 0}
    for ln0, line in enumerate(lines, 1):
        if not line.strip():
            continue
        stats_cov["nonempty"] += 1
        a = assign[ln0]
        nl = norm(line)
        if a is None:
            missing.append((ln0, line, "행이 어떤 블록에도 배정되지 않음"))
            continue
        if a[0] == "table_separator":
            if re.fullmatch(r"[\s|:\-]*", line):
                stats_cov["auto"] += 1
            else:
                missing.append((ln0, line, "구분행으로 소비되었으나 내용 문자가 있음"))
            continue
        if not nl:
            stats_cov["auto"] += 1  # 마커·공백뿐인 행(수평선 등)
            continue
        target = a[1]["text"] if a[0] == "excluded" else a[1]
        if nl in norm(target):
            stats_cov["checked"] += 1
        else:
            missing.append((ln0, line, "정규화 텍스트가 배정 블록에 없음"))
    return lines, blocks, excluded, excl_meta, ev, missing, stats_cov


def block_stats(blocks):
    st = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "p": 0, "table_caption": 0,
          "table": 0, "table_rows": 0, "figure_caption": 0, "figure_placeholder": 0}
    for b in blocks:
        st[b["type"]] += 1
        if b["type"] == "table":
            st["table_rows"] += len(b["rows"])
    return st


EV_LABEL = {
    "backtick_removed": "인라인 백틱 마커 제거(텍스트 보존)",
    "escape_unescaped": "마크다운 이스케이프 해제(\\* 등 → 리터럴)",
    "cell_bold_removed": "표 셀 굵게 마커 제거(텍스트 보존)",
    "bullet_stripped": "리스트 글머리(- ) 제거(텍스트 보존)",
    "numbered_stripped": "번호 리스트 마커 제거(텍스트 보존)",
    "h_level_mapped": "h5/h6 헤딩을 h1로 매핑",
    "marker_in_heading": "헤딩 텍스트에 마커 문자 잔존(검토 필요)",
    "unbalanced_bold": "불균형 ** 마커 — 리터럴로 보존",
    "unbalanced_code": "불균형 백틱 — 리터럴로 보존",
    "table_no_separator": "구분행 없는 표(첫 행을 헤더로 처리)",
    "row_len_mismatch": "표 행 칸수와 헤더 칸수 불일치",
    "escaped_pipe": "이스케이프된 파이프(\\|) 셀 내 보존",
    "unclosed_fence": "닫히지 않은 코드펜스(EOF까지 소비)",
    "nonstandard_comment": "한 행에 닫히지 않은 HTML 주석",
    "html_tag": "단독 HTML 태그 행 제외",
    "br_kept": "<br> 태그 verbatim 보존(조립기가 셀 내 줄바꿈으로 변환 예정)",
    "emsp_kept": "&emsp; 엔티티 verbatim 보존(조립기가 전각 공백으로 변환 예정)",
}
REASON_LABEL = {
    "editorial_blockquote": "blockquote(편집 메모)",
    "horizontal_rule": "수평선(---)",
    "blank": "빈 줄",
    "html_comment": "HTML 주석",
    "ascii_diagram": "코드펜스 ASCII 다이어그램",
    "editorial_section": "본문 아님 명시 섹션",
    "html_tag": "단독 HTML 태그 행",
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    report.append("# MD → blocks 변환 리포트 (T2)")
    report.append("")
    report.append("`python tools/hwpx_transfer/md_to_blocks.py` 실행 산출물이다. 8개 원고 MD를 verbatim 블록 JSON으로 변환하고, "
                  "모든 비어있지 않은 원본 행이 블록 텍스트 또는 excluded에 존재하는지 자기검증한 결과를 담는다.")
    report.append("")
    report.append("처리 방침(코디네이터 승인, 2026-07-25): 코드펜스 ASCII 다이어그램 3곳과 \"본문 아님\"/\"내부 관리용\" 명시 h2 섹션 2곳은 "
                  "excluded(원문 전문 보존), 부록2 h6 제목은 h1로 매핑, `<div>` 단독 행은 excluded(html_tag), "
                  "`<br>`·`&emsp;`는 verbatim 보존 후 아래 '조립기 처리 목록'에 인계한다.")
    report.append("")

    all_missing = []
    per_file = []
    total_blocks = 0
    for src, dst in FILES:
        lines, blocks, excluded, excl_meta, ev, missing, cov = parse_file(src)
        doc = {"source": src, "blocks": blocks, "excluded": excluded}
        out_path = OUT_DIR / dst
        payload = json.dumps(doc, ensure_ascii=False, indent=2)
        json.loads(payload)  # 유효 JSON 자기검증
        out_path.write_text(payload + "\n", encoding="utf-8")
        per_file.append((src, dst, blocks, excluded, excl_meta, ev, missing, cov))
        all_missing.extend((src, ln, line, why) for ln, line, why in missing)
        total_blocks += len(blocks)
        print("%s -> %s: blocks=%d excluded=%d missing=%d" % (src, dst, len(blocks), len(excluded), len(missing)))

    # 1. 파일별 블록 통계
    report.append("## 1. 파일별 블록 통계")
    report.append("")
    report.append("| 파일 | h1 | h2 | h3 | h4 | p | 표 캡션 | 표 | 표 행(데이터) | 그림 캡션 | 그림 자리 | excluded |")
    report.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        st = block_stats(blocks)
        report.append("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            src, st["h1"], st["h2"], st["h3"], st["h4"], st["p"], st["table_caption"],
            st["table"], st["table_rows"], st["figure_caption"], st["figure_placeholder"], len(excluded)))
    report.append("")

    # 2. 커버리지 자기검증
    report.append("## 2. 커버리지 자기검증")
    report.append("")
    report.append("모든 비어있지 않은 원본 행에 대해 (a) 블록 text/runs/cell 포함 또는 (b) excluded 기록을 확인했다. "
                  "비교 전 리스트 글머리와 마커 문자(`#`, `|`, `**`, 백틱, `-`, `\\`, `>`)·공백을 정규화했다. "
                  "'마커뿐'은 정규화 후 내용이 남지 않는 행(수평선·표 구분행 등)이다.")
    report.append("")
    report.append("| 파일 | 총 행 | 비어있지 않은 행 | 내용 대조 통과 | 마커뿐(자동 통과) | 누락 |")
    report.append("|---|---:|---:|---:|---:|---:|")
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        report.append("| %s | %d | %d | %d | %d | %d |" % (
            src, cov["total"], cov["nonempty"], cov["checked"], cov["auto"], len(missing)))
    report.append("")
    if all_missing:
        report.append("**누락 행 목록(원인 분석 필요):**")
        report.append("")
        for src, ln, line, why in all_missing:
            report.append("- %s:%d — %s — `%s`" % (src, ln, why, line))
    else:
        report.append("**누락 0 — 8개 파일 전체에서 커버리지 목표를 충족했다.**")
    report.append("")

    # 3. 제외 블록 전체 목록
    report.append("## 3. 제외 블록 전체 목록 (파일별, 사유·행 범위·전문)")
    report.append("")
    report.append("빈 줄(blank)은 개수만 표기하고, 그 외 모든 제외 블록은 원문 전문을 기록한다.")
    report.append("")
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        report.append("### %s" % src)
        report.append("")
        blanks = [m for m in excl_meta if m[0] == "blank"]
        if blanks:
            report.append("- 빈 줄 %d개 (excluded에 `{\"reason\": \"blank\", \"text\": \"\"}`로 기록)" % len(blanks))
        for reason, start, end, text in excl_meta:
            if reason == "blank":
                continue
            rng = "%d행" % start if start == end else "%d~%d행" % (start, end)
            report.append("- **%s** (%s) — %s" % (reason, REASON_LABEL.get(reason, reason), rng))
            report.append("")
            report.append("````")
            report.append(text if text else "(빈 텍스트)")
            report.append("````")
        report.append("")

    # 4. 마커 처리 집계
    report.append("## 4. 마커 처리 집계")
    report.append("")
    any_ev = False
    order = ["cell_bold_removed", "backtick_removed", "bullet_stripped", "numbered_stripped",
             "escape_unescaped", "h_level_mapped", "escaped_pipe", "row_len_mismatch",
             "table_no_separator", "marker_in_heading", "unbalanced_bold", "unbalanced_code",
             "unclosed_fence", "nonstandard_comment", "html_tag"]
    for kind in order:
        items = []
        for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
            items.extend((src, ln, detail) for k, ln, detail in ev if k == kind)
        if not items:
            continue
        any_ev = True
        report.append("### %s — %d건" % (EV_LABEL[kind], len(items)))
        report.append("")
        for src, ln, detail in items:
            report.append("- %s:%d — `%s`" % (src, ln, detail.replace("`", "'")))
        report.append("")
    if not any_ev:
        report.append("(해당 없음)")
        report.append("")

    # 5. 조립기 처리 목록 (T3 인계)
    report.append("## 5. 조립기 처리 목록 (T3 인계)")
    report.append("")
    report.append("파서는 아래 항목을 verbatim으로 보존만 했다. hwpx 조립 시 다음 변환·재구성이 필요하다.")
    report.append("")
    br_items, emsp_items = [], []
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        br_items.extend((src, ln) for k, ln, d in ev if k == "br_kept")
        emsp_items.extend((src, ln) for k, ln, d in ev if k == "emsp_kept")
    report.append("### 5-1. `<br>` → 셀 내 줄바꿈 변환 대상 (%d개 행)" % len(br_items))
    report.append("")
    for src, ln in br_items:
        report.append("- %s:%d (리커트 척도 표 헤더 셀)" % (src, ln))
    report.append("")
    report.append("### 5-2. `&emsp;` → 전각 공백 변환 대상 (%d개 행)" % len(emsp_items))
    report.append("")
    for src, ln in emsp_items:
        report.append("- %s:%d" % (src, ln))
    report.append("")
    report.append("### 5-3. ASCII 다이어그램 → 그림 개체 재구성 대상")
    report.append("")
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        for reason, start, end, text in excl_meta:
            if reason == "ascii_diagram":
                first = text.splitlines()[1] if len(text.splitlines()) > 1 else ""
                report.append("- %s:%d~%d행 — excluded(ascii_diagram)에 전문 보존. 캡션 블록이 삽입 자리를 표시한다." % (src, start, end))
    report.append("")
    report.append("부록1 표지 박스(부록1_설문지_양식.md:10~20행)는 그림이 아니라 설문지 표지 텍스트이므로, 조립 시 메인이 별도 서식(가운데 정렬 박스)으로 재구성해야 한다. 원문 전문은 위 제3절 부록1 항목에 있다.")
    report.append("")
    report.append("### 5-4. 제외된 편집용 섹션·HTML 태그 (본문에 넣지 말 것)")
    report.append("")
    for src, dst, blocks, excluded, excl_meta, ev, missing, cov in per_file:
        for reason, start, end, text in excl_meta:
            if reason in ("editorial_section", "html_tag"):
                rng = "%d행" % start if start == end else "%d~%d행" % (start, end)
                head = text.splitlines()[0] if text else ""
                report.append("- %s:%s — %s — `%s`" % (src, rng, REASON_LABEL[reason], head.replace("`", "'")))
    report.append("")
    report.append("### 5-5. 기타 계약 참고")
    report.append("")
    report.append("- 부록2 첫 행 `######`(h6) 제목은 승인에 따라 h1로 매핑했다(제4절 집계 참조).")
    report.append("- 표 구분행(`|:---:|…`)은 표 구조로 소비했고 excluded에는 넣지 않았다(내용 문자 없음 검증 통과).")
    report.append("- `[DATA PENDING…]`·`[확정 필요…]`·`[그림 삽입 예정…]` 표시는 본문의 일부로 그대로 유지했다.")
    report.append("")

    (OUT_DIR / "parse_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("report: %s" % (OUT_DIR / "parse_report.md"))
    print("total blocks=%d, coverage missing=%d" % (total_blocks, len(all_missing)))
    return 1 if all_missing else 0


if __name__ == "__main__":
    sys.exit(main())
