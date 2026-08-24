# -*- coding: utf-8 -*-
"""가이드 마커 run 분할의 최소 회귀 테스트."""

import importlib.util
import pathlib
import unittest
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tools" / "hwpx_transfer" / "blocks_to_hwpx.py"
SPEC = importlib.util.spec_from_file_location("blocks_to_hwpx", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

HP_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"


def run_pairs(fragment):
    root = ET.fromstring('<root xmlns:hp="%s">%s</root>' % (HP_NS, fragment))
    pairs = []
    for run in root.iter("{%s}run" % HP_NS):
        text = "".join(t.text or "" for t in run.iter("{%s}t" % HP_NS))
        if text:
            pairs.append((run.get("charPrIDRef"), text))
    return pairs


class RedMarkerRunTests(unittest.TestCase):
    def setUp(self):
        style_map = {
            "body": {"styleIDRef": "0", "paraPrIDRef": "51", "charPrIDRef": "61"}
        }
        self.asm = MODULE.Assembler(style_map, MODULE.IdGen())
        self.asm.red_char_pr = lambda char_pr: "red-" + str(char_pr)
        self.spec = {"style": "0", "para": "51", "char": "61"}

    def test_template_reads_all_zip_entries_before_archive_closes(self):
        template_path = next(ROOT.glob("공학대학원_건축안전_윤혁_*.hwpx"))
        try:
            template = MODULE.Template(template_path)
        except ValueError as error:
            self.fail("Template이 닫힌 ZIP을 읽었다: %s" % error)
        self.assertIn("Contents/header.xml", template.raw)

    def test_text_para_splits_only_prefixed_markers(self):
        text = (
            "앞 [38, 41, 44] [DATA PENDING: 값] 중간 "
            "[0.974, 0.991] [확정 필요 — 교수님 협의] 뒤"
        )
        pairs = run_pairs(self.asm.text_para(self.spec, text))
        self.assertEqual(
            pairs,
            [
                ("61", "앞 [38, 41, 44] "),
                ("red-61", "[DATA PENDING: 값]"),
                ("61", " 중간 [0.974, 0.991] "),
                ("red-61", "[확정 필요 — 교수님 협의]"),
                ("61", " 뒤"),
            ],
        )

    def test_runs_para_preserves_bold_around_marker(self):
        pairs = run_pairs(
            self.asm.runs_para(
                self.spec,
                [
                    {"text": "일반 [CITE_TODO: 출처] 끝", "bold": False},
                    {"text": "볼드 [UNVERIFIED — 확인] 끝", "bold": True},
                ],
            )
        )
        self.assertEqual(
            pairs,
            [
                ("61", "일반 "),
                ("red-61", "[CITE_TODO: 출처]"),
                ("61", " 끝"),
                (MODULE.BODY_BOLD_CHAR, "볼드 "),
                ("red-" + MODULE.BODY_BOLD_CHAR, "[UNVERIFIED — 확인]"),
                (MODULE.BODY_BOLD_CHAR, " 끝"),
            ],
        )

    def test_cell_paragraphs_marks_multiple_occurrences_but_not_labels(self):
        text = (
            "[양식 1: 도입 현장용] [그림 삽입 예정: 그림] / "
            "[DATA PENDING] / [양식 2: 미도입 현장용]"
        )
        fragment, line_count = self.asm.cell_paragraphs(text, "75", "7", 10000)
        self.assertEqual(line_count, 1)
        self.assertEqual(
            run_pairs(fragment),
            [
                ("7", "[양식 1: 도입 현장용] "),
                ("red-7", "[그림 삽입 예정: 그림]"),
                ("7", " / "),
                ("red-7", "[DATA PENDING]"),
                ("7", " / [양식 2: 미도입 현장용]"),
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
