"""Declared merges: parse real MD, assemble/patch in memory (no HWPX output)."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import md_to_blocks
import table_merges as tm
import patch_from_fresh as pff
import test_patch_from_fresh as fixtures
from test_blocks_to_hwpx_kjn import make_doc, paras


def block():
    result = md_to_blocks.parse_file('04_연구설계및실증분석.md')
    assert result[5] == [], result[5]
    return next(b for b in result[1] if b.get('layout'))


def plain(b, legacy=False):
    grid = copy.deepcopy([b['header']] + b['rows'])
    if legacy:
        for r, c, old in b['layout']['aliases']:
            grid[r][c] = old
    return fixtures.table([[(r, c, text) for c, text in enumerate(row)] for r, row in enumerate(grid)], len(grid[0]))


class DeclaredMergesTest(unittest.TestCase):
    def test_real_markdown_assembly_and_grid(self):
        b = block()
        doc, _, _ = make_doc()
        doc.add_blocks([{'type': 'table_caption', 'text': '<표 4-4> 설문지의 최종 구성'}, b])
        xml = next(p for p in paras(doc.build_section2()) if '<hp:tbl ' in p)
        tbl, cells, coverage = tm._grid(xml)
        self.assertEqual(len(coverage), 54)
        self.assertEqual(len(cells), 49)
        self.assertEqual(cells[4, 0][2:], (1, 3))
        self.assertEqual(cells[5, 0][2:], (2, 1))
        self.assertEqual(cells[7, 0][2:], (1, 3))
        self.assertEqual(cells[8, 0][2:], (1, 1))
        self.assertIn('미도입 현장 21문항', tm._text(cells[8, 1][0]))
        width = int(tbl.find(tm.HP + 'sz').get('width'))
        self.assertEqual(sum(int(cells[0, c][0].find(tm.HP + 'cellSz').get('width')) for c in range(6)), width)
        self.assertNotIn('hwpx-table-layout', xml)

    def test_minimal_preservation_and_idempotence(self):
        b = block()
        original = plain(b)
        _, before, _ = tm._grid(original)
        result = tm.apply_layout(original, b)
        tbl, after, _ = tm._grid(result)
        self.assertEqual(tbl.find(tm.HP + 'sz').get('width'), '60000')
        self.assertEqual(after[4, 0][0].find(tm.HP + 'cellSz').get('width'), '30000')
        for pos in [(0, 0), (1, 2), (5, 2), (8, 1)]:
            self.assertEqual(before[pos][1], after[pos][1])
        self.assertEqual(tm.apply_layout(result, b), result)

    def test_nonempty_covered_cell_refused(self):
        b = block()
        xml = plain(b)
        _, cells, _ = tm._grid(xml)
        raw = cells[4, 1][1]
        bad = raw.replace('<hp:run charPrIDRef="0"/>', '<hp:run charPrIDRef="0"><hp:t>사용자 메모</hp:t></hp:run>')
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            tm.apply_layout(xml.replace(raw, bad), b)
        b['rows'][3][1] = '삭제 금지'
        with self.assertRaisesRegex(ValueError, 'nonempty Markdown'):
            tm.validate_block(b)

    def test_invalid_or_orphan_directive_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.md'
            path.write_text('<!-- hwpx-table-layout: {"caption":"<표 4-4>","merges":[[4,0,1,3]]} -->', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'caption'):
                md_to_blocks.parse_file(path)

    def test_width_mismatch_refused(self):
        b = block()
        with self.assertRaisesRegex(ValueError, 'width'):
            tm.apply_layout(plain(b).replace('width="60000"', 'width="60001"'), b)

    def test_legacy_caption_row_offset(self):
        b = block()
        grid = [b['header']] + b['rows']
        rows = [[(0, 0, '<표 4-4> 설문지의 최종 구성', 1, 6)]]
        rows += [[(r + 1, c, value) for c, value in enumerate(row)] for r, row in enumerate(grid)]
        xml = tm.apply_layout(fixtures.table(rows, 6), b, row_offset=1)
        _, cells, _ = tm._grid(xml)
        self.assertEqual(cells[5, 0][2:], (1, 3))
        self.assertEqual(cells[6, 0][2:], (2, 1))
        self.assertEqual(cells[8, 0][2:], (1, 3))


class PatchDeclaredMergesTest(unittest.TestCase):
    setUp = fixtures.PatchFromFreshTest.setUp
    tearDown = fixtures.PatchFromFreshTest.tearDown
    _pkg = fixtures.PatchFromFreshTest._pkg

    def patch(self, base, fresh, **kw):
        cap = fixtures.para('<표 4-4> 설문지의 최종 구성')
        pt = pff.Patcher(self._pkg('base', [cap, base]), self._pkg('fresh', [cap, fresh]), kw.pop('protect', []), None, **kw)
        pt.patch_body()
        return pt

    def test_legacy_labels_merge_and_preserve_user_format(self):
        b = block()
        base = plain(b, legacy=True)
        # User's cell text and formatting outside the requested labels survive.
        base = base.replace('안전관리 실효성', '사용자 직접 수정').replace('borderFillIDRef="1"', 'borderFillIDRef="2"')
        fresh = tm.apply_layout(plain(b), b)
        pt = self.patch(base, fresh)
        result = next(u['xml'] for u in pff.Units(pt.s2, []).items if u['tbl'])
        self.assertEqual(result, tm.apply_layout(base, b, aliases=True))
        self.assertIn('사용자 직접 수정', result)
        self.assertIn('borderFillIDRef="2"', result)
        self.assertNotIn('전용부 E', result)
        self.assertIn('그 밖의 내용 차이', pt.manual[0])
        self.assertEqual(pt.stats['replace_fresh'], 0)

    def test_same_content_still_merges(self):
        b = block()
        base, fresh = plain(b), tm.apply_layout(plain(b), b)
        pt = self.patch(base, fresh)
        self.assertIn(tm.apply_layout(base, b), pt.s2)
        self.assertEqual(pt.manual, [])

    def test_explicit_protection_wins(self):
        b = block()
        base, fresh = plain(b, legacy=True), tm.apply_layout(plain(b), b)
        pt = self.patch(base, fresh, protect=['<표 4-4>'])
        self.assertIn(base, pt.s2)
        self.assertIn('자동 병합 생략', pt.manual[0])

    def test_allow_tables_still_preserves_layout_result(self):
        b = block()
        base, fresh = plain(b, legacy=True), tm.apply_layout(plain(b), b)
        pt = self.patch(base, fresh, allow_tables=['<표 4-4>'])
        self.assertIn(tm.apply_layout(base, b, aliases=True), pt.s2)

    def test_allow_tables_exclusion_wins(self):
        b = block()
        base, fresh = plain(b, legacy=True), tm.apply_layout(plain(b), b)
        pt = self.patch(base, fresh, allow_tables=['<표 4-3>'])
        self.assertIn(base, pt.s2)
        self.assertIn('자동 병합 생략', pt.manual[0])

    def test_fresh_without_merges_refused(self):
        b = block()
        with self.assertRaisesRegex(ValueError, 'rebuild fresh'):
            self.patch(plain(b), plain(b))

    def test_stale_fresh_refused(self):
        b = block()
        fresh = tm.apply_layout(plain(b), b).replace('안전관리 실효성', '오래된 변수명')
        with self.assertRaisesRegex(ValueError, 'Fresh table differs'):
            self.patch(plain(b), fresh)

    def test_unexpected_legacy_label_refused(self):
        b = block()
        base = plain(b, legacy=True).replace('전용부 E', '새 사용자 분류')
        with self.assertRaisesRegex(ValueError, 'Unexpected previous label'):
            self.patch(base, tm.apply_layout(plain(b), b))


if __name__ == '__main__':
    unittest.main()
