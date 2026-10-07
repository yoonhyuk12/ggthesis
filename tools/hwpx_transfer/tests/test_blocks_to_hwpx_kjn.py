# blocks_to_hwpx.py 양식 프로파일 주입형 확장(김정년 양식)과 옛 양식 회귀를 검증하는 단위 테스트
"""실행: python -m unittest tools/hwpx_transfer/tests/test_blocks_to_hwpx_kjn.py

hwpx 파일을 만들지 않는다. 양식은 추출본 디렉터리(staging/migrate_kjn/template_extracted)를 읽고,
조립 결과는 메모리 안 XML 문자열로 검사한다. 그림 테스트만 임시 폴더에 작은 PNG를 쓴다.
"""

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.dirname(HERE)
sys.path[:0] = [TOOL, HERE]

import blocks_to_hwpx  # noqa: E402
import kjn_profile  # noqa: E402
import legacy_harness  # noqa: E402
import table_layout  # noqa: E402

MIGRATE = os.path.join(TOOL, "staging", "migrate_kjn")
TEMPLATE_DIR = os.path.join(MIGRATE, "template_extracted")
STUB = os.path.join(MIGRATE, "stub_profile.json")
G_PROFILE = os.path.join(MIGRATE, "style_map_kjn.json")
INPUTS = legacy_harness.LEGACY_INPUTS
HP = "{%s}" % kjn_profile.NS["hp"]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_stub():
    return load_json(STUB)


def load_base():
    """기본 시험 프로파일 — Task G의 style_map_kjn.json(있으면), 없으면 스텁(코디네이터 지침 2026-10-08)."""
    return load_json(G_PROFILE) if os.path.exists(G_PROFILE) else load_stub()


def blocks_of(name):
    with open(os.path.join(INPUTS, name + ".blocks.json"), encoding="utf-8") as f:
        return json.load(f)["blocks"]


def caption_and_table(name, prefix):
    blocks = blocks_of(name)
    for i, b in enumerate(blocks):
        if b["type"] == "table_caption" and b["text"].startswith(prefix):
            assert blocks[i + 1]["type"] == "table"
            return b, blocks[i + 1]
    raise AssertionError("캡션 %s 없음" % prefix)


def make_doc(profile_data=None, **kw):
    profile = kjn_profile.load_profile(profile_data if profile_data is not None else load_base(), "test")
    tpl = kjn_profile.KjnTemplate(TEMPLATE_DIR, profile)
    return kjn_profile.KjnDocument(tpl, profile, **kw), tpl, profile


def paras(xml_text):
    return [xml_text[a:b] for a, b in kjn_profile.split_paragraphs(xml_text)]


def is_blank(p):
    return "<hp:t>" not in p and "<hp:tbl" not in p and "<hp:pic" not in p and "<hp:t/>" not in p


def para_pr(p):
    return re.match(r'<hp:p id="\d+" paraPrIDRef="(\d+)"', p).group(1)


def tbl_elem(p):
    root = ET.fromstring(kjn_profile._wrap(p))
    return next(root.iter(HP + "tbl"))


def rows_of(tbl):
    out = []
    for tr in tbl.findall(HP + "tr"):
        cells = []
        for tc in tr.findall(HP + "tc"):
            addr, span, sz = tc.find(HP + "cellAddr"), tc.find(HP + "cellSpan"), tc.find(HP + "cellSz")
            text = "".join(t.text or "" for t in tc.iter(HP + "t"))
            cells.append({"tc": tc, "row": int(addr.get("rowAddr")), "col": int(addr.get("colAddr")),
                          "rs": int(span.get("rowSpan")), "cs": int(span.get("colSpan")),
                          "w": int(sz.get("width")), "text": text})
        out.append(cells)
    return out


def tiny_png(w, h):
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@unittest.skipUnless(os.path.isdir(TEMPLATE_DIR), "양식 추출본 없음")
class KjnAssemblyTests(unittest.TestCase):

    # (a) 표 제목은 표 밖 앞 문단, 표 첫 행은 캡션이 아닌 머리행
    def test_a_caption_outside_before_table(self):
        doc, _tpl, pf = make_doc()
        cap, tbl = caption_and_table("ch04", "<표 4-3>")
        doc.add_blocks([{"type": "h1", "text": "제4장 연구설계"}, cap, tbl,
                        {"type": "p", "runs": [{"text": "자료: 연구자 작성.", "bold": False}]}])
        ps = paras("".join(doc.body))
        t_idx = next(i for i, p in enumerate(ps) if "<hp:tbl" in p)
        self.assertIn("&lt;표 4-3&gt;", ps[t_idx - 1])
        self.assertEqual(para_pr(ps[t_idx - 1]), pf.spec("table_caption")["para"])
        first_row = rows_of(tbl_elem(ps[t_idx]))[0]
        self.assertEqual([c["text"] for c in first_row], tbl["header"])
        self.assertEqual(len(first_row), len(tbl["header"]))  # 전체 열 병합 캡션 행이 없다
        self.assertNotIn("표 4-3", "".join(c["text"] for c in first_row))
        self.assertEqual(para_pr(ps[t_idx + 1]), pf.spec("source_note")["para"])
        self.assertEqual(doc.lot, ["<표 4-3> 변수의 조작적 정의와 측정도구의 구성"])

    # (b) 머리행 header="1"·회색 borderFill, 본문 행 좌우 개방
    def test_b_header_row_border_fill(self):
        doc, _tpl, pf = make_doc()
        cap, tbl = caption_and_table("ch02", "<표 2-1>")
        xml_text, _w = doc.asm.table_xml(tbl["header"], tbl["rows"])
        t = tbl_elem(xml_text)
        self.assertEqual(t.get("repeatHeader"), "1")
        self.assertEqual(t.get("pageBreak"), "NONE")
        bf = pf.get("table", "borderFills")
        rows = rows_of(t)
        head = rows[0]
        self.assertTrue(all(c["tc"].get("header") == "1" for c in head))
        self.assertEqual(head[0]["tc"].get("borderFillIDRef"), bf["header_gray_left_open"])
        self.assertEqual(head[-1]["tc"].get("borderFillIDRef"), bf["header_gray_right_open"])
        for c in head[1:-1]:
            self.assertEqual(c["tc"].get("borderFillIDRef"), bf["header_gray_top04"])
        for row in rows[1:]:
            self.assertTrue(all(c["tc"].get("header") == "0" for c in row))
            self.assertEqual(row[0]["tc"].get("borderFillIDRef"), bf["left_open"])
            self.assertEqual(row[-1]["tc"].get("borderFillIDRef"), bf["right_open"])
        # 머리행 가운데 정렬 paraPr, 셀 문단에는 linesegarray 없음
        self.assertIn('paraPrIDRef="%s"' % pf.get("table", "cell_paraPr", "header_center"),
                      ET.tostring(head[0]["tc"], encoding="unicode"))
        self.assertNotIn("linesegarray", xml_text)

    # (c) 열폭 합 = total_width, 병합 격자 보존, 균등 분할 아님
    def test_c_column_widths_content_based(self):
        doc, _tpl, pf = make_doc()
        total = int(pf.get("table", "total_width"))
        for name, prefix in (("ch04", "<표 4-3>"), ("ch02", "<표 2-1>")):
            _cap, tbl = caption_and_table(name, prefix)
            xml_text, widths = doc.asm.table_xml(tbl["header"], tbl["rows"])
            self.assertEqual(sum(widths), total, prefix)
            self.assertGreater(max(widths) - min(widths), total * 0.1, "%s 균등 분할 %r" % (prefix, widths))
            t = tbl_elem(xml_text)
            self.assertEqual(int(t.find(HP + "sz").get("width")), total)
            rows = rows_of(t)
            self.assertEqual(int(t.get("rowCnt")), len(rows))
            self.assertEqual(int(t.get("colCnt")), len(tbl["header"]))
            cells = [(c["row"], c["col"], c["rs"], c["cs"]) for r in rows for c in r]
            table_layout.occupancy_grid(cells, len(rows), len(tbl["header"]))
            for r in rows:
                self.assertEqual(sum(c["w"] for c in r), total)
        # 4-3: 짧은 '하위요인' 열보다 긴 '조작적 정의' 열이 넓다
        _cap, tbl = caption_and_table("ch04", "<표 4-3>")
        w = doc.asm.column_widths(tbl["header"], tbl["rows"])
        self.assertGreater(w[2], w[1])
        # 비슷한 폭 수치 열만 있으면 균등 분할
        eq = table_layout.design_column_widths(["A", "B", "C"], [["1.0", "2.0", "3.0"]], 30000)
        self.assertEqual(sum(eq), 30000)
        self.assertLessEqual(max(eq) - min(eq), 2)
        # 병합 격자 비례 재계산(이식 표용)
        self.assertEqual(sum(table_layout.scale_widths([7380, 3135, 9644, 18983], 39684)), 39684)

    # (d) 절·항 앞 빈 문단 1개, 중복 없음
    def test_d_blank_before_section_and_item(self):
        para = {"type": "p", "runs": [{"text": "본문.", "bold": False}]}
        _cap, tbl = caption_and_table("ch04", "<표 4-2>")
        blocks = [{"type": "h1", "text": "제1장 서론"}, {"type": "h2", "text": "제1절 배경"}, para,
                  {"type": "h3", "text": "제1항 개념"}, para, {"type": "h2", "text": "제2절 목적"}, para,
                  {"type": "table_caption", "text": "<표 4-2> 연구 가설 종합"}, tbl,
                  {"type": "h3", "text": "제2항 이어서"}, para, {"type": "h4", "text": "1. 소제목"}, para,
                  {"type": "h1", "text": "제2장 이론"}, {"type": "h2", "text": "제1절 개념"}, para]
        profiles = [("stub", load_stub())] + ([("task_g", load_json(G_PROFILE))] if os.path.exists(G_PROFILE) else [])
        for label, data in profiles:
            doc, _tpl, _pf = make_doc(data)
            doc.add_blocks(blocks)
            ps = paras("".join(doc.body))
            texts = [kjn_profile.plain_texts(p) for p in ps]
            section_breaks = str(data["h2_section"].get("pageBreak", "0")) == "1"
            blank_before = ["제 1 항 개념", "제 2 항 이어서", "1. 소제목"]
            if section_breaks:
                # 장 안 둘째 절부터 새 쪽(pageBreak_rule) — 새 쪽 제목 앞에는 빈 줄을 두지 않는다
                i = texts.index("제 2 절 목적")
                self.assertIn('pageBreak="1"', ps[i], label)
                self.assertFalse(is_blank(ps[i - 1]), label)
            else:
                blank_before.append("제 2 절 목적")
            for title in blank_before:
                i = texts.index(title)
                self.assertTrue(is_blank(ps[i - 1]), "%s: %s 앞 빈 줄 없음" % (label, title))
                self.assertFalse(is_blank(ps[i - 2]), "%s: %s 앞 빈 줄 중복" % (label, title))
            # 장 안 첫 절은 장 제목 쪽에 이어지고, 장 제목 뒤 빈 줄이 절 앞 빈 줄을 겸한다
            for first in ("제 1 절 배경", "제 1 절 개념"):
                i = texts.index(first)
                self.assertNotIn('pageBreak="1"', ps[i], label)
                self.assertTrue(is_blank(ps[i - 1]) and not is_blank(ps[i - 2]), label)
            self.assertEqual(texts[0], "제 1 장 서론")  # "제1장" → "제 1 장"
            self.assertIn('pageBreak="1"', ps[0])        # 장 제목은 새 쪽(빈 줄 규칙 제외)
            self.assertIn('pageBreak="1"', ps[texts.index("제 2 장 이론")])
            for a, b in zip(ps, ps[1:]):
                self.assertFalse(is_blank(a) and is_blank(b), "%s: 연속 빈 문단" % label)

    # (e) 마커 run 분리와 검정 대괄호 유지(본문·표 셀)
    def test_e_marker_runs_and_black_brackets(self):
        doc, tpl, pf = make_doc()
        text = "근거 [38, 41, 44]와 CI [0.974, 0.991], [양식 1: 도입 현장용], [DATA PENDING: 수치] 및 실험전 값"
        doc.add_blocks([{"type": "p", "runs": [{"text": text, "bold": False}]}])
        body_char = pf.spec("body")["char"]
        red = tpl.header.red_char_pr_id(body_char)
        runs = re.findall(r'<hp:run charPrIDRef="(\d+)"><hp:t>([^<]*)</hp:t></hp:run>', doc.body[0])
        red_texts = [t for c, t in runs if c == red]
        black = "".join(t for c, t in runs if c == body_char)
        self.assertEqual(red_texts, ["[DATA PENDING: 수치]", "실험전"])
        for keep in ("[38, 41, 44]", "[0.974, 0.991]", "[양식 1: 도입 현장용]"):
            self.assertIn(keep, black)
        red_xml = tpl.header.item_xml("charPr", red)
        self.assertIn('textColor="#FF0000"', red_xml)
        self.assertEqual(re.search(r'height="(\d+)"', red_xml).group(1),
                         re.search(r'height="(\d+)"', tpl.header.item_xml("charPr", body_char)).group(1))
        self.assertNotEqual(red, "47")  # 양식의 굵은 빨강 안내 charPr를 재사용하지 않는다
        # 표 셀
        xml_text, _w = doc.asm.table_xml(["구분", "값(%)"], [["H1", "실험전"], ["CI", "[0.974, 0.991]"]])
        cell_red = tpl.header.red_char_pr_id(pf.get("table", "cell_charPr", "normal10"))
        self.assertIn('<hp:run charPrIDRef="%s"><hp:t>실험전</hp:t>' % cell_red, xml_text)
        self.assertIn('<hp:t>[0.974, 0.991]</hp:t>', xml_text)
        self.assertNotIn('charPrIDRef="%s"><hp:t>[0.974' % cell_red, xml_text)
        # 머리행 "라벨(단위)" → 두 문단
        head = rows_of(tbl_elem(xml_text))[0][1]["tc"]
        self.assertEqual([t.text for t in head.iter(HP + "t")], ["값", "(%)"])
        # header.xml itemCnt가 실제 개수와 같다
        kjn_profile.HeaderEditor(tpl.header.xml)

    # (f) CELL 0건 — 양식에 있던 CELL도 NONE으로
    def test_f_no_cell_page_break(self):
        self.assertIn('pageBreak="CELL"', read_text(os.path.join(TEMPLATE_DIR, "Contents__section1.xml")))
        doc, _tpl, _pf, secs = full_assembly(STUB)
        for name, xml_text in secs.items():
            self.assertEqual(xml_text.count('pageBreak="CELL"'), 0, name)
            ET.fromstring(xml_text.encode("utf-8"))  # 잘 짜인 XML
        self.assertEqual(len(doc.lot), 30)
        # 프로파일이 CELL을 요구해도 조립기는 NONE만 만든다(생성 경로 없음)
        data = load_base()
        data["table"]["tbl_attrs"]["pageBreak"] = "CELL"
        doc2, _tpl2, _pf2 = make_doc(data)
        xml_text, _w = doc2.asm.table_xml(["구분", "값"], [["가", "1"]])
        self.assertIn('pageBreak="NONE"', xml_text)
        self.assertNotIn('pageBreak="CELL"', xml_text)
        # 이식·양식 문단 정리 함수도 CELL을 NONE으로 바꾼다
        self.assertEqual(kjn_profile.strip_cell_page_break('<hp:tbl id="1" pageBreak="CELL" x="1">'),
                         '<hp:tbl id="1" pageBreak="NONE" x="1">')

    # (h) 프로파일 키 누락 시 명시적 예외
    def test_h_missing_profile_key_raises(self):
        data = load_base()
        del data["table_caption"]
        with self.assertRaises(kjn_profile.ProfileError):
            kjn_profile.load_profile(data)
        data = load_base()
        del data["table"]["cell_paraPr"]["number_right"]
        doc, _tpl, _pf = make_doc(data)
        with self.assertRaises(kjn_profile.ProfileError):
            doc.asm.table_xml(["구분", "값"], [["가", "12"]])
        data = load_base()
        del data["conventions"]["blank_after_heading"]
        with self.assertRaises(kjn_profile.ProfileError):
            make_doc(data)
        legacy = load_json(os.path.join(INPUTS, "style_map.json"))
        broken = copy.deepcopy(legacy)
        del broken["front_matter_ranges"]
        with self.assertRaises(kjn_profile.ProfileError):
            kjn_profile.load_profile(broken)
        pf = kjn_profile.load_profile(legacy)
        with self.assertRaises(kjn_profile.ProfileError):
            pf.get("legacy", "없는_키")

    # (i) 표지 슬롯 치환 후 김정년 문자열 0건
    def test_i_cover_has_no_kjn_strings(self):
        for path in (STUB, G_PROFILE):
            if not os.path.exists(path):
                continue
            doc, tpl, pf = make_doc(load_json(path))
            s0 = doc.build_section0()
            text = kjn_profile.plain_texts(s0)
            self.assertEqual(kjn_profile.leftover_hits([text], pf), {}, path)
            self.assertIn("김 정 년", kjn_profile.plain_texts(tpl.s0))
            self.assertEqual(text.count("중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구"), 2)
            self.assertIn("지도교수 : 박 종 용", text)
            self.assertIn("의 석사학위논문을 인준함", text)
            self.assertIn("2026", text.split("\n")[0])
            red = tpl.header.red_char_pr_id("21")
            # 연구자 성명은 2026-10-08 확정('윤  혁') — 빨간 마커가 아니라 검은 본문으로 들어간다
            self.assertNotIn("연구자 성명", s0)
            self.assertIn("윤  혁의 석사학위논문을 인준함", text)
            self.assertNotIn('<hp:t>윤  혁</hp:t></hp:run>'.replace('<hp:t>', '<hp:run charPrIDRef="%s"><hp:t>' % red), s0)
            ET.fromstring(s0.encode("utf-8"))

    # (j) 7분류 참고문헌 번호 형식
    def test_j_references_seven_categories(self):
        doc, tpl, pf = make_doc()
        cats = ["가. 학위논문", "나. 학술지", "다. 보고서", "라. 관련법", "마. 기타", "바. 국외 단행본", "사. 국외 학술지"]
        refs = {"categories": {c: [{"no": 7, "text": "%s 서지 %d" % (c[0], n)} for n in range(1, (i % 3) + 2)]
                               for i, c in enumerate(cats)},
                "flagged": [{"text": "미확정 서지", "reason": "권호 결손", "category": "나. 학술지"}]}
        doc.add_references(refs)
        ps = paras("".join(doc.body))
        texts = [kjn_profile.plain_texts(p) for p in ps]
        self.assertEqual(texts[0], "참고문헌")
        self.assertIn('pageBreak="1"', ps[0])
        self.assertEqual([t for t, p in zip(texts, ps) if para_pr(p) == pf.spec("ref_category")["para"]
                          and t in cats], cats)
        items = [t for t, p in zip(texts, ps) if para_pr(p) == pf.spec("ref_item")["para"]]
        self.assertTrue(all(re.match(r"^\[\d{2}\] ", t) for t in items))
        self.assertEqual(items[0], "[01] 가 서지 1")
        b_items = [t for t in items if t.startswith("[") and ("나 서지" in t or "미확정" in t)]
        self.assertEqual([t[:4] for t in b_items], ["[01]", "[02]", "[03]"])  # 분류마다 [01]부터
        red = tpl.header.red_char_pr_id(pf.spec("ref_item")["char"])
        self.assertIn('<hp:run charPrIDRef="%s"><hp:t>[확정 필요: 권호 결손]</hp:t>' % red, "".join(doc.body))

    # 그림: 캡션 위·BinData·자료 아래, 매핑 없으면 빨간 자리표시
    def test_figure_caption_above_and_bindata(self):
        tmp = tempfile.mkdtemp()
        try:
            png = os.path.join(tmp, "f.png")
            with open(png, "wb") as f:
                f.write(tiny_png(1772, 900))
            doc, tpl, pf = make_doc(images={"<그림 3-1>": png})
            doc.add_blocks([{"type": "p", "runs": [{"text": "![아키텍처](figures/a.png)", "bold": False}]},
                            {"type": "figure_caption", "text": "<그림 3-1> 아키텍처"},
                            {"type": "figure_caption", "text": "<그림 3-2> 매핑 없음"}])
            ps = paras("".join(doc.body))
            texts = [kjn_profile.plain_texts(p) for p in ps]
            i = texts.index("<그림 3-1> 아키텍처")
            self.assertIn("<hp:pic", ps[i + 1])
            self.assertEqual(texts[i + 2], kjn_profile.DEFAULT_FIGURE_SOURCE)
            pic = next(ET.fromstring(kjn_profile._wrap(ps[i + 1])).iter(HP + "pic"))
            self.assertLessEqual(int(pic.find(HP + "sz").get("width")), int(pf.get("table", "total_width")))
            self.assertEqual(len(doc.bin_items), 1)
            item_id = doc.bin_items[0][0]
            self.assertIn('binaryItemIDRef="%s"' % item_id, ps[i + 1])
            j = texts.index("[그림 삽입 예정: <그림 3-2> 매핑 없음]")
            self.assertIn(tpl.header.red_char_pr_id(doc.asm.anchor_spec("figure")["char"]), ps[j])
            self.assertEqual(doc.lof, ["<그림 3-1> 아키텍처", "<그림 3-2> 매핑 없음"])
            secs = {"Contents/section2.xml": doc.build_section2(), "Contents/section0.xml": tpl.s0,
                    "Contents/section1.xml": tpl.s1}
            entries = kjn_profile.plan_package(tpl, secs, tpl.header.xml, doc.bin_items)
            names = [e[0] for e in entries]
            self.assertIn("BinData/%s.png" % item_id, names)
            self.assertNotIn("BinData/image1.png", names)  # 쓰지 않는 김정년 그림 제거
            hpf = dict((e[0], e[1]) for e in entries)["Contents/content.hpf"].decode("utf-8")
            self.assertIn('<opf:item id="%s" href="BinData/%s.png"' % (item_id, item_id), hpf)
            self.assertNotIn('id="image1"', hpf)
        finally:
            shutil.rmtree(tmp)

    # 목차 탭 구조·쪽수
    def test_toc_tab_and_pages(self):
        doc, _tpl, _pf = make_doc(toc_pages={"toc": {"제 1 장 서론": 1}, "lot": {"<표 4-2>": 33}})
        _cap, tbl = caption_and_table("ch04", "<표 4-2>")
        doc.add_blocks([{"type": "h1", "text": "제1장 서론"}, {"type": "h2", "text": "제1절 배경"},
                        {"type": "table_caption", "text": "<표 4-2> 연구 가설 종합"}, tbl])
        s1 = doc.build_section1(abstract_kr=["목적 문단", "[DATA PENDING: 결과]"])
        self.assertRegex(s1, r'<hp:t>제 1 장 서론<hp:tab width="\d+" leader="3" type="2"/>1</hp:t>')
        self.assertRegex(s1, r'<hp:t> 제 1 절 배경<hp:tab width="\d+" leader="3" type="2"/>0</hp:t>')
        self.assertRegex(s1, r'&lt;표 4-2&gt; 연구 가설 종합<hp:tab width="\d+" leader="3" type="2"/>33</hp:t>')
        self.assertIn("[확정 필요: 감사의 글", kjn_profile.plain_texts(s1))
        self.assertEqual(kjn_profile.leftover_hits([kjn_profile.plain_texts(s1)]), {})
        ET.fromstring(s1.encode("utf-8"))

    def test_abstract_skeleton_parse(self):
        md = os.path.join(os.path.dirname(os.path.dirname(TOOL)), "01.docs", "00_목차.md")
        if not os.path.exists(md):
            self.skipTest("00_목차.md 없음")
        out = kjn_profile.parse_abstract_skeleton(read_text(md))
        self.assertGreaterEqual(len(out), 6)
        self.assertTrue(any(t.startswith("[DATA PENDING") for t in out))
        self.assertTrue(out[-1].startswith("주제어"))

    # 이식: 스타일 재매핑·복제, itemCnt, 표 폭 재계산(병합 보존), CELL·linesegarray 제거
    def test_transplant_remap_and_rescale(self):
        tmp = tempfile.mkdtemp()
        try:
            header = read_text(os.path.join(TEMPLATE_DIR, "Contents__header.xml"))
            ed = kjn_profile.HeaderEditor(header)
            new_char = re.sub(r'\bheight="\d+"', 'height="1234"', ed.item_xml("charPr", "55"), count=1)
            src_char = ed.add("charPr", new_char)   # 원본에만 있는 charPr
            with open(os.path.join(tmp, "Contents__header.xml"), "w", encoding="utf-8") as f:
                f.write(ed.xml)
            tbl = ('<hp:tbl id="5" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
                   'lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="2" colCnt="2" cellSpacing="0" '
                   'borderFillIDRef="5" noAdjust="0"><hp:sz width="38402" widthRelTo="ABSOLUTE" height="100" '
                   'heightRelTo="ABSOLUTE" protect="0"/>%s</hp:tbl>')
            cell = ('<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="5">'
                    '<hp:subList id=""><hp:p id="0" paraPrIDRef="43" styleIDRef="3" pageBreak="0" columnBreak="0" '
                    'merged="0"><hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run><hp:linesegarray><hp:lineseg/>'
                    '</hp:linesegarray></hp:p></hp:subList><hp:cellAddr colAddr="%d" rowAddr="%d"/>'
                    '<hp:cellSpan colSpan="%d" rowSpan="1"/><hp:cellSz width="%d" height="100"/>'
                    '<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')
            rows = ("<hp:tr>" + cell % (src_char, "병합 제목", 0, 0, 2, 38402) + "</hp:tr>"
                    "<hp:tr>" + cell % ("55", "왼쪽", 0, 1, 1, 10000) + cell % ("55", "오른쪽", 1, 1, 1, 28402) + "</hp:tr>")
            para = ('<hp:p id="0" paraPrIDRef="43" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                    '<hp:run charPrIDRef="55">' + tbl % rows + '<hp:t/></hp:run></hp:p>')
            sec = ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec xmlns:hp="%s" xmlns:hs="%s">%s'
                   '<hp:p id="0" paraPrIDRef="43" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                   '<hp:run charPrIDRef="%s"><hp:t>둘째 문단</hp:t></hp:run></hp:p></hs:sec>'
                   % (kjn_profile.NS["hp"], kjn_profile.NS["hs"], para, src_char))
            with open(os.path.join(tmp, "Contents__section2.xml"), "w", encoding="utf-8") as f:
                f.write(sec)
            doc, tpl, pf = make_doc()
            before = len(tpl.header.items("charPr"))
            raw = kjn_profile.load_source(tmp)
            out, importer = kjn_profile.transplant_paragraphs(raw, 2, [0, 1], tpl.header, doc.ids, 39491)
            self.assertEqual(len(out), 2)
            self.assertEqual(importer.maps["charPr"]["55"], "55")          # 같은 서명 → 재사용
            new_id = importer.maps["charPr"][src_char]
            self.assertNotIn(new_id, ("55",))
            self.assertEqual(len(tpl.header.items("charPr")), before + 1)  # 없던 서명만 복제
            kjn_profile.HeaderEditor(tpl.header.xml)                         # itemCnt 정합
            self.assertIn('height="1234"', tpl.header.item_xml("charPr", new_id))
            self.assertNotIn('pageBreak="CELL"', out[0])
            self.assertNotIn("linesegarray", out[0])
            self.assertIn('styleIDRef="0"', out[0])
            t = tbl_elem(out[0])
            self.assertEqual(t.find(HP + "sz").get("width"), "39491")
            r = rows_of(t)
            self.assertEqual(r[0][0]["w"], 39491)
            self.assertEqual(r[1][0]["w"] + r[1][1]["w"], 39491)
            self.assertEqual(r[0][0]["cs"], 2)
            self.assertIn('charPrIDRef="%s"' % new_id, out[1])
        finally:
            shutil.rmtree(tmp)

    # 부록1 설문지 통째 이식(replace_appendix) + 감사의 글(옛 제목 상자·빨간 메모) — load_transplants 경유
    def test_transplant_replace_appendix_and_thanks(self):
        tmp = tempfile.mkdtemp()
        try:
            header = read_text(os.path.join(TEMPLATE_DIR, "Contents__header.xml"))
            ns = 'xmlns:hp="%s" xmlns:hs="%s"' % (kjn_profile.NS["hp"], kjn_profile.NS["hs"])

            def p(text, page_break=0, char="55"):
                return ('<hp:p id="0" paraPrIDRef="43" styleIDRef="0" pageBreak="%d" columnBreak="0" merged="0">'
                        '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run></hp:p>' % (page_break, char, text))
            box = ('<hp:p id="0" paraPrIDRef="45" styleIDRef="0" pageBreak="1" columnBreak="0" merged="0">'
                   '<hp:run charPrIDRef="56"><hp:tbl id="9" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
                   'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="1" '
                   'colCnt="1" cellSpacing="0" borderFillIDRef="5" noAdjust="0"><hp:sz width="36284" '
                   'widthRelTo="ABSOLUTE" height="282" heightRelTo="ABSOLUTE" protect="0"/><hp:tr>'
                   '<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="4">'
                   '<hp:subList id="">' + p("감사의 글", char="12") + '</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/>'
                   '<hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="36284" height="282"/>'
                   '<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc></hp:tr></hp:tbl>'
                   '<hp:t/></hp:run></hp:p>')
            s1 = '<hs:sec %s>%s%s%s%s</hs:sec>' % (ns, p("앞 문단"), box, p("  감사 본문 한 문장"), p("윤   혁"))
            s2 = '<hs:sec %s>%s%s%s%s</hs:sec>' % (ns, p("부   록 (도입 현장)", 1), p("설문 상자 이식본"),
                                                  p("Part B 응답표 이식본"), p("", 1))
            for name, text in (("Contents__header.xml", header), ("Contents__section1.xml", s1),
                               ("Contents__section2.xml", s2)):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                    f.write(text)
            spec = {"감사의글": {"source_hwpx": tmp, "section": 1, "range": [1, 3]},
                    "부록1_설문지": {"source_hwpx": tmp, "section": 2, "range": [1, 3],
                                  "replace_appendix": "부 록 — 설문지", "keep_until": "부 록 (도입 현장)"}}
            spec_path = os.path.join(tmp, "transplant.json")
            with open(spec_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, ensure_ascii=False)
            doc, tpl, pf = make_doc()
            thanks, after, _rc, notes, replaces = blocks_to_hwpx.load_transplants(
                spec_path, tpl, doc.ids, pf, tmp, asm=doc.asm)
            self.assertEqual(after, {})
            self.assertTrue(any("쪽 나눔 빈 문단" in n for n in notes))  # 범위 끝 빈 쪽 경고
                # 2026-10-08 사양 변경: 빨간 메모는 끝(날짜·성명 뒤)이 아니라 본문 첫 문단 바로 뒤에 온다.
            texts = [kjn_profile.plain_texts(x) for x in thanks]
            note_idx = texts.index(blocks_to_hwpx.THANKS_RED_NOTE)
            first_body = next(i for i, x in enumerate(thanks) if "<hp:tbl" not in x and texts[i].strip())
            self.assertEqual(note_idx, first_body + 1)
            self.assertNotEqual(texts[-1], blocks_to_hwpx.THANKS_RED_NOTE)
            self.assertIn(tpl.header.red_char_pr_id(pf.spec("abstract_body")["char"]), thanks[note_idx])
            apx = blocks_of("apx1")
            doc.add_blocks(apx, appendix=True, replace=replaces["부록—설문지"])
            body = [kjn_profile.plain_texts(x) for x in paras("".join(doc.body))]
            self.assertEqual(body[0], "부 록 — 설문지")
            i = body.index("부 록 (도입 현장)")
            self.assertEqual(body[i + 2:i + 4], ["설문 상자 이식본", "Part B 응답표 이식본"])
            self.assertNotIn("Part A. 인구통계학적 특성", body)          # 블록 본문은 이식본으로 대체
            toc = [t for _l, t in doc.toc]
            self.assertIn("Part A. 인구통계학적 특성", toc)              # 목차는 블록 기준 유지
            self.assertIn("부 록 (미도입 현장)", toc)
            s1_out = doc.build_section1(thanks_xml=thanks, abstract_kr=["개요"])
            text = kjn_profile.plain_texts(s1_out)
            boxes = [x for x in paras(s1_out) if "<hp:tbl" in x and "감사의 글" in kjn_profile.plain_texts(x)]
            self.assertEqual(len(boxes), 1)                                # 양식 상자와 옛 상자가 겹치지 않는다
            self.assertTrue(text.rstrip().endswith("개요"))
            self.assertIn("감사 본문 한 문장", text)
            self.assertNotIn('pageBreak="CELL"', s1_out)
            ET.fromstring(s1_out.encode("utf-8"))
            kjn_profile.HeaderEditor(tpl.header.xml)
        finally:
            shutil.rmtree(tmp)

    # 1열 표: 좌우 모두 열린 borderFill을 복제 추가(양식에 없음)
    def test_single_column_table_open_sides(self):
        doc, tpl, pf = make_doc()
        before = len(tpl.header.items("borderFill"))
        xml_text, widths = doc.asm.table_xml(["구분"], [["가"], ["나"]])
        self.assertEqual(widths, [int(pf.get("table", "total_width"))])
        ids = set(re.findall(r'<hp:tc [^>]*borderFillIDRef="(\d+)"', xml_text))
        self.assertEqual(len(ids), 2)
        for bf in ids:
            item = tpl.header.item_xml("borderFill", bf)
            self.assertRegex(item, r'<hh:leftBorder type="NONE"')
            self.assertRegex(item, r'<hh:rightBorder type="NONE"')
        # 같은 서명이 양식에 있으면 재사용(본문 셀은 좌우 NONE인 bf 9와 같다), 없으면 추가
        self.assertLessEqual(len(tpl.header.items("borderFill")), before + 2)
        head_bf = re.search(r'<hp:tc name="" header="1"[^>]*borderFillIDRef="(\d+)"', xml_text).group(1)
        self.assertIn("#D9D9D9", tpl.header.item_xml("borderFill", head_bf))
        kjn_profile.HeaderEditor(tpl.header.xml)

    # Task G 실제 프로파일로 전체 조립(파일 없이)
    @unittest.skipUnless(os.path.exists(G_PROFILE), "Task G 프로파일 없음")
    def test_full_assembly_with_task_g_profile(self):
        refs_v2 = os.path.join(MIGRATE, "references_kjn_v2.json")
        doc, tpl, pf, secs = full_assembly(G_PROFILE, refs_v2 if os.path.exists(refs_v2) else None)
        hits = kjn_profile.leftover_hits([kjn_profile.plain_texts(x) for x in secs.values()], pf)
        self.assertEqual(hits, {})
        self.assertEqual(len(doc.lot), 30)
        for name, xml_text in secs.items():
            self.assertEqual(xml_text.count('pageBreak="CELL"'), 0, name)
            ET.fromstring(xml_text.encode("utf-8"))
        for cap, widths in doc.table_widths:
            self.assertEqual(sum(widths), int(pf.get("table", "total_width")), cap)
            self.assertGreater(min(widths), 1000, cap)


def full_assembly(profile_path, references=None):
    args = argparse.Namespace(
        template=TEMPLATE_DIR, profile=profile_path,
        blocks=[os.path.join(INPUTS, n + ".blocks.json") for n in legacy_harness.BLOCK_FILES],
        references=references or os.path.join(INPUTS, "references.json"), images=None, toc_pages=None, transplant=None,
        front_md=None, no_tail=False)
    pf = kjn_profile.load_profile(profile_path)
    doc, tpl, secs, _pages = blocks_to_hwpx.assemble_kjn(args, pf, TOOL)
    return doc, tpl, pf, secs


class LegacyRegressionTests(unittest.TestCase):

    # (g) 옛 style_map.json 조립 section2 XML = 변경 전 코드 출력
    def test_g_legacy_section2_identical(self):
        with open(legacy_harness.BASELINE_XML, encoding="utf-8", newline="") as f:
            baseline = f.read()
        self.assertEqual(legacy_harness.build_legacy_section2(blocks_to_hwpx), baseline)

    def test_g_baseline_is_from_pre_change_code(self):
        path = os.path.join(legacy_harness.FIXTURES, "legacy_blocks_to_hwpx_pre.py")
        spec = importlib.util.spec_from_file_location("legacy_pre", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "TABLE_WIDTH"))  # 변경 전 하드코딩 상수가 있는 원본 코드
        with open(legacy_harness.BASELINE_XML, encoding="utf-8", newline="") as f:
            self.assertEqual(legacy_harness.build_legacy_section2(mod), f.read())

    def test_legacy_profile_extras_explicit(self):
        legacy = load_json(os.path.join(INPUTS, "style_map.json"))
        pf = kjn_profile.load_profile(legacy)
        self.assertEqual(pf.kind, "legacy")
        self.assertEqual(int(pf.get("table", "tbl_attrs", "sz", "width")), 39142)
        self.assertEqual(pf.get("legacy", "caption_row"), {"border": "13", "para": "11", "char": "58"})
        self.assertNotIn("legacy", legacy)  # 원본 dict는 바꾸지 않는다


class TableSplitTests(unittest.TestCase):
    """쪽 나눔 3단계: 한 쪽에 들어가는 표는 NONE·treatAsChar=1, 가용 높이를 넘는 표만 TABLE·treatAsChar=0."""

    def test_short_table_whole(self):
        doc, _tpl, _pf = make_doc()
        self.assertTrue(doc.asm.avail_height and doc.asm.avail_height > 40000)
        _cap, tbl = caption_and_table("ch02", "<표 2-1>")
        xml_text, _w = doc.asm.table_xml(tbl["header"], tbl["rows"])
        t = tbl_elem(xml_text)
        self.assertEqual(t.get("pageBreak"), "NONE")
        self.assertEqual(t.find(HP + "pos").get("treatAsChar"), "1")

    def test_tall_table_row_split(self):
        doc, _tpl, _pf = make_doc()
        _cap, tbl = caption_and_table("ch04", "<표 4-3>")
        xml_text, _w = doc.asm.table_xml(tbl["header"], tbl["rows"])
        t = tbl_elem(xml_text)
        self.assertEqual(t.get("pageBreak"), "TABLE")
        self.assertEqual(t.get("repeatHeader"), "1")
        pos = t.find(HP + "pos")
        self.assertEqual(pos.get("treatAsChar"), "0")
        self.assertEqual(pos.get("horzRelTo"), "COLUMN")
        self.assertNotEqual(t.get("zOrder"), "0")
        self.assertNotIn('pageBreak="CELL"', xml_text)
        self.assertEqual(len(doc.asm.split_tables), 1)


if __name__ == "__main__":
    unittest.main()
