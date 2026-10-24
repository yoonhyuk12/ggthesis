# patch_from_fresh.py(사용자 편집 hwpx에 MD 조립본 변경분만 반입)의 표 병합 판정·문단 반입·캡션 분리를 검증하는 단위 테스트
"""실행: python -m unittest tools/hwpx_transfer/tests/test_patch_from_fresh.py

hwpx를 만들지 않는다. 임시 폴더에 추출본 형식(`Contents__section2.xml` 등)의 작은 base·fresh 패키지를 만들고
Patcher.patch_body() 결과 XML 문자열을 검사한다. header는 양식 추출본(staging/migrate_kjn/template_extracted)을 쓴다.
"""

import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.dirname(HERE)
sys.path[:0] = [TOOL, HERE]

import kjn_profile  # noqa: E402
import patch_from_fresh as pff  # noqa: E402

TEMPLATE_DIR = os.path.join(TOOL, "staging", "migrate_kjn", "template_extracted")
NS_DECL = " ".join('xmlns:%s="%s"' % (k, v) for k, v in kjn_profile.NS.items())
SEC_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec %s>' % NS_DECL
SEC_TAIL = "</hs:sec>"

_ids = [3000000000]


def nid():
    _ids[0] += 1
    return _ids[0]


def para(text, char="0", ppr="0", lineseg=True):
    run = '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>' % (char, pff.esc(text)) if text else \
        '<hp:run charPrIDRef="%s"/>' % char
    seg = '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" baseline="850" ' \
          'spacing="600" horzpos="0" horzsize="42520" flags="393216"/></hp:linesegarray>' if lineseg else ""
    return '<hp:p id="%d" paraPrIDRef="%s" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">%s%s</hp:p>' % (
        nid(), ppr, run, seg)


def cell(row, col, text, rs=1, cs=1, width=10000):
    return ('<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">'
            '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
            'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">%s</hp:subList>'
            '<hp:cellAddr colAddr="%d" rowAddr="%d"/><hp:cellSpan colSpan="%d" rowSpan="%d"/>'
            '<hp:cellSz width="%d" height="1000"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>'
            ) % (para(text, lineseg=False), col, row, cs, rs, width * cs)


def table(rows, ncols):
    """rows: [[(row, col, text, rowSpan, colSpan), ...], ...] — 각 행에 그 행에서 시작하는 셀만 적는다."""
    trs = "".join("<hp:tr>%s</hp:tr>" % "".join(cell(*c) for c in r) for r in rows)
    tbl = ('<hp:tbl id="%d" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
           'dropcapstyle="None" pageBreak="TABLE" repeatHeader="1" rowCnt="%d" colCnt="%d" cellSpacing="0" '
           'borderFillIDRef="1" noAdjust="0"><hp:sz width="%d" widthRelTo="ABSOLUTE" height="3000" '
           'heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" '
           'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" '
           'vertOffset="0" horzOffset="0"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>%s</hp:tbl>'
           ) % (nid(), len(rows), ncols, 10000 * ncols, trs)
    return '<hp:p id="%d" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">' \
           '<hp:run charPrIDRef="0">%s<hp:t/></hp:run></hp:p>' % (nid(), tbl)


# 사용자 병합본: 1열 '구분'을 두 행에 걸쳐 병합(아래 칸 삭제), 마지막 행 '합  계'를 2열 병합
MERGED_ROWS = [
    [(0, 0, "구분", 2, 1), (0, 1, "항목"), (0, 2, "값")],
    [(1, 1, "가"), (1, 2, "1")],
    [(2, 0, "합  계", 1, 2), (2, 2, "1")],
]
# 조립본: 병합 없이 아래 칸은 빈칸, '합계'
PLAIN_ROWS = [
    [(0, 0, "구분"), (0, 1, "항목"), (0, 2, "값")],
    [(1, 0, ""), (1, 1, "가"), (1, 2, "1")],
    [(2, 0, "합계"), (2, 1, ""), (2, 2, "1")],
]


def swap_char_pr_ids(header, a, b):
    """fresh header를 흉내 낸다 — charPr a·b의 id를 맞바꿔 같은 서식이 다른 id를 갖게 한다."""
    tmp = "__SWAP__"
    header = header.replace('<hh:charPr id="%s"' % a, '<hh:charPr id="%s"' % tmp, 1)
    header = header.replace('<hh:charPr id="%s"' % b, '<hh:charPr id="%s"' % a, 1)
    return header.replace('<hh:charPr id="%s"' % tmp, '<hh:charPr id="%s"' % b, 1)


class PatchFromFreshTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pff_test_")
        with open(os.path.join(TEMPLATE_DIR, "Contents__header.xml"), encoding="utf-8") as f:
            self.header = f.read()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pkg(self, name, body, header=None):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        files = {"Contents__header.xml": header or self.header,
                 "Contents__section1.xml": SEC_HEAD + para("목차") + SEC_TAIL,
                 "Contents__section2.xml": SEC_HEAD + "".join(body) + SEC_TAIL}
        for fname, text in files.items():
            with open(os.path.join(d, fname), "w", encoding="utf-8") as f:
                f.write(text)
        return d

    def _patch(self, base_body, fresh_body, fresh_header=None):
        pt = pff.Patcher(self._pkg("base", base_body), self._pkg("fresh", fresh_body, fresh_header), [], None)
        pt.patch_body()
        return pt

    def test_merged_table_same_content_keeps_base(self):
        base_tbl = table(MERGED_ROWS, 3)
        base = [para("<표 5-1> 인구통계"), base_tbl, para("본문 끝")]
        fresh = [para("<표 5-1> 인구통계"), table(PLAIN_ROWS, 3), para("본문 끝")]
        pt = self._patch(base, fresh)
        self.assertIn(base_tbl, pt.s2)              # base 표 XML이 바이트 그대로 남는다
        self.assertEqual(pt.s2.count("<hp:tbl "), 1)
        self.assertIn('rowSpan="2"', pt.s2)
        self.assertIn("합  계", pt.s2)
        self.assertNotIn(">합계<", pt.s2)
        self.assertEqual(pt.manual, [])
        self.assertEqual(pt.stats["table_same_kept"], 1)
        self.assertEqual(pt.stats["replace_fresh"], 0)

    def test_merged_table_changed_content_keeps_base_and_reports(self):
        base_tbl = table(MERGED_ROWS, 3)
        changed = [r[:] for r in PLAIN_ROWS]
        changed[1] = [(1, 0, ""), (1, 1, "가"), (1, 2, "2")]  # MD에서 값이 바뀌었다
        base = [para("<표 5-1> 인구통계"), base_tbl, para("본문 끝")]
        fresh = [para("<표 5-1> 인구통계"), table(changed, 3), para("본문 끝")]
        pt = self._patch(base, fresh)
        self.assertIn(base_tbl, pt.s2)              # 덮어쓰지 않는다
        self.assertEqual(pt.s2.count("<hp:tbl "), 1)
        self.assertEqual(len(pt.manual), 1)
        self.assertIn("<표5-1>", pt.manual[0])
        self.assertIn("수동 재적용 필요", pt.manual[0])
        self.assertIn("## 수동 재적용 필요\n- <표5-1>", pt.summary())

    def test_merged_cell_covering_text_in_fresh_differs(self):
        # base 병합 셀이 덮는 fresh 칸에 다른 글이 있으면 내용이 다른 것으로 본다
        base_xml = table(MERGED_ROWS, 3)
        rows = [r[:] for r in PLAIN_ROWS]
        rows[1] = [(1, 0, "나"), (1, 1, "가"), (1, 2, "1")]
        same, merge_diff, _ = pff.compare_tables(base_xml, table(rows, 3))
        self.assertFalse(same)
        self.assertTrue(merge_diff)
        rows[1] = [(1, 0, "구 분"), (1, 1, "가"), (1, 2, "1")]  # 덮은 셀과 같은 글(공백 무시)은 동일
        same, _, _ = pff.compare_tables(base_xml, table(rows, 3))
        self.assertTrue(same)

    def test_changed_paragraph_taken_from_fresh_with_id_remap(self):
        # fresh header는 charPr 0·1의 id가 맞바뀌어 있다 → fresh의 charPr 1은 base의 charPr 0과 같은 서식이다
        fresh_header = swap_char_pr_ids(self.header, "0", "1")
        kept = para("바뀌지 않은 문단", char="1")
        base = [kept, para("바뀌기 전 문단", char="0"), para("끝 문단", char="1")]
        fresh = [para("바뀌지 않은 문단", char="0"), para("바뀐 뒤 문단", char="1"), para("끝 문단", char="0")]
        base_pkg = self._pkg("base", base)
        with open(os.path.join(base_pkg, "Contents__section2.xml"), encoding="utf-8") as f:
            base_ids = [int(i) for i in re.findall(r'<hp:p id="(\d+)"', f.read())]
        pt = pff.Patcher(base_pkg, self._pkg("fresh", fresh, fresh_header), [], None)
        pt.patch_body()
        self.assertIn(kept, pt.s2)                  # 같은 문단은 base 그대로
        units = pff.Units(pt.s2, set())
        new = [u for u in units.items if u["text"] == "바뀐 뒤 문단"]
        self.assertEqual(len(new), 1)
        self.assertNotIn("바뀌기 전 문단", pt.s2)
        self.assertIn('charPrIDRef="0"', new[0]["xml"])   # fresh id 1 → base id 0으로 재대응
        self.assertNotIn("<hp:linesegarray>", new[0]["xml"])
        new_id = int(re.search(r'<hp:p id="(\d+)"', new[0]["xml"]).group(1))
        self.assertGreater(new_id, max(base_ids))
        all_ids = re.findall(r'<hp:p id="(\d+)"', pt.s2)
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertEqual(pt.importer.added["charPr"], [])  # 같은 서식이 base에 있으니 header에 추가하지 않는다

    def test_merged_body_and_caption_split(self):
        # 사용자가 본문 끝과 캡션 사이 문단 경계를 지운 경우 → 본문은 base 서식, 캡션은 fresh 캡션 문단
        body = "  전체 구성은 <그림 3-1>과 같다."
        cap = "<그림 3-1> 시스템 아키텍처"
        base = [para(body + cap, char="1", ppr="1"), para("자료: 연구자 작성.")]
        fresh = [para(body, char="0", ppr="0"), para(cap, char="2", ppr="2"), para("자료: 연구자 작성.")]
        pt = self._patch(base, fresh)
        units = [u for u in pff.Units(pt.s2, set()).items]
        self.assertEqual([u["text"] for u in units], [body.strip(), cap, "자료: 연구자 작성."])
        self.assertIn('paraPrIDRef="1"', units[0]["xml"])
        self.assertIn('charPrIDRef="1"', units[0]["xml"])
        self.assertIn('paraPrIDRef="2"', units[1]["xml"])
        self.assertIn('charPrIDRef="2"', units[1]["xml"])
        self.assertNotIn("<hp:linesegarray>", units[0]["xml"])
        self.assertEqual(pt.stats["caption_split"], 1)


if __name__ == "__main__":
    unittest.main()
