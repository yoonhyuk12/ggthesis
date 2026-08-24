# QA 전용 MD 파서 — 조립기(md_to_blocks.py)와 무관하게 원고 MD를 항목 스트림으로 다시 읽는다
"""md_parse.py — 논문 MD를 (종류, 텍스트) 스트림으로 파싱한다.

조립 파이프라인의 파서를 쓰지 않고 QA를 위해 독립 구현했다. 제외 규칙은
staging/parse_report.md에 기록된 계약(코디네이터 승인분)을 따른다.

종류: h1 h2 h3 h4 / p / table_caption / figure_caption / figure_placeholder / table
표는 {"kind":"table","rows":[[cell,...],...]} 로 준다(헤더행 포함).
"""

import json
import re
import sys


def strip_inline(s):
    s = s.replace("**", "")
    s = s.replace("`", "'")          # 인라인 백틱 → 따옴표(조립 계약과 동일 결과 확인용)
    s = re.sub(r"\\([*_\[\]])", r"\1", s)
    return s


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [strip_inline(c.strip()) for c in line.split("|")]


DIVIDER = re.compile(r"^\|[\s:\-|]+\|?$")
EXCLUDED_SECTION = re.compile(r"^##\s+.*(본문 아님|내부 관리용)")


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    items = []
    i = 0
    in_fence = False
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        if not s:
            i += 1
            continue
        if s.startswith(">"):
            i += 1
            continue
        if re.fullmatch(r"-{3,}", s):
            i += 1
            continue
        if re.fullmatch(r"</?div[^>]*>", s):
            i += 1
            continue
        if EXCLUDED_SECTION.match(s):
            break                     # 본문 아님 섹션은 파일 끝까지 제외(계약)
        if s.startswith("#"):
            m = re.match(r"^(#+)\s*(.*)$", s)
            level = len(m.group(1))
            kind = "h1" if level in (1, 5, 6) else "h%d" % level
            items.append({"kind": kind, "text": strip_inline(m.group(2)).strip(),
                          "line": i + 1})
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                ln = lines[i].strip()
                if not DIVIDER.match(ln):
                    rows.append(split_row(ln))
                i += 1
            items.append({"kind": "table", "rows": rows, "line": i})
            continue
        text = s
        if text.startswith("- "):
            text = text[2:]
        text = strip_inline(text).strip()
        if re.match(r"^<표\s", text):
            kind = "table_caption"
        elif re.match(r"^<그림\s", text):
            kind = "figure_caption"
        elif text.startswith("[그림 삽입 예정"):
            kind = "figure_placeholder"
        else:
            kind = "p"
        items.append({"kind": kind, "text": text, "line": i + 1})
        i += 1
    return items


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}
    for p in sys.argv[1:]:
        out[p] = parse(p)
        counts = {}
        for it in out[p]:
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        print(p, counts, file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=1))
