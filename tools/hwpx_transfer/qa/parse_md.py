# 원고 MD를 QA 기준(ground truth)으로 독립 파싱해 제목·문단·표·제외블록으로 나누는 파서
"""parse_md.py — 조립기(md_to_blocks.py)와 무관하게 MD를 다시 파싱한다.

산출 항목:
  {"kind":"h1|h2|h3|h4","text":..,"line":..}
  {"kind":"para","text":..,"line":..}          # 표 캡션·그림 캡션·그림자리 포함(별도 sub 표시)
  {"kind":"table","rows":[[cell,..],..],"line":..}
  {"kind":"excluded","reason":..,"text":..,"line":..}
"""
import json
import re
import sys

TABLE_CAP = re.compile(r"^<표\s")
FIG_CAP = re.compile(r"^<그림\s")
FIG_PLACE = re.compile(r"^\[그림 삽입 예정")
# "본문 아님"/"내부 관리용"이 제목에 명시된 h2 섹션은 통째로 제외
EDITORIAL_H2 = re.compile(r"본문 아님|내부 관리용")


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_sep_row(line):
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    items = []
    i = 0
    in_editorial_section = False
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        ln = i + 1

        if not s:
            i += 1
            continue

        # 코드펜스: 통째로 제외
        if s.startswith("```"):
            j = i + 1
            buf = [raw]
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            if j < len(lines):
                buf.append(lines[j])
            items.append({"kind": "excluded", "reason": "code_fence",
                          "text": "\n".join(buf), "line": ln})
            i = j + 1
            continue

        # 헤딩
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 2 and EDITORIAL_H2.search(text):
                in_editorial_section = True
                items.append({"kind": "excluded", "reason": "editorial_section_head",
                              "text": s, "line": ln})
                i += 1
                continue
            in_editorial_section = False
            items.append({"kind": "h%d" % min(level, 4), "text": text, "line": ln})
            i += 1
            continue

        if in_editorial_section:
            items.append({"kind": "excluded", "reason": "editorial_section_body",
                          "text": s, "line": ln})
            i += 1
            continue

        # blockquote (편집 메모)
        if s.startswith(">"):
            buf = []
            j = i
            while j < len(lines) and (lines[j].strip().startswith(">") or
                                      (lines[j].strip() == "" and
                                       j + 1 < len(lines) and
                                       lines[j + 1].strip().startswith(">"))):
                buf.append(lines[j])
                j += 1
            items.append({"kind": "excluded", "reason": "editorial_blockquote",
                          "text": "\n".join(buf), "line": ln})
            i = j
            continue

        # 수평선
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", s):
            items.append({"kind": "excluded", "reason": "horizontal_rule",
                          "text": s, "line": ln})
            i += 1
            continue

        # 단독 HTML 태그
        if re.fullmatch(r"</?div[^>]*>", s):
            items.append({"kind": "excluded", "reason": "html_tag",
                          "text": s, "line": ln})
            i += 1
            continue

        # 표
        if s.startswith("|"):
            rows = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                if not is_sep_row(lines[j]):
                    rows.append(split_row(lines[j]))
                j += 1
            items.append({"kind": "table", "rows": rows, "line": ln})
            i = j
            continue

        # 그 외 = 본문 문단 (캡션·그림자리 포함)
        sub = "p"
        if TABLE_CAP.match(s):
            sub = "table_caption"
        elif FIG_CAP.match(s):
            sub = "figure_caption"
        elif FIG_PLACE.match(s):
            sub = "figure_placeholder"
        items.append({"kind": "para", "sub": sub, "text": s, "line": ln})
        i += 1
    return items


if __name__ == "__main__":
    items = parse(sys.argv[1])
    json.dump(items, open(sys.argv[2], "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    from collections import Counter
    print(sys.argv[1], Counter(x["kind"] for x in items))
