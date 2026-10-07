# 블록 JSON과 양식 hwpx를 입력받아 서식을 이식한 6장 구조 학위논문 hwpx를 조립하는 스크립트
"""blocks_to_hwpx.py — blocks JSON → 학위논문 hwpx 조립기(양식 프로파일 주입형).

사용 예(김정년 양식, 2026-10-08 이관):
    python tools/hwpx_transfer/blocks_to_hwpx.py \
        --template "00. hwpx/YYMMDD_HHMM_…김정년양식이관본.hwpx"(양식 기준 원본의 복사본) \
        --profile tools/hwpx_transfer/staging/migrate_kjn/style_map_kjn.json \
        --blocks ch01.blocks.json … apx2.blocks.json \
        --references tools/hwpx_transfer/staging/migrate_kjn/references_kjn.json \
        --images tools/hwpx_transfer/staging/migrate_kjn/images.json \
        --transplant <이식 JSON> --toc-pages <쪽수 JSON(3단계 갱신 시)> \
        --output <출력 hwpx>

옛 윤혁 양식: --profile(또는 --style-map) tools/hwpx_transfer/staging/style_map.json — 종전 동작 그대로.

설계 요약.
  - 프로파일 종류로 경로를 고른다. 옛 양식(style_map.json)은 Document(이 파일), 김정년 양식
    (style_map_kjn.json 스키마)은 kjn_profile.KjnDocument. 프로파일에 필요한 키가 없으면
    ProfileError로 멈춘다(조용한 기본값 금지).
  - 옛 양식: section1 목차류만 재생성하고 제목 상자·감사의 글·논문개요는 바이트 보존, 표 캡션은 표 첫 행.
  - 김정년 양식: section0 표지 슬롯 치환, section1 목차·표목차·그림목차(탭 리더+쪽수)·감사의 글(이식)·
    논문개요(00_목차.md 골격), section2 본문(표 밖 캡션·내용 기반 열폭·회색 머리행·절항 앞 빈 줄·
    그림 BinData)·7분류 참고문헌·부록·Abstract. `pageBreak="CELL"`은 생성하지 않고 양식에서 옮긴 것도 NONE으로.
"""

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kjn_profile  # noqa: E402
from kjn_profile import (  # noqa: E402,F401 — 옛 이름 그대로 재수출(테스트·다른 도구 호환)
    CELL_LINEBREAK_TOKEN, EMSP_CHAR, EMSP_TOKEN, GUIDE_MARKER_RE, XML_PROLOG,
    IdGen, ProfileError, esc, load_profile, split_paragraphs,
)

# 옛 양식 실측 상수(표 폭 39142·셀 최소 높이·참고문헌 스타일·볼드 짝 charPr 등)는 프로파일로 옮겼다.
# 옛 style_map.json에 없던 값은 kjn_profile.LEGACY_EXTRAS가 `legacy` 키로 붙는다.


# ── XML 조각 생성 ─────────────────────────────────────────────────────────────
def lineseg(height, horzsize=kjn_profile.LEGACY_EXTRAS["line_width"]):
    """레이아웃 캐시 linesegarray 1줄. 한글이 문서를 열 때 재계산하므로 근사값이면 된다."""
    h = int(height)
    return (
        '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="%d" '
        'textheight="%d" baseline="%d" spacing="%d" horzpos="0" horzsize="%d" '
        'flags="393216"/></hp:linesegarray>'
        % (h, h, round(h * 0.85), round(h * 0.70), horzsize)
    )


class Assembler(object):
    """옛 윤혁 양식(style_map.json) 조립 부품. 상수는 모두 프로파일(`legacy` 보충 키 포함)에서 읽는다."""

    def __init__(self, style_map, ids, red_char_pr=None):
        self.pf = load_profile(style_map)
        self.sm = self.pf.data
        self.ids = ids
        self.red_char_pr = red_char_pr
        self.char_height = self.pf.get("legacy", "char_heights")
        self.table_width = int(self.pf.get("table", "tbl_attrs", "sz", "width"))
        self.row_min_h = int(self.pf.get("legacy", "row_min_height"))
        self.line_w = int(self.pf.get("legacy", "line_width"))

    def lx(self, *path):
        """옛 양식 보충 상수(LEGACY_EXTRAS) 조회."""
        return self.pf.get("legacy", *path)

    def height_of(self, char_pr):
        return self.char_height.get(str(char_pr), self.lx("char_height_default"))

    @staticmethod
    def _text_run(char_pr, text):
        return '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>' % (char_pr, esc(text))

    def marker_aware_runs(self, text, char_pr):
        """텍스트를 가이드 마커 경계로 나눠 마커 조각에만 빨간 charPr를 적용한다."""
        matches = list(GUIDE_MARKER_RE.finditer(text))
        if not matches:
            return self._text_run(char_pr, text)
        if self.red_char_pr is None:
            raise RuntimeError("가이드 마커용 빨간 charPr 공급자가 설정되지 않았다")

        red_char_pr = self.red_char_pr(str(char_pr))
        parts = []
        cursor = 0
        for match in matches:
            if match.start() > cursor:
                parts.append(self._text_run(char_pr, text[cursor:match.start()]))
            parts.append(self._text_run(red_char_pr, match.group(0)))
            cursor = match.end()
        if cursor < len(text):
            parts.append(self._text_run(char_pr, text[cursor:]))
        return "".join(parts)

    # ── 문단 ──────────────────────────────────────────────────────────────
    def para(self, para_pr, style, runs_xml, char_for_height, page_break=False, horzsize=None):
        return (
            '<hp:p id="%d" paraPrIDRef="%s" styleIDRef="%s" pageBreak="%d" '
            'columnBreak="0" merged="0">%s%s</hp:p>'
            % (
                self.ids.next(), para_pr, style, 1 if page_break else 0,
                # lineseg 1줄 근사값을 넣으면 한글 PDF 변환이 재계산 없이 그대로 신뢰해
                # 여러 줄 문단이 한 줄에 겹쳐 찍힌다(2026-07-25 렌더 실측). 생략하면 한글이 계산한다.
                runs_xml, "",
            )
        )

    def text_para(self, spec, text, page_break=False, prefix=""):
        run = self.marker_aware_runs(prefix + text, spec["char"])
        return self.para(spec["para"], spec["style"], run, spec["char"], page_break)

    def runs_para(self, spec, runs, page_break=False, prefix=""):
        """runs=[{text, bold}] 를 볼드 여부에 따라 charPr을 나눠 한 문단으로 만든다."""
        parts = []
        for i, r in enumerate(runs):
            body = (prefix if i == 0 else "") + r.get("text", "")
            char = self.lx("body_bold_char") if r.get("bold") else spec["char"]
            parts.append(self.marker_aware_runs(body, char))
        if not parts:
            parts.append('<hp:run charPrIDRef="%s"/>' % spec["char"])
        return self.para(spec["para"], spec["style"], "".join(parts), spec["char"], page_break)

    def blank(self, char=None):
        char = char or self.lx("blank_char")
        run = '<hp:run charPrIDRef="%s"/>' % char
        body = self.sm["body"]
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run, char)

    # ── 표 ────────────────────────────────────────────────────────────────
    def column_widths(self, ncols):
        """옛 양식 동작: 표 폭을 열 수로 균등 분할하되 나머지를 마지막 열에 준다(회귀 보존용).
        김정년 양식은 kjn_profile.KjnAssembler가 내용 기반 열폭(table_layout)을 쓴다."""
        total = self.table_width
        base = total // ncols
        widths = [base] * (ncols - 1) + [total - base * (ncols - 1)]
        assert sum(widths) == total
        return widths

    def border_fill(self, col, ncols):
        """좌우 개방형 테두리: 왼쪽 끝·오른쪽 끝·내부 borderFill(프로파일 legacy.edge_borders)."""
        edge = self.lx("edge_borders")
        if ncols == 1:
            return edge["single"]
        if col == 0:
            return edge["left"]
        if col == ncols - 1:
            return edge["right"]
        return edge["inner"]

    def cell_paragraphs(self, text, para_pr, char_pr, width):
        """셀 텍스트를 문단 XML로. <br>은 셀 안 별도 문단으로 나눈다(&emsp; 변환은 esc가 담당)."""
        lines = text.split(CELL_LINEBREAK_TOKEN)
        inner = max(width - self.lx("cell_hpad"), 1000)  # 좌우 셀 패딩을 뺀 실사용 폭
        out = []
        for line in lines:
            if line:
                run = self.marker_aware_runs(line, char_pr)
            else:
                run = '<hp:run charPrIDRef="%s"/>' % char_pr
            out.append(self.para(para_pr, "0", run, char_pr, horzsize=inner))
        return "".join(out), len(lines)

    def cell(self, text, col, row, width, ncols, col_span=1, border=None,
             para_pr=None, char_pr=None, height=None):
        sm_tbl = self.sm["table"]
        height = self.row_min_h if height is None else height
        para_pr = para_pr or sm_tbl["cell_paraPr"]
        char_pr = char_pr or sm_tbl["cell_charPr"]
        border = border or self.border_fill(col, ncols)
        paras, nlines = self.cell_paragraphs(text, para_pr, char_pr, width)
        pad = sm_tbl["cell_padding"]
        return (
            '<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" '
            'borderFillIDRef="%s"><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" '
            'vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" '
            'textHeight="0" hasTextRef="0" hasNumRef="0">%s</hp:subList>'
            '<hp:cellAddr colAddr="%d" rowAddr="%d"/>'
            '<hp:cellSpan colSpan="%d" rowSpan="1"/>'
            '<hp:cellSz width="%d" height="%d"/>'
            '<hp:cellMargin left="%s" right="%s" top="%s" bottom="%s"/></hp:tc>'
            % (border, paras, col, row, col_span, width, max(height, self.row_min_h * nlines),
               pad["left"], pad["right"], pad["top"], pad["bottom"])
        )

    def table_xml(self, header, rows, caption=None):
        """표 하나를 담은 문단 XML을 만든다. caption이 있으면 양식 관행대로 첫 행에 병합해 넣는다."""
        ncols = len(header)
        widths = self.column_widths(ncols)
        sm_tbl = self.sm["table"]
        attrs = sm_tbl["tbl_attrs"]
        trs = []
        row_idx = 0
        if caption is not None:
            # 캡션 행: 전체 열 병합 + 아래만 실선 borderFill (프로파일 legacy.caption_row)
            cap = self.lx("caption_row")
            trs.append("<hp:tr>%s</hp:tr>" % self.cell(
                caption, 0, row_idx, self.table_width, ncols, col_span=ncols, border=cap["border"],
                para_pr=cap["para"], char_pr=cap["char"]))
            row_idx += 1
        for data_row in [header] + rows:
            cells = []
            for col, value in enumerate(data_row):
                cells.append(self.cell(value, col, row_idx, widths[col], ncols))
            trs.append("<hp:tr>%s</hp:tr>" % "".join(cells))
            row_idx += 1

        pos, out_m, in_m = attrs["pos"], attrs["outMargin"], attrs["inMargin"]
        tbl = (
            '<hp:tbl id="%d" zOrder="0" numberingType="%s" textWrap="%s" textFlow="%s" '
            'lock="%s" dropcapstyle="%s" pageBreak="%s" repeatHeader="%s" rowCnt="%d" '
            'colCnt="%d" cellSpacing="%s" borderFillIDRef="%s" noAdjust="%s">'
            '<hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" heightRelTo="ABSOLUTE" protect="0"/>'
            '<hp:pos treatAsChar="%s" affectLSpacing="0" flowWithText="%s" allowOverlap="0" '
            'holdAnchorAndSO="0" vertRelTo="%s" horzRelTo="%s" vertAlign="TOP" horzAlign="LEFT" '
            'vertOffset="0" horzOffset="0"/>'
            '<hp:outMargin left="%s" right="%s" top="%s" bottom="%s"/>'
            '<hp:inMargin left="%s" right="%s" top="%s" bottom="%s"/>%s</hp:tbl>'
            % (
                self.ids.next(), attrs["numberingType"], attrs["textWrap"], attrs["textFlow"],
                attrs["lock"], attrs["dropcapstyle"], attrs["pageBreak"], attrs["repeatHeader"],
                row_idx, ncols, attrs["cellSpacing"], attrs["borderFillIDRef"], attrs["noAdjust"],
                self.table_width, self.row_min_h * row_idx,
                pos["treatAsChar"], pos["flowWithText"], pos["vertRelTo"], pos["horzRelTo"],
                out_m["left"], out_m["right"], out_m["top"], out_m["bottom"],
                in_m["left"], in_m["right"], in_m["top"], in_m["bottom"],
                "".join(trs),
            )
        )
        # 표는 문단 run 안에 treatAsChar=1로 인라인 배치된다(양식 s2 p223: run charPr 67, 표 뒤 빈 hp:t).
        body = self.sm["body"]
        run = '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (self.sm["h2_section"]["charPrIDRef"], tbl)
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run, self.lx("table_anchor_height_char"),
                         horzsize=self.line_w)


# ── 양식 hwpx 해체 ────────────────────────────────────────────────────────────
def set_page_break(para_xml, value="1"):
    return re.sub(r'(<hp:p [^>]*?pageBreak=")\d(")', r"\g<1>%s\g<2>" % value, para_xml, count=1)


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _char_pr_signature(element, root=True):
    """charPr의 id·본문색만 제외한 구조 서명. 기존 빨간 charPr의 정확한 재사용 판정용."""
    attrs = tuple(sorted(
        (key, value)
        for key, value in element.attrib.items()
        if not (root and key in ("id", "textColor"))
    ))
    children = tuple(_char_pr_signature(child, root=False) for child in element)
    return _local_name(element.tag), attrs, children


class Template(object):
    """양식 hwpx에서 재사용할 XML 조각을 뽑아 둔다."""

    def __init__(self, path, profile):
        self.path = path
        self.pf = load_profile(profile)
        with zipfile.ZipFile(path) as z:
            self.infos = z.infolist()
            self.raw = {i.filename: z.read(i.filename) for i in self.infos}
        self.header_xml = self.raw["Contents/header.xml"].decode("utf-8")
        self.s1 = self.raw["Contents/section1.xml"].decode("utf-8")
        self.s2 = self.raw["Contents/section2.xml"].decode("utf-8")
        self.s1_paras = split_paragraphs(self.s1)
        self.s2_paras = split_paragraphs(self.s2)
        self._prepare_char_prs()
        self._slice_front_matter()
        self._slice_sec2_controls()

    def _prepare_char_prs(self):
        root = ET.fromstring(self.header_xml)
        char_prs = {
            element.get("id"): element
            for element in root.iter()
            if _local_name(element.tag) == "charPr"
        }
        char_properties = next(
            (element for element in root.iter() if _local_name(element.tag) == "charProperties"),
            None,
        )
        if char_properties is None:
            raise SystemExit("양식 header.xml에서 charProperties를 찾지 못했다")
        declared = int(char_properties.get("itemCnt", "-1"))
        if declared != len(char_prs):
            raise SystemExit(
                "양식 header.xml의 charPr itemCnt(%d)와 실제 개수(%d)가 다르다"
                % (declared, len(char_prs))
            )

        self._char_prs = char_prs
        self._char_pr_signatures = {
            char_id: _char_pr_signature(element) for char_id, element in char_prs.items()
        }
        self._red_char_by_signature = {
            self._char_pr_signatures[char_id]: char_id
            for char_id, element in char_prs.items()
            if element.get("textColor", "").upper() == "#FF0000"
        }
        self._red_char_by_base = {}
        self._char_pr_count = len(char_prs)
        self._next_char_pr_id = max(int(char_id) for char_id in char_prs) + 1

    def red_char_pr_id(self, base_char_pr_id):
        """원본과 id·textColor 외 속성이 같은 빨간 charPr ID를 돌려준다."""
        base_char_pr_id = str(base_char_pr_id)
        if base_char_pr_id in self._red_char_by_base:
            return self._red_char_by_base[base_char_pr_id]
        if base_char_pr_id not in self._char_prs:
            raise SystemExit("양식 header.xml에 charPr id=%s가 없다" % base_char_pr_id)

        signature = self._char_pr_signatures[base_char_pr_id]
        existing = self._red_char_by_signature.get(signature)
        if existing is not None:
            self._red_char_by_base[base_char_pr_id] = existing
            return existing

        pattern = re.compile(
            r'<hh:charPr\b[^>]*\bid="%s"[^>]*>.*?</hh:charPr>' % re.escape(base_char_pr_id),
            re.S,
        )
        match = pattern.search(self.header_xml)
        if not match:
            raise SystemExit("양식 header.xml에서 charPr id=%s XML을 찾지 못했다" % base_char_pr_id)

        new_id = str(self._next_char_pr_id)
        self._next_char_pr_id += 1
        clone = re.sub(
            r'\bid="%s"' % re.escape(base_char_pr_id), 'id="%s"' % new_id,
            match.group(0), count=1,
        )
        clone, color_subs = re.subn(
            r'\btextColor="[^"]*"', 'textColor="#FF0000"', clone, count=1,
        )
        if color_subs != 1:
            raise SystemExit("charPr id=%s에 textColor 속성이 없다" % base_char_pr_id)

        closing = "</hh:charProperties>"
        if closing not in self.header_xml:
            raise SystemExit("양식 header.xml의 charProperties 닫는 태그를 찾지 못했다")
        self.header_xml = self.header_xml.replace(closing, clone + closing, 1)
        self._char_pr_count += 1
        self.header_xml, count_subs = re.subn(
            r'(<hh:charProperties\b[^>]*\bitemCnt=")\d+(")',
            lambda item: item.group(1) + str(self._char_pr_count) + item.group(2),
            self.header_xml,
            count=1,
        )
        if count_subs != 1:
            raise SystemExit("양식 header.xml의 charPr itemCnt를 갱신하지 못했다")

        self._red_char_by_base[base_char_pr_id] = new_id
        self._red_char_by_signature[signature] = new_id
        return new_id

    def _para(self, xml_text, spans, idx):
        a, b = spans[idx]
        return xml_text[a:b]

    def _slice_front_matter(self):
        s1, ps = self.s1, self.s1_paras
        expected = next((int(sec["paragraphs"]) for sec in self.pf.get("sections")
                         if sec.get("file") == "section1.xml"), None)
        if expected is None:
            raise ProfileError("프로파일 sections에 section1.xml 문단 수가 없다")
        if len(ps) != expected:
            raise SystemExit("양식 section1 문단 수가 %d가 아니다(%d) — 전면부 경계 재확인 필요" % (expected, len(ps)))
        rng = {k: kjn_profile.range_bounds(v, k) for k, v in self.pf.get("front_matter_ranges").items()
               if not k.startswith("_")}
        toc, lot, lof = rng["목차"][0], rng["표목차"][0], rng["그림목차"][0]
        thanks, abstract = rng["감사의글"], rng["논문개요"]
        self.s1_head = s1[: ps[toc][0]]                     # 프롤로그 + <hs:sec …> (secPr는 p0 안에 있음)
        self.toc_title = self._para(s1, ps, toc)            # 목차 제목 상자(secPr 포함) — 바이트 보존
        self.lot_title = set_page_break(self._para(s1, ps, lot))   # 표목차 제목 상자
        self.lof_title = self._para(s1, ps, lof)            # 그림목차 제목 상자(이미 pageBreak=1)
        self.thanks = s1[ps[thanks[0]][0]: ps[thanks[1]][1]]        # 감사의 글 — 사용자 작성분, 바이트 보존
        self.abstract_kr = s1[ps[abstract[0]][0]: ps[abstract[1]][1]]  # 논문개요 — 바이트 보존
        tail = s1[ps[abstract[1]][1]:]
        if tail.strip() != "</hs:sec>":
            raise SystemExit("양식 section1 말미가 예상과 다르다: %r" % tail[:80])

    def _slice_sec2_controls(self):
        p0 = self._para(self.s2, self.s2_paras, 0)
        m = re.search(r"(<hp:ctrl><hp:colPr.*?</hp:secPr>)", p0, re.S)
        if not m:
            raise SystemExit("양식 section2 첫 문단에서 colPr/secPr 블록을 찾지 못했다")
        self.sec2_secpr = m.group(1)
        self.sec2_pagectrl = "".join(re.findall(r"<hp:ctrl><hp:page(?:Num|Hiding)[^>]*/></hp:ctrl>", p0))
        self.sec2_newnum = "".join(re.findall(r"<hp:ctrl><hp:newNum[^>]*/></hp:ctrl>", p0))
        self.s2_head = self.s2[: self.s2_paras[0][0]]

    def cover_texts(self):
        """표지(section0) 문단별 텍스트. 구 제목 문자열 위치 보고용."""
        s0 = self.raw["Contents/section0.xml"].decode("utf-8")
        out = []
        for idx, (a, b) in enumerate(split_paragraphs(s0)):
            seg = s0[a:b]
            texts = re.findall(r"<hp:t>(.*?)</hp:t>", seg, re.S)
            out.append((idx, " ".join(t for t in texts if t.strip())))
        return out


# ── 본문 조립 ─────────────────────────────────────────────────────────────────
class Document(object):
    def __init__(self, template, style_map):
        self.tpl = template
        self.pf = load_profile(style_map)
        if self.pf.kind != "legacy":
            raise ProfileError("Document는 옛 양식 프로파일 전용이다 — 김정년 양식은 kjn_profile.KjnDocument를 쓴다")
        self.sm = self.pf.data
        self.ids = IdGen()
        self.asm = Assembler(self.pf, self.ids, template.red_char_pr_id)
        self.body = []          # section2 문단 XML 목록
        self.toc = []           # (level, 제목)
        self.lot = []           # 표 목차 항목
        self.lof = []           # 그림 목차 항목
        self.notes = []         # 조립 중 남길 메모

    # 스타일 스펙 헬퍼
    def spec(self, key):
        s = self.sm[key]
        return {"style": s["styleIDRef"], "para": s["paraPrIDRef"], "char": s["charPrIDRef"]}

    def add_blocks(self, blocks, first_paragraph=False, survey_cover=False):
        body_spec = self.spec("body")
        cap_spec = self.spec("caption")
        pending_caption = None
        i = 0
        while i < len(blocks):
            b = blocks[i]
            kind = b["type"]

            # 표 캡션은 바로 뒤 표가 있으면 표 첫 행에 병합한다(양식 관행).
            if pending_caption is not None and kind != "table":
                self.body.append(self.asm.text_para(cap_spec, pending_caption))
                pending_caption = None

            if kind == "h1":
                self.toc.append((1, b["text"]))
                if first_paragraph:
                    self.body.append(self._first_paragraph(b["text"]))
                    first_paragraph = False
                else:
                    self.body.append(self.asm.text_para(self.spec("h1_chapter"), b["text"], page_break=True))
                self.body.append(self.asm.blank())
                if survey_cover:
                    self.add_survey_cover()
                    survey_cover = False
            elif kind == "h2":
                self.toc.append((2, b["text"]))
                self.body.append(self.asm.text_para(self.spec("h2_section"), b["text"]))
                self.body.append(self.asm.blank())
            elif kind == "h3":
                self.toc.append((3, b["text"]))
                self.body.append(self.asm.text_para(self.spec("h3_item"), b["text"]))
                self.body.append(self.asm.blank())
            elif kind == "h4":
                spec = dict(body_spec)
                spec["char"] = self.asm.lx("h4_char")
                self.body.append(self.asm.text_para(spec, b["text"]))
            elif kind == "p":
                runs = b.get("runs", [])
                prefix = "" if (runs and runs[0].get("text", "")[:1].isspace()) else " "
                self.body.append(self.asm.runs_para(body_spec, runs, prefix=prefix))
            elif kind == "table_caption":
                self.lot.append(b["text"])
                pending_caption = b["text"]
            elif kind == "table":
                self.body.append(self.asm.table_xml(b["header"], b["rows"], caption=pending_caption))
                pending_caption = None
            elif kind == "figure_caption":
                self.lof.append(b["text"])
                self.body.append(self.asm.text_para(cap_spec, b["text"]))
            elif kind == "figure_placeholder":
                self.body.append(self.asm.text_para(body_spec, b["text"]))
            else:
                raise SystemExit("알 수 없는 블록 타입: %r" % kind)
            i += 1

        if pending_caption is not None:
            self.body.append(self.asm.text_para(cap_spec, pending_caption))
        self.body.append(self.asm.blank())
        return first_paragraph

    def _first_paragraph(self, title):
        """section2 첫 문단 — 양식의 colPr·secPr·쪽번호 제어 블록을 그대로 이식한다."""
        h1 = self.sm["h1_chapter"]
        runs = (
            '<hp:run charPrIDRef="%s">%s%s</hp:run>'
            '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t>%s</hp:run>'
            % (h1["charPrIDRef"], self.tpl.sec2_secpr, self.tpl.sec2_pagectrl,
               h1["charPrIDRef"], esc(title), self.tpl.sec2_newnum)
        )
        return self.asm.para(h1["paraPrIDRef"], h1["styleIDRef"], runs, h1["charPrIDRef"])

    def add_references(self, refs):
        self.toc.append((1, "참고문헌"))
        lx = self.asm.lx
        self.body.append(self.asm.text_para(lx("ref_title"), "참고문헌", page_break=True))
        self.body.append(self.asm.blank())
        for category, items in refs["categories"].items():
            self.body.append(self.asm.text_para(lx("ref_category"), category))
            for item in items:
                self.body.append(self.asm.text_para(
                    lx("ref_entry"), "[%02d] %s" % (item["no"], item["text"])))
            self.body.append(self.asm.blank(lx("ref_blank_char")))
            if not items:
                self.notes.append("참고문헌 분류 '%s'에 확정 항목이 없어 제목만 생성했다." % category)
        flagged = len(refs.get("flagged", []))
        if flagged:
            self.notes.append("references.json의 flagged %d건은 지시대로 본문에 넣지 않았다." % flagged)

    def add_survey_cover(self):
        """부록1 설문지 표지 박스 — 원고 코드펜스를 가운데 정렬 문단으로 재구성한다."""
        center = self.spec("toc_entry")  # paraPr 25 = CENTER
        cover = self.asm.lx("survey_cover")
        for line in SURVEY_COVER_TITLE:
            self.body.append(self.asm.text_para(
                {"style": center["style"], "para": center["para"], "char": cover["title_char"]}, line))
        self.body.append(self.asm.blank())
        self.body.append(self.asm.text_para(
            {"style": center["style"], "para": center["para"], "char": cover["label_char"]}, SURVEY_COVER_LABEL))
        self.body.append(self.asm.blank())

    def add_placeholder_section(self, title):
        self.toc.append((1, title))
        self.body.append(self.asm.text_para(self.asm.lx("appendix_title"), title, page_break=True))
        self.body.append(self.asm.blank())
        self.body.append(self.asm.text_para(self.spec("body"), "[내용 확정 후 작성]", prefix=" "))
        self.body.append(self.asm.blank())

    # ── 전면부(section1) ─────────────────────────────────────────────────
    def build_section1(self):
        toc_spec = self.spec("toc_entry")
        # 양식 목차 paraPr 25는 CENTER — 양식은 탭·리더점·쪽번호로 줄을 채워 무력화했지만
        # 쪽번호 없는 재생성 목차는 그대로 가운데 정렬돼 보인다(QA F-2). 표·그림 목차와
        # 같은 JUSTIFY 문단(paraPr)을 쓰고, 쪽번호는 한글 자동 목차로 최종화한다.
        toc_spec = {"style": toc_spec["style"],
                    "para": self.spec("toc_lot_entry")["para"], "char": self.asm.lx("toc_char")}  # 빨강(116) 대신 흑색
        lot_spec = self.spec("toc_lot_entry")
        front_blank = self.asm.lx("front_blank_char")
        parts = [self.tpl.s1_head, self.tpl.toc_title, self.asm.blank(front_blank)]
        for level, title in self.toc:
            parts.append(self.asm.text_para(toc_spec, title, prefix=" " * (level - 1)))
        parts.append(self.asm.blank(front_blank))

        parts.append(self.tpl.lot_title)
        parts.append(self.asm.blank())
        for text in self.lot:
            parts.append(self.asm.text_para(lot_spec, text))
        parts.append(self.asm.blank())

        parts.append(self.tpl.lof_title)
        parts.append(self.asm.blank())
        for text in self.lof:
            parts.append(self.asm.text_para(lot_spec, text))
        parts.append(self.asm.blank())

        parts.append(self.tpl.thanks)
        parts.append(self.tpl.abstract_kr)
        parts.append("</hs:sec>")
        return "".join(parts)

    def build_section2(self):
        return self.tpl.s2_head + "".join(self.body) + "</hs:sec>"


# ── 출력 ──────────────────────────────────────────────────────────────────────
def write_hwpx(template, output, replacements):
    """양식 ZIP의 엔트리 순서·압축 방식을 유지한 채 지정 엔트리만 교체해 새 파일로 쓴다."""
    out_dir = os.path.dirname(os.path.abspath(output))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with zipfile.ZipFile(output, "w") as zout:
        for info in template.infos:
            data = replacements.get(info.filename, template.raw[info.filename])
            if isinstance(data, str):
                data = data.encode("utf-8")
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            new_info.internal_attr = info.internal_attr
            new_info.create_system = info.create_system
            zout.writestr(new_info, data)


def load_blocks(paths):
    out = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        out.append((path, data["blocks"]))
    return out


# 부록1 설문지 표지 박스(원고 코드펜스, parse_report §5-3 — 메인이 별도 서식으로 재구성).
# 논문 제목이 바뀌면 `01.docs/부록1_설문지_양식.md`의 표지 박스와 함께 여기도 고쳐야 한다.
SURVEY_COVER_TITLE = [
    "중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템",
    "개발 및 실증 연구",
    ": 도입 현장과 미도입 현장의 안전관리 실효성 비교를",
    "중심으로",
]
SURVEY_COVER_LABEL = "설  문  지"


def is_appendix(blocks):
    """블록 파일의 첫 h1 제목이 '부록'으로 시작하면 부록 파일로 본다(참고문헌 삽입 위치 판정용)."""
    for b in blocks:
        if b["type"] == "h1":
            # 부록1 제목은 "부 록 — …"처럼 띄어 쓰므로 공백을 걷어내고 판정한다(QA 발견).
            return b["text"].replace(" ", "").startswith("부록")
    return False


def build_report(doc, template, args, output):
    lines = ["# 조립 리포트", "",
             "- 양식: `%s`" % args.template,
             "- 출력: `%s`" % output,
             "- 본문 문단 수: %d" % len(doc.body),
             "- 목차 항목: %d (장 %d)" % (len(doc.toc), sum(1 for l, _ in doc.toc if l == 1)),
             "- 표 목차 항목: %d / 그림 목차 항목: %d" % (len(doc.lot), len(doc.lof)),
             ""]
    if doc.notes:
        lines += ["## 메모", ""] + ["- %s" % n for n in doc.notes] + [""]
    lines += ["## 표지(section0) 원문 텍스트 — 구 제목 문자열 확인용(치환하지 않음)", ""]
    for idx, text in template.cover_texts():
        lines.append("- section0 p%d: %s" % (idx, text[:400] if text else "(텍스트 없음)"))
    lines.append("")
    return "\n".join(lines)


def _resolve(path, base_dirs):
    if os.path.isabs(path) and os.path.exists(path):
        return path
    for base in base_dirs:
        cand = os.path.join(base, path)
        if os.path.exists(cand):
            return cand
    raise SystemExit("파일을 찾지 못했다: %s (기준 %s)" % (path, ", ".join(base_dirs)))


def load_images_arg(path, repo_root):
    """--images JSON → {캡션 접두사: PNG 경로}.

    단순 사전 {"<그림 1-1>": "a.png"} 또는 images.json 형식({"mapping": [{caption_prefix, source,
    extract_to}]})을 받는다. source가 "old:…"(옛 hwpx BinData)이면 추출본 extract_to를 쓴다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    bases = [os.getcwd(), repo_root, os.path.dirname(os.path.abspath(path))]
    out = {}
    if isinstance(data, dict) and isinstance(data.get("mapping"), list):
        for entry in data["mapping"]:
            src = entry.get("source") or ""
            if not src or src.startswith("old:"):
                src = entry.get("extract_to") or entry.get("old_extract_to")
            if not src:
                raise SystemExit("images 매핑 %r에 그림 경로가 없다" % entry.get("caption_prefix"))
            out[entry["caption_prefix"]] = _resolve(src, bases)
    elif isinstance(data, dict):
        out = {k: _resolve(v, bases) for k, v in data.items() if not k.startswith("_")}
    else:
        raise SystemExit("--images JSON 형식을 해석할 수 없다")
    return out


THANKS_RED_NOTE = "[확정 필요: 감사의 글 완성]"


def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_transplants(path, template, ids, profile, repo_root, asm=None):
    """--transplant JSON → (감사의 글 문단 목록|None, {제목 접두사: 문단 목록}, 부록1 표지 대체 여부, 메모, 대체 목록).

    형식:
      {"감사의글": {"source_hwpx": …, "section": 1, "range": [127, 151],
                   "append_red_note": "[확정 필요: 감사의 글 완성]"},          # 생략 시 이 문구, ""면 안 붙임
       "부록1_설문지": {"source_hwpx": …, "section": 2, "range": [631, 694],
                      "replace_appendix": "부 록 — 설문지",                    # 이 h1로 시작하는 블록 파일을 대체
                      "keep_until": "부 록 (도입 현장)"},                      # 이 제목까지 블록으로 조립 후 이식
       "부록1_PartA_도입": {…, "insert_after_heading": "부 록 (도입 현장)"}}   # 제목 뒤에 끼워 넣기
    source_hwpx는 hwpx 경로 또는 추출 디렉터리. 감사의 글 외 항목은 replace_appendix 또는
    insert_after_heading이 필수다. 감사의 글 범위가 옛 제목 상자로 시작하면 양식 상자 대신 그 상자를 쓴다.
    """
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    bases = [os.getcwd(), repo_root, os.path.dirname(os.path.abspath(path))]
    thanks, after, replace_cover, notes, replaces = None, {}, False, [], {}
    width_body = int(profile.get("table", "total_width"))
    width_apx = int(profile.first(("table", "total_width_appendix"), ("table", "total_width")))
    # 감사의 글 범위의 표는 옛 제목 상자뿐이므로 양식 제목 상자 폭(front_heading_box.tbl.width)에 맞춘다
    width_front = int(profile.get("front_heading_box", "tbl", "width"))
    for name, item in spec.items():
        if name.startswith("_"):
            continue
        for need in ("source_hwpx", "section", "range"):
            if need not in item:
                raise SystemExit("--transplant '%s'에 '%s'가 없다" % (name, need))
        raw = kjn_profile.load_source(_resolve(item["source_hwpx"], bases))
        is_thanks = name.replace(" ", "") in ("감사의글", "감사의_글")
        width = width_front if is_thanks else width_apx
        paras, importer = kjn_profile.transplant_paragraphs(
            raw, item["section"], item["range"], template.header, ids, width)
        # 이식 원본(옛 hwpx)이 현행 MD보다 오래된 문구를 담고 있으면 MD 기준으로 치환한다(MD 단일 원본).
        # 각 항목은 {"old","new","count"} — 실제 치환 횟수가 count와 다르면 멈춘다(2026-10-08 설문 A-6 4구간).
        for rep in item.get("text_replacements", []):
            old_x, new_x = _esc(rep["old"]), _esc(rep["new"])
            hits = sum(x.count(old_x) for x in paras)
            if hits != int(rep.get("count", 1)):
                raise ValueError("이식 '%s' 치환 '%s…' 출현 %d회 ≠ 기대 %s회"
                                 % (name, rep["old"][:30], hits, rep.get("count", 1)))
            paras = [x.replace(old_x, new_x) for x in paras]
        if item.get("drop_first"):
            paras = paras[1:]
        if is_thanks:
            note = item.get("append_red_note", THANKS_RED_NOTE)
            if note:
                if asm is None:
                    raise SystemExit("감사의 글 빨간 메모를 만들 조립기가 없다")
                note_para = asm.text_para(profile.spec("abstract_body"), note)
                # 날짜·성명 뒤(쪽 끝)가 아니라 본문 첫 문단 바로 뒤에 둔다(제목 상자·빈 문단은 건너뛴다).
                pos = None
                for i, para_xml in enumerate(paras):
                    if "<hp:tbl" in para_xml:
                        continue
                    if kjn_profile.plain_texts(para_xml).strip():
                        pos = i
                        break
                if pos is None:
                    paras = paras + [note_para]
                elif (pos + 1 < len(paras) and "<hp:tbl" not in paras[pos + 1]
                      and not kjn_profile.plain_texts(paras[pos + 1]).strip()):
                    # 바로 뒤 빈 문단을 메모로 바꿔 문단 수를 유지한다(옛 감사의 글은 빈 문단으로 날짜·성명을
                    # 쪽 아래로 밀어 두어, 한 줄만 늘어나도 성명이 다음 쪽으로 넘어간다 — 2026-10-08 스모크).
                    paras = paras[:pos + 1] + [note_para] + paras[pos + 2:]
                else:
                    paras = paras[:pos + 1] + [note_para] + paras[pos + 1:]
        added = {k: len(v) for k, v in importer.added.items() if v}
        notes.append("이식 '%s': 문단 %d개, header 추가 %s" % (name, len(paras), added or "없음(전부 재매핑)"))
        if is_thanks:
            thanks = paras
        elif item.get("replace_appendix"):
            key = re.sub(r"\s+", "", item["replace_appendix"])
            replaces[key] = {"keep_until": item.get("keep_until"), "paras": paras,
                             "drop_heading": bool(item.get("drop_heading"))}
            if paras and 'pageBreak="1"' in paras[-1] and not kjn_profile.plain_texts(paras[-1]).strip():
                notes.append("이식 '%s'의 마지막 문단이 쪽 나눔 빈 문단이다 — 다음 부록 제목도 새 쪽이라 빈 쪽이 "
                             "생길 수 있다(범위 끝을 하나 줄이는 것을 검토)." % name)
        else:
            anchor = item.get("insert_after_heading")
            if not anchor:
                raise SystemExit("--transplant '%s'에 replace_appendix 또는 insert_after_heading이 필요하다" % name)
            after.setdefault(anchor, []).extend(paras)
            replace_cover = replace_cover or bool(item.get("replace_survey_cover"))
    _ = width_body
    return thanks, after, replace_cover, notes, replaces


def write_package(output, entries, date_time):
    out_dir = os.path.dirname(os.path.abspath(output))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with zipfile.ZipFile(output, "w") as zout:
        for name, data, ctype, info in entries:
            new_info = zipfile.ZipInfo(name, date_time=info.date_time if info is not None else date_time)
            new_info.compress_type = ctype
            if info is not None:
                new_info.external_attr = info.external_attr
                new_info.internal_attr = info.internal_attr
                new_info.create_system = info.create_system
            zout.writestr(new_info, data)


def run_kjn(args, profile, here, output, report_path):
    doc, template, sections, toc_pages = assemble_kjn(args, profile, here)
    entries = kjn_profile.plan_package(template, sections, template.header.xml, doc.bin_items)
    first_info = next((info for _n, _c, info in template.infos if info is not None), None)
    write_package(output, entries, first_info.date_time if first_info else (2026, 1, 1, 0, 0, 0))

    lines = ["# 조립 리포트(김정년 양식 프로파일)", "",
             "- 양식: `%s`" % args.template, "- 프로파일: `%s`" % args.profile, "- 출력: `%s`" % output,
             "- 본문 문단 수: %d" % len(doc.body),
             "- 목차 항목: %d / 표 목차: %d / 그림 목차: %d / 그림 BinData: %d"
             % (len(doc.toc), len(doc.lot), len(doc.lof), len(doc.bin_items)),
             "- 목차 쪽수: %s" % ("--toc-pages 반영" if toc_pages else "임시값 0(3단계에서 갱신)"), ""]
    lines += ["## 표 열폭(HWPUNIT)", ""] + ["- %s: %s" % (cap or "(캡션 없음)", w) for cap, w in doc.table_widths] + [""]
    if doc.notes:
        lines += ["## 메모", ""] + ["- %s" % n for n in doc.notes] + [""]
    report = "\n".join(lines)
    if report_path:
        rep_dir = os.path.dirname(os.path.abspath(report_path))
        if rep_dir and not os.path.isdir(rep_dir):
            os.makedirs(rep_dir)
        with open(report_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
    sys.stdout.write(report)
    return 0


def assemble_kjn(args, profile, here):
    """김정년 양식 조립(메모리 안). 파일을 쓰지 않는다 — (doc, template, sections, toc_pages)."""
    repo_root = os.path.dirname(os.path.dirname(here))
    template = kjn_profile.KjnTemplate(args.template, profile)
    images = load_images_arg(args.images, repo_root) if args.images else {}
    toc_pages = {}
    if args.toc_pages:
        with open(args.toc_pages, encoding="utf-8") as f:
            toc_pages = json.load(f)
    doc = kjn_profile.KjnDocument(template, profile, images=images, toc_pages=toc_pages)
    thanks, after, replace_cover, t_notes, replaces = (None, {}, False, [], {})
    if args.transplant:
        thanks, after, replace_cover, t_notes, replaces = load_transplants(
            args.transplant, template, doc.ids, profile, repo_root, asm=doc.asm)
    doc.notes.extend(t_notes)

    files = load_blocks(args.blocks)
    refs = None
    if args.references:
        with open(args.references, encoding="utf-8") as f:
            refs = json.load(f)
    first = True
    refs_done = False
    for _path, blocks in files:
        appendix = is_appendix(blocks)
        if refs is not None and not refs_done and appendix:
            doc.add_references(refs)
            refs_done = True
        is_survey = any(b["type"] == "h1" and "설문지" in b["text"] for b in blocks)
        first_h1 = next((re.sub(r"\s+", "", b["text"]) for b in blocks if b["type"] == "h1"), "")
        replace = next((v for k, v in replaces.items() if first_h1.startswith(k)), None)
        first = doc.add_blocks(blocks, first_paragraph=first, appendix=appendix, transplants_after=after,
                               survey_cover=is_survey and not replace_cover and replace is None, replace=replace)
        if replace is not None:
            replace["used"] = True
    if refs is not None and not refs_done:
        doc.add_references(refs)
    unused = [k for k, v in replaces.items() if not v.get("used")]
    if unused:
        raise SystemExit("--transplant replace_appendix와 맞는 블록 파일이 없다: %s" % unused)
    if not args.no_tail:
        doc.add_placeholder_appendix("부록 3. 시스템 화면 및 LLM 검증 사례 이미지")
        doc.add_abstract_en()

    front_md = args.front_md or os.path.join(repo_root, "01.docs", "00_목차.md")
    with open(front_md, encoding="utf-8") as f:
        abstract_kr = kjn_profile.parse_abstract_skeleton(f.read())

    s0 = doc.build_section0()
    s1 = doc.build_section1(thanks_xml=thanks, abstract_kr=abstract_kr)
    s2 = doc.build_section2()
    sections = {"Contents/section0.xml": s0, "Contents/section1.xml": s1, "Contents/section2.xml": s2}
    for name, xml_text in sections.items():
        if 'pageBreak="CELL"' in xml_text:
            raise SystemExit('%s에 pageBreak="CELL"이 남았다 — 금지 속성' % name)
    hits = kjn_profile.leftover_hits([kjn_profile.plain_texts(x) for x in sections.values()], profile)
    if hits:
        raise SystemExit("김정년 양식 고유 문구가 남았다(표절 의심 산출물): %r" % hits)
    return doc, template, sections, toc_pages


def main(argv=None):
    ap = argparse.ArgumentParser(description="blocks JSON → 학위논문 hwpx 조립기(양식 프로파일 주입형)")
    ap.add_argument("--template", required=True, help="양식 hwpx (읽기 전용) — 김정년 양식은 추출 디렉터리도 허용")
    ap.add_argument("--profile", "--style-map", dest="profile", required=True,
                    help="양식 프로파일 JSON (옛 양식 style_map.json 또는 김정년 양식 style_map_kjn.json)")
    ap.add_argument("--blocks", nargs="+", required=True, help="blocks JSON (본문 순서대로)")
    ap.add_argument("--references", help="참고문헌 JSON {categories:{분류:[{no,text}]}, flagged:[…]}")
    ap.add_argument("--images", help="그림 매핑 JSON — {캡션 접두사: PNG} 또는 images.json(mapping 목록)")
    ap.add_argument("--toc-pages", dest="toc_pages",
                    help="목차 쪽수 JSON {toc:{제목:쪽}, lot:{<표 n-m>:쪽}, lof:{<그림 n-m>:쪽}} — 없으면 0")
    ap.add_argument("--transplant", help="옛 hwpx 문단 이식 JSON {감사의글:{source_hwpx,section,range}, …}")
    ap.add_argument("--front-md", dest="front_md", help="논문개요 골격 MD (기본 01.docs/00_목차.md)")
    ap.add_argument("--output", help="출력 hwpx 경로")
    ap.add_argument("--report", help="조립 리포트 MD 경로")
    ap.add_argument("--smoke", action="store_true",
                    help="스테이징 스모크 모드 — staging/test_out/smoke.hwpx 로 출력")
    ap.add_argument("--no-tail", action="store_true",
                    help="부록 3·Abstract 자리 문단을 생성하지 않는다")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    output = args.output
    report_path = args.report
    if args.smoke:
        test_out = os.path.join(here, "staging", "test_out")
        output = output or os.path.join(test_out, "smoke.hwpx")
        report_path = report_path or os.path.join(test_out, "assembly_report.md")
    if not output:
        ap.error("--output 또는 --smoke 중 하나가 필요하다")

    profile = load_profile(args.profile)
    if profile.kind == "kjn":
        return run_kjn(args, profile, here, output, report_path)
    for opt in ("images", "toc_pages", "transplant"):
        if getattr(args, opt):
            ap.error("--%s는 김정년 양식 프로파일에서만 쓴다" % opt.replace("_", "-"))

    template = Template(args.template, profile)
    doc = Document(template, profile)

    files = load_blocks(args.blocks)
    refs = None
    if args.references:
        with open(args.references, encoding="utf-8") as f:
            refs = json.load(f)

    first = True
    refs_done = False
    for path, blocks in files:
        if refs is not None and not refs_done and is_appendix(blocks):
            doc.add_references(refs)
            refs_done = True
        is_survey = any(b["type"] == "h1" and "설문지" in b["text"] for b in blocks)
        first = doc.add_blocks(blocks, first_paragraph=first, survey_cover=is_survey)
    if refs is not None and not refs_done:
        doc.add_references(refs)

    if not args.no_tail:
        doc.add_placeholder_section("부록 3. 시스템 화면 및 LLM 검증 사례 이미지")
        doc.add_placeholder_section("Abstract")

    s1 = doc.build_section1()   # s1_head에 XML 프롤로그와 <hs:sec …> 열림 태그가 포함돼 있다
    s2 = doc.build_section2()
    write_hwpx(template, output, {
        "Contents/header.xml": template.header_xml,
        "Contents/section1.xml": s1,
        "Contents/section2.xml": s2,
    })

    report = build_report(doc, template, args, output)
    if report_path:
        rep_dir = os.path.dirname(os.path.abspath(report_path))
        if rep_dir and not os.path.isdir(rep_dir):
            os.makedirs(rep_dir)
        with open(report_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
    sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
