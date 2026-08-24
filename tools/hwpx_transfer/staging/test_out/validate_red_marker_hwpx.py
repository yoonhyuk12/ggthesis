# -*- coding: utf-8 -*-
"""red_marker_test.hwpx의 빨간 마커·제외 대상·텍스트 보존을 검증한다."""

import collections
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parents[4]
NEW_HWPX = pathlib.Path(__file__).with_name("red_marker_test.hwpx")
BASELINE_HWPX = pathlib.Path(__file__).with_name("red_marker_baseline.hwpx")
REPORT = pathlib.Path(__file__).with_name("red_marker_validation.txt")
TEMPLATE = next(ROOT.glob("공학대학원_건축안전_윤혁_*.hwpx"))

PREFIXES = [
    "[DATA PENDING",
    "[확정 필요",
    "[CITE_TODO",
    "[그림 삽입 예정",
    "[UNVERIFIED",
]
EXPECTED = {
    "[DATA PENDING": 546,
    "[확정 필요": 41,
    "[CITE_TODO": 21,
    "[그림 삽입 예정": 6,
    "[UNVERIFIED": 1,
}
MARKER_RE = re.compile(
    r"\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]"
)
REFERENCE_RE = re.compile(r"\[\d{2}(?:,\s*\d{2})+\]")
CI_RE = re.compile(r"\[(?:0|1)\.\d+,\s*(?:0|1)\.\d+\]")
FORM_RE = re.compile(r"\[양식 [12]:[^\]]*\]")
REPRESENTATIVES = ["[38, 41, 44]", "[0.974, 0.991]", "[양식 1", "[양식 2"]


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def signature(element, root=True):
    attrs = tuple(sorted(
        (key, value)
        for key, value in element.attrib.items()
        if not (root and key in ("id", "textColor"))
    ))
    return local_name(element.tag), attrs, tuple(signature(child, False) for child in element)


def read_parts(path):
    with zipfile.ZipFile(path) as archive:
        bad_entry = archive.testzip()
        parts = {
            name: archive.read(name)
            for name in ["Contents/header.xml", "Contents/section1.xml", "Contents/section2.xml"]
        }
    return bad_entry, parts


def parse_char_prs(header_bytes):
    root = ET.fromstring(header_bytes)
    char_prs = {
        element.get("id"): element
        for element in root.iter()
        if local_name(element.tag) == "charPr"
    }
    char_properties = next(
        element for element in root.iter() if local_name(element.tag) == "charProperties"
    )
    return char_prs, int(char_properties.get("itemCnt"))


def direct_run_entries(section_root):
    entries = []

    def visit(element, in_table=False):
        current_in_table = in_table or local_name(element.tag) == "tbl"
        if local_name(element.tag) == "run":
            text = "".join(
                child.text or ""
                for child in element
                if local_name(child.tag) == "t"
            )
            if text:
                entries.append({
                    "char": element.get("charPrIDRef"),
                    "text": text,
                    "in_table": current_in_table,
                })
        for child in element:
            visit(child, current_in_table)

    visit(section_root)
    return entries


def full_text(section_root):
    return "".join(
        element.text or ""
        for element in section_root.iter()
        if local_name(element.tag) == "t"
    )


errors = []
new_bad, new_parts = read_parts(NEW_HWPX)
baseline_bad, baseline_parts = read_parts(BASELINE_HWPX)
template_bad, template_parts = read_parts(TEMPLATE)
new_char_prs, new_declared_count = parse_char_prs(new_parts["Contents/header.xml"])
template_char_prs, template_declared_count = parse_char_prs(template_parts["Contents/header.xml"])
red_ids = {
    char_id
    for char_id, element in new_char_prs.items()
    if element.get("textColor", "").upper() == "#FF0000"
}

new_section = ET.fromstring(new_parts["Contents/section2.xml"])
baseline_section = ET.fromstring(baseline_parts["Contents/section2.xml"])
entries = direct_run_entries(new_section)
section1_entries = direct_run_entries(ET.fromstring(new_parts["Contents/section1.xml"]))
section1_red_marker_count = sum(
    1
    for entry in section1_entries
    if entry["char"] in red_ids and MARKER_RE.fullmatch(entry["text"])
)
red_entries = [entry for entry in entries if entry["char"] in red_ids]
red_marker_entries = [entry for entry in red_entries if MARKER_RE.fullmatch(entry["text"])]
red_non_markers = [entry for entry in red_entries if not MARKER_RE.fullmatch(entry["text"])]

all_marker_occurrences = []
marker_not_red = []
for entry in entries:
    for match in MARKER_RE.finditer(entry["text"]):
        record = (entry, match.group(0))
        all_marker_occurrences.append(record)
        if entry["char"] not in red_ids:
            marker_not_red.append(record)

type_counts = collections.Counter()
for entry in red_marker_entries:
    prefix = next(prefix for prefix in PREFIXES if entry["text"].startswith(prefix))
    type_counts[prefix] += 1

inside_table_count = sum(1 for entry in red_marker_entries if entry["in_table"])
outside_table_count = len(red_marker_entries) - inside_table_count

reference_matches = []
ci_matches = []
form_matches = []
for entry in entries:
    if entry["in_table"]:
        reference_matches.extend((entry, m.group(0)) for m in REFERENCE_RE.finditer(entry["text"]))
    ci_matches.extend((entry, m.group(0)) for m in CI_RE.finditer(entry["text"]))
    form_matches.extend((entry, m.group(0)) for m in FORM_RE.finditer(entry["text"]))

reference_red = [item for item in reference_matches if item[0]["char"] in red_ids]
ci_red = [item for item in ci_matches if item[0]["char"] in red_ids]
form_red = [item for item in form_matches if item[0]["char"] in red_ids]

new_paragraph_count = sum(1 for child in new_section if local_name(child.tag) == "p")
baseline_paragraph_count = sum(1 for child in baseline_section if local_name(child.tag) == "p")
new_text = full_text(new_section)
baseline_text = full_text(baseline_section)
full_text_equal = new_text == baseline_text
marker_stripped_equal = MARKER_RE.sub("", new_text) == MARKER_RE.sub("", baseline_text)

used_red_counts = collections.Counter(entry["char"] for entry in red_marker_entries)
style_matches = {}
for red_id in sorted(used_red_counts, key=int):
    red_signature = signature(new_char_prs[red_id])
    matches = [
        char_id
        for char_id, element in template_char_prs.items()
        if element.get("textColor", "").upper() != "#FF0000"
        and signature(element) == red_signature
    ]
    style_matches[red_id] = matches

representative_evidence = {}
for needle in REPRESENTATIVES:
    all_hits = sum(entry["text"].count(needle) for entry in entries)
    red_hits = sum(entry["text"].count(needle) for entry in red_entries)
    representative_evidence[needle] = (all_hits, red_hits)

if new_bad is not None or baseline_bad is not None or template_bad is not None:
    errors.append("ZIP CRC 오류가 있다")
if len(red_entries) != 615:
    errors.append("빨간 run 개수가 615가 아니다")
if len(red_marker_entries) != 615:
    errors.append("빨간 마커 run 개수가 615가 아니다")
if red_non_markers:
    errors.append("마커가 아닌 빨간 run이 있다")
if marker_not_red:
    errors.append("검은색으로 남은 마커가 있다")
if dict(type_counts) != EXPECTED:
    errors.append("종류별 마커 개수가 기대값과 다르다")
if reference_red or ci_red or form_red:
    errors.append("제외 대상이 빨간 run에 들어갔다")
if not reference_matches or len(ci_matches) != 5 or len(form_matches) != 2:
    errors.append("제외 대상 원문 개수가 예상과 다르다")
if new_paragraph_count != 668 or baseline_paragraph_count != 668:
    errors.append("본문 문단 수가 668이 아니다")
if not full_text_equal or not marker_stripped_equal:
    errors.append("기준 조립분과 본문 텍스트가 다르다")
if new_declared_count != len(new_char_prs):
    errors.append("새 header.xml itemCnt와 실제 charPr 개수가 다르다")
if template_declared_count != len(template_char_prs):
    errors.append("양식 header.xml itemCnt와 실제 charPr 개수가 다르다")
if any(not matches for matches in style_matches.values()):
    errors.append("사용한 빨간 charPr 중 원본과 서식이 일치하지 않는 항목이 있다")

lines = [
    "검증 결과=" + ("PASS" if not errors else "FAIL"),
    "새 HWPX ZIP CRC=" + ("정상" if new_bad is None else str(new_bad)),
    "빨간 run 수=%d" % len(red_entries),
    "빨간 마커 run 수=%d" % len(red_marker_entries),
    "검은색으로 남은 마커 수=%d" % len(marker_not_red),
    "마커가 아닌 빨간 run 수=%d" % len(red_non_markers),
    "표 안 빨간 마커 수=%d" % inside_table_count,
    "표 밖 빨간 마커 수=%d" % outside_table_count,
    "전면부 목차에 복제된 빨간 마커 수=%d" % section1_red_marker_count,
    "블록 재집계 참고=05장 전체 553, 05장 표 셀 491, 전 장 표 셀 499",
]
for prefix in PREFIXES:
    lines.append("종류 %s=%d" % (prefix, type_counts[prefix]))
lines.extend([
    "표 안 근거 문헌 참조번호 수=%d, 빨간 run 수=%d" % (len(reference_matches), len(reference_red)),
    "신뢰구간 수 수=%d, 빨간 run 수=%d" % (len(ci_matches), len(ci_red)),
    "설문 양식 라벨 수=%d, 빨간 run 수=%d" % (len(form_matches), len(form_red)),
])
for needle, (all_hits, red_hits) in representative_evidence.items():
    lines.append("대표 제외 %s 전체=%d 빨강=%d" % (needle, all_hits, red_hits))
lines.extend([
    "새 본문 문단 수=%d" % new_paragraph_count,
    "기준 본문 문단 수=%d" % baseline_paragraph_count,
    "전체 본문 텍스트 동일=%s" % full_text_equal,
    "마커 제거 후 본문 텍스트 동일=%s" % marker_stripped_equal,
    "양식 charPr itemCnt=%d 실제=%d" % (template_declared_count, len(template_char_prs)),
    "새 charPr itemCnt=%d 실제=%d" % (new_declared_count, len(new_char_prs)),
    "사용 빨간 charPr별 run 수=" + ", ".join(
        "%s:%d" % (char_id, used_red_counts[char_id])
        for char_id in sorted(used_red_counts, key=int)
    ),
    "빨간 charPr와 동일 서식 원본=" + ", ".join(
        "%s->%s" % (char_id, "/".join(style_matches[char_id]) or "없음")
        for char_id in sorted(style_matches, key=int)
    ),
])
if errors:
    lines.append("오류=" + " | ".join(errors))

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
sys.exit(1 if errors else 0)
