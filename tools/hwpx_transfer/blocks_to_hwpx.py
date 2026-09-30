# 블록 JSON과 양식 hwpx를 입력받아 서식을 이식한 6장 구조 학위논문 hwpx를 조립하는 스크립트
"""blocks_to_hwpx.py — blocks JSON → 학위논문 hwpx 조립기.

사용 예:
    python tools/hwpx_transfer/blocks_to_hwpx.py \
        --template "공학대학원_건축안전_윤혁_…YOLO-VLM… - 복사본.hwpx" \
        --style-map tools/hwpx_transfer/staging/style_map.json \
        --blocks ch01.blocks.json ch02.blocks.json ... apx2.blocks.json \
        --references tools/hwpx_transfer/staging/references.json \
        --output <출력 hwpx>

설계 요약.
  - 양식 hwpx의 ZIP 엔트리 순서·압축 방식을 그대로 유지하고 Contents/section1.xml,
    Contents/section2.xml을 교체한다. 가이드 마커에 필요한 빨간 charPr가 양식에 없으면
    Contents/header.xml에 원본 charPr의 색상만 바꾼 복제본을 추가한다.
  - section1(전면부)은 목차·표목차·그림목차만 재생성하고 제목 상자·감사의 글·논문개요
    문단은 양식의 XML을 바이트 수준 그대로 옮긴다.
  - section2(본문)는 blocks 순서대로 새로 만든다. 첫 문단에는 양식 section2 첫 문단의
    colPr·secPr·pageNum 제어 블록을 그대로 이식해 페이지 설정을 보존한다.
"""

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

# ── 양식 실측 상수 ────────────────────────────────────────────────────────────
# 표 폭. 양식 대표 표(<표 3-1>, section2 p223)의 sz.width 실측값을 그대로 쓴다.
TABLE_WIDTH = 39142
# 셀 최소 높이. 양식 최소 셀(cellSz height=1565)을 최소값으로 두고 내용에 따라 자라게 한다.
ROW_MIN_H = 1565
# 본문 줄 폭. 양식 linesegarray의 horzsize 실측값.
LINE_W = 39684

# style_map.json에 없어 양식 XML에서 직접 실측한 스타일(참고문헌·부록 영역).
REF_TITLE = {"style": "0", "para": "5", "char": "63"}      # s2 p300 "참고문헌"
REF_CATEGORY = {"style": "0", "para": "12", "char": "36"}  # s2 p303 "가 . 학위논문"
REF_ENTRY = {"style": "0", "para": "59", "char": "62"}     # s2 p304 서지 항목
APPENDIX_TITLE = {"style": "0", "para": "31", "char": "14"}  # s2 p317 "부   록"
# 본문 볼드 run. charPr 9는 charPr 61(본문)과 같은 11pt·한양신명조·borderFill 2에 bold만 추가된 짝.
BODY_BOLD_CHAR = "9"
# 표 셀 볼드 run. charPr 122는 charPr 7(셀 기본)과 같은 10pt·한양신명조·borderFill 3의 bold 짝.
CELL_BOLD_CHAR = "122"
# h4(소제목)는 양식에 실측 대응이 없다 — 본문 문단 서식 + 볼드로 대체한다(가정).
H4_FALLBACK_CHAR = BODY_BOLD_CHAR

# 표 셀 텍스트 변환 대상(parse_report.md 5-1·5-2 인계 목록).
CELL_LINEBREAK_TOKEN = "<br>"
EMSP_TOKEN = "&emsp;"
EMSP_CHAR = " "

# 본문이 아니라 미확정 자리·인용·그림 지시임을 나타내는 마커. 대괄호 전부가 아니라
# 이 다섯 접두사만 판정하며 콜론·줄표 등 접두사 뒤 구분 문자는 제한하지 않는다.
# 대괄호 없는 `실험전`은 결과표의 미수집 자리 표기(2026-09-30 사용자 지시)로, 낱말 전체를 빨갛게 한다.
GUIDE_MARKER_RE = re.compile(
    r"\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전"
)

XML_PROLOG = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'


# ── XML 조각 생성 ─────────────────────────────────────────────────────────────
def esc(text):
    """hp:t에 넣을 텍스트 — &emsp; 토큰을 전각 공백으로 바꾼 뒤 XML 이스케이프한다.

    &emsp;는 부록1 본문 문단(선택지 들여쓰기)에만 남아 있어 문단·셀 구분 없이 여기서 처리한다
    (parse_report.md 5-2 인계 목록). <br>은 표 셀 안에서만 쓰이므로 cell_paragraphs에서 다룬다.
    """
    text = text.replace(EMSP_TOKEN, EMSP_CHAR)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def lineseg(height, horzsize=LINE_W):
    """레이아웃 캐시 linesegarray 1줄. 한글이 문서를 열 때 재계산하므로 근사값이면 된다."""
    h = int(height)
    return (
        '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="%d" '
        'textheight="%d" baseline="%d" spacing="%d" horzpos="0" horzsize="%d" '
        'flags="393216"/></hp:linesegarray>'
        % (h, h, round(h * 0.85), round(h * 0.70), horzsize)
    )


class IdGen(object):
    """문단·표 id 발급기. 양식이 쓰는 값 범위(2147483648~)에서 고유하게 증가시킨다."""

    def __init__(self, start=2147483648):
        self._n = start

    def next(self):
        self._n += 1
        return self._n


class Assembler(object):
    def __init__(self, style_map, ids, red_char_pr=None):
        self.sm = style_map
        self.ids = ids
        self.red_char_pr = red_char_pr
        self.char_height = self._char_heights()

    def _char_heights(self):
        """linesegarray vertsize 계산용 charPr 높이표(양식 실측)."""
        return {
            "63": 1600, "42": 1600, "67": 1500, "52": 1500, "41": 1400,
            "14": 1400, "13": 1200, "36": 1200, "116": 1200,
            "61": 1100, "62": 1100, "9": 1100, "56": 1100, "57": 1100,
            "7": 1000, "58": 1000, "122": 1000,
        }

    def height_of(self, char_pr):
        return self.char_height.get(str(char_pr), 1100)

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
    def para(self, para_pr, style, runs_xml, char_for_height, page_break=False, horzsize=LINE_W):
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
            char = BODY_BOLD_CHAR if r.get("bold") else spec["char"]
            parts.append(self.marker_aware_runs(body, char))
        if not parts:
            parts.append('<hp:run charPrIDRef="%s"/>' % spec["char"])
        return self.para(spec["para"], spec["style"], "".join(parts), spec["char"], page_break)

    def blank(self, char="61"):
        run = '<hp:run charPrIDRef="%s"/>' % char
        body = self.sm["body"]
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run, char)

    # ── 표 ────────────────────────────────────────────────────────────────
    @staticmethod
    def column_widths(ncols):
        """본문 폭을 열 수로 균등 분할하되 합이 표 폭과 정확히 일치하게 나머지를 마지막 열에 준다."""
        base = TABLE_WIDTH // ncols
        widths = [base] * (ncols - 1) + [TABLE_WIDTH - base * (ncols - 1)]
        assert sum(widths) == TABLE_WIDTH
        return widths

    @staticmethod
    def border_fill(col, ncols):
        """좌우 개방형 테두리: 왼쪽 끝 45, 오른쪽 끝 46, 내부 6."""
        if ncols == 1:
            return "6"
        if col == 0:
            return "45"
        if col == ncols - 1:
            return "46"
        return "6"

    def cell_paragraphs(self, text, para_pr, char_pr, width):
        """셀 텍스트를 문단 XML로. <br>은 셀 안 별도 문단으로 나눈다(&emsp; 변환은 esc가 담당)."""
        lines = text.split(CELL_LINEBREAK_TOKEN)
        inner = max(width - 1020, 1000)  # 좌우 셀 패딩 510씩을 뺀 실사용 폭
        out = []
        for line in lines:
            if line:
                run = self.marker_aware_runs(line, char_pr)
            else:
                run = '<hp:run charPrIDRef="%s"/>' % char_pr
            out.append(self.para(para_pr, "0", run, char_pr, horzsize=inner))
        return "".join(out), len(lines)

    def cell(self, text, col, row, width, ncols, col_span=1, border=None,
             para_pr=None, char_pr=None, height=ROW_MIN_H):
        sm_tbl = self.sm["table"]
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
            % (border, paras, col, row, col_span, width, max(height, ROW_MIN_H * nlines),
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
            # 캡션 행: 전체 열 병합 + borderFill 13(아래만 실선), paraPr 11 · charPr 58 (양식 실측)
            trs.append("<hp:tr>%s</hp:tr>" % self.cell(
                caption, 0, row_idx, TABLE_WIDTH, ncols, col_span=ncols, border="13",
                para_pr="11", char_pr="58"))
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
                TABLE_WIDTH, ROW_MIN_H * row_idx,
                pos["treatAsChar"], pos["flowWithText"], pos["vertRelTo"], pos["horzRelTo"],
                out_m["left"], out_m["right"], out_m["top"], out_m["bottom"],
                in_m["left"], in_m["right"], in_m["top"], in_m["bottom"],
                "".join(trs),
            )
        )
        # 표는 문단 run 안에 treatAsChar=1로 인라인 배치된다(양식 s2 p223: run charPr 67, 표 뒤 빈 hp:t).
        body = self.sm["body"]
        run = '<hp:run charPrIDRef="%s">%s<hp:t/></hp:run>' % (self.sm["h2_section"]["charPrIDRef"], tbl)
        return self.para(body["paraPrIDRef"], body["styleIDRef"], run, "62", horzsize=LINE_W)


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

    def __init__(self, path):
        self.path = path
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
        if len(ps) != 112:
            raise SystemExit("양식 section1 문단 수가 112가 아니다(%d) — 전면부 경계 재확인 필요" % len(ps))
        self.s1_head = s1[: ps[0][0]]                       # 프롤로그 + <hs:sec …> (secPr는 p0 안에 있음)
        self.toc_title = self._para(s1, ps, 0)              # 목차 제목 상자(secPr 포함) — 바이트 보존
        self.lot_title = set_page_break(self._para(s1, ps, 78))   # 표목차 제목 상자
        self.lof_title = self._para(s1, ps, 82)             # 그림목차 제목 상자(이미 pageBreak=1)
        self.thanks = s1[ps[85][0]: ps[109][1]]             # 감사의 글 — 사용자 작성분, 바이트 보존
        self.abstract_kr = s1[ps[110][0]: ps[111][1]]       # 논문개요 — 바이트 보존
        tail = s1[ps[111][1]:]
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
        self.sm = style_map
        self.ids = IdGen()
        self.asm = Assembler(style_map, self.ids, template.red_char_pr_id)
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
                self.body.append(self.asm.blank("61"))
                if survey_cover:
                    self.add_survey_cover()
                    survey_cover = False
            elif kind == "h2":
                self.toc.append((2, b["text"]))
                self.body.append(self.asm.text_para(self.spec("h2_section"), b["text"]))
                self.body.append(self.asm.blank("61"))
            elif kind == "h3":
                self.toc.append((3, b["text"]))
                self.body.append(self.asm.text_para(self.spec("h3_item"), b["text"]))
                self.body.append(self.asm.blank("61"))
            elif kind == "h4":
                spec = dict(body_spec)
                spec["char"] = H4_FALLBACK_CHAR
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
        self.body.append(self.asm.blank("61"))
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
        self.body.append(self.asm.text_para(REF_TITLE, "참고문헌", page_break=True))
        self.body.append(self.asm.blank("61"))
        for category, items in refs["categories"].items():
            self.body.append(self.asm.text_para(REF_CATEGORY, category))
            for item in items:
                self.body.append(self.asm.text_para(
                    REF_ENTRY, "[%02d] %s" % (item["no"], item["text"])))
            self.body.append(self.asm.blank("62"))
            if not items:
                self.notes.append("참고문헌 분류 '%s'에 확정 항목이 없어 제목만 생성했다." % category)
        flagged = len(refs.get("flagged", []))
        if flagged:
            self.notes.append("references.json의 flagged %d건은 지시대로 본문에 넣지 않았다." % flagged)

    def add_survey_cover(self):
        """부록1 설문지 표지 박스 — 원고 코드펜스를 가운데 정렬 문단으로 재구성한다."""
        center = self.spec("toc_entry")  # paraPr 25 = CENTER
        for line in SURVEY_COVER_TITLE:
            self.body.append(self.asm.text_para(
                {"style": center["style"], "para": center["para"], "char": "41"}, line))
        self.body.append(self.asm.blank("61"))
        self.body.append(self.asm.text_para(
            {"style": center["style"], "para": center["para"], "char": "63"}, SURVEY_COVER_LABEL))
        self.body.append(self.asm.blank("61"))

    def add_placeholder_section(self, title):
        self.toc.append((1, title))
        self.body.append(self.asm.text_para(APPENDIX_TITLE, title, page_break=True))
        self.body.append(self.asm.blank("61"))
        self.body.append(self.asm.text_para(self.spec("body"), "[내용 확정 후 작성]", prefix=" "))
        self.body.append(self.asm.blank("61"))

    # ── 전면부(section1) ─────────────────────────────────────────────────
    def build_section1(self):
        toc_spec = self.spec("toc_entry")
        # 양식 목차 paraPr 25는 CENTER — 양식은 탭·리더점·쪽번호로 줄을 채워 무력화했지만
        # 쪽번호 없는 재생성 목차는 그대로 가운데 정렬돼 보인다(QA F-2). 표·그림 목차와
        # 같은 JUSTIFY 문단(paraPr)을 쓰고, 쪽번호는 한글 자동 목차로 최종화한다.
        toc_spec = {"style": toc_spec["style"],
                    "para": self.spec("toc_lot_entry")["para"], "char": "13"}  # 빨강(116) 대신 흑색
        lot_spec = self.spec("toc_lot_entry")
        parts = [self.tpl.s1_head, self.tpl.toc_title, self.asm.blank("13")]
        for level, title in self.toc:
            parts.append(self.asm.text_para(toc_spec, title, prefix=" " * (level - 1)))
        parts.append(self.asm.blank("13"))

        parts.append(self.tpl.lot_title)
        parts.append(self.asm.blank("61"))
        for text in self.lot:
            parts.append(self.asm.text_para(lot_spec, text))
        parts.append(self.asm.blank("61"))

        parts.append(self.tpl.lof_title)
        parts.append(self.asm.blank("61"))
        for text in self.lof:
            parts.append(self.asm.text_para(lot_spec, text))
        parts.append(self.asm.blank("61"))

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


def main(argv=None):
    ap = argparse.ArgumentParser(description="blocks JSON → 학위논문 hwpx 조립기")
    ap.add_argument("--template", required=True, help="양식 hwpx (읽기 전용)")
    ap.add_argument("--style-map", required=True, help="style_map.json")
    ap.add_argument("--blocks", nargs="+", required=True, help="blocks JSON (본문 순서대로)")
    ap.add_argument("--references", help="references.json")
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

    with open(args.style_map, encoding="utf-8") as f:
        style_map = json.load(f)
    template = Template(args.template)
    doc = Document(template, style_map)

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
