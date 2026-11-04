"""Image-grid geometry, complete PNG payloads and patch-package integration."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import image_grid
import kjn_profile as kp
import md_to_blocks
import patch_from_fresh as pf
import test_blocks_to_hwpx_kjn as fixture
import test_patch_from_fresh as patch_fixture

HP = "{" + kp.NS["hp"] + "}"
HC = "{" + kp.NS["hc"] + "}"


class ImageGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = md_to_blocks.parse_file("부록3_jamovi_원출력.md")[1]

    def test_parser_35_cells_five_captions(self):
        grids = [b["image_grid"] for b in self.blocks if b["type"] == "table"]
        self.assertEqual(len(grids), 5)
        self.assertEqual(sum(c is not None for g in grids for r in g["rows"] for c in r), 35)
        self.assertEqual(sum(b["type"] == "table_caption" for b in self.blocks), 5)

    def test_body_grids_unnumbered_and_manifest_targeted(self):
        blocks = md_to_blocks.parse_file("04_연구설계및실증분석.md")[1]
        grids = [b for b in blocks if b.get("image_grid")]
        self.assertEqual([b["image_grid"]["target"] for b in grids],
                         ["<표 4-7>", "<표 4-10>", "<표 4-11>", "<표 4-12>"])
        self.assertEqual(sum(c is not None for b in grids for r in b["image_grid"]["rows"] for c in r), 12)
        doc, _, _ = fixture.make_doc()
        for b in grids:
            grid = b["image_grid"]
            heading = {"type": "p", "runs": [{"text": grid["heading"]}]}
            doc.add_blocks([heading, b])
        self.assertEqual(doc.lot, [])
        self.assertEqual(doc.lof, [])
        self.assertEqual(len(doc.bin_items), 12)
        self.assertTrue(all(e["caption"] is None and e["unnumbered"] for e in doc.image_grid_evidence))
        root = ET.fromstring(kp._wrap("".join(doc.body)))
        self.assertEqual(len(list(root.iter(HP + "tbl"))), 4)
        self.assertTrue(all(t.get("pageBreak") == "NONE" for t in root.iter(HP + "tbl")))
        for b in grids:
            with self.assertRaisesRegex(ValueError, "manifest target"):
                image_grid.parse_cells(b, md_to_blocks.SRC_DIR / "04_연구설계및실증분석.md",
                                       "jamovi 원출력(<표 9-99>).")

    def test_all_grids_preserve_sizes_and_complete_occupancy(self):
        doc, tpl, _ = fixture.make_doc()
        doc.add_blocks(self.blocks, appendix=True)
        self.assertEqual(len(doc.bin_items), 35)
        self.assertEqual(len(doc.lot), 5)
        root = ET.fromstring(kp._wrap("".join(doc.body)))
        tables = list(root.iter(HP + "tbl"))
        for tbl, evidence in zip(tables, doc.image_grid_evidence):
            widths = evidence["widths"]
            self.assertEqual(sum(widths), int(tbl.find(HP + "sz").get("width")))
            self.assertEqual(tbl.get("repeatHeader"), "0")
            self.assertNotIn("linesegarray", ET.tostring(tbl, encoding="unicode"))
            self.assertNotEqual(tbl.get("pageBreak"), "CELL")
            for ri, tr in enumerate(tbl.findall(HP + "tr")):
                occupied = set()
                for tc in tr.findall(HP + "tc"):
                    a, sp = tc.find(HP + "cellAddr"), tc.find(HP + "cellSpan")
                    col, span = int(a.get("colAddr")), int(sp.get("colSpan"))
                    self.assertEqual(int(a.get("rowAddr")), ri)
                    columns = set(range(col, col + span))
                    self.assertFalse(occupied & columns)
                    occupied |= columns
                    width = int(tc.find(HP + "cellSz").get("width"))
                    self.assertEqual(width, sum(widths[col:col + span]))
                    pic = tc.find(".//" + HP + "pic")
                    self.assertEqual(pic.find(HP + "pos").get("treatAsChar"), "1")
                    margin = tc.find(HP + "cellMargin")
                    self.assertLessEqual(int(pic.find(HP + "sz").get("width")),
                                         width - int(margin.get("left")) - int(margin.get("right")))
                self.assertEqual(occupied, set(range(int(tbl.get("colCnt")))))
        for e in doc.image_grid_evidence:
            for c in e["cells"]:
                expected = next(m for b in self.blocks if b.get("image_grid")
                                for row in b["image_grid"]["rows"] for m in row
                                if m and m["path"] == c["file"])
                self.assertEqual(c["picture_width"], min(doc.asm.total_width, round(min(expected["width_mm"], 140) * image_grid.MM)))

    def test_patch_imports_assets_manifest_and_new_appendix(self):
        doc, tpl, _ = fixture.make_doc()
        subset = self.blocks  # includes two distinct cells with identical PNG bytes
        doc.add_blocks(subset, appendix=True)
        fresh_s2 = doc.build_section2()
        entries = kp.plan_package(tpl, {"Contents/section2.xml": fresh_s2}, tpl.header.xml, doc.bin_items)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fresh = tmp / "fresh.hwpx"
            base = tmp / "base.hwpx"
            out = tmp / "patched.hwpx"
            fixture.blocks_to_hwpx.write_package(str(fresh), entries, (2026, 1, 1, 0, 0, 0))
            # The original template has assets whose numeric IDs can collide.
            with zipfile.ZipFile(base, "w") as z:
                for name, raw in tpl.raw.items():
                    if name == "Contents/section2.xml":
                        raw = (tpl.s2_head + doc.asm.text_para(doc.spec("appendix_heading"),
                                "부 록 (도입 현장)") + "</hs:sec>").encode()
                    z.writestr(name, raw)
            patch = pf.Patcher(str(base), str(fresh), [], None)
            patch.append_new_appendices()
            patch.write(str(out))
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                manifest = ET.fromstring(z.read("Contents/content.hpf"))
                items = {e.get("id"): e.get("href") for e in manifest.iter() if e.tag.endswith("}item")}
                root = ET.fromstring(z.read("Contents/section2.xml"))
                for img, (_, _, original) in zip(root.iter(HC + "img"), doc.bin_items):
                    self.assertEqual(z.read(items[img.get("binaryItemIDRef")]), original)
                for name, raw in tpl.raw.items():
                    if name.startswith("BinData/"):
                        self.assertEqual(z.read(name), raw)
                self.assertEqual(len(list(root.iter(HC + "img"))), 35)
                self.assertEqual(len(patch.bin_imports),35)


class StructuralPatchTests(unittest.TestCase):
    setUp = patch_fixture.PatchFromFreshTest.setUp
    tearDown = patch_fixture.PatchFromFreshTest.tearDown
    _pkg = patch_fixture.PatchFromFreshTest._pkg

    def test_verified_structure_reorders_and_keeps_merged_table_xml(self):
        f=patch_fixture
        table=f.table(f.MERGED_ROWS,3)
        base=[f.para('old paragraph'),f.para('<표 4-2> old caption'),table,f.para('keep paragraph')]
        fresh=[f.para('keep paragraph'),f.para('new paragraph'),f.para('<표 4-5> new caption'),f.table(f.PLAIN_ROWS,3)]
        pt=pf.Patcher(self._pkg('base',base),self._pkg('fresh',fresh),[],None)
        pt.patch_verified_body(f.SEC_HEAD+''.join(base)+f.SEC_TAIL)
        self.assertIn(table,pt.s2)
        self.assertNotIn('old paragraph',pt.s2)
        self.assertLess(pt.s2.index('keep paragraph'),pt.s2.index('new paragraph'))
        self.assertIn(base[-1],pt.s2)

    def test_unknown_user_text_blocks_structural_replacement(self):
        f=patch_fixture
        pt=pf.Patcher(self._pkg('base',[f.para('user addition')]),self._pkg('fresh',[f.para('new MD')]),[],None)
        before=pt.s2
        with self.assertRaisesRegex(ValueError,'provenance failed'):
            pt.patch_verified_body(f.SEC_HEAD+f.para('old MD')+f.SEC_TAIL)
        self.assertEqual(pt.s2,before)

    def test_target_change_clears_ancestor_cache_only(self):
        f=patch_fixture
        changed=f.para('old target')
        untouched=f.para('keep sibling')
        outer=f.para('anchor')
        xml=outer.replace('</hp:run>',changed+untouched+'</hp:run>',1)
        new=pf.replace_literal_text(xml,'old target','new target',1)
        self.assertIn(untouched,new)
        self.assertEqual(new.count('<hp:linesegarray>'),1)
        self.assertIn('new target',new)


if __name__ == "__main__":
    unittest.main()
