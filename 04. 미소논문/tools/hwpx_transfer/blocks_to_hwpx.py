# 블록 JSON과 양식 hwpx를 입력받아 서식을 이식한 학위논문 hwpx를 조립하는 스크립트
"""blocks_to_hwpx.py — blocks JSON → 학위논문 hwpx 조립기 (미소 논문 · 260912 양식).

사용 예:
    python "04. 미소논문/tools/hwpx_transfer/blocks_to_hwpx.py" \
        --template "04. 미소논문/00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx" \
        --style-map "04. 미소논문/tools/hwpx_transfer/staging/style_map_miso.json" \
        --front "04. 미소논문/tools/hwpx_transfer/staging/front.blocks.json" \
        --cover "04. 미소논문/tools/hwpx_transfer/staging/cover_miso.json" \
        --blocks ch01.blocks.json … apx2.blocks.json \
        --references "04. 미소논문/tools/hwpx_transfer/staging/references.json" \
        --smoke

설계 요약.
  - 양식 hwpx의 ZIP 엔트리 순서·압축 방식을 그대로 유지하고 Contents/{header,section0,
    section1,section2}.xml을 교체한다. 그림이 있으면 BinData/*.png 엔트리를 뒤에 덧붙이고
    Contents/content.hpf의 manifest에 등록한다.
  - 양식 id(charPr·paraPr·borderFill)와 치수 상수는 **소스에 두지 않는다**. 전부
    style_map.json의 `constants`·`table`·`front_matter`·`cover`에서 읽는다. 양식이 바뀌면
    style_map만 다시 실측하면 된다.
  - section1(전면부)은 목차·표목차·그림목차를 재생성하고, 제목 상자 문단은 양식 XML을
    바이트 그대로 옮긴다. 경계는 `front_matter`의 앵커 idx로 잡고 앵커 문단 텍스트를 검사한다.
  - 감사의 글 본문과 논문개요 본문은 새로 생성한다(감사의 글은 자리표시자, 논문개요는 --front).
  - section0(표지)은 --cover로 지정한 role의 run 텍스트만 바꾸고 run·charPr는 보존한다.
  - section2(본문)는 blocks 순서대로 새로 만든다. 첫 문단에는 양식 section2 첫 문단의
    colPr·secPr·pageNum 제어 블록을 그대로 이식해 페이지 설정을 보존한다.
"""

import argparse
import json
import os
import re
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

# ── 양식과 무관한 고정값 ──────────────────────────────────────────────────────
# 표 셀 텍스트 변환 대상(parse_report 인계 목록).
CELL_LINEBREAK_TOKEN = "<br>"
EMSP_TOKEN = "&emsp;"
EMSP_CHAR = "　"

# 96dpi 가정. 1 inch = 7200 HWPUNIT = 96 px → 1 px = 75 HWPUNIT.
PX_TO_HWPUNIT = 75
# 그림 기본 폭은 본문 줄 폭(LINE_W)의 90%까지만 쓴다.
IMAGE_WIDTH_RATIO = 0.90

# 본문이 아니라 미확정 자리·인용·그림 지시·작성 가이드임을 나타내는 마커. 대괄호 전부가
# 아니라 이 여섯 접두사만 판정하며 콜론·줄표 등 접두사 뒤 구분 문자는 제한하지 않는다.
GUIDE_MARKER_RE = re.compile(
    r"\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED|작성 가이드)[^\]]*\]"
)

XML_PROLOG = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

# style_map.constants 에서 반드시 있어야 하는 키(없으면 조립을 멈춘다).
REQUIRED_CONSTANTS = (
    "TABLE_WIDTH", "ROW_MIN_H", "LINE_W",
    "REF_TITLE", "REF_CATEGORY", "REF_ENTRY", "APPENDIX_TITLE",
    "BODY_BOLD_CHAR", "CELL_BOLD_CHAR",
    "BLANK_CHAR", "TOC_BLANK_CHAR", "TOC_ENTRY_CHAR",
    "BORDER_INNER", "BORDER_LEFT_EDGE", "BORDER_RIGHT_EDGE", "BORDER_CAPTION_ROW",
)
REQUIRED_FRONT_MATTER = (
    "s1_toc_title_idx", "s1_lot_title_idx", "s1_lof_title_idx",
    "s1_thanks_range", "s1_abstract_range", "abstract_body", "thanks_body",
)

# 전면부 앵커 문단이 시작해야 하는 텍스트(공백을 접어 비교한다).
FRONT_ANCHOR_TEXT = {
    "s1_toc_title_idx": "목 차",
    "s1_lot_title_idx": "표 목 차",
    "s1_lof_title_idx": "그 림 목 차",
    "s1_thanks_range": "감사의 글",
    "s1_abstract_range": "논 문 개 요",
}
# section2 첫 문단이 시작해야 하는 텍스트.
SEC2_FIRST_ANCHOR = "제1장"

# 감사의 글·영문초록 자리표시자(본문이 아니라 마커이므로 빨갛게 출력된다).
THANKS_PLACEHOLDER = "[확정 필요: 감사의 글 작성]"
THANKS_DATE_TEXT = "2026 년  월"
THANKS_NAME_TEXT = "김 미 소"
ABSTRACT_PLACEHOLDER = "[확정 필요: 영문초록 작성]"

# 양식(윤혁 논문) 부록의 설문 틀을 찾는 텍스트 앵커. 문단 idx는 양식이 바뀌면 밀리므로 쓰지 않는다.
SURVEY_ANCHORS = {
    "cover": "안녕하십니까?",              # 설문지 표지 상자 (2행 3열)
    "partA": "A. 실태조사 대상자 개요",      # 인구통계 상자 (1x1 + 중첩 제목 표)
    "likert": "전혀그렇지않다",              # 리커트 12열 격자
    "labels": "소    속 :",                # 표지 상자 뒤 pp30 라벨 문단
}


class Constants(object):
    """style_map의 상수 묶음. 소스에 양식 id를 남기지 않기 위한 단일 창구."""

    def __init__(self, style_map):
        const = style_map.get("constants")
        if not isinstance(const, dict):
            raise SystemExit("style_map에 constants 블록이 없다 — 양식 id 외부화 계약 위반")
        missing = [key for key in REQUIRED_CONSTANTS if const.get(key) in (None, "")]
        if missing:
            raise SystemExit("style_map.constants에 필수 키가 없다: %s" % ", ".join(missing))

        self.raw = const
        self.TABLE_WIDTH = int(const["TABLE_WIDTH"])
        self.ROW_MIN_H = int(const["ROW_MIN_H"])
        self.LINE_W = int(const["LINE_W"])
        self.REF_TITLE = dict(const["REF_TITLE"])
        self.REF_CATEGORY = dict(const["REF_CATEGORY"])
        self.REF_ENTRY = dict(const["REF_ENTRY"])
        self.APPENDIX_TITLE = dict(const["APPENDIX_TITLE"])
        self.BODY_BOLD_CHAR = str(const["BODY_BOLD_CHAR"])
        self.CELL_BOLD_CHAR = str(const["CELL_BOLD_CHAR"])
        self.H4_FALLBACK_CHAR = str(const.get("H4_FALLBACK_CHAR") or self.BODY_BOLD_CHAR)
        self.BLANK_CHAR = str(const["BLANK_CHAR"])
        self.TOC_BLANK_CHAR = str(const["TOC_BLANK_CHAR"])
        self.TOC_ENTRY_CHAR = str(const["TOC_ENTRY_CHAR"])
        self.BORDER_INNER = str(const["BORDER_INNER"])
        self.BORDER_LEFT_EDGE = str(const["BORDER_LEFT_EDGE"])
        self.BORDER_RIGHT_EDGE = str(const["BORDER_RIGHT_EDGE"])
        self.BORDER_CAPTION_ROW = str(const["BORDER_CAPTION_ROW"])
        self.RED_CHAR_BY_BASE = {
            str(k): str(v) for k, v in (const.get("RED_CHAR_BY_BASE") or {}).items()
        }
        self.CHAR_HEIGHTS = {
            str(k): int(v) for k, v in (const.get("CHAR_HEIGHTS") or {}).items()
        }

        table = style_map.get("table") or {}
        self.notes = []
        # 표 안 캡션 행 서식 — table 쪽 키를 먼저 보고, 없으면 constants, 그것도 없으면 일반 셀 서식.
        caption_row = table.get("caption_row") or {}
        self.CAPTION_ROW_PARAPR = str(
            caption_row.get("paraPrIDRef")
            or table.get("caption_paraPr")
            or const.get("TABLE_CAPTION_PARAPR")
            or table.get("cell_paraPr", "")
        )
        self.CAPTION_ROW_CHAR = str(
            caption_row.get("charPrIDRef")
            or table.get("caption_charPr")
            or const.get("TABLE_CAPTION_CHAR")
            or table.get("cell_charPr", "")
        )
        if caption_row.get("borderFillIDRef"):
            self.BORDER_CAPTION_ROW = str(caption_row["borderFillIDRef"])
        if not self.CAPTION_ROW_PARAPR or not self.CAPTION_ROW_CHAR:
            raise SystemExit("표 캡션 행 서식(table.caption_paraPr/caption_charPr)을 찾지 못했다")
        # 표 셀 문단의 styleIDRef. 양식은 바탕글 스타일을 쓰지만 id는 양식마다 다를 수 있다.
        self.CELL_STYLE = str(
            table.get("cell_style")
            or caption_row.get("styleIDRef")
            or const.get("CELL_STYLE")
            or (style_map.get("body") or {}).get("styleIDRef", "")
        )
        if not self.CELL_STYLE:
            raise SystemExit("표 셀 문단의 styleIDRef(table.cell_style)를 찾지 못했다")
        if not (caption_row.get("paraPrIDRef") or table.get("caption_paraPr")
                or const.get("TABLE_CAPTION_PARAPR")):
            self.notes.append(
                "표 캡션 행 서식이 style_map에 없어 일반 셀 서식(paraPr %s · charPr %s)으로 대체했다."
                % (self.CAPTION_ROW_PARAPR, self.CAPTION_ROW_CHAR)
            )


# ── XML 조각 생성 ─────────────────────────────────────────────────────────────
def esc(text):
    """hp:t에 넣을 텍스트 — &emsp; 토큰을 전각 공백으로 바꾼 뒤 XML 이스케이프한다."""
    text = text.replace(EMSP_TOKEN, EMSP_CHAR)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def unesc(text):
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def collapse(text):
    return re.sub(r"\s+", " ", text or "").strip()


def strip_linesegarray(xml_text):
    """레이아웃 캐시 제거. 텍스트 길이가 바뀐 문단은 캐시를 지워야 한글이 재계산한다."""
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", xml_text, flags=re.S)


def png_size(path):
    """PNG IHDR에서 (폭, 높이) 픽셀을 읽는다. 표준 라이브러리만 쓴다."""
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise SystemExit("PNG 파일이 아니거나 IHDR을 찾지 못했다: %s" % path)
    width, height = struct.unpack(">II", head[16:24])
    if width <= 0 or height <= 0:
        raise SystemExit("PNG 크기가 비정상이다: %s (%dx%d)" % (path, width, height))
    return width, height


class IdGen(object):
    """문단·표·그림 id 발급기. 양식이 쓰는 값 범위(2147483648~)에서 고유하게 증가시킨다."""

    def __init__(self, start=2147483648):
        self._n = start

    def next(self):
        self._n += 1
        return self._n


class Assembler(object):
    def __init__(self, style_map, const, ids, red_char_pr=None):
        self.sm = style_map
        self.c = const
        self.ids = ids
        self.red_char_pr = red_char_pr

    def lineseg(self, height, horzsize=None):
        """레이아웃 캐시 linesegarray 1줄. 현재 조립기는 캐시를 내보내지 않는다(한글이 계산)."""
        h = int(height)
        horz = self.c.LINE_W if horzsize is None else int(horzsize)
        return (
            '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="%d" '
            'textheight="%d" baseline="%d" spacing="%d" horzpos="0" horzsize="%d" '
            'flags="393216"/></hp:linesegarray>'
            % (h, h, round(h * 0.85), round(h * 0.70), horz)
        )

    def height_of(self, char_pr):
        return self.c.CHAR_HEIGHTS.get(str(char_pr), 1100)

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
        # lineseg 1줄 근사값을 넣으면 한글 PDF 변환이 재계산 없이 그대로 신뢰해 여러 줄
        # 문단이 한 줄에 겹쳐 찍힌다(2026-07-25 렌더 실측). 생략하면 한글이 계산한다.
        return (
            '<hp:p id="%d" paraPrIDRef="%s" styleIDRef="%s" pageBreak="%d" '
            'columnBreak="0" merged="0">%s</hp:p>'
            % (self.ids.next(), para_pr, style, 1 if page_break else 0, runs_xml)
        )

    def text_para(self, spec, text, page_break=False, prefix=""):
        run = self.marker_aware_runs(prefix + text, spec["char"])
        return self.para(spec["para"], spec["style"], run, spec["char"], page_break)

    def red_of(self, char_pr):
        """본문 charPr의 빨간 짝. 가이드 문단(문단 전체 빨강)에 쓴다."""
        if self.red_char_pr is None:
            raise RuntimeError("빨간 charPr 공급자가 설정되지 않았다")
        return self.red_char_pr(str(char_pr))

    def runs_para(self, spec, runs, page_break=False, prefix="", guide=False):
        """runs=[{text, bold}] 를 볼드 여부에 따라 charPr을 나눠 한 문단으로 만든다.

        guide=True(원고의 `> [작성 가이드] …` 인용구)면 본문이 아니라 집필 지시이므로
        문단 전체를 빨간 글자로 낸다 — 마커 정규식과는 별개의 경로다.
        """
        parts = []
        for i, r in enumerate(runs):
            body = (prefix if i == 0 else "") + r.get("text", "")
            char = self.c.BODY_BOLD_CHAR if r.get("bold") else spec["char"]
            if guide:
                char = self.red_of(char)
            parts.append(self.marker_aware_runs(body, char))
        if not parts:
            parts.append('<hp:run charPrIDRef="%s"/>' % spec["char"])
        return self.para(spec["para"], spec["style"], "".join(parts), spec["char"], page_break)

    def blank(self, char=None):
        char = self.c.BLANK_CHAR if char is None else char
        run = '<hp:run charPrIDRef="%s"/>' % char
        body = self.sm["body"]
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run, char)

    # ── 그림 ──────────────────────────────────────────────────────────────
    def image_para(self, spec, binary_item_id, width, height):
        """<hp:pic> 문단. 필수 자식이 하나라도 빠지면 한글이 크래시한다."""
        pic_id = self.ids.next()
        inst_id = self.ids.next()
        cx, cy = width // 2, height // 2
        pic = (
            '<hp:pic id="%d" zOrder="0" numberingType="PICTURE" '
            'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
            'href="" groupLevel="0" instid="%d" reverse="0">'
            '<hp:offset x="0" y="0"/>'
            '<hp:orgSz width="%d" height="%d"/>'
            '<hp:curSz width="%d" height="%d"/>'
            '<hp:flip horizontal="0" vertical="0"/>'
            '<hp:rotationInfo angle="0" centerX="%d" centerY="%d" rotateimage="0"/>'
            '<hp:renderingInfo>'
            '<hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
            '<hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
            '<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
            '</hp:renderingInfo>'
            '<hc:img binaryItemIDRef="%s" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
            '<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="%d" y="0"/>'
            '<hc:pt2 x="%d" y="%d"/><hc:pt3 x="0" y="%d"/></hp:imgRect>'
            '<hp:imgClip left="0" right="%d" top="0" bottom="%d"/>'
            '<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
            '<hp:imgDim dimwidth="%d" dimheight="%d"/>'
            '<hp:effects/>'
            '<hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" heightRelTo="ABSOLUTE" protect="0"/>'
            '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
            'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" '
            'horzAlign="CENTER" vertOffset="0" horzOffset="0"/>'
            '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
            '</hp:pic>'
            % (pic_id, inst_id, width, height, width, height, cx, cy, binary_item_id,
               width, width, height, height, width, height, width, height, width, height)
        )
        run = '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (spec["char"], pic)
        return self.para(spec["para"], spec["style"], run, spec["char"])

    # ── 표 ────────────────────────────────────────────────────────────────
    def column_widths(self, ncols):
        """본문 폭을 열 수로 균등 분할하되 합이 표 폭과 정확히 일치하게 나머지를 마지막 열에 준다."""
        total = self.c.TABLE_WIDTH
        base = total // ncols
        widths = [base] * (ncols - 1) + [total - base * (ncols - 1)]
        assert sum(widths) == total
        return widths

    def border_fill(self, col, ncols):
        """좌우 개방형 테두리: 왼쪽 끝·오른쪽 끝은 바깥선 없는 borderFill, 내부는 사방 실선."""
        if ncols == 1:
            return self.c.BORDER_INNER
        if col == 0:
            return self.c.BORDER_LEFT_EDGE
        if col == ncols - 1:
            return self.c.BORDER_RIGHT_EDGE
        return self.c.BORDER_INNER

    def cell_paragraphs(self, text, para_pr, char_pr, width):
        """셀 텍스트를 문단 XML로. <br>은 셀 안 별도 문단으로 나눈다(&emsp; 변환은 esc가 담당)."""
        lines = text.split(CELL_LINEBREAK_TOKEN)
        pad = self.sm["table"]["cell_padding"]
        inner = max(width - (int(pad["left"]) + int(pad["right"])), 1000)
        out = []
        for line in lines:
            if line:
                run = self.marker_aware_runs(line, char_pr)
            else:
                run = '<hp:run charPrIDRef="%s"/>' % char_pr
            out.append(self.para(para_pr, self.c.CELL_STYLE, run, char_pr, horzsize=inner))
        return "".join(out), len(lines)

    def cell(self, text, col, row, width, ncols, col_span=1, border=None,
             para_pr=None, char_pr=None, height=None):
        sm_tbl = self.sm["table"]
        para_pr = para_pr or sm_tbl["cell_paraPr"]
        char_pr = char_pr or sm_tbl["cell_charPr"]
        border = border or self.border_fill(col, ncols)
        height = self.c.ROW_MIN_H if height is None else height
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
            % (border, paras, col, row, col_span, width,
               max(height, self.c.ROW_MIN_H * nlines),
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
            # 캡션 행: 전체 열 병합 + 아래만 실선인 borderFill (양식 실측, style_map 제공)
            trs.append("<hp:tr>%s</hp:tr>" % self.cell(
                caption, 0, row_idx, self.c.TABLE_WIDTH, ncols, col_span=ncols,
                border=self.c.BORDER_CAPTION_ROW,
                para_pr=self.c.CAPTION_ROW_PARAPR, char_pr=self.c.CAPTION_ROW_CHAR))
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
                self.c.TABLE_WIDTH, self.c.ROW_MIN_H * row_idx,
                pos["treatAsChar"], pos["flowWithText"], pos["vertRelTo"], pos["horzRelTo"],
                out_m["left"], out_m["right"], out_m["top"], out_m["bottom"],
                in_m["left"], in_m["right"], in_m["top"], in_m["bottom"],
                "".join(trs),
            )
        )
        # 표는 문단 run 안에 treatAsChar=1로 인라인 배치된다(양식 실측: 절 제목 charPr, 표 뒤 빈 hp:t).
        body = self.sm["body"]
        run = '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (
            self.sm["h2_section"]["charPrIDRef"], tbl)
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run,
                         body["charPrIDRef"], horzsize=self.c.LINE_W)

    # ── 설문 양식 클론 ─────────────────────────────────────────────────────
    # 설문 표 3종은 새로 만들지 않는다. 양식(윤혁 논문) 부록의 표 XML을 통째로 복제해
    # 텍스트만 갈아끼우고, 행 수가 달라지는 곳만 cellAddr·cellSz·rowCnt를 다시 계산한다.
    # 격자 정합(행마다 cellSz.width 합 = 표 폭, colAddr/colSpan이 열 격자와 일치)이
    # 깨지면 한글이 행을 재배치하므로 폭은 전부 열 격자에서 유도한다.

    @staticmethod
    def _sample_chars(para_xml):
        """문단에서 쓰인 charPrIDRef를 등장 순서대로(중복 제거) 돌려준다."""
        seen = []
        for cid in re.findall(r'<hp:run charPrIDRef="(\d+)"', para_xml):
            if cid not in seen:
                seen.append(cid)
        return seen

    def _clone_para(self, sample, runs_xml):
        """sample 문단의 paraPr·styleIDRef를 그대로 쓰고 run만 갈아끼운다(lineseg 제거)."""
        open_tag = re.match(r"<hp:p\b[^>]*>", sample).group(0)
        open_tag = re.sub(r'\sid="[^"]*"', ' id="%d"' % self.ids.next(), open_tag, count=1)
        if not runs_xml:
            chars = self._sample_chars(sample)
            runs_xml = ['<hp:run charPrIDRef="%s"/>' % (chars[0] if chars else self.c.BLANK_CHAR)]
        return open_tag + "".join(runs_xml) + "</hp:p>"

    def _text_para_like(self, sample, runs, char, bold_char=None):
        """runs=[{text,bold}] 또는 문자열 하나를 sample 문단 서식으로 만든다."""
        if isinstance(runs, str):
            runs = [{"text": runs}]
        parts = []
        for r in runs:
            text = r.get("text", "")
            if text == "":
                continue
            use = bold_char if (r.get("bold") and bold_char) else char
            parts.append(self.marker_aware_runs(text, use))
        return self._clone_para(sample, parts)

    @staticmethod
    def _wrap_lines(text, horzsize, char_h, hint=None):
        """셀·문단 폭 안에서 몇 줄이 되는지.

        한 줄에 들어가는 글자수는 양식 문단의 두 번째 lineseg `textpos`(=첫 줄 글자수)를
        실측 힌트로 쓴다. 힌트가 없으면 줄 폭 ÷ (글자 높이 × 0.9)로 근사한다.
        """
        per_line = float(hint) if hint else max(horzsize / float((char_h or 1000) * 0.9), 1.0)
        return max(int(-(-display_width(text) // max(per_line, 1.0))), 1)

    def _cell_text(self, tc, texts, char=None, bold_char=None,
                   col=None, row=None, col_span=None, width=None, height=None):
        """셀의 문단을 texts로 갈아끼우고 주소·폭·높이를 조정한다.

        texts 원소는 문자열이거나 runs 목록([{text,bold}])이다. 셀의 첫 문단을 서식
        표본으로 삼아 복제하므로 정렬·글꼴·테두리는 양식 그대로 유지된다.
        """
        prefix, inner, suffix = sublist_body(tc)
        samples = [inner[a:b] for a, b in split_paragraphs(inner)]
        sample = samples[0]
        base_char = char or (self._sample_chars(sample) or [self.c.BLANK_CHAR])[0]
        paras = [self._text_para_like(sample, t, base_char, bold_char) for t in texts] \
            or [self._clone_para(sample, [])]
        out = prefix + "".join(paras) + suffix
        if col is not None or row is not None or col_span is not None:
            out = set_cell_addr(out, col=col, row=row, col_span=col_span)
        if height is not None or width is not None:
            out = set_cell_size(out, height if height is not None else cell_addr(out)[5],
                                width)
        return out

    # ── A. 설문지 표지 상자 ────────────────────────────────────────────────
    def survey_cover_box(self, tpl_para, title_lines, subtitle, body_paras, date_text):
        """양식 표지 상자(2행 3열)에 제목·안내문·연월을 갈아끼운 문단 XML을 만든다."""
        (ta, tb), = tbl_spans(tpl_para)[:1]
        head, tbl, tail = tpl_para[:ta], tpl_para[ta:tb], tpl_para[tb:]
        rows = tr_spans(tbl)
        r0, r1 = tbl[rows[0][0]:rows[0][1]], tbl[rows[1][0]:rows[1][1]]

        # r0 가운데 셀 — 제목 2줄(굵게) + 부제 1줄
        cells0 = [r0[a:b] for a, b in tc_spans(r0)]
        title_tc = cells0[1]
        _, t_inner, _ = sublist_body(title_tc)
        t_samples = [t_inner[a:b] for a, b in split_paragraphs(t_inner)]
        title_char = self._sample_chars(t_samples[0])[0]
        sub_char = self._sample_chars(t_samples[-1])[0]
        t_line_h, t_horz, _, t_char_h = lineseg_metrics(t_samples[0])
        title_lines = list(title_lines)
        new_title = [self._text_para_like(t_samples[0], line, title_char)
                     for line in title_lines]
        new_title.append(self._text_para_like(t_samples[-1], subtitle, sub_char))
        t_rows = sum(self._wrap_lines(x, t_horz, t_char_h)
                    for x in title_lines + [subtitle])
        t_height = max(t_rows * t_line_h + cell_pad(title_tc), self.c.ROW_MIN_H)
        prefix, _, suffix = sublist_body(title_tc)
        title_tc = set_cell_size(prefix + "".join(new_title) + suffix, t_height)
        cells0[1] = title_tc
        cells0[0] = set_cell_size(cells0[0], t_height)
        cells0[2] = set_cell_size(cells0[2], t_height)
        r0 = "<hp:tr>%s</hp:tr>" % "".join(cells0)

        # r1 — 안내문 문단 + 빈 줄 + 연월 + 빈 줄
        cells1 = [r1[a:b] for a, b in tc_spans(r1)]
        body_tc = cells1[0]
        prefix1, b_inner, suffix1 = sublist_body(body_tc)
        b_samples = [b_inner[a:b] for a, b in split_paragraphs(b_inner)]
        body_para_pr = re.search(r'paraPrIDRef="(\d+)"', b_samples[0]).group(1)
        body_group = [p for p in b_samples
                      if re.search(r'paraPrIDRef="(\d+)"', p).group(1) == body_para_pr]
        tail_group = [p for p in b_samples if p not in body_group]
        chars = []
        for p in body_group:
            for cid in self._sample_chars(p):
                if cid not in chars:
                    chars.append(cid)
        body_char = chars[0]
        bold_char = chars[1] if len(chars) > 1 else self.c.BODY_BOLD_CHAR
        blank_body = next((p for p in body_group if "<hp:t>" not in p), body_group[0])
        date_sample = next((p for p in tail_group if "<hp:t>" in p), b_samples[-1])
        blank_date = next((p for p in tail_group if "<hp:t>" not in p), date_sample)
        date_char = self._sample_chars(date_sample)[0]
        b_line_h, b_horz, b_hint, b_char_h = lineseg_metrics(next(
            (p for p in body_group if len(re.findall(r"<hp:lineseg", p)) > 1), body_group[0]))
        d_line_h, _, _, _ = lineseg_metrics(date_sample)

        new_body, nlines = [], 0
        for runs in body_paras:
            new_body.append(self._text_para_like(blank_body if not runs else body_group[0],
                                                 runs, body_char, bold_char))
            text = "".join(r.get("text", "") for r in runs)
            nlines += self._wrap_lines(text, b_horz, b_char_h, b_hint)
        new_body.append(self._clone_para(blank_body, []))
        nlines += 1
        new_body.append(self._text_para_like(date_sample, date_text, date_char))
        new_body.append(self._clone_para(blank_date, []))

        b_height = nlines * b_line_h + 2 * d_line_h + cell_pad(body_tc)
        cells1[0] = set_cell_size(prefix1 + "".join(new_body) + suffix1, b_height)
        r1 = "<hp:tr>%s</hp:tr>" % "".join(cells1)

        body_open = tbl[:rows[0][0]]
        body_open = re.sub(r'(<hp:sz width="\d+" widthRelTo="ABSOLUTE" height=")\d+',
                           r"\g<1>%d" % (t_height + b_height), body_open, count=1)
        out = head + body_open + r0 + r1 + tbl[rows[1][1]:] + tail
        return renumber_ids(strip_linesegarray(out), self.ids)

    @staticmethod
    def _pad_label(label, pad):
        """`소속` → `소    속` 처럼 라벨을 전각 pad칸 폭으로 벌린다(양식 관행).

        빈 칸은 글자 사이 간격에 고르게 나눠 넣는다. 전각 1칸 = 반각 공백 2칸.
        """
        gaps = len(label) - 1
        if gaps <= 0 or len(label) >= pad:
            return label
        total = (pad - len(label)) * 2
        out = []
        for i, ch in enumerate(label):
            if i:
                share = total // gaps + (1 if i <= total % gaps else 0)
                out.append(" " * share)
            out.append(ch)
        return "".join(out)

    def survey_label_para(self, tpl_para, label, value, pad):
        """표지 상자 뒤 pp30 라벨 문단(`소    속 : …`). 양식 문단의 들여쓰기를 그대로 쓴다."""
        char = self._sample_chars(tpl_para)[0]
        indent = re.match(r"\s*", para_plain_text(tpl_para)).group(0)
        text = "%s%s : %s" % (indent, self._pad_label(label, pad), value)
        return renumber_ids(strip_linesegarray(
            self._text_para_like(tpl_para, text, char)), self.ids)

    # ── B. Part A 인구통계 상자 ────────────────────────────────────────────
    def survey_partA_box(self, tpl_para, title, items):
        """양식 인구통계 상자(1×1 + 중첩 제목 표)에 제목·문항을 갈아끼운다.

        items 원소: ("q", 번호, 질문) / ("c", 선택지) / ("p", runs)
        """
        (ta, tb), = tbl_spans(tpl_para)[:1]
        head, tbl, tail = tpl_para[:ta], tpl_para[ta:tb], tpl_para[tb:]
        rows = tr_spans(tbl)
        r0 = tbl[rows[0][0]:rows[0][1]]
        cells = [r0[a:b] for a, b in tc_spans(r0)]
        outer_tc = cells[0]
        prefix, inner, suffix = sublist_body(outer_tc)
        samples = [inner[a:b] for a, b in split_paragraphs(inner)]

        title_para = samples[0]                       # 중첩 제목 표를 담은 문단
        blank_para = samples[1]
        q_sample = next(p for p in samples[2:] if len(self._sample_chars(p)) >= 2)
        c_sample = next(p for p in samples[2:] if len(self._sample_chars(p)) == 1
                        and "<hp:t>" in p)
        num_char = self._sample_chars(q_sample)[0]
        body_char = self._sample_chars(c_sample)[0]
        q_line_h, q_horz, _, q_char_h = lineseg_metrics(c_sample)
        t_line_h, _, _, _ = lineseg_metrics(title_para)
        b_line_h, _, _, _ = lineseg_metrics(blank_para)

        # 중첩 제목 표 — 셀 문단 텍스트만 바꾼다
        (na, nb), = tbl_spans(title_para)[:1]
        nested = title_para[na:nb]
        n_rows = tr_spans(nested)
        n_r0 = nested[n_rows[0][0]:n_rows[0][1]]
        n_cells = [n_r0[a:b] for a, b in tc_spans(n_r0)]
        n_cells[0] = self._cell_text(n_cells[0], [title])
        nested = nested[:n_rows[0][0]] + "<hp:tr>%s</hp:tr>" % "".join(n_cells) \
            + nested[n_rows[0][1]:]
        new_title_para = title_para[:na] + nested + title_para[nb:]
        new_title_para = re.sub(r'(<hp:p\s+id=")[^"]*',
                                r"\g<1>%d" % self.ids.next(), new_title_para, count=1)

        out_paras = [new_title_para, self._clone_para(blank_para, [])]
        nlines = 0
        for item in items:
            if item[0] == "q":
                runs = ['<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>'
                        % (num_char, esc(" %s)" % item[1])),
                        self.marker_aware_runs(" " + item[2], body_char)]
                out_paras.append(self._clone_para(q_sample, runs))
                text = " %s) %s" % (item[1], item[2])
            elif item[0] == "c":
                out_paras.append(self._text_para_like(c_sample, item[1], body_char))
                text = item[1]
            else:
                out_paras.append(self._text_para_like(
                    c_sample, item[1], body_char, self.c.BODY_BOLD_CHAR))
                text = "".join(r.get("text", "") for r in item[1])
            nlines += self._wrap_lines(text, q_horz, q_char_h)

        height = t_line_h + b_line_h + nlines * q_line_h + cell_pad(outer_tc)
        cells[0] = set_cell_size(prefix + "".join(out_paras) + suffix, height)
        r0 = "<hp:tr>%s</hp:tr>" % "".join(cells)
        body_open = tbl[:rows[0][0]]
        body_open = re.sub(r'(<hp:sz width="\d+" widthRelTo="ABSOLUTE" height=")\d+',
                           r"\g<1>%d" % height, body_open, count=1)
        out = head + body_open + r0 + tbl[rows[0][1]:] + tail
        return renumber_ids(strip_linesegarray(out), self.ids)

    # ── C. 리커트 격자 ─────────────────────────────────────────────────────
    def survey_likert(self, tpl_para, var_name, labels, rows, split=None):
        """양식 리커트 12열 격자를 복제해 변수명·척도 라벨·문항 행을 갈아끼운다.

        split=[w1, w2]이면 진술문 열(1열)을 두 열로 쪼개 13열 격자로 만든다
        (7.2 평정 양식). 쪼갠 두 폭의 합은 원래 진술문 열 폭과 같아야 한다.
        """
        (ta, tb), = tbl_spans(tpl_para)[:1]
        head, tbl, tail = tpl_para[:ta], tpl_para[ta:tb], tpl_para[tb:]
        trs = tr_spans(tbl)
        t_r = [tbl[a:b] for a, b in trs]
        shift = 1 if split else 0
        lead = 2 + shift                 # 문항 열(번호+진술문[+설명]) 개수
        scale0 = lead                    # 척도 열이 시작하는 colAddr

        # 열 격자 — 양식 r1(장식 행)에서 개별 열 폭을 그대로 읽는다
        deco = [cell_addr(t_r[1][a:b]) for a, b in tc_spans(t_r[1])]
        unit_w = [d[4] for d in deco]                     # 척도 10열 개별 폭
        item_cells = [t_r[3][a:b] for a, b in tc_spans(t_r[3])]
        num_w = cell_addr(item_cells[0])[4]
        stmt_w = cell_addr(item_cells[1])[4]
        if split:
            if int(split[0]) + int(split[1]) != stmt_w:
                raise SystemExit(
                    "평정 양식 split 합(%d)이 양식 진술문 열 폭(%d)과 다르다 — 격자가 깨진다"
                    % (int(split[0]) + int(split[1]), stmt_w))
            lead_w = [num_w, int(split[0]), int(split[1])]
        else:
            lead_w = [num_w, stmt_w]
        scale_w = [cell_addr(t_r[0][a:b])[4] for a, b in tc_spans(t_r[0])][1:]
        total_w = sum(lead_w) + sum(unit_w)

        # r0 — 변수명 셀 + 척도 라벨 5셀
        c0 = [t_r[0][a:b] for a, b in tc_spans(t_r[0])]
        var_h = cell_addr(c0[0])[5]
        head_h = cell_addr(c0[1])[5]
        c0[0] = self._cell_text(c0[0], [var_name], col=0, row=0, col_span=lead,
                                width=sum(lead_w), height=var_h)
        for i in range(5):
            lines = list(labels[i]) if i < len(labels) else []
            c0[i + 1] = self._cell_text(c0[i + 1], lines or [""],
                                        col=scale0 + 2 * i, row=0, col_span=2,
                                        width=scale_w[i], height=head_h)
        out_rows = ["<hp:tr>%s</hp:tr>" % "".join(c0)]

        # r1·r2 — 눈금 장식 행(텍스트 없음). colAddr만 격자에 맞춰 민다
        for ri in (1, 2):
            cells = [t_r[ri][a:b] for a, b in tc_spans(t_r[ri])]
            moved = []
            for cell in cells:
                col, _, _, _, w, h = cell_addr(cell)
                moved.append(set_cell_addr(cell, col=col + shift, row=ri))
            out_rows.append("<hp:tr>%s</hp:tr>" % "".join(moved))
        r1_h = cell_addr([t_r[1][a:b] for a, b in tc_spans(t_r[1])][1])[5]
        r2_h = cell_addr([t_r[2][a:b] for a, b in tc_spans(t_r[2])][0])[5]
        heights = [head_h, r1_h, r2_h]

        # 문항 행 — 첫 문항 행을 표본으로 복제하고, 마지막 행만 양식의 마지막 행(아래 테두리)
        last_cells = [t_r[-1][a:b] for a, b in tc_spans(t_r[-1])]
        # 진술문 열의 "한 줄에 몇 글자" 힌트 — 양식 문항 행 중 두 줄 이상인 것에서 실측한다
        stmt_samples = [sublist_body([t_r[ri][a:b] for a, b in tc_spans(t_r[ri])][1])[1]
                        for ri in range(3, len(t_r))]
        stmt_src = next((p for p in stmt_samples
                         if len(re.findall(r"<hp:lineseg", p)) > 1), stmt_samples[0])
        stmt_line_h, stmt_horz, stmt_hint, stmt_char_h = lineseg_metrics(stmt_src)
        min_item_h = cell_addr(item_cells[0])[5]
        for ri, data in enumerate(rows):
            src = last_cells if ri == len(rows) - 1 else item_cells
            row_idx = 3 + ri
            texts = list(data[1:1 + len(lead_w) - 1])
            lines = 1
            for k, text in enumerate(texts):
                horz = int(stmt_horz * lead_w[k + 1] / float(stmt_w))
                hint = int(stmt_hint * lead_w[k + 1] / float(stmt_w)) if stmt_hint else None
                lines = max(lines, self._wrap_lines(text, horz, stmt_char_h, hint))
            height = max(lines * stmt_line_h + (min_item_h - stmt_line_h), min_item_h)
            cells = [self._cell_text(src[0], [data[0]], col=0, row=row_idx,
                                     col_span=1, width=lead_w[0], height=height)]
            for k, text in enumerate(texts):
                char = self.c.CELL_BOLD_CHAR if (split and k == 0) else None
                cells.append(self._cell_text(src[1], [text], char=char,
                                             col=k + 1, row=row_idx, col_span=1,
                                             width=lead_w[k + 1], height=height))
            for k in range(5):
                cells.append(self._cell_text(src[2 + k], [self.SCALE_MARKS[k]],
                                             col=scale0 + 2 * k, row=row_idx,
                                             col_span=2, width=scale_w[k], height=height))
            out_rows.append("<hp:tr>%s</hp:tr>" % "".join(cells))
            heights.append(height)

        body_open = tbl[:trs[0][0]]
        body_open = re.sub(r'\browCnt="\d+"', 'rowCnt="%d"' % (3 + len(rows)), body_open, count=1)
        body_open = re.sub(r'\bcolCnt="\d+"', 'colCnt="%d"' % (12 + shift), body_open, count=1)
        body_open = re.sub(r'(<hp:sz width=")\d+', r"\g<1>%d" % total_w, body_open, count=1)
        body_open = re.sub(r'(<hp:sz width="\d+" widthRelTo="ABSOLUTE" height=")\d+',
                           r"\g<1>%d" % sum(heights), body_open, count=1)
        out = head + body_open + "".join(out_rows) + tbl[trs[-1][1]:] + tail
        return renumber_ids(strip_linesegarray(out), self.ids)

    SCALE_MARKS = ("①", "②", "③", "④", "⑤")


# ── 양식 hwpx 해체 ────────────────────────────────────────────────────────────
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


def run_text_spans(para_xml):
    """문단 XML 안 <hp:run>의 첫 <hp:t> 텍스트 구간 목록.

    run 순번은 표 셀 안 run까지 **문서 순서로 평탄하게** 세되, 빈 self-closing run
    (<hp:run …/>)은 빼고 센다 — analysis/section*_paras.json 덤프의 runs 순번과 같은 규칙이다.
    각 원소는 (텍스트 시작, 텍스트 끝) 이거나, 텍스트가 없는 run이면 None이다.
    """
    opens = [m for m in re.finditer(r"<hp:run\b[^>]*>", para_xml)
             if not m.group(0).endswith("/>")]
    spans = []
    for i, m in enumerate(opens):
        region_start = m.end()
        region_end = opens[i + 1].start() if i + 1 < len(opens) else len(para_xml)
        t = re.search(r"<hp:t>(.*?)</hp:t>", para_xml[region_start:region_end], re.S)
        if t is None:
            spans.append(None)
        else:
            spans.append((region_start + t.start(1), region_start + t.end(1)))
    return spans


def para_plain_text(para_xml):
    """문단 XML의 모든 <hp:t> 텍스트를 이어 붙인다(표 셀 포함)."""
    return "".join(unesc(t) for t in re.findall(r"<hp:t>(.*?)</hp:t>", para_xml, re.S))


# ── 설문 양식 클론용 XML 구조 헬퍼 ────────────────────────────────────────────
# 양식의 설문 틀은 표 안에 표가 들어가는 중첩 구조라, `</hp:tbl>` 첫 등장으로 자르면
# 안쪽 표에서 끊긴다. 아래 함수들은 모두 **깊이를 세어** 제 층의 요소만 잘라낸다.
def tbl_spans(xml_text):
    """최상위 hp:tbl 요소의 (시작, 끝) 목록."""
    spans, depth, stack = [], 0, []
    for m in re.finditer(r"<hp:tbl(?=[\s/>])[^>]*>|</hp:tbl>", xml_text):
        if m.group(0).startswith("</"):
            depth -= 1
            start = stack.pop()
            if depth == 0:
                spans.append((start, m.end()))
        else:
            if m.group(0).endswith("/>"):
                continue
            stack.append(m.start())
            depth += 1
    return spans


def tr_spans(tbl_xml):
    """표 XML 안에서 **이 표에 직접 속한** hp:tr의 (시작, 끝) 목록(중첩 표의 행은 뺀다)."""
    spans, tdepth, rdepth, start = [], 0, 0, None
    for m in re.finditer(r"<hp:tbl(?=[\s/>])[^>]*>|</hp:tbl>|<hp:tr>|</hp:tr>", tbl_xml):
        token = m.group(0)
        if token.startswith("<hp:tbl"):
            if not token.endswith("/>"):
                tdepth += 1
        elif token == "</hp:tbl>":
            tdepth -= 1
        elif token == "<hp:tr>":
            if tdepth == 1 and rdepth == 0:
                start = m.start()
            rdepth += 1
        else:
            rdepth -= 1
            if tdepth == 1 and rdepth == 0:
                spans.append((start, m.end()))
    return spans


def tc_spans(tr_xml):
    """행 XML 안에서 이 행에 직접 속한 hp:tc의 (시작, 끝) 목록(중첩 표의 셀은 뺀다)."""
    spans, tdepth, cdepth, start = [], 0, 0, None
    for m in re.finditer(r"<hp:tbl(?=[\s/>])[^>]*>|</hp:tbl>|<hp:tc(?=[\s/>])[^>]*>|</hp:tc>",
                         tr_xml):
        token = m.group(0)
        if token.startswith("<hp:tbl"):
            if not token.endswith("/>"):
                tdepth += 1
        elif token == "</hp:tbl>":
            tdepth -= 1
        elif token.startswith("<hp:tc"):
            if tdepth == 0 and cdepth == 0:
                start = m.start()
            cdepth += 1
        else:
            cdepth -= 1
            if tdepth == 0 and cdepth == 0:
                spans.append((start, m.end()))
    return spans


def cell_addr(tc_xml):
    """셀 자신의 (colAddr, rowAddr, colSpan, rowSpan, width, height).

    중첩 표가 있으면 안쪽 셀의 값이 먼저 나오므로 **마지막** 항목이 자기 값이다.
    """
    addrs = re.findall(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', tc_xml)
    spans = re.findall(r'<hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/>', tc_xml)
    sizes = re.findall(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', tc_xml)
    return (int(addrs[-1][0]), int(addrs[-1][1]), int(spans[-1][0]), int(spans[-1][1]),
            int(sizes[-1][0]), int(sizes[-1][1]))


def sublist_body(tc_xml):
    """셀의 hp:subList 안쪽 문단 영역을 (앞부분, 안쪽, 뒷부분)으로 나눈다."""
    m = re.search(r"<hp:subList\b[^>]*>", tc_xml)
    if not m:
        raise SystemExit("표 셀에서 hp:subList를 찾지 못했다")
    end = tc_xml.rindex("</hp:subList>")
    return tc_xml[:m.end()], tc_xml[m.end():end], tc_xml[end:]


def cell_pad(tc_xml):
    """셀 자신의 위·아래 안쪽 여백 합. 클론 셀 높이를 잴 때 줄 높이에 더한다."""
    margins = re.findall(r'<hp:cellMargin left="\d+" right="\d+" top="(\d+)" bottom="(\d+)"/>',
                         tc_xml)
    if not margins:
        return 0
    return int(margins[-1][0]) + int(margins[-1][1])


def set_cell_size(tc_xml, height, width=None):
    """셀 자신의 cellSz를 바꾼다(중첩 표 셀은 건드리지 않으므로 마지막 것만 교체)."""
    matches = list(re.finditer(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', tc_xml))
    last = matches[-1]
    new_w = last.group(1) if width is None else str(int(width))
    replacement = '<hp:cellSz width="%s" height="%d"/>' % (new_w, int(height))
    return tc_xml[:last.start()] + replacement + tc_xml[last.end():]


def set_cell_addr(tc_xml, col=None, row=None, col_span=None):
    """셀 자신의 cellAddr/cellSpan을 바꾼다(마지막 것이 자기 값)."""
    out = tc_xml
    if col is not None or row is not None:
        matches = list(re.finditer(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', out))
        last = matches[-1]
        c = last.group(1) if col is None else str(int(col))
        r = last.group(2) if row is None else str(int(row))
        out = (out[:last.start()] + '<hp:cellAddr colAddr="%s" rowAddr="%s"/>' % (c, r)
               + out[last.end():])
    if col_span is not None:
        matches = list(re.finditer(r'<hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/>', out))
        last = matches[-1]
        out = (out[:last.start()]
               + '<hp:cellSpan colSpan="%d" rowSpan="%s"/>' % (int(col_span), last.group(2))
               + out[last.end():])
    return out


def first_lineseg(para_xml):
    """문단 첫 lineseg의 속성 dict. 줄 높이·줄 폭·글자수 힌트를 양식에서 실측하는 창구."""
    m = re.search(r"<hp:lineseg\b[^>]*/>", para_xml)
    if not m:
        return {}
    return {k: int(v) for k, v in re.findall(r'(\w+)="(-?\d+)"', m.group(0))}


def lineseg_metrics(para_xml):
    """(줄 높이, 줄 폭, 첫 줄 글자수 힌트, 글자 높이).

    줄 높이 = vertsize + spacing(줄 간격 포함), 글자 높이 = vertsize(줄바꿈 계산용).
    힌트는 두 번째 lineseg의 textpos — 그 폭에서 한 줄에 실제로 들어간 글자 수다.
    """
    segs = re.findall(r"<hp:lineseg\b[^>]*/>", para_xml)
    if not segs:
        return 0, 0, None, 1000
    first = {k: int(v) for k, v in re.findall(r'(\w+)="(-?\d+)"', segs[0])}
    char_h = first.get("vertsize", 1000) or 1000
    line_h = char_h + first.get("spacing", 0)
    horz = first.get("horzsize", 0)
    hint = None
    if len(segs) > 1:
        second = {k: int(v) for k, v in re.findall(r'(\w+)="(-?\d+)"', segs[1])}
        hint = second.get("textpos") or None
    return line_h, horz, hint, char_h


def display_width(text):
    """줄바꿈 계산용 표시 폭 — 전각(한글·기호·전각공백)은 1, 나머지는 0.5로 센다."""
    total = 0.0
    for ch in text:
        total += 1.0 if (ord(ch) > 0x1100 and ch != " ") else 0.5
    return total


def renumber_ids(xml_text, ids):
    """클론한 XML의 hp:p·hp:tbl id를 전부 새로 발급한다(양식 id 중복 방지)."""
    def sub(match):
        return '%s id="%d"' % (match.group(1), ids.next())
    return re.sub(r'(<hp:p|<hp:tbl)\s+id="[^"]*"', sub, xml_text)


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

    def __init__(self, path, style_map, const):
        self.path = path
        self.sm = style_map
        self.c = const
        with zipfile.ZipFile(path) as z:
            self.infos = z.infolist()
            self.raw = {i.filename: z.read(i.filename) for i in self.infos}
        self.header_xml = self.raw["Contents/header.xml"].decode("utf-8")
        self.s0 = self.raw["Contents/section0.xml"].decode("utf-8")
        self.s1 = self.raw["Contents/section1.xml"].decode("utf-8")
        self.s2 = self.raw["Contents/section2.xml"].decode("utf-8")
        self.content_hpf = self.raw["Contents/content.hpf"].decode("utf-8")
        self.s1_paras = split_paragraphs(self.s1)
        self.s2_paras = split_paragraphs(self.s2)
        self.cover_replacements = []   # (section0_idx, run_ordinal, role, old, new)
        self._prepare_char_prs()
        self._slice_front_matter()
        self._slice_sec2_controls()
        self._slice_survey_templates()

    # ── 설문 양식(section2 부록) 슬라이스 ────────────────────────────────
    def _slice_survey_templates(self):
        """양식 부록의 설문 틀 3종 + 라벨 문단을 **텍스트 앵커**로 잘라 보관한다.

        idx를 박으면 양식이 조금만 바뀌어도 엉뚱한 문단을 복제하므로 앵커로 찾는다.
        찾은 것은 최상위 hp:p 전체(표를 감싼 run 포함)이며, 클론 시 텍스트만 바꾼다.
        """
        found = {}
        for key, anchor in SURVEY_ANCHORS.items():
            for start, end in self.s2_paras:
                para = self.s2[start:end]
                if anchor in para_plain_text(para):
                    if key != "labels" and "<hp:tbl" not in para:
                        continue
                    found[key] = para
                    break
        missing = [key for key in SURVEY_ANCHORS if key not in found]
        if missing:
            raise SystemExit(
                "양식 section2에서 설문 틀을 찾지 못했다: %s (앵커: %s)"
                % (", ".join(missing), ", ".join(SURVEY_ANCHORS[k] for k in missing))
            )
        self.survey = found

    # ── charPr(빨간 마커) ────────────────────────────────────────────────
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
        # style_map이 명시한 짝(RED_CHAR_BY_BASE)을 먼저 신뢰한다. 양식에 실재하는 id만 받는다.
        self._red_char_by_base = {}
        for base, red in self.c.RED_CHAR_BY_BASE.items():
            if base in char_prs and red in char_prs:
                self._red_char_by_base[base] = red
        self._char_pr_count = len(char_prs)
        self._next_char_pr_id = max(int(char_id) for char_id in char_prs) + 1
        self.cloned_red_char_prs = []

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
        self.cloned_red_char_prs.append((base_char_pr_id, new_id))
        return new_id

    # ── 전면부(section1) 슬라이스 ────────────────────────────────────────
    def _para(self, xml_text, spans, idx):
        a, b = spans[idx]
        return xml_text[a:b]

    def _check_anchor(self, key, idx):
        text = collapse(para_plain_text(self._para(self.s1, self.s1_paras, idx)))
        want = FRONT_ANCHOR_TEXT[key]
        if not text.startswith(want):
            raise SystemExit(
                "전면부 앵커 불일치: %s(section1 p%d)는 %r로 시작해야 하는데 %r이다"
                % (key, idx, want, text[:40])
            )

    def _slice_front_matter(self):
        fm = self.sm.get("front_matter")
        if not isinstance(fm, dict):
            raise SystemExit("style_map에 front_matter 블록이 없다 — 전면부 앵커 계약 위반")
        missing = [key for key in REQUIRED_FRONT_MATTER if fm.get(key) in (None, "")]
        if missing:
            raise SystemExit("style_map.front_matter에 필수 키가 없다: %s" % ", ".join(missing))

        s1, ps = self.s1, self.s1_paras
        toc_idx = int(fm["s1_toc_title_idx"])
        lot_idx = int(fm["s1_lot_title_idx"])
        lof_idx = int(fm["s1_lof_title_idx"])
        thanks_a, thanks_b = (int(v) for v in fm["s1_thanks_range"])
        abs_a, abs_b = (int(v) for v in fm["s1_abstract_range"])
        for idx in (toc_idx, lot_idx, lof_idx, thanks_a, thanks_b, abs_a, abs_b):
            if not (0 <= idx < len(ps)):
                raise SystemExit(
                    "front_matter 앵커 idx %d가 section1 문단 범위(0~%d) 밖이다"
                    % (idx, len(ps) - 1))
        self._check_anchor("s1_toc_title_idx", toc_idx)
        self._check_anchor("s1_lot_title_idx", lot_idx)
        self._check_anchor("s1_lof_title_idx", lof_idx)
        self._check_anchor("s1_thanks_range", thanks_a)
        self._check_anchor("s1_abstract_range", abs_a)

        self.s1_head = s1[: ps[toc_idx][0]]             # 프롤로그 + <hs:sec …> (secPr는 첫 문단 안)
        self.toc_title = self._para(s1, ps, toc_idx)    # 목차 제목 상자(secPr 포함) — 바이트 보존
        self.lot_title = set_page_break(self._para(s1, ps, lot_idx))
        self.lof_title = set_page_break(self._para(s1, ps, lof_idx))
        self.thanks_title = set_page_break(self._para(s1, ps, thanks_a))
        self.abstract_title = set_page_break(self._para(s1, ps, abs_a))
        self.front_matter_idx = {
            "toc": toc_idx, "lot": lot_idx, "lof": lof_idx,
            "thanks": [thanks_a, thanks_b], "abstract": [abs_a, abs_b],
        }
        tail = s1[ps[abs_b][1]:]
        if tail.strip() != "</hs:sec>":
            raise SystemExit("양식 section1 말미가 예상과 다르다: %r" % tail[:80])

    def _slice_sec2_controls(self):
        p0 = self._para(self.s2, self.s2_paras, 0)
        head_text = collapse(para_plain_text(p0))
        if not head_text.startswith(SEC2_FIRST_ANCHOR):
            raise SystemExit(
                "양식 section2 첫 문단이 %r로 시작하지 않는다: %r"
                % (SEC2_FIRST_ANCHOR, head_text[:40]))
        m = re.search(r"(<hp:ctrl><hp:colPr.*?</hp:secPr>)", p0, re.S)
        if not m:
            raise SystemExit("양식 section2 첫 문단에서 colPr/secPr 블록을 찾지 못했다")
        self.sec2_secpr = m.group(1)
        self.sec2_pagectrl = "".join(
            re.findall(r"<hp:ctrl><hp:page(?:Num|Hiding)[^>]*/></hp:ctrl>", p0))
        self.sec2_newnum = "".join(re.findall(r"<hp:ctrl><hp:newNum[^>]*/></hp:ctrl>", p0))
        self.s2_head = self.s2[: self.s2_paras[0][0]]

    # ── 표지(section0) 치환 ──────────────────────────────────────────────
    def cover_texts(self):
        """표지(section0) 문단별 텍스트. 리포트용."""
        out = []
        for idx, (a, b) in enumerate(split_paragraphs(self.s0)):
            seg = self.s0[a:b]
            texts = re.findall(r"<hp:t>(.*?)</hp:t>", seg, re.S)
            out.append((idx, " ".join(unesc(t) for t in texts if t.strip())))
        return out

    def apply_cover(self, new_by_role):
        """style_map["cover"] 앵커를 따라 run의 <hp:t> 텍스트만 바꾼다(run·charPr 보존)."""
        anchors = self.sm.get("cover")
        if not isinstance(anchors, list) or not anchors:
            raise SystemExit("style_map에 cover 앵커 목록이 없다 — 표지 치환 불가")

        expected = [a for a in anchors if a.get("role") in new_by_role]
        unknown = sorted(set(new_by_role) - {a.get("role") for a in anchors})
        if unknown:
            raise SystemExit(
                "cover JSON의 role이 style_map.cover에 없다: %s" % ", ".join(unknown))
        if not expected:
            raise SystemExit("치환할 표지 role이 하나도 없다")

        s0 = self.s0
        spans = split_paragraphs(s0)
        plan = []
        for anchor in expected:
            pidx = int(anchor["section0_idx"])
            ridx = int(anchor["run_ordinal"])
            if not (0 <= pidx < len(spans)):
                raise SystemExit("cover 앵커 section0_idx %d가 범위 밖이다" % pidx)
            pa, pb = spans[pidx]
            para = s0[pa:pb]
            runs = run_text_spans(para)
            old_want = anchor.get("old", "")
            if not collapse(old_want):
                raise SystemExit("cover 앵커에 old(기존 문자열)가 없다: %r" % anchor)
            # 위치의 단일 근거는 원문 텍스트다. run_ordinal은 같은 문자열이 한 문단에
            # 두 번 이상 나올 때만 쓰는 보조 지표다(덤프마다 run 번호 규칙이 다를 수 있다).
            cands = [
                (i, sp) for i, sp in enumerate(runs)
                if sp is not None and collapse(unesc(para[sp[0]:sp[1]])) == collapse(old_want)
            ]
            if not cands:
                raise SystemExit(
                    "cover 앵커 원문을 section0 p%d에서 찾지 못했다: %r" % (pidx, old_want))
            if len(cands) == 1:
                used_idx, (ta, tb) = cands[0]
            else:
                exact = [c for c in cands if c[0] == ridx]
                if not exact:
                    raise SystemExit(
                        "cover 앵커 원문이 section0 p%d에 %d번 나오는데 run_ordinal %d와 "
                        "일치하는 것이 없다(후보 run: %s)"
                        % (pidx, len(cands), ridx, ", ".join(str(c[0]) for c in cands)))
                used_idx, (ta, tb) = exact[0]
            old_actual = unesc(para[ta:tb])
            new_text = new_by_role[anchor["role"]]
            plan.append((pa + ta, pa + tb, esc(new_text), pidx, used_idx, anchor["role"],
                         old_actual, new_text))

        # 뒤에서 앞으로 치환해야 앞선 치환이 뒤 오프셋을 어긋내지 않는다.
        for start, end, new_xml, pidx, ridx, role, old_actual, new_text in sorted(
                plan, key=lambda item: item[0], reverse=True):
            s0 = s0[:start] + new_xml + s0[end:]
        # 텍스트 길이가 바뀐 문단의 레이아웃 캐시는 지운다(한글이 재계산한다).
        s0 = strip_linesegarray(s0)
        self.s0 = s0
        self.cover_replacements = [
            (pidx, ridx, role, old_actual, new_text)
            for _, _, _, pidx, ridx, role, old_actual, new_text in plan
        ]
        if len(self.cover_replacements) != len(expected):
            raise SystemExit(
                "표지 치환 건수 불일치: 기대 %d, 실제 %d"
                % (len(expected), len(self.cover_replacements)))
        return len(self.cover_replacements)

    # ── content.hpf(그림 manifest) ───────────────────────────────────────
    def register_images(self, images):
        """images=[{"item_id","arcname"}] 를 content.hpf manifest에 등록한다."""
        if not images:
            return
        closing = "</opf:manifest>"
        if closing not in self.content_hpf:
            raise SystemExit("content.hpf에서 </opf:manifest>를 찾지 못했다")
        items = "".join(
            '<opf:item id="%s" href="%s" media-type="image/png" isEmbeded="1"/>'
            % (img["item_id"], img["arcname"])
            for img in images
        )
        self.content_hpf = self.content_hpf.replace(closing, items + closing, 1)


# ── 본문 조립 ─────────────────────────────────────────────────────────────────
class Document(object):
    def __init__(self, template, style_map, const, image_root, survey_layout=None,
                 keep_guide=False):
        self.tpl = template
        self.sm = style_map
        self.c = const
        self.image_root = image_root
        self.survey = survey_layout or None   # None이면 설문 양식을 입히지 않는다(기존 동작)
        self.survey_applied = []              # 리포트용 (틀 이름, 대상, 규모)
        # `> [작성 가이드] …` 인용구 등 집필 안내 문단은 원고에만 두고 논문 hwpx에는 넣지 않는다
        # (2026-09-12 사용자 지시). --keep-guide 로만 빨간 문단으로 되살린다.
        self.keep_guide = bool(keep_guide)
        self.guide_skipped = 0
        self.ids = IdGen()
        self.asm = Assembler(style_map, const, self.ids, template.red_char_pr_id)
        self.body = []          # section2 문단 XML 목록
        self.front = []         # section1 논문개요 본문 문단 XML 목록
        self.toc = []           # (level, 제목)
        self.lot = []           # 표 목차 항목
        self.lof = []           # 그림 목차 항목
        self.images = []        # {"item_id","arcname","src","px","hwpunit"}
        self.notes = list(const.notes)
        self._last_blank = False   # 절·항 제목 앞 빈 줄 규칙용 (빈 줄 중복 방지)

    def emit(self, xml, blank=False):
        self.body.append(xml)
        self._last_blank = blank

    def emit_blank(self, char=None):
        self.emit(self.asm.blank(char), blank=True)

    def blank_before_heading(self):
        """절·항(및 하위) 제목 앞에 빈 줄 1줄. 이미 빈 줄이면 더 넣지 않는다.

        규칙 출처: .claude/rules/hwpx-output-verification.md "절·항 제목 앞 빈 줄"
        (장 제목은 pageBreak=1로 새 쪽에서 시작하므로 제외).
        """
        if self.body and not self._last_blank:
            self.emit_blank()

    # 스타일 스펙 헬퍼
    def spec(self, key):
        s = self.sm[key]
        return {"style": s["styleIDRef"], "para": s["paraPrIDRef"], "char": s["charPrIDRef"]}

    @staticmethod
    def const_spec(entry):
        return {"style": entry["style"], "para": entry["para"], "char": entry["char"]}

    # ── 그림 ──────────────────────────────────────────────────────────────
    def resolve_image(self, rel_path, source):
        candidates = []
        if source:
            candidates.append(os.path.join(os.path.dirname(os.path.abspath(source)), rel_path))
        if self.image_root:
            candidates.append(os.path.join(self.image_root, rel_path))
        candidates.append(os.path.abspath(rel_path))
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
        raise SystemExit(
            "그림 파일을 찾지 못했다: %s (찾아본 곳: %s)" % (rel_path, " | ".join(candidates)))

    def add_image(self, block, source):
        rel_path = block.get("path") or block.get("src") or ""
        if not rel_path:
            raise SystemExit("figure_image 블록에 path가 없다: %r" % block)
        src = self.resolve_image(rel_path.replace("\\", "/"), source)
        px_w, px_h = png_size(src)
        max_w = int(self.c.LINE_W * IMAGE_WIDTH_RATIO)
        width = min(px_w * PX_TO_HWPUNIT, max_w)
        height = max(int(round(width * px_h / float(px_w))), 1)
        item_id = "image%d" % (len(self.images) + 1)
        arcname = "BinData/%s.png" % item_id
        self.images.append({
            "item_id": item_id, "arcname": arcname, "src": src,
            "px": (px_w, px_h), "hwpunit": (width, height),
            "alt": block.get("alt", ""),
        })
        self.emit(self.asm.image_para(self.spec("caption"), item_id, width, height))

    # ── 본문 블록 ─────────────────────────────────────────────────────────
    def add_blocks(self, blocks, first_paragraph=False, appendix=False, source=None):
        body_spec = self.spec("body")
        cap_spec = self.spec("caption")
        apx_spec = self.const_spec(self.c.APPENDIX_TITLE)
        pending_caption = None
        i = 0
        while i < len(blocks):
            b = blocks[i]
            i += 1
            kind = b["type"]

            # 표 캡션은 바로 뒤 표가 있으면 표 첫 행에 병합한다(양식 관행).
            if pending_caption is not None and kind != "table":
                self.emit(self.asm.text_para(cap_spec, pending_caption))
                pending_caption = None

            if kind == "h1":
                self.toc.append((1, b["text"]))
                if first_paragraph:
                    self.emit(self._first_paragraph(b["text"]))
                    first_paragraph = False
                elif appendix:
                    self.emit(self.asm.text_para(apx_spec, b["text"], page_break=True))
                else:
                    self.emit(self.asm.text_para(
                        self.spec("h1_chapter"), b["text"], page_break=True))
                self.emit_blank()
            elif kind == "h2":
                self.toc.append((2, b["text"]))
                self.blank_before_heading()
                self.emit(self.asm.text_para(self.spec("h2_section"), b["text"]))
                self.emit_blank()
                if self.survey:
                    i = self._survey_section(b["text"], blocks, i)
            elif kind == "h3":
                self.toc.append((3, b["text"]))
                self.blank_before_heading()
                self.emit(self.asm.text_para(self.spec("h3_item"), b["text"]))
                self.emit_blank()
            elif kind == "h4":
                spec = dict(body_spec)
                spec["char"] = self.c.H4_FALLBACK_CHAR
                self.blank_before_heading()
                self.emit(self.asm.text_para(spec, b["text"]))
            elif kind == "p":
                if b.get("guide") and not self.keep_guide:
                    self.guide_skipped += 1
                    continue
                runs = b.get("runs", [])
                # 리커트 표 바로 앞의 굵은 변수명 문단(예: **J. 사고예방 효과** (…))은
                # 굵은 부분을 표의 변수명 셀로 올리고, 나머지 설명만 문단으로 남긴다.
                var_name = self._likert_var_name(blocks, i, runs)
                if var_name is not None:
                    self._pending_var_name = var_name
                    runs = runs[1:]
                    if not any(r.get("text", "").strip() for r in runs):
                        continue
                prefix = "" if (runs and runs[0].get("text", "")[:1].isspace()) else " "
                self.emit(self.asm.runs_para(
                    body_spec, runs, prefix=prefix, guide=bool(b.get("guide"))))
            elif kind == "table_caption":
                self.lot.append(b["text"])
                pending_caption = b["text"]
            elif kind == "table":
                if self.survey and self._survey_table(b):
                    pending_caption = None
                    continue
                self.emit(self.asm.table_xml(b["header"], b["rows"], caption=pending_caption))
                pending_caption = None
            elif kind == "figure_caption":
                self.lof.append(b["text"])
                self.emit(self.asm.text_para(cap_spec, b["text"]))
            elif kind == "figure_image":
                self.add_image(b, source)
            elif kind == "figure_placeholder":
                self.emit(self.asm.text_para(body_spec, b["text"]))
            else:
                raise SystemExit("알 수 없는 블록 타입: %r" % kind)

        if pending_caption is not None:
            self.emit(self.asm.text_para(cap_spec, pending_caption))
        self.emit_blank()
        return first_paragraph

    # ── 설문 양식 적용 ────────────────────────────────────────────────────
    _pending_var_name = None
    CHOICE_RE = re.compile(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]")
    QUESTION_RE = re.compile(r"^\s*(\d+)\.\s*(.+)$")
    COVER_LABEL_RE = re.compile(r"^\s*([^\s:]+)\s*:\s*(.*)$")

    def _survey_section(self, title, blocks, i):
        """h2 제목 뒤에 설문 상자를 입힌다. 소비한 블록 다음 인덱스를 돌려준다."""
        layout = self.survey
        if title == layout.get("cover_section"):
            return self._survey_cover(blocks, i)
        if title in (layout.get("partA_sections") or []):
            return self._survey_partA(title, blocks, i)
        return i

    def _survey_cover(self, blocks, i):
        """`1. 연구 설명문 및 참여 안내` — 표지 상자 + 뒤따르는 pp30 라벨 4줄."""
        layout = self.survey
        labels = list(layout.get("cover_labels") or [])
        body, label_lines = [], []
        while i < len(blocks) and blocks[i]["type"] == "p" and not blocks[i].get("guide"):
            runs = blocks[i].get("runs", [])
            text = "".join(r.get("text", "") for r in runs)
            m = self.COVER_LABEL_RE.match(text)
            if m and m.group(1) in labels:
                label_lines.append((m.group(1), m.group(2)))
            else:
                body.append(runs)
            i += 1
        if not body:
            return i
        self.emit(self.asm.survey_cover_box(
            self.tpl.survey["cover"],
            layout.get("cover_title_lines") or [],
            layout.get("cover_subtitle", ""),
            body,
            layout.get("cover_date", "")))
        pad = int(layout.get("cover_label_pad", 4))
        order = {name: n for n, name in enumerate(labels)}
        for name, value in sorted(label_lines, key=lambda x: order.get(x[0], 99)):
            self.emit(self.asm.survey_label_para(
                self.tpl.survey["labels"], name, value, pad))
        self.emit_blank()
        self.survey_applied.append(("표지 상자", layout.get("cover_section"),
                                    "안내문 %d문단 · 라벨 %d줄" % (len(body), len(label_lines))))
        return i

    def _survey_partA(self, title, blocks, i):
        """`2. 사전 설문` — 인구통계 상자. guide 인용구는 상자 밖에 남긴다."""
        layout = self.survey
        items = []
        while i < len(blocks) and blocks[i]["type"] == "p" and not blocks[i].get("guide"):
            runs = blocks[i].get("runs", [])
            text = "".join(r.get("text", "") for r in runs)
            m = self.QUESTION_RE.match(text)
            if m and runs and runs[0].get("bold"):
                items.append(("q", m.group(1), m.group(2)))
            elif self.CHOICE_RE.match(text):
                items.append(("c", "   " + text.strip()))
            else:
                items.append(("p", runs))
            i += 1
        if not items:
            return i
        for box_title, chunk in self._partA_chunks(title, items):
            self.emit(self.asm.survey_partA_box(self.tpl.survey["partA"], box_title, chunk))
            self.emit_blank()
            self.survey_applied.append(
                ("Part A 상자", box_title,
                 "문항 %d · 선택지 %d" % (sum(1 for x in chunk if x[0] == "q"),
                                         sum(1 for x in chunk if x[0] == "c"))))
        return i

    def _partA_chunks(self, title, items):
        """Part A 문항을 상자별로 나눈다 — 규칙은 survey_layout.partA_boxes(데이터).

        상자 하나에 문항을 다 넣으면 한 쪽을 넘는 절이 있어(미소 사전 설문 8문항),
        의미 단위로 끊어 여러 상자에 담는다. 규칙이 없으면 한 상자로 낸다.
        """
        layout = self.survey
        boxes = (layout.get("partA_boxes") or {}).get(title)
        if not boxes:
            return [((layout.get("partA_titles") or {}).get(title, title), items)]

        # 문항 단위(질문 + 뒤따르는 선택지)로 묶고, 앞머리 안내 문단은 따로 둔다
        intro, units = [], []
        for item in items:
            if item[0] == "q":
                units.append([item])
            elif units:
                units[-1].append(item)
            else:
                intro.append(item)

        out, cursor = [], 0
        for n, box in enumerate(boxes):
            count = int(box.get("questions", 0)) or (len(units) - cursor)
            chunk = list(intro) if box.get("intro") else []
            for unit in units[cursor:cursor + count]:
                chunk.extend(unit)
            cursor += count
            if chunk:
                out.append((box.get("title", title), chunk))
        if cursor < len(units):     # 규칙이 문항 수를 다 덮지 못하면 마지막 상자에 몰아넣는다
            leftover = [x for unit in units[cursor:] for x in unit]
            if out:
                out[-1] = (out[-1][0], out[-1][1] + leftover)
            else:
                out.append((title, leftover))
            self.notes.append(
                "Part A '%s' 규칙이 문항 %d개를 덮지 못해 마지막 상자에 붙였다 — "
                "survey_layout.partA_boxes를 확인할 것" % (title, len(units) - cursor))
        return out

    def _likert_var_name(self, blocks, i, runs):
        """이 문단이 리커트 표 바로 앞의 변수명 문단이면 굵은 텍스트를 돌려준다."""
        if not self.survey or not runs or not runs[0].get("bold"):
            return None
        if i >= len(blocks) or blocks[i]["type"] != "table":
            return None
        if blocks[i].get("header") != (self.survey.get("likert_header") or []):
            return None
        return runs[0].get("text", "").strip()

    def _survey_table(self, block):
        """리커트·평정 표면 양식 격자로 만들어 emit하고 True를 돌려준다."""
        layout = self.survey
        header = block.get("header")
        rating = layout.get("rating") or {}
        if header == (layout.get("likert_header") or []):
            var_name = self._pending_var_name or ""
            self._pending_var_name = None
            self.emit(self.asm.survey_likert(
                self.tpl.survey["likert"], var_name,
                layout.get("likert_labels") or [], block["rows"]))
            self.survey_applied.append(("리커트 격자", var_name, "문항 %d" % len(block["rows"])))
            return True
        if header == (rating.get("header") or []):
            self.emit(self.asm.survey_likert(
                self.tpl.survey["likert"], rating.get("var_name", ""),
                rating.get("labels") or [], block["rows"], split=rating.get("split")))
            self.survey_applied.append(
                ("리커트 격자(13열)", rating.get("var_name", ""), "문항 %d" % len(block["rows"])))
            return True
        return False

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
        ref_title = self.const_spec(self.c.REF_TITLE)
        ref_category = self.const_spec(self.c.REF_CATEGORY)
        ref_entry = self.const_spec(self.c.REF_ENTRY)
        self.emit(self.asm.text_para(ref_title, "참고문헌", page_break=True))
        self.emit_blank()
        for category, items in refs["categories"].items():
            self.blank_before_heading()
            self.emit(self.asm.text_para(ref_category, category))
            for item in items:
                self.emit(self.asm.text_para(
                    ref_entry, "[%02d] %s" % (item["no"], item["text"])))
            self.emit_blank()
            if not items:
                self.notes.append("참고문헌 분류 '%s'에 확정 항목이 없어 제목만 생성했다." % category)
        flagged = len(refs.get("flagged", []))
        if flagged:
            self.notes.append("references.json의 flagged %d건은 지시대로 본문에 넣지 않았다." % flagged)

    def add_placeholder_section(self, title, text):
        self.toc.append((1, title))
        self.emit(self.asm.text_para(
            self.const_spec(self.c.APPENDIX_TITLE), title, page_break=True))
        self.emit_blank()
        self.emit(self.asm.text_para(self.spec("body"), text, prefix=" "))
        self.emit_blank()

    # ── 전면부(section1) ─────────────────────────────────────────────────
    def add_front_blocks(self, blocks):
        """논문개요 본문 — --front 블록을 abstract_body 서식으로 만든다."""
        fm = self.sm["front_matter"]
        spec = self.const_spec(fm["abstract_body"])
        bold_spec = dict(spec)
        bold_spec["char"] = self.c.BODY_BOLD_CHAR
        for b in blocks:
            kind = b["type"]
            if kind == "h1":
                # 양식의 '논 문  개 요' 제목 상자가 이미 장 제목 노릇을 하므로 중복 제목은 버린다.
                self.notes.append("논문개요(--front)의 h1 '%s'는 제목 상자와 중복이라 넣지 않았다."
                                  % b["text"])
            elif kind in ("h2", "h3", "h4"):
                self.front.append(self.asm.text_para(bold_spec, b["text"]))
            elif kind == "p":
                if b.get("guide") and not self.keep_guide:
                    self.guide_skipped += 1
                    continue
                runs = b.get("runs", [])
                prefix = "" if (runs and runs[0].get("text", "")[:1].isspace()) else " "
                self.front.append(self.asm.runs_para(
                    spec, runs, prefix=prefix, guide=bool(b.get("guide"))))
            elif kind in ("table_caption", "figure_caption", "figure_placeholder"):
                self.front.append(self.asm.text_para(spec, b["text"]))
            elif kind == "table":
                self.front.append(self.asm.table_xml(b["header"], b["rows"]))
            elif kind == "figure_image":
                self.notes.append("논문개요(--front)의 figure_image 블록은 넣지 않았다: %s"
                                  % b.get("path", ""))
            else:
                raise SystemExit("논문개요에 넣을 수 없는 블록 타입: %r" % kind)

    def build_thanks(self):
        """감사의 글 — 제목 상자는 바이트 보존, 본문은 자리표시자로 재구성한다."""
        fm = self.sm["front_matter"]
        body_spec = self.const_spec(fm["thanks_body"])
        date_spec = self.const_spec(fm.get("thanks_date") or fm["thanks_body"])
        name_spec = self.const_spec(fm.get("thanks_name") or fm["thanks_body"])
        if not fm.get("thanks_date") or not fm.get("thanks_name"):
            self.notes.append(
                "front_matter.thanks_date/thanks_name이 없어 thanks_body 서식으로 대체했다.")
        return [
            self.tpl.thanks_title,
            self.asm.text_para(body_spec, THANKS_PLACEHOLDER),
            self.asm.blank(),
            self.asm.text_para(date_spec, THANKS_DATE_TEXT),
            self.asm.text_para(name_spec, THANKS_NAME_TEXT),
        ]

    def build_section1(self):
        # 양식 목차 문단은 가운데정렬 변형이 섞여 있어, 표·그림 목차와 같은 문단 서식(paraPr)에
        # 흑색 charPr을 써서 재생성한다. 쪽번호는 한글 자동 목차로 최종화한다.
        toc_spec = {
            "style": self.spec("toc_entry")["style"],
            "para": self.spec("toc_lot_entry")["para"],
            "char": self.c.TOC_ENTRY_CHAR,
        }
        lot_spec = self.spec("toc_lot_entry")
        parts = [self.tpl.s1_head, self.tpl.toc_title, self.asm.blank(self.c.TOC_BLANK_CHAR)]
        for level, title in self.toc:
            parts.append(self.asm.text_para(toc_spec, title, prefix=" " * (level - 1)))
        parts.append(self.asm.blank(self.c.TOC_BLANK_CHAR))

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

        parts.extend(self.build_thanks())

        parts.append(self.tpl.abstract_title)
        if self.front:
            parts.extend(self.front)
        else:
            fm = self.sm["front_matter"]
            parts.append(self.asm.text_para(
                self.const_spec(fm["abstract_body"]), "[확정 필요: 국문 논문개요 작성]"))
            self.notes.append("--front가 없어 논문개요 본문을 자리표시자 한 문단으로 넣었다.")
        parts.append("</hs:sec>")
        return "".join(parts)

    def build_section2(self):
        return self.tpl.s2_head + "".join(self.body) + "</hs:sec>"


# ── 출력 ──────────────────────────────────────────────────────────────────────
def write_hwpx(template, output, replacements, extra_entries=()):
    """양식 ZIP의 엔트리 순서·압축 방식을 유지한 채 지정 엔트리만 교체하고, 새 엔트리는 뒤에 붙인다."""
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
        base_date = template.infos[0].date_time if template.infos else (1980, 1, 1, 0, 0, 0)
        for arcname, payload in extra_entries:
            info = zipfile.ZipInfo(arcname, date_time=base_date)
            info.compress_type = zipfile.ZIP_STORED
            zout.writestr(info, payload)


def load_blocks(paths):
    out = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        out.append((path, data.get("source"), data["blocks"]))
    return out


def is_appendix(blocks):
    """블록 파일의 첫 h1 제목이 '부록'으로 시작하면 부록 파일로 본다(참고문헌 삽입 위치 판정용)."""
    for b in blocks:
        if b["type"] == "h1":
            # 부록 제목은 "부 록 1. …"처럼 띄어 쓰므로 공백을 걷어내고 판정한다.
            return b["text"].replace(" ", "").startswith("부록")
    return False


def build_report(doc, template, args, output, marker_runs):
    lines = ["# 조립 리포트", "",
             "- 양식: `%s`" % args.template,
             "- style_map: `%s`" % args.style_map,
             "- 출력: `%s`" % output,
             "- 본문 문단 수: %d (section2)" % len(doc.body),
             "- 논문개요 문단 수: %d (section1)" % len(doc.front),
             "- 목차 항목: %d (장 %d)" % (len(doc.toc), sum(1 for l, _ in doc.toc if l == 1)),
             "- 표 목차 항목: %d / 그림 목차 항목: %d" % (len(doc.lot), len(doc.lof)),
             "- 빨간 마커 run: %d" % marker_runs,
             "- guide 문단 제외: %d%s" % (
                 doc.guide_skipped,
                 " (--keep-guide 로 살릴 수 있다)" if not doc.keep_guide
                 else " — --keep-guide 지정, 빨간 문단으로 유지"),
             "- 빨간 charPr 신규 복제: %d %s" % (
                 len(template.cloned_red_char_prs),
                 ("(%s)" % ", ".join("%s→%s" % pair for pair in template.cloned_red_char_prs))
                 if template.cloned_red_char_prs else ""),
             ""]

    lines += ["## 설문 양식 적용 (--survey-layout)", ""]
    if doc.survey is None:
        lines.append("- 적용하지 않음(--survey-layout 미지정) — 설문 표도 일반 표로 조립")
    elif not doc.survey_applied:
        lines.append("- 규칙은 읽었으나 대응되는 절·표를 찾지 못했다 — 앵커/헤더를 확인할 것")
    else:
        lines += ["| 틀 | 대상 | 규모 |", "| --- | --- | --- |"]
        for frame, target, size in doc.survey_applied:
            lines.append("| %s | %s | %s |" % (frame, target, size))
    lines.append("")

    lines += ["## 전면부 앵커 (style_map.front_matter)", ""]
    for key, value in template.front_matter_idx.items():
        lines.append("- %s: %s" % (key, value))
    lines.append("")

    lines += ["## 표지(section0) 치환", ""]
    if template.cover_replacements:
        lines.append("| section0 p | run | role | 기존 | 변경 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for pidx, ridx, role, old, new in template.cover_replacements:
            lines.append("| %d | %d | %s | %s | %s |" % (pidx, ridx, role, old, new))
        lines.append("")
        lines.append("- 치환 건수: %d" % len(template.cover_replacements))
    else:
        lines.append("- 치환 없음(--cover 미지정)")
    lines.append("")
    lines += ["### 치환 후 표지 문단 텍스트", ""]
    for idx, text in template.cover_texts():
        lines.append("- section0 p%d: %s" % (idx, text[:400] if text else "(텍스트 없음)"))
    lines.append("")

    lines += ["## 그림 삽입 (BinData)", ""]
    if doc.images:
        lines.append("| 항목 id | ZIP 엔트리 | 원본 | px | HWPUNIT |")
        lines.append("| --- | --- | --- | --- | --- |")
        for img in doc.images:
            lines.append("| %s | %s | %s | %dx%d | %dx%d |" % (
                img["item_id"], img["arcname"], os.path.basename(img["src"]),
                img["px"][0], img["px"][1], img["hwpunit"][0], img["hwpunit"][1]))
    else:
        lines.append("- 삽입한 그림 없음")
    lines.append("")

    if doc.notes:
        lines += ["## 메모", ""] + ["- %s" % n for n in doc.notes] + [""]
    return "\n".join(lines)


def count_marker_runs(*xml_texts):
    """빨간 마커가 별도 run으로 분리된 횟수(리포트용)."""
    total = 0
    for xml_text in xml_texts:
        for text in re.findall(r"<hp:t>(.*?)</hp:t>", xml_text, re.S):
            if GUIDE_MARKER_RE.search(unesc(text)):
                total += 1
    return total


def main(argv=None):
    ap = argparse.ArgumentParser(description="blocks JSON → 학위논문 hwpx 조립기")
    ap.add_argument("--template", required=True, help="양식 hwpx (읽기 전용)")
    ap.add_argument("--style-map", required=True, help="style_map_miso.json")
    ap.add_argument("--blocks", nargs="+", required=True, help="blocks JSON (본문 순서대로)")
    ap.add_argument("--front", help="논문개요 블록 JSON (front.blocks.json)")
    ap.add_argument("--cover", help="표지 치환값 JSON (cover_miso.json)")
    ap.add_argument("--references", help="references.json")
    ap.add_argument("--keep-guide", action="store_true",
                    help="`> [작성 가이드] …` 집필 안내 문단을 빨간 문단으로 살려 둔다 "
                         "(기본은 hwpx에서 제외 — 2026-09-12 사용자 지시)")
    ap.add_argument("--survey-layout",
                    help="설문 양식 적용 규칙 JSON (staging/survey_layout.json). "
                         "주지 않으면 설문 표도 일반 표로 조립한다(기존 동작)")
    ap.add_argument("--image-root", help="그림 파일 기준 디렉토리 (기본: <repo>/01.docs)")
    ap.add_argument("--output", help="출력 hwpx 경로")
    ap.add_argument("--report", help="조립 리포트 MD 경로")
    ap.add_argument("--smoke", action="store_true",
                    help="스테이징 스모크 모드 — staging/test_out/smoke.hwpx 로 출력")
    ap.add_argument("--no-tail", action="store_true",
                    help="Abstract 자리 문단을 생성하지 않는다")
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

    image_root = args.image_root or os.path.abspath(
        os.path.join(here, os.pardir, os.pardir, "01.docs"))

    with open(args.style_map, encoding="utf-8") as f:
        style_map = json.load(f)
    const = Constants(style_map)
    template = Template(args.template, style_map, const)
    survey_layout = None
    if args.survey_layout:
        with open(args.survey_layout, encoding="utf-8") as f:
            survey_layout = json.load(f)
    doc = Document(template, style_map, const, image_root, survey_layout, args.keep_guide)

    if args.cover:
        with open(args.cover, encoding="utf-8") as f:
            cover = json.load(f)
        new_by_role = {}
        for entry in cover:
            if "role" not in entry:      # 주석용 항목(_note/_omitted만 있는 원소)은 건너뛴다
                continue
            role, new_text = entry["role"], entry["new"]
            if role in new_by_role and new_by_role[role] != new_text:
                raise SystemExit("cover JSON에 role '%s'의 값이 서로 다르게 두 번 있다" % role)
            new_by_role[role] = new_text
        template.apply_cover(new_by_role)

    if args.front:
        with open(args.front, encoding="utf-8") as f:
            doc.add_front_blocks(json.load(f)["blocks"])

    files = load_blocks(args.blocks)
    refs = None
    if args.references:
        with open(args.references, encoding="utf-8") as f:
            refs = json.load(f)

    first = True
    refs_done = False
    for path, source, blocks in files:
        appendix = is_appendix(blocks)
        if refs is not None and not refs_done and appendix:
            doc.add_references(refs)
            refs_done = True
        first = doc.add_blocks(blocks, first_paragraph=first, appendix=appendix,
                               source=source or path)
    if refs is not None and not refs_done:
        doc.add_references(refs)

    if not args.no_tail:
        doc.add_placeholder_section("Abstract", ABSTRACT_PLACEHOLDER)

    s1 = doc.build_section1()   # s1_head에 XML 프롤로그와 <hs:sec …> 열림 태그가 포함돼 있다
    s2 = doc.build_section2()
    template.register_images(doc.images)

    extra_entries = []
    for img in doc.images:
        with open(img["src"], "rb") as f:
            extra_entries.append((img["arcname"], f.read()))

    write_hwpx(template, output, {
        "Contents/header.xml": template.header_xml,
        "Contents/section0.xml": template.s0,
        "Contents/section1.xml": s1,
        "Contents/section2.xml": s2,
        "Contents/content.hpf": template.content_hpf,
    }, extra_entries)

    report = build_report(doc, template, args, output, count_marker_runs(s1, s2))
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
