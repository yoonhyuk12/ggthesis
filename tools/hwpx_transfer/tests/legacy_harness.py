# 회귀 테스트용 공용 하네스 — hwpx 양식 파일 없이 본문(section2) 문단 XML을 만들어 비교한다
"""옛 양식(style_map.json) 회귀 하네스.

양식 hwpx 대신 고정 문자열을 돌려주는 FakeTemplate을 써서, 조립기 모듈의 Document로
section2 본문을 조립한다. 변경 전 코드(fixtures/legacy_blocks_to_hwpx_pre.py)와 변경 후 코드에
같은 입력(fixtures/legacy_inputs/)을 넣어 만든 XML이 바이트 단위로 같아야 한다.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
LEGACY_INPUTS = os.path.join(FIXTURES, "legacy_inputs")
BASELINE_XML = os.path.join(FIXTURES, "legacy_section2_baseline.xml")
BLOCK_FILES = ["ch01", "ch02", "ch03", "ch04", "ch05", "ch06", "apx1", "apx2"]


class FakeTemplate(object):
    """Template의 section2 조립에 필요한 속성만 고정값으로 흉내낸다."""

    s2_head = '<?xml version="1.0"?><hs:sec>'
    sec2_secpr = "<hp:ctrl><hp:colPr/></hp:ctrl><hp:secPr/>"
    sec2_pagectrl = "<hp:ctrl><hp:pageNum/></hp:ctrl>"
    sec2_newnum = "<hp:ctrl><hp:newNum/></hp:ctrl>"

    def red_char_pr_id(self, base):
        return "R" + str(base)


def legacy_inputs():
    with open(os.path.join(LEGACY_INPUTS, "style_map.json"), encoding="utf-8") as f:
        style_map = json.load(f)
    files = []
    for name in BLOCK_FILES:
        path = os.path.join(LEGACY_INPUTS, name + ".blocks.json")
        with open(path, encoding="utf-8") as f:
            files.append((path, json.load(f)["blocks"]))
    with open(os.path.join(LEGACY_INPUTS, "references.json"), encoding="utf-8") as f:
        refs = json.load(f)
    return style_map, files, refs


def build_legacy_section2(module):
    """변경 전 main()의 본문 조립 순서를 그대로 재현한다(옛 모듈·새 모듈 공용)."""
    style_map, files, refs = legacy_inputs()
    doc = module.Document(FakeTemplate(), style_map)
    first = True
    refs_done = False
    for _path, blocks in files:
        if not refs_done and module.is_appendix(blocks):
            doc.add_references(refs)
            refs_done = True
        is_survey = any(b["type"] == "h1" and "설문지" in b["text"] for b in blocks)
        first = doc.add_blocks(blocks, first_paragraph=first, survey_cover=is_survey)
    if not refs_done:
        doc.add_references(refs)
    doc.add_placeholder_section("부록 3. 시스템 화면 및 LLM 검증 사례 이미지")
    doc.add_placeholder_section("Abstract")
    return doc.build_section2()
