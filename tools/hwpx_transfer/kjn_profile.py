# 양식 프로파일(JSON)을 읽어 옛 윤혁 양식과 김정년 양식 모두에 맞춰 학위논문 hwpx XML을 조립하는 모듈
"""kjn_profile.py — 양식 프로파일 주입형 조립 부품.

구성.
  - 공용 XML 부품: esc, GUIDE_MARKER_RE, split_paragraphs, IdGen (blocks_to_hwpx가 재수출한다).
  - Profile: 프로파일 키 접근. 키가 없으면 ProfileError로 멈춘다(조용한 기본값 금지).
    옛 `style_map.json`에는 없던 옛 양식 실측 상수는 LEGACY_EXTRAS로 명시해 붙인다.
  - HeaderEditor: header.xml의 charPr·paraPr·borderFill·tabPr·글꼴 항목 재사용·복제(itemCnt 갱신).
  - KjnDocument: 김정년 양식 프로파일로 section0(표지)·section1(전면부)·section2(본문·참고문헌·부록·Abstract)를
    조립하고 BinData 그림과 content.hpf manifest를 갱신한다.
  - transplant_paragraphs: 옛 hwpx 문단 XML 이식(스타일 ID 재매핑, 표 열폭 비례 재계산).

hwpx 파일 쓰기는 blocks_to_hwpx.main()만 한다. 이 모듈의 함수는 모두 문자열·바이트를 돌려준다.
"""

import copy
import json
import os
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

import table_layout

# ── 공용 XML 부품 ──────────────────────────────────────────────────────────────
CELL_LINEBREAK_TOKEN = "<br>"
EMSP_TOKEN = "&emsp;"
EMSP_CHAR = " "  # 전각 공백(EM SPACE)

# 본문이 아니라 미확정 자리·인용·그림 지시임을 나타내는 마커. 대괄호 전부가 아니라
# 이 다섯 접두사만 판정하며 콜론·줄표 등 접두사 뒤 구분 문자는 제한하지 않는다.
# 대괄호 없는 `실험전`은 결과표의 미수집 자리 표기(2026-09-30 사용자 지시)로, 낱말 전체를 빨갛게 한다.
GUIDE_MARKER_RE = re.compile(
    r"\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전"
)

XML_PROLOG = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

NS = {
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hp10": "http://www.hancom.co.kr/hwpml/2016/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hhs": "http://www.hancom.co.kr/hwpml/2011/history",
    "hm": "http://www.hancom.co.kr/hwpml/2011/master-page",
    "hpf": "http://www.hancom.co.kr/schema/2011/hpf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf/",
    "ooxmlchart": "http://www.hancom.co.kr/hwpml/2016/ooxmlchart",
    "hwpunitchar": "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar",
    "epub": "http://www.idpf.org/2007/ops",
    "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
}
for _prefix, _uri in NS.items():
    ET.register_namespace(_prefix, _uri)


def esc(text):
    """hp:t에 넣을 텍스트 — &emsp; 토큰을 전각 공백으로 바꾼 뒤 XML 이스케이프한다."""
    text = text.replace(EMSP_TOKEN, EMSP_CHAR)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def split_paragraphs(xml_text):
    """최상위 hp:p 요소의 (시작, 끝) 오프셋 목록. 표 안 중첩 문단은 깊이로 걸러낸다."""
    spans, depth, start = [], 0, None
    for m in re.finditer(r"<hp:p(?=[\s/>])|</hp:p>", xml_text):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    return spans


class IdGen(object):
    """문단·표 id 발급기. 양식이 쓰는 값 범위(2147483648~)에서 고유하게 증가시킨다."""

    def __init__(self, start=2147483648):
        self._n = start

    def next(self):
        self._n += 1
        return self._n


def strip_cell_page_break(xml_text):
    """`pageBreak="CELL"`(표 셀 단위 나눔)은 저장소 규칙상 금지 — 양식에서 옮긴 표도 NONE으로 바꾼다."""
    return re.sub(r'(<hp:tbl\b[^>]*?\bpageBreak=")CELL(")', r"\g<1>NONE\g<2>", xml_text)


def strip_linesegs(xml_text):
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", xml_text, flags=re.S)


def plain_texts(xml_text):
    """hp:t 안 텍스트(탭 등 자식 태그 제거)를 이어 붙인다 — 잔존 문구 검사용."""
    out = []
    for m in re.finditer(r"<hp:t>(.*?)</hp:t>", xml_text, re.S):
        out.append(re.sub(r"<[^>]+>", "", m.group(1)))
    text = "\n".join(out)
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


# ── 프로파일 ──────────────────────────────────────────────────────────────────
class ProfileError(Exception):
    """프로파일에 필요한 키가 없거나 형식이 다르다 — 조용한 기본값 대신 명시적으로 멈춘다."""


# 옛 윤혁 양식(style_map.json, 2026-07-25 실측)에는 키로 없고 blocks_to_hwpx.py에 상수로 박혀 있던 값.
# style_map.json은 수정하지 않으므로 옛 프로파일을 읽을 때 이 값을 `legacy` 키로 붙인다.
LEGACY_EXTRAS = {
    # 셀 최소 높이. 양식 최소 셀(cellSz height=1565)
    "row_min_height": 1565,
    # 본문 줄 폭. 양식 linesegarray의 horzsize 실측값
    "line_width": 39684,
    # style_map.json에 없어 양식 XML에서 직접 실측한 스타일(참고문헌·부록 영역)
    "ref_title": {"style": "0", "para": "5", "char": "63"},      # s2 p300 "참고문헌"
    "ref_category": {"style": "0", "para": "12", "char": "36"},  # s2 p303 "가 . 학위논문"
    "ref_entry": {"style": "0", "para": "59", "char": "62"},     # s2 p304 서지 항목
    "appendix_title": {"style": "0", "para": "31", "char": "14"},  # s2 p317 "부   록"
    # 본문 볼드 run. charPr 9는 charPr 61(본문)과 같은 11pt·한양신명조에 bold만 추가된 짝
    "body_bold_char": "9",
    # 표 셀 볼드 run. charPr 122는 charPr 7(셀 기본)의 bold 짝
    "cell_bold_char": "122",
    # h4(소제목)는 양식에 실측 대응이 없다 — 본문 문단 서식 + 볼드로 대체(가정)
    "h4_char": "9",
    # 표 안 캡션 행: 전체 열 병합 + borderFill 13(아래만 실선), paraPr 11 · charPr 58
    "caption_row": {"border": "13", "para": "11", "char": "58"},
    # 좌우 개방형 테두리: 왼쪽 끝 45, 오른쪽 끝 46, 내부 6
    "edge_borders": {"left": "45", "right": "46", "inner": "6", "single": "6"},
    # linesegarray vertsize 계산용 charPr 높이표(양식 실측)
    "char_heights": {
        "63": 1600, "42": 1600, "67": 1500, "52": 1500, "41": 1400,
        "14": 1400, "13": 1200, "36": 1200, "116": 1200,
        "61": 1100, "62": 1100, "9": 1100, "56": 1100, "57": 1100,
        "7": 1000, "58": 1000, "122": 1000,
    },
    "char_height_default": 1100,
    # 빈 문단·목차 글자 charPr
    "blank_char": "61",
    "ref_blank_char": "62",
    "toc_char": "13",          # 목차 항목: 빨강(116) 대신 흑색 12pt
    "front_blank_char": "13",
    "table_anchor_height_char": "62",
    # 부록1 설문지 표지 박스 글자(가운데 정렬 문단)
    "survey_cover": {"title_char": "41", "label_char": "63"},
    # 셀 패딩 합(좌 510 + 우 510)
    "cell_hpad": 1020,
}

KJN_REQUIRED_TOP = (
    "page", "front_ranges", "back_ranges", "cover",
    "h1_chapter", "h2_section", "h3_item", "h4_sub", "body", "body_bold_charPr",
    "table_caption", "figure_caption", "source_note", "toc_entry", "toc_lot_entry",
    "ref_heading", "ref_category", "ref_item", "appendix_heading",
    "abstract_heading", "abstract_meta", "abstract_body", "blank_para",
    "table", "figure", "red_charPr", "page_number_control", "conventions",
)


class Profile(object):
    """프로파일 dict 래퍼. get()은 키가 없으면 ProfileError를 던진다."""

    def __init__(self, data, kind, source=""):
        self.data = data
        self.kind = kind
        self.source = source

    def get(self, *path):
        node = self.data
        walked = []
        for key in path:
            walked.append(str(key))
            if isinstance(node, dict) and key in node:
                node = node[key]
            elif isinstance(node, list) and isinstance(key, int) and -len(node) <= key < len(node):
                node = node[key]
            else:
                raise ProfileError(
                    "프로파일(%s, %s)에 키 '%s'가 없다" % (self.kind, self.source or "dict", ".".join(walked))
                )
        return node

    def has(self, *path):
        try:
            self.get(*path)
            return True
        except ProfileError:
            return False

    def first(self, *paths):
        """여러 후보 경로 중 처음 있는 값. 하나도 없으면 후보 전부를 적어 ProfileError."""
        for path in paths:
            if self.has(*path):
                return self.get(*path)
        raise ProfileError(
            "프로파일(%s)에 다음 키가 모두 없다: %s"
            % (self.kind, ", ".join(".".join(str(k) for k in p) for p in paths))
        )

    def spec(self, key):
        s = self.get(key)
        for sub in ("styleIDRef", "paraPrIDRef", "charPrIDRef"):
            if sub not in s:
                raise ProfileError("프로파일 '%s'에 '%s'가 없다" % (key, sub))
        return {"style": str(s["styleIDRef"]), "para": str(s["paraPrIDRef"]), "char": str(s["charPrIDRef"])}

    def __getitem__(self, key):
        return self.get(key)


def load_profile(obj, source=""):
    """dict·경로·Profile → Profile. 옛 style_map.json이면 LEGACY_EXTRAS를 `legacy` 키로 붙인다."""
    if isinstance(obj, Profile):
        return obj
    if isinstance(obj, str):
        with open(obj, encoding="utf-8") as f:
            data = json.load(f)
        source = source or obj
    elif isinstance(obj, dict):
        data = obj
    else:
        raise ProfileError("프로파일은 dict 또는 JSON 경로여야 한다: %r" % type(obj))

    if "table_caption" in data or "front_ranges" in data:
        prof = Profile(data, "kjn", source)
        missing = [k for k in KJN_REQUIRED_TOP if k not in data]
        if missing:
            raise ProfileError("김정년 양식 프로파일에 최상위 키가 없다: %s" % ", ".join(missing))
        return prof
    if "caption" in data and "front_matter_ranges" in data:
        merged = dict(data)
        merged["legacy"] = copy.deepcopy(LEGACY_EXTRAS)
        return Profile(merged, "legacy", source)
    raise ProfileError("프로파일 종류를 판정할 수 없다 — table_caption/front_ranges(김정년) 또는 "
                       "caption/front_matter_ranges(옛 양식) 키가 필요하다")


def range_bounds(value, name="range"):
    """프로파일 문단 범위 표기 → (시작, 끝) 포함 구간. [a,b] · ["section1",a,b] · {start,end} 허용."""
    if isinstance(value, dict):
        if "start" in value and "end" in value:
            return int(value["start"]), int(value["end"])
        if "range" in value:
            return range_bounds(value["range"], name)
    if isinstance(value, (list, tuple)):
        nums = [v for v in value if isinstance(v, int) or (isinstance(v, str) and v.isdigit())]
        if len(nums) >= 2:
            return int(nums[-2]), int(nums[-1])
        if len(nums) == 1:
            return int(nums[0]), int(nums[0])
    raise ProfileError("프로파일 범위 '%s'의 형식을 해석할 수 없다: %r" % (name, value))


# ── header.xml 편집기 ─────────────────────────────────────────────────────────
HEADER_KINDS = {
    # kind: (항목 태그, 컨테이너 태그, 개수 속성)
    "charPr": ("hh:charPr", "hh:charProperties", "itemCnt"),
    "paraPr": ("hh:paraPr", "hh:paraProperties", "itemCnt"),
    "borderFill": ("hh:borderFill", "hh:borderFills", "itemCnt"),
    "tabPr": ("hh:tabPr", "hh:tabProperties", "itemCnt"),
}


def _element_pattern(tag, item_id=None):
    if item_id is None:
        return re.compile(r'<%s\b[^>]*?\bid="(\d+)"[^>]*?(?:/>|>.*?</%s>)' % (tag, tag), re.S)
    return re.compile(r'<%s\b[^>]*?\bid="%s"[^>]*?(?:/>|>.*?</%s>)' % (tag, re.escape(str(item_id)), tag), re.S)


def _canonical(xml_text, drop_color=False):
    """서명 비교용 정규화 — 루트 id 속성 제거, 태그 사이 공백 제거."""
    text = re.sub(r'^(<[^>]*?)\s\bid="\d+"', r"\1", xml_text, count=1)
    if drop_color:
        text = re.sub(r'^(<[^>]*?)\s\btextColor="[^"]*"', r"\1", text, count=1)
    return re.sub(r">\s+<", "><", text.strip())


class HeaderEditor(object):
    """header.xml 문자열 편집기. 항목 추가 시 itemCnt를 실제 개수로 갱신한다."""

    def __init__(self, header_xml):
        self.xml = header_xml
        self._red_by_base = {}
        self._verify_counts()

    def _verify_counts(self):
        for kind, (tag, container, cnt_attr) in HEADER_KINDS.items():
            m = re.search(r'<%s\b[^>]*\b%s="(\d+)"' % (container, cnt_attr), self.xml)
            if not m:
                continue
            actual = len(self.items(kind))
            if int(m.group(1)) != actual:
                raise ValueError("header.xml %s itemCnt(%s)와 실제 개수(%d)가 다르다" % (container, m.group(1), actual))

    def items(self, kind):
        tag = HEADER_KINDS[kind][0]
        return {m.group(1): m.group(0) for m in _element_pattern(tag).finditer(self.xml)}

    def item_xml(self, kind, item_id):
        m = _element_pattern(HEADER_KINDS[kind][0], item_id).search(self.xml)
        if not m:
            raise ValueError("header.xml에 %s id=%s가 없다" % (kind, item_id))
        return m.group(0)

    def has(self, kind, item_id):
        return _element_pattern(HEADER_KINDS[kind][0], item_id).search(self.xml) is not None

    def find_same(self, kind, xml_text, drop_color=False):
        sig = _canonical(xml_text, drop_color)
        for item_id, item in self.items(kind).items():
            if _canonical(item, drop_color) == sig:
                return item_id
        return None

    def add(self, kind, xml_text):
        """id를 새로 매겨 항목을 컨테이너 끝에 추가하고 itemCnt를 갱신한다. 새 id를 돌려준다."""
        tag, container, cnt_attr = HEADER_KINDS[kind]
        existing = self.items(kind)
        new_id = str(max([int(i) for i in existing] or [-1]) + 1)
        clone = re.sub(r'^(<%s\b[^>]*?\bid=")\d+(")' % re.escape(tag), r"\g<1>%s\g<2>" % new_id, xml_text, count=1)
        closing = "</%s>" % container
        if closing not in self.xml:
            raise ValueError("header.xml에 %s 닫는 태그가 없다" % container)
        self.xml = self.xml.replace(closing, clone + closing, 1)
        count = len(existing) + 1
        self.xml, n = re.subn(
            r'(<%s\b[^>]*\b%s=")\d+(")' % (container, cnt_attr),
            lambda m: m.group(1) + str(count) + m.group(2), self.xml, count=1)
        if n != 1:
            raise ValueError("header.xml %s itemCnt를 갱신하지 못했다" % container)
        return new_id

    def red_char_pr_id(self, base_char_pr_id):
        """원본과 id·textColor 외 속성이 같은 빨간 charPr ID(없으면 복제 추가)."""
        base = str(base_char_pr_id)
        if base in self._red_by_base:
            return self._red_by_base[base]
        if not self.has("charPr", base):
            raise ValueError("header.xml에 charPr id=%s가 없다" % base)
        base_xml = self.item_xml("charPr", base)
        sig = _canonical(base_xml, drop_color=True)
        for item_id, item in self.items("charPr").items():
            if re.search(r'\btextColor="#FF0000"', item, re.I) and _canonical(item, drop_color=True) == sig:
                self._red_by_base[base] = item_id
                return item_id
        clone, n = re.subn(r'\btextColor="[^"]*"', 'textColor="#FF0000"', base_xml, count=1)
        if n != 1:
            raise ValueError("charPr id=%s에 textColor 속성이 없다" % base)
        new_id = self.add("charPr", clone)
        self._red_by_base[base] = new_id
        return new_id

    # 글꼴(언어별 fontface)
    def fonts(self):
        out = {}
        for fm in re.finditer(r'<hh:fontface\b[^>]*\blang="([A-Z]+)"[^>]*>(.*?)</hh:fontface>', self.xml, re.S):
            lang = fm.group(1)
            for f in re.finditer(r'<hh:font\b[^>]*\bid="(\d+)"[^>]*\bface="([^"]*)"', fm.group(2)):
                out[(lang, f.group(2))] = f.group(1)
        return out

    def font_face(self, lang, font_id):
        fm = re.search(r'<hh:fontface\b[^>]*\blang="%s"[^>]*>(.*?)</hh:fontface>' % lang, self.xml, re.S)
        if not fm:
            return None
        f = re.search(r'(<hh:font\b[^>]*\bid="%s"[^>]*?(?:/>|>.*?</hh:font>))' % re.escape(font_id), fm.group(1), re.S)
        return f.group(1) if f else None

    def add_font(self, lang, font_xml):
        fm = re.search(r'(<hh:fontface\b[^>]*\blang="%s"[^>]*>)(.*?)(</hh:fontface>)' % lang, self.xml, re.S)
        if not fm:
            raise ValueError("header.xml에 fontface lang=%s가 없다" % lang)
        ids = [int(i) for i in re.findall(r'<hh:font\b[^>]*\bid="(\d+)"', fm.group(2))]
        new_id = str(max(ids or [-1]) + 1)
        new_font = re.sub(r'(<hh:font\b[^>]*\bid=")\d+(")', r"\g<1>%s\g<2>" % new_id, font_xml, count=1)
        head = re.sub(r'\bfontCnt="\d+"', 'fontCnt="%d"' % (len(ids) + 1), fm.group(1), count=1)
        self.xml = self.xml[:fm.start()] + head + fm.group(2) + new_font + fm.group(3) + self.xml[fm.end():]
        return new_id


FONT_LANG_ATTRS = {"hangul": "HANGUL", "latin": "LATIN", "hanja": "HANJA", "japanese": "JAPANESE",
                   "other": "OTHER", "symbol": "SYMBOL", "user": "USER"}


class StyleImporter(object):
    """원본 header의 charPr·paraPr·borderFill·tabPr를 대상 header로 옮긴다.

    같은 서명(참조 ID까지 재매핑한 뒤 id만 뺀 XML)이 대상에 있으면 그 ID를 재사용하고,
    없으면 대상 header에 복제 추가한다. ID 충돌은 HeaderEditor.add가 새 ID를 매겨 막는다.
    """

    def __init__(self, source_header_xml, target):
        self.src = HeaderEditor.__new__(HeaderEditor)
        self.src.xml = source_header_xml
        self.src._red_by_base = {}
        self.dst = target
        self.maps = {"charPr": {}, "paraPr": {}, "borderFill": {}, "tabPr": {}, "font": {}}
        self.added = {"charPr": [], "paraPr": [], "borderFill": [], "tabPr": [], "font": []}

    def font(self, lang, font_id):
        key = (lang, font_id)
        if key in self.maps["font"]:
            return self.maps["font"][key]
        font_xml = self.src.font_face(lang, font_id)
        if font_xml is None:
            raise ValueError("원본 header에 %s 글꼴 id=%s가 없다" % (lang, font_id))
        face = re.search(r'\bface="([^"]*)"', font_xml).group(1)
        new_id = self.dst.fonts().get((lang, face))
        if new_id is None:
            new_id = self.dst.add_font(lang, font_xml)
            self.added["font"].append((lang, new_id))
        self.maps["font"][key] = new_id
        return new_id

    def _import(self, kind, item_id, rewrite):
        item_id = str(item_id)
        if item_id in self.maps[kind]:
            return self.maps[kind][item_id]
        xml_text = rewrite(self.src.item_xml(kind, item_id))
        found = self.dst.find_same(kind, xml_text)
        if found is None:
            found = self.dst.add(kind, xml_text)
            self.added[kind].append(found)
        self.maps[kind][item_id] = found
        return found

    def border_fill(self, item_id):
        return self._import("borderFill", item_id, lambda x: x)

    def tab_pr(self, item_id):
        return self._import("tabPr", item_id, lambda x: x)

    def char_pr(self, item_id):
        def rewrite(x):
            x = re.sub(r'\bborderFillIDRef="(\d+)"', lambda m: 'borderFillIDRef="%s"' % self.border_fill(m.group(1)), x)

            def font_ref(m):
                attrs = re.sub(
                    r'\b(hangul|latin|hanja|japanese|other|symbol|user)="(\d+)"',
                    lambda a: '%s="%s"' % (a.group(1), self.font(FONT_LANG_ATTRS[a.group(1)], a.group(2))),
                    m.group(1))
                return "<hh:fontRef%s/>" % attrs
            return re.sub(r"<hh:fontRef(\s[^>]*?)/>", font_ref, x)
        return self._import("charPr", item_id, rewrite)

    def para_pr(self, item_id):
        def rewrite(x):
            x = re.sub(r'\btabPrIDRef="(\d+)"', lambda m: 'tabPrIDRef="%s"' % self.tab_pr(m.group(1)), x)
            return re.sub(r'\bborderFillIDRef="(\d+)"', lambda m: 'borderFillIDRef="%s"' % self.border_fill(m.group(1)), x)
        return self._import("paraPr", item_id, rewrite)

    def remap_body(self, xml_text):
        """본문 XML의 charPr/paraPr/borderFill 참조를 대상 ID로 바꾼다. styleIDRef는 바탕글(0)로 둔다."""
        xml_text = re.sub(r'\bcharPrIDRef="(\d+)"', lambda m: 'charPrIDRef="%s"' % self.char_pr(m.group(1)), xml_text)
        xml_text = re.sub(r'\bparaPrIDRef="(\d+)"', lambda m: 'paraPrIDRef="%s"' % self.para_pr(m.group(1)), xml_text)
        xml_text = re.sub(r'\bborderFillIDRef="(\d+)"', lambda m: 'borderFillIDRef="%s"' % self.border_fill(m.group(1)), xml_text)
        return re.sub(r'\bstyleIDRef="\d+"', 'styleIDRef="0"', xml_text)


# ── 양식 패키지 읽기 ───────────────────────────────────────────────────────────
def read_package(path):
    """hwpx(ZIP) 또는 추출 디렉터리(`Contents__header.xml`처럼 '/'를 '__'로 바꾼 파일명) →
    (infos, raw). infos는 [(name, compress_type, ZipInfo|None)] 순서 목록."""
    if os.path.isdir(path):
        names = sorted(os.listdir(path))
        raw, infos = {}, []
        for fname in names:
            full = os.path.join(path, fname)
            if not os.path.isfile(full):
                continue
            name = fname.replace("__", "/")
            with open(full, "rb") as f:
                raw[name] = f.read()
            infos.append((name, zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED, None))
        infos.sort(key=lambda t: (t[0] != "mimetype", t[0]))
        return infos, raw
    with zipfile.ZipFile(path) as z:
        zinfos = z.infolist()
        raw = {i.filename: z.read(i.filename) for i in zinfos}
    return [(i.filename, i.compress_type, i) for i in zinfos], raw


def png_size(data):
    """PNG 바이트의 (가로, 세로) 픽셀. PNG가 아니면 ValueError."""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("PNG 파일이 아니다(그림은 PNG만 지원)")
    return struct.unpack(">II", data[16:24])


# ── 김정년 양식 조립 ───────────────────────────────────────────────────────────
CAPTION_RE = re.compile(r"^<표\s*\d+\s*-\s*\d+>\s+\S")
FIGURE_CAPTION_RE = re.compile(r"^<그림\s*\d+\s*-\s*\d+>")
SOURCE_NOTE_RE = re.compile(r"^\s*(?:자료\s*[:：]|주\s*[:：)]|주\))")
IMAGE_MD_RE = re.compile(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$")
HEADING_NUM_RE = re.compile(r"^제\s*(\d+)\s*(장|절|항)\s*")
DEFAULT_FIGURE_SOURCE = "자료: 연구자 작성."

# 김정년 고유 문구 — 조립 결과에 한 건이라도 남으면 표절 의심 산출물이다(CLAUDE.md 🟦).
KJN_FORBIDDEN = (
    "김 정 년", "김정년", "Kim Jung Neon", "안전시설물", "떨어짐 사고위험",
    "근로자의 안전행동 매개효과", "[작성지침]", "[자리표시자]", "[입력:", "[미작성]", "k2kim2002",
)
# 주의: 원고 부록1에는 정상 문구 "배포코드: [입력]"이 있으므로 김정년 고유 형식 "[입력:"만 금지한다.

# 전면부 목차 첫 묶음(양식 section1 p2∼p5의 구성)과 후면부 항목
FRONT_TOC_LABELS = ("표 목 차", "그림목차", "감사의 글", "논문개요")

# 부록1 설문지 표지(원고 `01.docs/부록1_설문지_양식.md` 코드펜스) — Part A 상자 이식이 없을 때만 쓴다.
SURVEY_COVER_TITLE = [
    "중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템",
    "개발 및 실증 연구",
    ": 도입 현장과 미도입 현장의 안전관리 실효성 비교를",
    "중심으로",
]
SURVEY_COVER_LABEL = "설  문  지"

# 표지 슬롯 role → 새 텍스트. 원고 단일 원본은 `01.docs/00_목차.md` 표지 골격(2026-08-24 확정 제목).
COVER_TEXT = {
    "title": "중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구",
    "subtitle": "도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로",
    "advisor": "박 종 용",
    "graduate_school": "경기대학교 공학대학원",
    "major": "건축·안전공학전공",
    "author": "윤  혁",  # 2026-10-08 사용자 확정("연구자 이름은 윤  혁"), 00_목차.md 표지 골격과 동일
}
COVER_ROLE_ALIASES = {
    "title": "title", "thesis_title": "title", "main_title": "title", "제목": "title",
    "subtitle": "subtitle", "sub_title": "subtitle", "부제": "subtitle",
    "advisor": "advisor", "supervisor": "advisor", "지도교수": "advisor",
    "graduate_school": "graduate_school", "school": "graduate_school", "university": "graduate_school",
    "대학원": "graduate_school", "school_name": "graduate_school",
    "major": "major", "department": "major", "dept": "major", "전공": "major",
    "author": "author", "name": "author", "student": "author", "성명": "author", "author_name": "author",
    "date": "date", "submit_date": "date", "year_month": "date", "approval_date": "date", "연월": "date",
    "approval": "approval", "approval_line": "approval", "approval_statement": "approval", "인준": "approval",
    "committee": "committee", "committee_name": "committee", "committee_blank": "committee",
    "reviewer": "committee", "심사위원": "committee",
    "keep": "keep", "degree": "keep", "degree_year": "keep", "label": "keep", "submission": "keep",
    "submission_statement": "keep", "fixed": "keep", "static": "keep", "seal": "keep",
    "committee_label": "keep", "year": "keep",
    # Task G 프로파일(style_map_kjn.json)의 한국어 role
    "연월": "date", "성명": "author", "대학원": "graduate_school", "학위문구": "keep", "기타": "keep",
}


def _norm(text):
    return re.sub(r"\s+", "", text)


def normalize_heading_number(text):
    """"제1장 서론" → "제 1 장 서론" (양식 conventions.heading_number_spacing)."""
    return HEADING_NUM_RE.sub(lambda m: "제 %s %s " % (m.group(1), m.group(2)), text, count=1)


def runs_text(block):
    return "".join(r.get("text", "") for r in block.get("runs", []))


def is_source_note(block):
    return block.get("type") == "p" and bool(SOURCE_NOTE_RE.match(runs_text(block)))


def image_md(block):
    if block.get("type") != "p":
        return None
    m = IMAGE_MD_RE.match(runs_text(block))
    return (m.group(1), m.group(2)) if m else None


def group_figures(blocks):
    """figure_caption을 앞뒤 그림 md·자료/주 문단과 묶어 합성 블록 `_figure`로 바꾼다.

    양식은 그림 제목이 그림 **위**, 출처가 아래다. 원고(MD)는 그림 → (주) → 캡션 순서일 수 있으므로
    캡션 바로 앞의 자료/주 문단과 그 앞 그림 md를 끌어와 캡션 → 그림 → 자료/주 순으로 재배열한다.
    단 자료/주 앞이 표이면 그 자료/주는 표의 것이므로 끌어오지 않는다.
    """
    out = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b.get("type") != "figure_caption":
            out.append(b)
            i += 1
            continue
        pre_notes = []
        k = len(out)
        while k > 0 and is_source_note(out[k - 1]):
            k -= 1
        if k < len(out) and (k == 0 or out[k - 1].get("type") != "table"):
            pre_notes = out[k:]
            del out[k:]
        img = None
        if out and image_md(out[-1]):
            img = image_md(out.pop())
        post_notes = []
        j = i + 1
        while j < len(blocks) and is_source_note(blocks[j]):
            post_notes.append(blocks[j])
            j += 1
        out.append({"type": "_figure", "caption": b["text"], "image_md": img,
                    "notes": pre_notes + post_notes})
        i = j
    return out


def parse_abstract_skeleton(md_text):
    """00_목차.md '2. 국문초록(골격)'의 불릿과 주제어 행 → 문단 텍스트 목록."""
    m = re.search(r"^##\s*2\.\s*국문초록.*?$(.*?)(?=^---\s*$|^##\s)", md_text, re.S | re.M)
    if not m:
        raise ValueError("00_목차.md에서 '## 2. 국문초록' 절을 찾지 못했다")
    paras = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith("- "):
            paras.append(s[2:].strip())
        elif s.startswith("**주제어"):
            paras.append(s.replace("**", "").strip())
    if not paras:
        raise ValueError("국문초록 골격에서 불릿을 찾지 못했다")
    return paras


def body_avail_height(section_xml):
    """본문 가용 높이 = pagePr@height - margin(top+bottom+header+footer) (hwpx-table-layout 규칙)."""
    pg = re.search(r'<hp:pagePr\b[^>]*\bheight="(\d+)"', section_xml)
    mg = re.search(r'<hp:margin\b[^>]*/>', section_xml)
    if not pg or not mg:
        raise ValueError("section XML에서 pagePr/margin을 찾지 못했다")

    def get(k):
        return int(re.search(r'\b%s="(\d+)"' % k, mg.group(0)).group(1))
    return int(pg.group(1)) - get("top") - get("bottom") - get("header") - get("footer")


class KjnTemplate(object):
    """김정년 양식 패키지(hwpx 또는 추출 디렉터리)와 프로파일을 묶는다."""

    def __init__(self, path, profile):
        self.path = path
        self.pf = profile
        self.infos, self.raw = read_package(path)
        for need in ("Contents/header.xml", "Contents/section0.xml", "Contents/section1.xml",
                     "Contents/section2.xml", "Contents/content.hpf"):
            if need not in self.raw:
                raise ValueError("양식 패키지에 %s가 없다" % need)
        self.header = HeaderEditor(self.raw["Contents/header.xml"].decode("utf-8"))
        self.s0 = self.raw["Contents/section0.xml"].decode("utf-8")
        self.s1 = self.raw["Contents/section1.xml"].decode("utf-8")
        self.s2 = self.raw["Contents/section2.xml"].decode("utf-8")
        self.hpf = self.raw["Contents/content.hpf"].decode("utf-8")
        self.s1_paras = split_paragraphs(self.s1)
        self.s2_paras = split_paragraphs(self.s2)
        self._slice_sec2_controls()

    def red_char_pr_id(self, base):
        return self.header.red_char_pr_id(base)

    def s1_para(self, idx):
        a, b = self.s1_paras[idx]
        return self.s1[a:b]

    def _slice_sec2_controls(self):
        idx = int(self.pf.get("page_number_control", "section2_first_para_idx"))
        a, b = self.s2_paras[idx]
        p0 = self.s2[a:b]
        m = re.search(r"(<hp:ctrl><hp:colPr.*?</hp:secPr>)", p0, re.S)
        if not m:
            raise ValueError("양식 section2 첫 문단에서 colPr/secPr 블록을 찾지 못했다")
        self.sec2_secpr = m.group(1)
        self.sec2_pagectrl = "".join(re.findall(r"<hp:ctrl><hp:page(?:Num|Hiding)[^>]*/></hp:ctrl>", p0))
        self.sec2_newnum = "".join(re.findall(r"<hp:ctrl><hp:newNum[^>]*/></hp:ctrl>", p0))
        self.s2_head = self.s2[: self.s2_paras[0][0]]
        numbering = self.pf.get("page", "page_numbering", "section2")
        hide = str(numbering.get("hidePageNum_first", "")) if isinstance(numbering, dict) else ""
        if hide == "1" and 'hidePageNum="1"' not in self.sec2_pagectrl:
            raise ValueError("프로파일은 본문 첫 쪽 번호 숨김(hidePageNum_first=1)인데 양식 section2 첫 문단에 없다")
        if not self.sec2_newnum:
            raise ValueError("양식 section2 첫 문단에 newNum 제어가 없다")


class KjnAssembler(object):
    """김정년 양식 프로파일로 문단·표·그림 XML 조각을 만든다."""

    def __init__(self, profile, ids, red_char_pr, header=None):
        self.pf = profile
        self.ids = ids
        self.red_char_pr = red_char_pr
        self.header = header
        self.added_border_fills = {}  # 원본 borderFill → 좌우 개방 복제본(1열 표용)
        self.sublist = profile.get("table", "cell_subList")
        self.total_width = int(profile.get("table", "total_width"))
        self.pad = profile.get("table", "cell_padding")
        self.hpad = int(self.pad["left"]) + int(self.pad["right"])
        self.vpad = int(self.pad["top"]) + int(self.pad["bottom"])
        self.avail_height = None  # KjnDocument가 양식 section2 pagePr/margin으로 채운다
        self.split_tables = []    # (추정 높이, 가용 높이) — 행 경계 나눔으로 바꾼 표
        self._z_order = 0         # treatAsChar=0 개체의 zOrder(겹침 순서) — 표마다 고유값
        self._keep_body_para = {}

    @staticmethod
    def _text_run(char_pr, text):
        return '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>' % (char_pr, esc(text))

    def marker_aware_runs(self, text, char_pr):
        matches = list(GUIDE_MARKER_RE.finditer(text))
        if not matches:
            return self._text_run(char_pr, text)
        red = self.red_char_pr(str(char_pr))
        parts, cursor = [], 0
        for match in matches:
            if match.start() > cursor:
                parts.append(self._text_run(char_pr, text[cursor:match.start()]))
            parts.append(self._text_run(red, match.group(0)))
            cursor = match.end()
        if cursor < len(text):
            parts.append(self._text_run(char_pr, text[cursor:]))
        return "".join(parts)

    def para(self, spec, runs_xml, page_break=False):
        return ('<hp:p id="%d" paraPrIDRef="%s" styleIDRef="%s" pageBreak="%d" columnBreak="0" merged="0">%s</hp:p>'
                % (self.ids.next(), spec["para"], spec["style"], 1 if page_break else 0, runs_xml))

    def text_para(self, spec, text, page_break=False):
        return self.para(spec, self.marker_aware_runs(text, spec["char"]), page_break)

    def keep_with_next_spec(self, spec):
        """spec의 paraPr를 keepWithNext="1"로 복제한 spec. 캡션과 표 사이의 '패널 A는 …' 문장이
        캡션만 앞 쪽에 남기고 표를 다음 쪽으로 보내던 문제(2026-10-08 스모크 <표 5-6>)를 막는다."""
        if self.header is None:
            return spec
        key = spec["para"]
        if key not in self._keep_body_para:
            xml_text = self.header.item_xml("paraPr", key)
            if 'keepWithNext="1"' in xml_text:
                self._keep_body_para[key] = key
            else:
                clone = xml_text.replace('keepWithNext="0"', 'keepWithNext="1"', 1)
                if clone == xml_text:
                    raise ValueError("paraPr %s에 keepWithNext 속성이 없다" % key)
                self._keep_body_para[key] = (self.header.find_same("paraPr", clone)
                                             or self.header.add("paraPr", clone))
        return dict(spec, para=self._keep_body_para[key])

    def runs_para(self, spec, runs, bold_char, prefix=""):
        parts = []
        for i, r in enumerate(runs):
            body = (prefix if i == 0 else "") + r.get("text", "")
            parts.append(self.marker_aware_runs(body, bold_char if r.get("bold") else spec["char"]))
        if not parts:
            parts.append('<hp:run charPrIDRef="%s"/>' % spec["char"])
        return self.para(spec, "".join(parts))

    def blank(self):
        spec = self.pf.spec("blank_para")
        return self.para(spec, '<hp:run charPrIDRef="%s"/>' % spec["char"])

    # ── 표 ──────────────────────────────────────────────────────────────
    def _border(self, row, col, ncols):
        bf = self.pf.get("table", "borderFills")
        if row == 0:
            base = str(self.pf.get("table", "borderFills", "header_gray_top04"))
            left = bf.get("header_gray_left_open") or bf.get("header_left_open") or base
            right = bf.get("header_gray_right_open") or bf.get("header_right_open") or base
        else:
            base = str(self.pf.get("table", "borderFills", "inner_012"))
            left = self.pf.get("table", "borderFills", "left_open") or base
            right = self.pf.get("table", "borderFills", "right_open") or base
        if ncols == 1:
            return self._both_open(base)
        if col == 0:
            return str(left)
        if col == ncols - 1:
            return str(right)
        return base

    def _both_open(self, base):
        """1열 표 셀: 양식에 좌우가 모두 열린 borderFill이 없어 base의 좌·우 선만 NONE으로 바꾼 것을
        찾거나 header.xml에 추가한다(Task G 분석 9-4)."""
        base = str(base)
        if base in self.added_border_fills:
            return self.added_border_fills[base]
        if self.header is None:
            raise ValueError("1열 표의 좌우 개방 borderFill을 만들 header 편집기가 없다")
        xml_text = self.header.item_xml("borderFill", base)
        xml_text = re.sub(r'(<hh:leftBorder\b[^>]*?\btype=")[A-Z_]+(")', r"\g<1>NONE\g<2>", xml_text, count=1)
        xml_text = re.sub(r'(<hh:rightBorder\b[^>]*?\btype=")[A-Z_]+(")', r"\g<1>NONE\g<2>", xml_text, count=1)
        found = self.header.find_same("borderFill", xml_text) or self.header.add("borderFill", xml_text)
        self.added_border_fills[base] = found
        return found

    def cell(self, text, row, col, width, ncols, header):
        if header:
            para_pr = str(self.pf.get("table", "cell_paraPr", "header_center"))
        elif table_layout.is_number_cell(text):
            para_pr = str(self.pf.get("table", "cell_paraPr", "number_right"))
        else:
            para_pr = str(self.pf.get("table", "cell_paraPr", "text_left"))
        char_pr = str(self.pf.get("table", "cell_charPr", "normal10"))
        bold_pr = str(self.pf.get("table", "cell_charPr", "bold10"))
        lines = table_layout.cell_lines(text, header=header)
        paras = []
        for line in lines:
            m = re.match(r"^\*\*(.+)\*\*$", line.strip())
            cp = bold_pr if m else char_pr
            body = m.group(1) if m else line
            run = self.marker_aware_runs(body, cp) if body else '<hp:run charPrIDRef="%s"/>' % cp
            # 셀 문단에는 linesegarray를 두지 않는다 — 한글이 재조판한다(hwpx-output-verification 규칙)
            paras.append('<hp:p id="%d" paraPrIDRef="%s" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">%s</hp:p>'
                         % (self.ids.next(), para_pr, run))
        height = len(lines) * 1300 + int(self.pad["top"]) + int(self.pad["bottom"])
        header_attr = "1" if header else "0"
        return ('<hp:tc name="" header="%s" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="%s">'
                '<hp:subList id="" textDirection="%s" lineWrap="%s" vertAlign="%s" linkListIDRef="0" '
                'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">%s</hp:subList>'
                '<hp:cellAddr colAddr="%d" rowAddr="%d"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                '<hp:cellSz width="%d" height="%d"/><hp:cellMargin left="%s" right="%s" top="%s" bottom="%s"/></hp:tc>'
                % (header_attr, self._border(row, col, ncols), self.sublist["textDirection"],
                   self.sublist["lineWrap"], self.sublist["vertAlign"], "".join(paras), col, row, width, height,
                   self.pad["left"], self.pad["right"], self.pad["top"], self.pad["bottom"]))

    def column_widths(self, header, rows):
        return table_layout.design_column_widths(header, rows, self.total_width, size_pt=10.0, pad=self.hpad)

    def table_xml(self, header, rows):
        ncols = len(header)
        norm_rows = [list(r) + [""] * (ncols - len(r)) for r in rows]
        if any(len(r) > ncols for r in rows):
            raise ValueError("표 본문 행의 열 수가 머리행보다 많다: %r" % header)
        widths = self.column_widths(header, norm_rows)
        trs = []
        for r_idx, data_row in enumerate([header] + norm_rows):
            cells = [self.cell(v, r_idx, c, widths[c], ncols, r_idx == 0) for c, v in enumerate(data_row)]
            trs.append("<hp:tr>%s</hp:tr>" % "".join(cells))
        attrs = self.pf.get("table", "tbl_attrs")
        pos = attrs["pos"]
        out_m, in_m = attrs["outMargin"], attrs["inMargin"]
        nrows = len(trs)
        # 쪽 나눔 3단계(hwpx-table-layout 규칙): 한 쪽에 들어갈 표는 NONE(통째). 추정 높이가 본문 가용
        # 높이를 넘는 표만 행 경계 나눔 TABLE + 머리행 반복(머리행 셀 header="1"은 cell()이 이미 준다).
        # 'CELL'은 절대 쓰지 않는다. 추정은 참고값이므로 재조판 PDF로 확인한다(2026-10-08 <표 3-2>·<표 4-3> 잘림).
        # line_height 1500: 2026-10-08 스모크4 재조판 PDF 실측(표 20개, 실측/추정 0.79~0.94, 1700 기준)으로 보정.
        page_break = "NONE"
        est = table_layout.estimate_table_height(header, norm_rows, widths, size_pt=10.0, pad=self.hpad,
                                                 line_height=1500, vpad=self.vpad)
        # 행 경계 나눔 표는 글자처럼 취급(treatAsChar=1)이면 한글이 실제로 나누지 않고 쪽 아래로 잘라 낸다
        # (2026-10-08 스모크5 <표 4-3>). 규칙대로 그 표만 treatAsChar=0(단 너비 기준 COLUMN)으로 전환한다 —
        # 옛 hwpx 부록 설문표(treatAsChar=0, horzRelTo=COLUMN)가 쪽을 넘어 정상 분할된 것을 따른다.
        treat_as_char, horz_rel_to = pos["treatAsChar"], pos["horzRelTo"]
        z_order = 0
        if self.avail_height and est > self.avail_height:
            page_break = "TABLE"
            treat_as_char, horz_rel_to = "0", "COLUMN"
            self._z_order += 1
            z_order = self._z_order
            self.split_tables.append((est, self.avail_height))
        tbl = ('<hp:tbl id="%d" zOrder="%d" numberingType="%s" textWrap="%s" textFlow="%s" lock="%s" '
               'dropcapstyle="%s" pageBreak="%s" repeatHeader="1" rowCnt="%d" colCnt="%d" cellSpacing="%s" '
               'borderFillIDRef="%s" noAdjust="%s">'
               '<hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" heightRelTo="ABSOLUTE" protect="0"/>'
               '<hp:pos treatAsChar="%s" affectLSpacing="0" flowWithText="%s" allowOverlap="0" holdAnchorAndSO="0" '
               'vertRelTo="%s" horzRelTo="%s" vertAlign="TOP" horzAlign="%s" vertOffset="0" horzOffset="0"/>'
               '<hp:outMargin left="%s" right="%s" top="%s" bottom="%s"/>'
               '<hp:inMargin left="%s" right="%s" top="%s" bottom="%s"/>%s</hp:tbl>'
               % (self.ids.next(), z_order, attrs["numberingType"], attrs["textWrap"], attrs["textFlow"], attrs["lock"],
                  attrs["dropcapstyle"], page_break, nrows, ncols, attrs["cellSpacing"], attrs["borderFillIDRef"],
                  attrs["noAdjust"], self.total_width, nrows * 1582,
                  treat_as_char, pos["flowWithText"], pos["vertRelTo"], horz_rel_to,
                  pos.get("horzAlign", "LEFT"),
                  out_m["left"], out_m["right"], out_m["top"], out_m["bottom"],
                  in_m["left"], in_m["right"], in_m["top"], in_m["bottom"], "".join(trs)))
        anchor = self.anchor_spec("table")
        return self.para(anchor, '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (anchor["char"], tbl)), widths

    def anchor_spec(self, kind):
        """표·그림을 담는 문단 서식 — table.anchor_para, 없으면 figure.anchor_para."""
        if kind == "table" and self.pf.has("table", "anchor_para"):
            a = self.pf.get("table", "anchor_para")
        else:
            a = self.pf.get("figure", "anchor_para")
        para = a.get("paraPrIDRef", a.get("paraPr"))
        char = a.get("charPrIDRef", a.get("charPr"))
        if para is None or char is None:
            raise ProfileError("프로파일 %s.anchor_para에 paraPr(IDRef)·charPr(IDRef)가 없다" % kind)
        # anchor_para에 styleIDRef가 없으면 바탕글(0) — 양식 표·그림 문단은 모두 style 0(실측)
        return {"style": str(a.get("styleIDRef", "0")), "para": str(para), "char": str(char)}

    # ── 그림 ────────────────────────────────────────────────────────────
    def picture_para(self, item_id, px_w, px_h, max_width, dpi=300, name=""):
        nat_w = int(round(px_w * 7200.0 / dpi))
        nat_h = int(round(px_h * 7200.0 / dpi))
        if nat_w > max_width:
            w = int(max_width)
            h = int(round(nat_h * float(max_width) / nat_w))
        else:
            w, h = nat_w, nat_h
        dim_w, dim_h = px_w * 75, px_h * 75  # 양식 실측: imgDim = 픽셀 × 75 (96dpi 기준 HWPUNIT)
        pid = self.ids.next()
        pa = self.pf.get("figure", "pic_attrs")
        pic = ('<hp:pic id="%d" zOrder="0" numberingType="%s" textWrap="%s" textFlow="BOTH_SIDES" '
               'lock="0" dropcapstyle="None" href="" groupLevel="0" instid="%d" reverse="0">'
               '<hp:offset x="0" y="0"/><hp:orgSz width="%d" height="%d"/><hp:curSz width="0" height="0"/>'
               '<hp:flip horizontal="0" vertical="0"/>'
               '<hp:rotationInfo angle="0" centerX="%d" centerY="%d" rotateimage="1"/>'
               '<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
               '<hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
               '<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
               '<hc:img binaryItemIDRef="%s" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
               '<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="%d" y="0"/><hc:pt2 x="%d" y="%d"/><hc:pt3 x="0" y="%d"/></hp:imgRect>'
               '<hp:imgClip left="0" right="%d" top="0" bottom="%d"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>'
               '<hp:imgDim dimwidth="%d" dimheight="%d"/><hp:effects/>'
               '<hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" heightRelTo="ABSOLUTE" protect="0"/>'
               '<hp:pos treatAsChar="%s" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
               'vertRelTo="PARA" horzRelTo="%s" vertAlign="TOP" horzAlign="%s" vertOffset="0" horzOffset="0"/>'
               '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
               '<hp:shapeComment>그림입니다.\n원본 그림의 이름: %s\n원본 그림의 크기: 가로 %dpixel, 세로 %dpixel</hp:shapeComment>'
               '</hp:pic>'
               % (pid, pa["numberingType"], pa["textWrap"], pid, w, h, w // 2, h // 2, item_id, w, w, h, h,
                  dim_w, dim_h, dim_w, dim_h, w, h, pa["treatAsChar"], pa["horzRelTo"], pa["horzAlign"],
                  esc(name), px_w, px_h))
        anchor = self.anchor_spec("figure")
        return self.para(anchor, '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (anchor["char"], pic)), (w, h)


class KjnDocument(object):
    """김정년 양식 프로파일 기반 학위논문 조립."""

    def __init__(self, template, profile, images=None, toc_pages=None):
        self.tpl = template
        self.pf = profile
        self.ids = IdGen()
        self.asm = KjnAssembler(profile, self.ids, template.red_char_pr_id, header=template.header)
        self.asm.avail_height = body_avail_height(template.s2)
        self.images = images or {}
        self.toc_pages = toc_pages or {}
        self.body = []
        self.last_blank = False
        self.toc = []
        self.lot = []
        self.lof = []
        self.notes = []
        self.bin_items = []        # (item_id, href, bytes)
        self.table_widths = []     # (캡션, 열폭 배열) — 보고·검증용
        self.blank_after = self._blank_after()
        self._first_section_pending = True
        # 장 안 첫 절 예외는 h2_section.pageBreak_rule("장 안 첫 절(장 제목 다음)=0, 나머지 절=1")을 따른다.
        rule = str(profile.get("h2_section").get("pageBreak_rule", ""))
        self._first_section_exempt = ("첫 절" in rule) or not rule
        self.body_indent = self._body_indent()

    def _body_indent(self):
        """본문 첫줄 들여쓰기 문자열 — 양식은 문단 속성이 아니라 실제 공백 두 칸(H4 결정)."""
        conv = self.pf.get("conventions")
        for key in ("body_indent", "first_line_indent"):
            if key in conv:
                return str(conv[key])
        if "first_line_two_spaces" in conv:
            return "  "
        raise ProfileError("프로파일 conventions에 body_indent·first_line_indent·first_line_two_spaces가 모두 없다")

    def _blank_after(self):
        """제목 뒤 빈 문단 리듬. bool·목록(["h1",…])·서술 문자열("장·절·항 제목 직후 빈 문단 1개…") 허용."""
        v = self.pf.get("conventions", "blank_after_heading")
        if isinstance(v, bool):
            return {"h1", "h2", "h3"} if v else set()
        if isinstance(v, str):
            head = re.split(r"[.(（]", v, 1)[0]
            out = {key for key, word in (("h1", "장"), ("h2", "절"), ("h3", "항")) if word in head}
            if not out:
                raise ProfileError("conventions.blank_after_heading 서술에서 장·절·항을 읽지 못했다: %r" % v)
            return out
        return set(v)

    # 본문 문단 추가
    def _add(self, xml_text, blank=False):
        self.body.append(xml_text)
        self.last_blank = blank

    def _blank(self):
        self._add(self.asm.blank(), blank=True)

    def _blank_once(self):
        if not self.last_blank:
            self._blank()

    def spec(self, key):
        return self.pf.spec(key)

    # ── 블록 ─────────────────────────────────────────────────────────────
    def add_blocks(self, blocks, first_paragraph=False, appendix=False, transplants_after=None,
                   survey_cover=False, replace=None):
        """replace={"keep_until": 제목 접두사|None, "paras": [이식 문단 XML]} — 그 제목(없으면 첫 h1)까지만
        블록으로 조립하고 이식 문단을 넣은 뒤 나머지 블록은 목차 항목만 남긴다(부록1 설문지 통째 이식)."""
        transplants_after = transplants_after or {}
        items = group_figures(blocks)
        bold_char = str(self.pf.get("body_bold_charPr"))
        skipping = False
        toc_from_transplant = False
        for i, b in enumerate(items):
            kind = b["type"]
            nxt = items[i + 1] if i + 1 < len(items) else None
            if skipping:
                if not toc_from_transplant:
                    self._toc_only(b, appendix)
                continue
            if (replace is not None and replace.get("drop_heading") and kind in ("h1", "h2", "h3")
                    and replace.get("keep_until") is not None
                    and _norm(b["text"]).startswith(_norm(replace["keep_until"]))):
                # 포장 제목(예: '부 록 — 설문지')은 본문·목차 어디에도 내지 않고, 그 자리에 옛 hwpx의
                # 제목 문단부터 통째로 이식한다(옛 제목이 pageBreak=1을 갖고 있어 새 쪽에서 시작).
                # 목차는 MD 블록이 아니라 실제로 실리는 이식 문단의 제목(부 록 (…)=1수준, Part X.=2수준)으로 만든다.
                # MD의 묶음 제목('공통부 — …' 등)은 본문에 없으므로 목차에도 넣지 않는다(2026-10-08 스모크7).
                n_toc = 0
                for x in replace["paras"]:
                    self._add(x)
                    t = re.sub(r"\s+", " ", plain_texts(x)).strip()
                    if re.match(r"^부 ?록 ?\(", t):
                        self.toc.append((1, t.replace("부록", "부 록")))
                        n_toc += 1
                    elif re.match(r"^Part [A-Z]\.", t):
                        self.toc.append((2, t))
                        n_toc += 1
                self.last_blank = False
                self.notes.append("'%s' 제목을 생략하고 그 자리에 이식 문단 %d개를 넣었다(목차 항목 %d개는 이식 문단 제목 기준)."
                                  % (b["text"], len(replace["paras"]), n_toc))
                skipping = True
                toc_from_transplant = True
                continue
            if kind == "h1":
                text = normalize_heading_number(b["text"])
                if appendix:
                    if b["text"].replace(" ", "").startswith("부록"):
                        self.toc.append((1, text))
                        self._add(self.asm.text_para(self.spec("appendix_heading"), text, page_break=True))
                        if "h1" in self.blank_after:
                            self._blank()
                        if survey_cover:
                            self.add_survey_cover()
                            survey_cover = False
                    else:
                        # 부록 안의 하위 묶음 제목(공통부·전용부)은 절 제목 서식으로 둔다
                        self.toc.append((2, text))
                        self._blank_once()
                        self._add(self.asm.text_para(self.spec("h2_section"), text))
                        if "h2" in self.blank_after:
                            self._blank()
                else:
                    self.toc.append((1, text))
                    self._first_section_pending = True
                    if first_paragraph:
                        self._add(self._first_paragraph(text))
                        first_paragraph = False
                    else:
                        self._add(self.asm.text_para(self.spec("h1_chapter"), text, page_break=True))
                    if "h1" in self.blank_after:
                        self._blank()
                for key, xml_list in transplants_after.items():
                    if b["text"].strip().startswith(key):
                        for x in xml_list:
                            self._add(x)
                        self._blank_once()
            elif kind in ("h2", "h3"):
                text = normalize_heading_number(b["text"])
                key = "h2_section" if kind == "h2" else "h3_item"
                self.toc.append((2 if kind == "h2" else 3, text))
                # 프로파일 pageBreak="1"이면 새 쪽 시작(장 안 첫 절은 장 제목과 같은 쪽 — pageBreak_rule).
                # 새 쪽에서 시작하는 제목은 장 제목처럼 앞 빈 줄을 두지 않는다.
                # 이 규칙은 본문 장에서 실측한 것이므로 부록(짧은 절이 이어짐)에는 적용하지 않는다.
                page_break = (not appendix and str(self.pf.get(key).get("pageBreak", "0")) == "1"
                              and not (kind == "h2" and self._first_section_pending and self._first_section_exempt))
                if kind == "h2":
                    self._first_section_pending = False
                if not page_break:
                    self._blank_once()  # 절·항 제목 앞 빈 줄 1개(이미 있으면 추가하지 않는다)
                self._add(self.asm.text_para(self.spec(key), text, page_break=page_break))
                if kind in self.blank_after:
                    self._blank()
                for key, xml_list in transplants_after.items():
                    if b["text"].strip().startswith(key):
                        for x in xml_list:
                            self._add(x)
                        self._blank_once()
            elif kind == "h4":
                self._blank_once()
                self._add(self.asm.text_para(self.spec("h4_sub"), b["text"]))
            elif kind == "p":
                text = runs_text(b)
                if is_source_note(b):
                    self._add(self.asm.text_para(self.spec("source_note"), text.strip()))
                    if not (nxt is not None and is_source_note(nxt)):
                        self._blank()
                elif image_md(b):
                    alt, path = image_md(b)
                    self._figure({"caption": None, "image_md": (alt, path), "notes": []})
                else:
                    runs = b.get("runs", [])
                    prefix = "" if (runs and runs[0].get("text", "")[:1].isspace()) else self.body_indent
                    spec = self.spec("body")
                    if nxt is not None and nxt["type"] == "table":
                        spec = self.asm.keep_with_next_spec(spec)  # 표 바로 앞 문장은 표와 같은 쪽에
                    self._add(self.asm.runs_para(spec, runs, bold_char, prefix=prefix))
            elif kind == "table_caption":
                if CAPTION_RE.match(b["text"]):
                    self.lot.append(b["text"])
                    self._add(self.asm.text_para(self.spec("table_caption"), b["text"]))
                else:
                    # md_to_blocks가 "<표 n-m>에서 …"로 시작하는 본문 문단을 캡션으로 분류한 경우
                    self.notes.append("캡션 형식이 아닌 table_caption을 본문 문단으로 넣었다: %s" % b["text"][:40])
                    self._add(self.asm.text_para(self.spec("body"), self.body_indent + b["text"]))
            elif kind == "table":
                xml_text, widths = self.asm.table_xml(b["header"], b["rows"])
                self.table_widths.append((self.lot[-1] if self.lot else "", widths))
                self._add(xml_text)
                if not (nxt is not None and is_source_note(nxt)):
                    self._blank()
            elif kind == "_figure":
                self._figure(b)
            elif kind == "figure_placeholder":
                self._add(self.asm.text_para(self.asm.anchor_spec("figure"), b["text"]))
            elif kind == "figure_caption":  # group_figures가 모두 바꾸므로 도달하지 않는다
                raise ValueError("묶이지 않은 figure_caption")
            else:
                raise ValueError("알 수 없는 블록 타입: %r" % kind)
            if replace is not None and kind in ("h1", "h2", "h3"):
                until = replace.get("keep_until")
                if until is None or _norm(b["text"]).startswith(_norm(until)):
                    self._blank_once()
                    for x in replace["paras"]:
                        self._add(x)
                    self.last_blank = False
                    self.notes.append("'%s' 뒤 블록을 이식 문단 %d개로 대체했다(목차 항목은 블록 기준 유지)."
                                      % (b["text"], len(replace["paras"])))
                    skipping = True
        if replace is not None and not skipping:
            raise ValueError("이식 대체 기준 제목 '%s'를 블록에서 찾지 못했다" % replace.get("keep_until"))
        self._blank_once()
        return first_paragraph

    def _toc_only(self, b, appendix):
        """이식으로 대체된 블록의 제목은 목차에만 남긴다(본문 조립과 같은 수준 규칙)."""
        kind = b["type"]
        if kind == "h1":
            text = normalize_heading_number(b["text"])
            top = not appendix or b["text"].replace(" ", "").startswith("부록")
            self.toc.append((1 if top else 2, text))
        elif kind in ("h2", "h3"):
            level = 2 if kind == "h2" else 3
            if appendix and kind == "h2" and b["text"].replace(" ", "").startswith("부록"):
                level = 1  # 포장 제목을 생략했을 때 '부 록 (도입 현장)'류는 최상위 목차 항목
            self.toc.append((level, normalize_heading_number(b["text"])))
        elif kind == "table_caption" and CAPTION_RE.match(b["text"]):
            self.lot.append(b["text"])
        elif kind == "_figure" and b.get("caption"):
            self.lof.append(b["caption"])

    def _first_paragraph(self, title):
        """section2 첫 문단 — 양식의 colPr·secPr·쪽번호 제어 블록을 그대로 이식한다."""
        h1 = self.spec("h1_chapter")
        runs = ('<hp:run charPrIDRef="%s">%s</hp:run>'
                '<hp:run charPrIDRef="%s">%s<hp:t>%s</hp:t>%s<hp:t/></hp:run>'
                % (h1["char"], self.tpl.sec2_secpr, h1["char"], self.tpl.sec2_pagectrl,
                   esc(title), self.tpl.sec2_newnum))
        # 본문 첫 장 제목은 구역 첫 문단이므로 pageBreak를 주지 않는다(구역 시작이 이미 새 쪽)
        return self.asm.para(h1, runs)

    def _image_for(self, caption, md_path):
        for key, path in self.images.items():
            if caption and (caption.startswith(key) or key in caption):
                return path
            if md_path and (key == md_path or md_path.endswith(key)):
                return path
        return None

    def _figure(self, fig):
        caption = fig.get("caption")
        md_path = fig["image_md"][1] if fig.get("image_md") else None
        if caption:
            self.lof.append(caption)
            self._add(self.asm.text_para(self.spec("figure_caption"), caption))
        src = self._image_for(caption, md_path)
        if src:
            with open(src, "rb") as f:
                data = f.read()
            px_w, px_h = png_size(data)
            item_id = self._next_bin_id()
            self.bin_items.append((item_id, "BinData/%s.png" % item_id, data))
            max_w = int(self.pf.first(("figure", "max_width"), ("figure", "pic_attrs", "sz_width"),
                                      ("table", "total_width")))
            xml_text, _size = self.asm.picture_para(item_id, px_w, px_h, max_w, name=os.path.basename(src))
            self._add(xml_text)
        else:
            label = caption or (fig["image_md"][0] if fig.get("image_md") else "그림")
            self.notes.append("그림 이미지 매핑 없음 — 빨간 자리표시로 넣었다: %s" % label)
            self._add(self.asm.text_para(self.asm.anchor_spec("figure"), "[그림 삽입 예정: %s]" % label))
        notes = fig.get("notes") or []
        if not any(runs_text(n).strip().startswith("자료") for n in notes):
            self._add(self.asm.text_para(self.spec("source_note"), DEFAULT_FIGURE_SOURCE))
        for n in notes:
            self._add(self.asm.text_para(self.spec("source_note"), runs_text(n).strip()))
        self._blank()

    def _next_bin_id(self):
        used = set(re.findall(r'<opf:item id="(image\d+)"', self.tpl.hpf)) | {i for i, _h, _d in self.bin_items}
        n = 1
        while "image%d" % n in used:
            n += 1
        return "image%d" % n

    # ── 참고문헌 ─────────────────────────────────────────────────────────
    def add_references(self, refs):
        title = "참고문헌"
        self.toc.append((1, title))
        self._add(self.asm.text_para(self.spec("ref_heading"), title, page_break=True))
        self._blank()
        cats = refs.get("categories")
        if not isinstance(cats, dict):
            raise ValueError("references JSON에 categories 객체가 없다")
        cats = {k: list(v) for k, v in cats.items()}
        unplaced = []
        for item in refs.get("flagged", []) or []:
            entry = dict(item)
            entry["_flag"] = True
            if entry.get("category") in cats:
                cats[entry["category"]].append(entry)
            else:
                unplaced.append(entry)
        if unplaced:
            cats["[확정 필요: 분류 미정 서지]"] = unplaced
        first = True
        for category, items in cats.items():
            if not first:
                self._blank()
            first = False
            self._add(self.asm.text_para(self.spec("ref_category"), category))
            for n, item in enumerate(items, 1):
                text = item["text"]
                flag = item.get("_flag") or item.get("flagged")
                if flag and "[확정 필요" not in text:
                    reason = item.get("reason") or item.get("confirm") or "서지 확인"
                    text = "%s [확정 필요: %s]" % (text, reason)
                self._add(self.asm.text_para(self.spec("ref_item"), "[%02d] %s" % (n, text)))
            if not items:
                self.notes.append("참고문헌 분류 '%s'에 항목이 없어 제목만 생성했다." % category)
        self._blank()

    def add_survey_cover(self, transplant_xml=None):
        if transplant_xml:
            for x in transplant_xml:
                self._add(x)
            self._blank_once()
            return
        meta = self.spec("abstract_meta")
        for line in SURVEY_COVER_TITLE:
            self._add(self.asm.text_para(meta, line))
        self._blank()
        self._add(self.asm.text_para(self.spec("appendix_heading"), SURVEY_COVER_LABEL))
        self._blank()

    def add_placeholder_appendix(self, title):
        self.toc.append((1, title))
        self._add(self.asm.text_para(self.spec("appendix_heading"), title, page_break=True))
        self._blank()
        self._add(self.asm.text_para(self.spec("body"), self.body_indent + "[내용 확정 후 작성]"))
        self._blank()

    def add_abstract_en(self):
        self.toc.append((1, "Abstract"))
        self._add(self.asm.text_para(self.spec("abstract_heading"), "Abstract", page_break=True))
        self._blank()
        meta = self.spec("abstract_meta")
        for line in ("Master's Thesis", "[확정 필요: 영문 논문 제목]", "[확정 필요: 영문 부제]"):
            self._add(self.asm.text_para(meta, line))
        self._blank()
        for line in ("[확정 필요: 연구자 영문 성명]", "Dept. of Architecture & Safety Engineering",
                     "Graduate School of Engineering", "Kyonggi University"):
            self._add(self.asm.text_para(meta, line))
        self._blank()
        self._add(self.asm.text_para(self.spec("abstract_body"), self.body_indent + "[확정 필요: 영문초록 작성]"))

    # ── 목차 ─────────────────────────────────────────────────────────────
    def _toc_tab(self, key):
        return self.pf.first((key, "tab"), (key, "inline_tab"), ("toc_entry", "tab"), ("toc_entry", "inline_tab"),
                             ("conventions", "toc_tab"))

    def _page_of(self, kind, text):
        table = self.toc_pages.get(kind, {}) if isinstance(self.toc_pages, dict) else {}
        if text in table:
            v = table[text]
            if isinstance(v, list):  # 같은 제목이 두 번(부록 두 양식의 Part A·B·C) — 문서 순서대로 소비
                v = v.pop(0) if v else "0"
            return str(v)
        m = re.match(r"^(<(?:표|그림)\s*\d+-\d+>)", text)
        if m and m.group(1) in table:
            return str(table[m.group(1)])
        return "0"

    def toc_line(self, key, text, page, indent=""):
        spec = self.spec(key)
        tab = self._toc_tab(key)
        page_cfg = self.pf.get("page")
        width = int(page_cfg["width"]) - int(self.pf.get("page", "margins", "section1_front", "left")) \
            - int(self.pf.get("page", "margins", "section1_front", "right"))
        used = table_layout.text_width(indent + text, 11.0) + table_layout.text_width(page, 11.0)
        tab_w = max(width - used, 0)
        body = ('%s<hp:tab width="%d" leader="%s" type="%s"/>%s'
                % (esc(indent + text), tab_w, tab["leader"], tab["type"], esc(page)))
        return self.asm.para(spec, '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>' % (spec["char"], body))

    # ── 섹션 조립 ────────────────────────────────────────────────────────
    def _front_box(self, name):
        start, _end = range_bounds(self.pf.get("front_ranges", name), "front_ranges." + name)
        box = self.tpl.s1_para(start)
        title = self.pf.get("front_heading_box", "titles", name)
        if title not in plain_texts(box):
            raise ValueError("front_ranges.%s 첫 문단(s1:%d)이 제목 상자 '%s'가 아니다" % (name, start, title))
        if "<hp:tbl" not in box:
            raise ValueError("front_ranges.%s 첫 문단(s1:%d)에 제목 상자 표가 없다" % (name, start))
        return strip_cell_page_break(box)

    def build_section1(self, thanks_xml=None, abstract_kr=None):
        ranges = {k: range_bounds(v, "front_ranges." + k) for k, v in self.pf.get("front_ranges").items()
                  if not k.startswith("_")}
        for need in ("목차", "표목차", "그림목차", "감사의글", "논문개요"):
            if need not in ranges:
                raise ProfileError("프로파일 front_ranges에 '%s'가 없다" % need)
        first_idx = ranges["목차"][0]
        last_idx = max(e for _s, e in ranges.values())
        if last_idx != len(self.tpl.s1_paras) - 1:
            raise ValueError("front_ranges 끝(%d)이 양식 section1 마지막 문단(%d)과 다르다"
                             % (last_idx, len(self.tpl.s1_paras) - 1))
        tail = self.tpl.s1[self.tpl.s1_paras[-1][1]:]
        if tail.strip() != "</hs:sec>":
            raise ValueError("양식 section1 말미가 예상과 다르다: %r" % tail[:80])
        toc_box = self._front_box("목차")
        loc = str(self.pf.get("page", "page_numbering", "section1").get("newNum_location", ""))
        if "제목 상자" in loc and "<hp:newNum" not in toc_box:
            raise ValueError("프로파일은 section1 newNum이 목차 제목 상자 안에 있다고 하나 상자에 newNum이 없다")
        parts = [self.tpl.s1[: self.tpl.s1_paras[first_idx][0]], toc_box, self.asm.blank()]
        for label in FRONT_TOC_LABELS:
            parts.append(self.toc_line("toc_entry", label, self._page_of("toc", label)))
        parts.append(self.asm.blank())
        prev_level = None
        for level, title in self.toc:
            if level == 1 and prev_level is not None:
                parts.append(self.asm.blank())
            parts.append(self.toc_line("toc_entry", title, self._page_of("toc", title), indent=" " * (level - 1)))
            prev_level = level
        parts.append(self._front_box("표목차"))
        parts.append(self.asm.blank())
        for text in self.lot:
            parts.append(self.toc_line("toc_lot_entry", text, self._page_of("lot", text)))
        parts.append(self._front_box("그림목차"))
        parts.append(self.asm.blank())
        for text in self.lof:
            parts.append(self.toc_line("toc_lot_entry", text, self._page_of("lof", text)))
        thanks_has_box = bool(thanks_xml) and "<hp:tbl" in thanks_xml[0] \
            and "감사의" in plain_texts(thanks_xml[0]).replace(" ", "")
        if thanks_has_box:
            # 이식 범위가 옛 "감사의 글" 제목 상자부터 시작하면 양식 상자를 겹쳐 넣지 않는다
            self.notes.append("감사의 글: 이식 범위의 옛 제목 상자를 쓰고 양식 제목 상자는 넣지 않았다.")
        else:
            parts.append(self._front_box("감사의글"))
        if thanks_xml:
            parts.extend(thanks_xml)
        else:
            self.notes.append("감사의 글 이식(--transplant 감사의글)이 없어 빨간 자리표시를 넣었다.")
            parts.append(self.asm.text_para(self.spec("abstract_body"), self.body_indent
                                            + "[확정 필요: 감사의 글 — 옛 hwpx에서 이식]"))
        parts.append(self._front_box("논문개요"))
        parts.append(self.asm.blank())
        for text in abstract_kr or ["[확정 필요: 논문개요 작성]"]:
            parts.append(self.asm.text_para(self.spec("abstract_body"), self.body_indent + text))
        parts.append("</hs:sec>")
        return "".join(parts)

    def build_section2(self):
        return self.tpl.s2_head + "".join(self.body) + "</hs:sec>"

    def build_section0(self):
        return replace_cover(self.tpl.s0, self.pf.get("cover"), self.asm)


# ── 표지(section0) 치환 ───────────────────────────────────────────────────────
def _cover_new_text(role, current):
    canon = COVER_ROLE_ALIASES.get(role)
    if canon is None:
        raise ProfileError("표지 슬롯 role '%s'를 알 수 없다(허용: %s)"
                           % (role, ", ".join(sorted(set(COVER_ROLE_ALIASES)))))
    if canon == "keep":
        return None
    if canon == "committee":
        # 심사위원 서명란은 비운다 — 공백 자리는 그대로, 글자가 있으면 같은 길이의 공백으로
        return None if not current.strip() else " " * len(current)
    if canon == "subtitle":
        sub = COVER_TEXT["subtitle"]
        return "— %s —" % sub if current.strip().startswith("—") else sub
    if canon == "advisor":
        m = re.match(r"^(\s*지도교수\s*[:：]?\s*)", current)
        return (m.group(1) if m else "") + COVER_TEXT["advisor"]
    if canon == "date":
        if re.fullmatch(r"\s*\d{4}\s*", current):
            return None  # "2026학년도"의 연도 조각 — 학년도는 확정값이므로 유지
        if re.search(r"\d+\s*월", current):
            return re.sub(r"\d+\s*월", "[확정 필요: 월]", current, count=1)
        return "2026년 [확정 필요: 월]"
    if canon == "author" and "인준" in current:
        canon = "approval"
    if canon == "approval":
        return re.sub(r"^.*?(의\s*석사학위논문을\s*인준함.*)$", COVER_TEXT["author"] + r"\1", current) \
            if "인준" in current else COVER_TEXT["author"] + "의 석사학위논문을 인준함"
    return COVER_TEXT[canon]


def _slot_t_index(path):
    if isinstance(path, int):
        return path
    if isinstance(path, str):
        m = re.search(r"(?:t_index[:=]|t\[|hp:t\[)(\d+)", path)
        if m:
            return int(m.group(1))
    return None


def replace_cover(s0, cover_cfg, asm):
    """cover.section0 슬롯 텍스트를 role별 새 텍스트로 바꾼다. 빨간 마커는 run을 나눠 빨강 charPr로."""
    entries = cover_cfg.get("section0") if isinstance(cover_cfg, dict) else None
    if entries is None:
        raise ProfileError("프로파일 cover.section0이 없다")
    spans = split_paragraphs(s0)
    # 같은 문단(겉표지·제출지가 한 문단 안 표 2개)의 슬롯은 문서 순서대로 한 커서로 찾는다.
    by_para = {}
    for entry in entries:
        p_idx = int(entry["para_idx"])
        if p_idx >= len(spans):
            raise ValueError("cover para_idx %d가 section0 문단 수(%d)를 넘는다" % (p_idx, len(spans)))
        for slot in entry.get("slots", []):
            by_para.setdefault(p_idx, []).append((slot, entry.get("role"), entry.get("tbl_idx")))
    new_paras = {}
    for p_idx, slots in by_para.items():
        a, b = spans[p_idx]
        para = s0[a:b]
        t_iter = list(re.finditer(r"<hp:t>(.*?)</hp:t>", para, re.S))
        tables = _top_table_spans(para)
        # hp:t 안에 <hp:lineBreak/> 등 자식이 있으면(겉표지 제목 두 줄) 태그를 걷어낸 텍스트로 비교한다.
        # 프로파일 current_text가 첫 줄만 적었어도 hp:t 전체(둘째 줄 포함)를 바꾼다.
        plain = [re.sub(r"<[^>]+>", "\n", t.group(1)) for t in t_iter]

        def same(k, current):
            text = plain[k]
            return text == esc(current) or (text.split("\n")[0] == esc(current) and "\n" in text)
        edits = []
        cursor = 0
        for slot, entry_role, tbl_idx in slots:
            role = slot.get("role") or entry_role
            lo, hi = 0, len(para)
            if tbl_idx is not None:
                if int(tbl_idx) >= len(tables):
                    raise ValueError("cover tbl_idx %s가 section0 p%d의 표 수(%d)를 넘는다" % (tbl_idx, p_idx, len(tables)))
                lo, hi = tables[int(tbl_idx)]
                cursor = max(cursor, next((k for k, t in enumerate(t_iter) if t.start() >= lo), len(t_iter)))
            current = slot.get("current_text", "")
            new_text = _cover_new_text(role, current)
            idx = _slot_t_index(slot.get("path"))
            match = None
            if idx is not None and idx < len(t_iter) and same(idx, current):
                match = t_iter[idx]
            else:
                for k in range(cursor, len(t_iter)):
                    if t_iter[k].start() >= hi:
                        break
                    if same(k, current):
                        match = t_iter[k]
                        cursor = k + 1
                        break
            if match is None:
                raise ValueError("표지 슬롯 '%s'(role %s)를 section0 p%d에서 찾지 못했다" % (current, role, p_idx))
            if new_text is None or (new_text == current and plain[t_iter.index(match)] == esc(current)):
                continue
            run_open = list(re.finditer(r'<hp:run charPrIDRef="(\d+)"', para[:match.start()]))
            if not run_open:
                raise ValueError("표지 슬롯 '%s'의 run charPr를 찾지 못했다" % current)
            char_pr = slot.get("charPrIDRef") or run_open[-1].group(1)
            edits.append((match.start(), match.end(), _cover_t_xml(new_text, str(char_pr), asm)))
        for start, end, repl in sorted(edits, reverse=True):
            para = para[:start] + repl + para[end:]
            para = _strip_enclosing_lineseg(para, start)
        para = _rebalance_protected_cover_rows(para)
        new_paras[p_idx] = para
    out, last = [], 0
    for p_idx, (a, b) in enumerate(spans):
        if p_idx in new_paras:
            out.append(s0[last:a])
            out.append(new_paras[p_idx])
            last = b
    out.append(s0[last:])
    return strip_cell_page_break("".join(out))


def _rebalance_protected_cover_rows(para):
    """표지 표가 protect="1"(전체 높이 고정)이면 제목·부제가 들어간 셀이 늘어나지 못해 잘린다.
    제목 셀의 필요 높이를 추정해 모자란 만큼 키우고, 가장 큰 빈 간격 행에서 같은 양을 빼 총 높이를 유지한다.
    (2026-10-08 스모크: 양식 제목 3줄 자리에 5줄이 들어가 둘째 부제 줄이 잘렸다.)"""
    m_sz = re.search(r'<hp:sz width="\d+" widthRelTo="ABSOLUTE" height="(\d+)" heightRelTo="ABSOLUTE" protect="1"/>', para)
    if not m_sz:
        return para
    rows = list(re.finditer(r"<hp:tr>.*?</hp:tr>", para, re.S))
    if not rows:
        return para
    info = []
    for r in rows:
        cs = re.search(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', r.group(0))
        texts = [re.sub(r"<[^>]+>", "", t) for t in re.findall(r"<hp:t>(.*?)</hp:t>", r.group(0), re.S)]
        heights = [int(h) for h in re.findall(r'charPrIDRef="(\d+)"', r.group(0))]
        info.append({"m": r, "h": int(cs.group(2)) if cs else 0, "texts": [t for t in texts if t.strip()]})
    # 제목 셀: 텍스트 길이가 가장 긴 행. 줄 수 추정: 22pt 제목 16자/줄(3740/줄), 18pt 부제 20자/줄(3060/줄)
    title = max(info, key=lambda x: sum(len(t) for t in x["texts"]))
    if not title["texts"]:
        return para
    parts = title["texts"]
    lines_title = max(1, -(-len(parts[0]) // 16))
    lines_sub = sum(max(1, -(-len(t) // 20)) for t in parts[1:])
    need = lines_title * 3740 + lines_sub * 3060 + 4000
    extra = need - title["h"]
    if extra <= 0:
        return para
    donors = [x for x in info if not x["texts"] and x is not title]
    if not donors:
        return para
    donor = max(donors, key=lambda x: x["h"])
    extra = min(extra, donor["h"] - 1500)
    if extra <= 0:
        return para

    def set_h(row_xml, new_h):
        return re.sub(r'(<hp:cellSz width="\d+" height=")\d+(")', lambda m: m.group(1) + str(new_h) + m.group(2), row_xml, count=1)
    t_new = set_h(title["m"].group(0), title["h"] + extra)
    d_new = set_h(donor["m"].group(0), donor["h"] - extra)
    for row, repl in sorted(((title["m"], t_new), (donor["m"], d_new)), key=lambda x: -x[0].start()):
        para = para[:row.start()] + repl + para[row.end():]
    return para


def _top_table_spans(xml_text):
    """문단 안 최상위 hp:tbl의 (시작, 끝) 오프셋 — 표지처럼 한 run에 표가 여러 개일 때 쓴다."""
    spans, depth, start = [], 0, None
    for m in re.finditer(r"<hp:tbl\b|</hp:tbl>", xml_text):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    return spans


def _cover_t_xml(text, char_pr, asm):
    """hp:t 하나를 마커 경계로 나눈다 — 마커 조각은 run을 닫고 빨간 run으로 다시 연다."""
    matches = list(GUIDE_MARKER_RE.finditer(text))
    if not matches:
        return "<hp:t>%s</hp:t>" % esc(text)
    red = asm.red_char_pr(char_pr)
    parts, cursor = [], 0
    for m in matches:
        if m.start() > cursor:
            parts.append(("n", text[cursor:m.start()]))
        parts.append(("r", m.group(0)))
        cursor = m.end()
    if cursor < len(text):
        parts.append(("n", text[cursor:]))
    xml_parts = []
    for i, (kind, chunk) in enumerate(parts):
        cp = red if kind == "r" else char_pr
        if i == 0:
            if kind == "r":
                xml_parts.append('<hp:t/></hp:run><hp:run charPrIDRef="%s"><hp:t>%s</hp:t>' % (cp, esc(chunk)))
            else:
                xml_parts.append("<hp:t>%s</hp:t>" % esc(chunk))
        else:
            xml_parts.append('</hp:run><hp:run charPrIDRef="%s"><hp:t>%s</hp:t>' % (cp, esc(chunk)))
    if parts[-1][0] == "r":
        xml_parts.append('</hp:run><hp:run charPrIDRef="%s"><hp:t/>' % char_pr)
    return "".join(xml_parts)


def _strip_enclosing_lineseg(para, pos):
    """pos를 감싸는 가장 안쪽 hp:p의 linesegarray를 지운다(내용이 바뀐 문단만 재조판)."""
    starts = [m.start() for m in re.finditer(r"<hp:p(?=[\s>])", para[:pos])]
    for s in reversed(starts):
        close = _matching_close(para, s)
        if close is not None and close > pos:
            inner = para[s:close]
            # 이 문단 직속 linesegarray만 지운다 — 중첩 표 안 문단의 것은 그대로 둔다
            depth_free = re.sub(r"<hp:tbl\b.*?</hp:tbl>", lambda m: "\x00" * len(m.group(0)), inner, flags=re.S)
            m = re.search(r"<hp:linesegarray>.*?</hp:linesegarray>", depth_free, re.S)
            if m:
                inner = inner[:m.start()] + inner[m.end():]
                para = para[:s] + inner + para[close:]
            return para
    return para


def _matching_close(xml_text, start):
    depth = 0
    for m in re.finditer(r"<hp:p(?=[\s/>])|</hp:p>", xml_text[start:]):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return start + m.end()
        else:
            depth += 1
    return None


def leftover_hits(texts, profile=None):
    """조립 결과 텍스트에서 김정년 고유 문구를 찾는다. {문구: 횟수}."""
    needles = list(KJN_FORBIDDEN)
    if profile is not None and profile.has("template_leftovers_to_strip"):
        def walk(v):
            if isinstance(v, str):
                if 2 <= len(v) <= 60 and not v.startswith("_"):
                    needles.append(v)
            elif isinstance(v, dict):
                for k, x in v.items():
                    if not k.startswith("_"):
                        walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(profile.get("template_leftovers_to_strip"))
    hits = {}
    for needle in set(needles):
        n = sum(t.count(needle) for t in texts)
        if n:
            hits[needle] = n
    return hits


# ── 패키지(manifest·BinData) ──────────────────────────────────────────────────
def update_manifest(hpf, bin_items, drop_ids):
    """content.hpf manifest에서 drop_ids 이미지 항목을 빼고 bin_items를 추가한다."""
    for item_id in drop_ids:
        hpf = re.sub(r'<opf:item id="%s"[^>]*/>' % re.escape(item_id), "", hpf)
    add = "".join('<opf:item id="%s" href="%s" media-type="image/png" isEmbeded="1"/>' % (i, h)
                  for i, h, _d in bin_items)
    if add:
        if "</opf:manifest>" not in hpf:
            raise ValueError("content.hpf에 manifest 닫는 태그가 없다")
        hpf = hpf.replace("</opf:manifest>", add + "</opf:manifest>", 1)
    return hpf


def plan_package(template, sections, header_xml, bin_items):
    """출력 패키지 엔트리 목록 [(name, data, compress_type, ZipInfo|None)].

    본문에서 참조하지 않는 양식 BinData(김정년 그림)는 manifest와 함께 뺀다.
    """
    used_text = "".join(sections.values())
    referenced = set(re.findall(r'binaryItemIDRef="([^"]+)"', used_text))
    tpl_items = dict(re.findall(r'<opf:item id="([^"]+)" href="(BinData/[^"]+)"', template.hpf))
    drop = [i for i in tpl_items if i not in referenced]
    hpf = update_manifest(template.hpf, bin_items, drop)
    drop_paths = {tpl_items[i] for i in drop}
    out = []
    replace = dict(sections)
    replace["Contents/header.xml"] = header_xml
    replace["Contents/content.hpf"] = hpf
    for name, ctype, info in template.infos:
        if name in drop_paths:
            continue
        data = replace.get(name, template.raw[name])
        if isinstance(data, str):
            data = data.encode("utf-8")
        out.append((name, data, ctype, info))
    for item_id, href, data in bin_items:
        out.append((href, data, zipfile.ZIP_STORED, None))
    return out


# ── 이식 ─────────────────────────────────────────────────────────────────────
def _wrap(xml_text):
    decl = " ".join('xmlns:%s="%s"' % (p, u) for p, u in NS.items())
    return "<wrap %s>%s</wrap>" % (decl, xml_text)


def _unwrap(elem):
    text = ET.tostring(elem, encoding="unicode")
    text = re.sub(r"^<wrap\b[^>]*>", "", text)
    return re.sub(r"</wrap>\s*$", "", text)


def _q(tag):
    p, local = tag.split(":")
    return "{%s}%s" % (NS[p], local)


def rescale_tables(xml_text, total_width):
    """최상위 표 폭을 total_width로 비례 재계산한다. 열 경계를 유지하므로 병합 격자가 보존되고,
    중첩 표는 부모 셀 폭의 변화 비율로 다시 맞춘다."""
    root = ET.fromstring(_wrap(xml_text))

    def fit(tbl, target):
        cells = []
        for tr in tbl.findall(_q("hp:tr")):
            for tc in tr.findall(_q("hp:tc")):
                addr = tc.find(_q("hp:cellAddr"))
                span = tc.find(_q("hp:cellSpan"))
                sz = tc.find(_q("hp:cellSz"))
                cells.append((tc, int(addr.get("rowAddr")), int(addr.get("colAddr")),
                              int(span.get("rowSpan")), int(span.get("colSpan")), sz))
        col_cnt = int(tbl.get("colCnt"))
        row_cnt = int(tbl.get("rowCnt"))
        table_layout.occupancy_grid([(r, c, rs, cs) for _tc, r, c, rs, cs, _sz in cells], row_cnt, col_cnt)
        x = {0: 0}
        changed = True
        while changed:
            changed = False
            for _tc, _r, c, _rs, cs, sz in cells:
                w = int(sz.get("width"))
                if c in x and c + cs not in x:
                    x[c + cs] = x[c] + w
                    changed = True
                elif c + cs in x and c not in x:
                    x[c] = x[c + cs] - w
                    changed = True
        if sorted(x) != list(range(col_cnt + 1)):
            # 어떤 셀도 시작·종료하지 않는 열(모든 행에서 병합 안에 묻힌 열)은 셀 폭만으로 경계를
            # 정할 수 없다. 이웃한 알려진 경계 사이를 균등 분할해 채운다(병합 격자·셀 폭 합은 보존).
            known = sorted(k for k in x if 0 <= k <= col_cnt)
            if not known or known[0] != 0 or known[-1] != col_cnt:
                raise ValueError("이식 표의 열 경계를 모두 구하지 못했다(열 %d개, 경계 %r)" % (col_cnt, sorted(x)))
            for lo, hi in zip(known, known[1:]):
                for i in range(lo + 1, hi):
                    x[i] = x[lo] + int(round((x[hi] - x[lo]) * (i - lo) / float(hi - lo)))
            if sorted(x) != list(range(col_cnt + 1)):
                raise ValueError("이식 표의 열 경계를 모두 구하지 못했다(열 %d개, 경계 %r)" % (col_cnt, sorted(x)))
        old_cols = [x[i + 1] - x[i] for i in range(col_cnt)]
        new_cols = table_layout.scale_widths(old_cols, target)
        for tc, _r, c, _rs, cs, sz in cells:
            old_w = int(sz.get("width"))
            new_w = sum(new_cols[c:c + cs])
            sz.set("width", str(new_w))
            margin = tc.find(_q("hp:cellMargin"))
            hpad = int(margin.get("left")) + int(margin.get("right")) if margin is not None else 0
            for inner in tc.iter(_q("hp:tbl")):
                if inner is tbl:
                    continue
                parent_ok = _direct_parent_cell(tc, inner)
                if parent_ok:
                    inner_old = int(inner.find(_q("hp:sz")).get("width"))
                    ratio = float(max(new_w - hpad, 1)) / max(old_w - hpad, 1)
                    fit(inner, max(int(round(inner_old * ratio)), col_cnt))
        tbl.find(_q("hp:sz")).set("width", str(target))

    for tbl in _top_tables(root):
        fit(tbl, total_width)
    return _unwrap(root)


def _top_tables(root):
    out = []

    def walk(node, inside):
        for child in node:
            if child.tag == _q("hp:tbl"):
                if not inside:
                    out.append(child)
                walk(child, True)
            else:
                walk(child, inside)
    walk(root, False)
    return out


def _direct_parent_cell(tc, inner):
    """inner 표가 tc의 직속 하위 표(다른 셀을 거치지 않음)인가."""
    def walk(node):
        for child in node:
            if child is inner:
                return True
            if child.tag == _q("hp:tc"):
                continue
            if walk(child):
                return True
        return False
    return walk(tc)


def load_source(spec_source):
    """이식 원본: hwpx 경로 또는 추출 디렉터리 → raw dict."""
    _infos, raw = read_package(spec_source)
    return raw


def transplant_paragraphs(source_raw, section, rng, target_header, ids, total_width):
    """옛 hwpx 문단(section, [a,b] 포함 구간)을 대상 양식으로 옮긴 문단 XML 목록.

    - charPr/paraPr/borderFill(+그 안의 글꼴·tabPr) 참조는 대상 header에 같은 서명이 있으면 재매핑,
      없으면 대상 header에 복제 추가한다(itemCnt 갱신, 기존 ID와 충돌 없음).
    - 표는 total_width로 열폭 비례 재계산(병합 보존), `pageBreak="CELL"`은 NONE으로 바꾼다.
    - 폭이 바뀌므로 이식 문단의 linesegarray는 모두 지워 한글이 재조판하게 한다.
    """
    header_xml = source_raw["Contents/header.xml"]
    sec_xml = source_raw["Contents/section%d.xml" % int(section)]
    if isinstance(header_xml, bytes):
        header_xml = header_xml.decode("utf-8")
    if isinstance(sec_xml, bytes):
        sec_xml = sec_xml.decode("utf-8")
    spans = split_paragraphs(sec_xml)
    a, b = int(rng[0]), int(rng[1])
    if not (0 <= a <= b < len(spans)):
        raise ValueError("이식 범위 [%d,%d]가 section%s 문단 수(%d)를 벗어난다" % (a, b, section, len(spans)))
    importer = StyleImporter(header_xml, target_header)
    out = []
    for idx in range(a, b + 1):
        s, e = spans[idx]
        para = sec_xml[s:e]
        para = strip_linesegs(para)
        para = strip_cell_page_break(para)
        para = importer.remap_body(para)
        para = re.sub(r'(<hp:(?:tbl|pic)\b[^>]*?\bid=")\d+(")', lambda m: m.group(1) + str(ids.next()) + m.group(2), para)
        if "<hp:tbl" in para:
            para = rescale_tables(para, total_width)
        out.append(para)
    return out, importer
