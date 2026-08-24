# -*- coding: utf-8 -*-
"""양식 header.xml의 기존 빨간 charPr와 조립기 사용 charPr를 실측한다."""

import copy
import pathlib
import zipfile
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parents[4]
TEMPLATE = next(ROOT.glob("공학대학원_건축안전_윤혁_*.hwpx"))
OUTPUT = pathlib.Path(__file__).with_name("red_charpr_inspection.txt")


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def comparable_xml(element):
    clone = copy.deepcopy(element)
    clone.attrib.pop("id", None)
    clone.attrib.pop("textColor", None)
    return ET.tostring(clone, encoding="unicode")


with zipfile.ZipFile(TEMPLATE) as archive:
    header_bytes = archive.read("Contents/header.xml")

root = ET.fromstring(header_bytes)
char_prs = {
    element.get("id"): element
    for element in root.iter()
    if local_name(element.tag) == "charPr"
}
red_ids = [
    char_id
    for char_id, element in char_prs.items()
    if element.get("textColor", "").upper() == "#FF0000"
]

lines = [
    "template=" + str(TEMPLATE),
    "charPr_count=" + str(len(char_prs)),
    "red_ids=" + ",".join(red_ids),
]

for char_id in red_ids:
    element = char_prs[char_id]
    font_ref = next((child for child in element if local_name(child.tag) == "fontRef"), None)
    bold = any(local_name(child.tag) == "bold" for child in element)
    matching_black = [
        candidate_id
        for candidate_id, candidate in char_prs.items()
        if candidate.get("textColor", "").upper() != "#FF0000"
        and comparable_xml(candidate) == comparable_xml(element)
    ]
    lines.append(
        "red id=%s height=%s font=%s bold=%s borderFill=%s exact_black_matches=%s"
        % (
            char_id,
            element.get("height"),
            dict(font_ref.attrib) if font_ref is not None else {},
            bold,
            element.get("borderFillIDRef"),
            ",".join(matching_black) or "none",
        )
    )

for char_id in ["61", "9", "7", "58"]:
    element = char_prs[char_id]
    font_ref = next((child for child in element if local_name(child.tag) == "fontRef"), None)
    bold = any(local_name(child.tag) == "bold" for child in element)
    matching_red = [
        red_id
        for red_id in red_ids
        if comparable_xml(char_prs[red_id]) == comparable_xml(element)
    ]
    lines.append(
        "target id=%s height=%s font=%s bold=%s borderFill=%s exact_red_matches=%s"
        % (
            char_id,
            element.get("height"),
            dict(font_ref.attrib) if font_ref is not None else {},
            bold,
            element.get("borderFillIDRef"),
            ",".join(matching_red) or "none",
        )
    )

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
