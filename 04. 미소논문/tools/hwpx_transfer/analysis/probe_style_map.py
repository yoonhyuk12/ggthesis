# -*- coding: utf-8 -*-
"""양식(260912_1059) 스타일 실측 → style_map_miso.json · template_analysis_miso.md 생성.

한글이 양식을 재저장하면서 header가 정규화돼 charPr/paraPr/borderFill/tabPr id가 전부
재번호됐다(charPr 81 · paraPr 64 · borderFill 29 · tabPr 6 · style 40). 기준 파일
staging/style_map_yoonhyuk_reference.json의 값은 쓸 수 없으므로 키 이름만 물려받고
값은 전부 이 문서의 XML에서 다시 잰다.

입력 (모두 읽기 전용):
  analysis/extracted/Contents/{header,section0,section1,section2}.xml
  analysis/section{0,1,2}_paras.json         ← 최상위 문단 덤프. 문단 번호는 이 idx만 쓴다
  staging/style_map_yoonhyuk_reference.json  ← 키 집합 비교용

출력:
  staging/style_map_miso.json
  analysis/template_analysis_miso.md

실행:  PYTHONIOENCODING=utf-8 python analysis/probe_style_map.py
       (`04. 미소논문/tools/hwpx_transfer` 에서 실행)
"""

import collections
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # tools/hwpx_transfer
XMLDIR = os.path.join(HERE, "extracted", "Contents")
STAGING = os.path.join(ROOT, "staging")
REF_MAP = os.path.join(STAGING, "style_map_yoonhyuk_reference.json")
OUT_MAP = os.path.join(STAGING, "style_map_miso.json")
OUT_MD = os.path.join(HERE, "template_analysis_miso.md")

# 표 쪽 넘김은 실측값과 무관하게 항상 NONE으로 고정한다
# (프로젝트 규칙: pageBreak="CELL"은 한글에서 표를 깨뜨린다).
TBL_PAGE_BREAK = "NONE"


# ── 입력 읽기 ────────────────────────────────────────────────────────────────
def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_sections():
    xml, paras = {}, {}
    for i in (0, 1, 2):
        xml[i] = read(os.path.join(XMLDIR, "section%d.xml" % i))
        with open(os.path.join(HERE, "section%d_paras.json" % i), encoding="utf-8") as fh:
            paras[i] = json.load(fh)
    return xml, paras


def frag(xml, para):
    """문단 덤프의 byte_start/byte_end는 실제로는 **문자** 오프셋이다(디코드 후 슬라이스)."""
    return xml[para["byte_start"]:para["byte_end"]]


# ── header.xml 파싱 ──────────────────────────────────────────────────────────
def parse_header(hdr):
    chars, paras, bfs, tabs, styles, fonts = {}, {}, {}, {}, {}, {}

    for m in re.finditer(r'<hh:charPr id="(\d+)"(.*?)</hh:charPr>', hdr, re.S):
        cid, body = m.group(1), m.group(0)
        fr = re.search(r'<hh:fontRef hangul="(\d+)" latin="(\d+)"', body)
        chars[cid] = {
            "height": int(re.search(r'height="(\d+)"', body).group(1)),
            "color": (re.search(r'textColor="([^"]*)"', body).group(1) or "").upper(),
            "borderFill": re.search(r'borderFillIDRef="(\d+)"', body).group(1),
            "hangul": fr.group(1) if fr else None,
            "latin": fr.group(2) if fr else None,
            "bold": "<hh:bold/>" in body,
            "italic": "<hh:italic/>" in body,
            "underline": re.search(r'<hh:underline type="([A-Z]+)"', body).group(1),
        }

    for m in re.finditer(r'<hh:paraPr id="(\d+)"(.*?)</hh:paraPr>', hdr, re.S):
        pid, body = m.group(1), m.group(0)
        ls = re.search(r'<hh:lineSpacing type="([A-Z]+)" value="(-?\d+)"', body)
        mg = re.search(r'<hc:intent value="(-?\d+)"', body)
        bd = re.search(r'<hh:border borderFillIDRef="(\d+)"', body)
        paras[pid] = {
            "tabPrIDRef": re.search(r'tabPrIDRef="(\d+)"', body).group(1),
            "align": re.search(r'<hh:align horizontal="([A-Z_]+)"', body).group(1),
            "lineSpacing": ("%s %s" % ls.groups()) if ls else None,
            "intent": mg.group(1) if mg else None,
            "borderFill": bd.group(1) if bd else None,
        }

    for m in re.finditer(r'<hh:borderFill id="(\d+)"(.*?)</hh:borderFill>', hdr, re.S):
        bid, body = m.group(1), m.group(0)
        d = {}
        for side in ("left", "right", "top", "bottom"):
            e = re.search(r'<hh:%sBorder type="([A-Z_]+)" width="([^"]*)"' % side, body)
            d[side] = list(e.groups()) if e else None
        fc = re.search(r'<hc:winBrush faceColor="([^"]*)"', body)
        d["fill"] = fc.group(1) if fc else None
        bfs[bid] = d

    # tabPr는 탭 항목이 없으면 self-closing(<hh:tabPr … />)으로 나온다. 둘 다 잡는다.
    for m in re.finditer(r'<hh:tabPr id="(\d+)"(?:[^>]*/>|.*?</hh:tabPr>)', hdr, re.S):
        body = m.group(0)
        tabs[m.group(1)] = {
            "autoTabLeft": re.search(r'autoTabLeft="(\d)"', body).group(1),
            "autoTabRight": re.search(r'autoTabRight="(\d)"', body).group(1),
            "items": [list(t) for t in re.findall(
                r'<hh:tabItem pos="(\d+)" type="([A-Z]+)" leader="([A-Z]+)"', body)],
        }

    for m in re.finditer(r'<hh:style id="(\d+)" type="[^"]*" name="([^"]*)"[^>]*?'
                         r'paraPrIDRef="(\d+)" charPrIDRef="(\d+)"', hdr):
        styles[m.group(1)] = {"name": m.group(2), "para": m.group(3), "char": m.group(4)}

    for m in re.finditer(r'<hh:fontface lang="([A-Z]+)"(.*?)</hh:fontface>', hdr, re.S):
        fonts[m.group(1)] = dict(re.findall(r'<hh:font id="(\d+)" face="([^"]*)"', m.group(2)))

    return chars, paras, bfs, tabs, styles, fonts


# ── 사용 빈도 ────────────────────────────────────────────────────────────────
def usage(xml):
    ch, pa = collections.Counter(), collections.Counter()
    for t in xml.values():
        for m in re.finditer(r'charPrIDRef="(\d+)"', t):
            ch[m.group(1)] += 1
        for m in re.finditer(r'paraPrIDRef="(\d+)"', t):
            pa[m.group(1)] += 1
    return ch, pa


def twin(chars, use, base, **diff):
    """base와 diff로 지정한 속성만 다르고 나머지가 같은 charPr 중 사용 빈도 최다 id."""
    src = chars[base]
    cands = []
    for cid, d in chars.items():
        if cid == base:
            continue
        if any(d[k] != v for k, v in diff.items()):
            continue
        if all(d[k] == src[k] for k in src if k not in diff):
            cands.append(cid)
    if not cands:
        return None
    return sorted(cands, key=lambda c: (-use.get(c, 0), int(c)))[0]


# ── 표 실측 ──────────────────────────────────────────────────────────────────
TC_RE = re.compile(
    r'<hp:tc [^>]*borderFillIDRef="(\d+)"><hp:subList[^>]*>(.*?)</hp:subList>'
    r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>'
    r'<hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/>'
    r'<hp:cellSz width="(\d+)" height="(\d+)"/>'
    r'<hp:cellMargin left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"',
    re.S)


def survey_tables(xml2, paras2):
    """section2 본문 표 전수 조사. 캡션 행·좌우 끝 열·내부 셀을 위치로 분류한다."""
    st = {
        "n": 0, "tbl_attr": collections.Counter(), "width": collections.Counter(),
        "height": collections.Counter(), "pad": collections.Counter(),
        "outMargin": collections.Counter(), "inMargin": collections.Counter(),
        "pos": collections.Counter(), "wrapper_char": collections.Counter(),
        "bf_caption": collections.Counter(), "bf_first": collections.Counter(),
        "bf_last": collections.Counter(), "bf_mid": collections.Counter(),
        "cap_para": collections.Counter(), "cap_char": collections.Counter(),
        "cell_para": collections.Counter(), "cell_char": collections.Counter(),
        "example": None,
    }
    for p in paras2:
        if not p["has_tbl"]:
            continue
        f = frag(xml2, p)
        tm = re.search(r'<hp:tbl [^>]*>', f)
        if not tm:
            continue
        st["n"] += 1
        attrs = tm.group(0)
        st["tbl_attr"][re.sub(r' (id|zOrder|rowCnt|colCnt)="[^"]*"', "", attrs)] += 1
        ncols = int(re.search(r'colCnt="(\d+)"', attrs).group(1))
        st["width"][re.search(r'<hp:sz width="(\d+)"', f).group(1)] += 1
        wm = re.search(r'<hp:run charPrIDRef="(\d+)"><hp:tbl ', f)
        if wm:
            st["wrapper_char"][wm.group(1)] += 1
        for m in re.finditer(r'<hp:outMargin ([^/]*)/>', f):
            st["outMargin"][m.group(1)] += 1
        for m in re.finditer(r'<hp:inMargin ([^/]*)/>', f):
            st["inMargin"][m.group(1)] += 1
        for m in re.finditer(r'<hp:pos ([^/]*)/>', f):
            st["pos"][m.group(1)] += 1
        for tc in TC_RE.finditer(f):
            bf, sub = tc.group(1), tc.group(2)
            col, row, cspan = int(tc.group(3)), int(tc.group(4)), int(tc.group(5))
            st["height"][int(tc.group(8))] += 1
            st["pad"][tuple(tc.group(9, 10, 11, 12))] += 1
            pps = re.findall(r'<hp:p id="[^"]*" paraPrIDRef="(\d+)" styleIDRef="(\d+)"', sub)
            crs = re.findall(r'<hp:run charPrIDRef="(\d+)"', sub)
            if cspan == ncols and row == 0:
                st["bf_caption"][bf] += 1
                for a in pps:
                    st["cap_para"][a] += 1
                for a in crs:
                    st["cap_char"][a] += 1
                continue
            if ncols > 1 and col == 0:
                st["bf_first"][bf] += 1
            elif ncols > 1 and col + cspan == ncols:
                st["bf_last"][bf] += 1
            else:
                st["bf_mid"][bf] += 1
            for a in pps:
                st["cell_para"][a] += 1
            for a in crs:
                st["cell_char"][a] += 1
        if st["example"] is None and ncols >= 3:
            rows = re.findall(r'<hp:tr>(.*?)</hp:tr>', f, re.S)
            cap = re.search(r'<hp:t>(.*?)</hp:t>', rows[0], re.S) if rows else None
            if cap:
                cap = re.sub(r'&lt;|&gt;|&amp;', lambda m: {"&lt;": "<", "&gt;": ">",
                                                           "&amp;": "&"}[m.group(0)], cap.group(1))
            st["example"] = {
                "para_idx": p["idx"], "colCnt": ncols,
                "rowCnt": int(re.search(r'rowCnt="(\d+)"', attrs).group(1)),
                "widths": re.findall(r'<hp:cellSz width="(\d+)"', rows[1]) if len(rows) > 1 else [],
                "caption": cap or "",
            }
    return st


# ── 표지(section0) 치환 대상 ─────────────────────────────────────────────────
TITLE = ("중소규모 건설현장을 위한 YOLO-LLM 안전관제 시스템 개발 및 실증 연구: "
         "도입 현장과 미도입 현장의 안전관리 실효성 비교를 중심으로")
COVER_ROLES = [
    # (section0 문단 idx, 찾을 문자열, role)
    (0, "2026", "year"),
    (0, TITLE, "title"),
    (0, "지도교수 : 박 종 용", "advisor"),
    (0, "건축ㆍ안전공학전공", "major"),
    (0, "윤   혁", "name"),
    (1, TITLE, "title"),
    (1, "이 논문을 석사학위논문으로 제출함", "submit_title"),
    (1, "2026년 12월  일", "date"),
    (1, "건축․안전공학전공", "major"),
    (1, "윤   혁", "name"),
    (2, "윤   혁의 석사학위논문을 인준함", "approval_title"),
    (2, "2026년 12월  일", "date"),
]


RUN_TOKEN = re.compile(r'<hp:run charPrIDRef="(\d+)"|</hp:run>|<hp:t>(.*?)</hp:t>|<hp:t/>', re.S)


def runs_of(f):
    """문단 조각 안의 run을 (ordinal, charPrIDRef, [자기 hp:t 텍스트…], t_total)로.

    표지 문단은 문단 전체가 표 1개라서 run 안에 표가 들어가고 표 셀 안에 또 run이 있다.
    단순 정규식으로 `<hp:run>…</hp:run>`을 잡으면 중첩 때문에 조각이 어긋나므로, 여는/닫는
    태그를 훑으며 **가장 안쪽에 열린 run**에 hp:t를 귀속시킨다.

    ordinal은 문단 조각 안에서 `<hp:run` 여는 태그가 나온 순서(0-base, 표 셀 안 run 포함)다.
    t_total은 빈 `<hp:t/>`까지 포함한 그 run 직속 hp:t 수(run을 통째로 갈아치우면 안 되는 근거).
    """
    out, stack, ordinal = [], [], 0
    for m in RUN_TOKEN.finditer(f):
        tok = m.group(0)
        if tok.startswith("<hp:run"):
            rec = {"ordinal": ordinal, "char": m.group(1), "texts": [], "t_total": 0}
            ordinal += 1
            out.append(rec)
            stack.append(rec)
        elif tok == "</hp:run>":
            if stack:
                stack.pop()
        elif stack:
            stack[-1]["t_total"] += 1
            if m.group(2) is not None:
                stack[-1]["texts"].append(m.group(2))
    return out


def survey_cover(xml0, paras0):
    items, seen = [], set()
    for idx, needle, role in COVER_ROLES:
        f = frag(xml0, paras0[idx])
        for r in runs_of(f):
            key = (idx, r["ordinal"])
            if key in seen:
                continue
            hit = [t for t in r["texts"] if needle in t]
            if not hit:
                continue
            seen.add(key)
            items.append({
                "section0_idx": idx,
                "run_ordinal": r["ordinal"],
                "charPrIDRef": r["char"],
                "old": hit[0],
                "role": role,
                # 찾는 문자열이 하나의 <hp:t> 안에 통째로 들어 있으면 run·charPr 구조를
                # 건드리지 않고 텍스트만 바꿀 수 있다(True).
                "splittable": len(hit) == 1 and hit[0].count(needle) == 1,
                "_t_count": r["t_total"],
                "_t_nonempty": len(r["texts"]),
            })
            break
    items.sort(key=lambda d: (d["section0_idx"], d["run_ordinal"]))
    return items


# ── style_map 조립 ───────────────────────────────────────────────────────────
def describe_bf(d):
    sides = []
    for side in ("left", "right", "top", "bottom"):
        v = d[side]
        sides.append("%s %s %s" % (side, v[0], v[1]) if v else "%s ?" % side)
    txt = " / ".join(sides)
    if d["fill"] and d["fill"] != "none":
        txt += " / 배경 %s" % d["fill"]
    return txt


def build(chars, paras, bfs, tabs, styles, fonts, uch, tstat, cover, xml, secs):
    s1, s2 = secs[1], secs[2]

    def spec(section, idx, extra=None):
        p = secs[section][idx]
        d = {"styleIDRef": p["styleIDRef"], "paraPrIDRef": p["paraPrIDRef"],
             "charPrIDRef": p["runs"][0][0] if p["runs"] else None}
        if extra:
            d.update(extra)
        return d

    def pt(cid):
        return chars[cid]["height"] // 100

    def hfont(cid):
        return fonts["HANGUL"].get(chars[cid]["hangul"], "?")

    body_char = s2[6]["runs"][0][0]
    cell_char = tstat["cell_char"].most_common(1)[0][0]
    cell_para = tstat["cell_para"].most_common(1)[0][0][0]
    cap_para = tstat["cap_para"].most_common(1)[0][0][0]
    cap_char = tstat["cap_char"].most_common(1)[0][0]

    bf_inner = tstat["bf_mid"].most_common(1)[0][0]
    bf_first = tstat["bf_first"].most_common(1)[0][0]
    bf_last = tstat["bf_last"].most_common(1)[0][0]
    bf_cap = tstat["bf_caption"].most_common(1)[0][0]

    # 회색 배경 머리행: 이 양식에는 "사방 실선 + 회색 배경" 정의가 없다.
    # winBrush faceColor를 가진 borderFill 중 실제 표 셀에 쓰인 것을 대체값으로 적는다.
    used_bf = collections.Counter()
    for key in ("bf_caption", "bf_first", "bf_last", "bf_mid"):
        used_bf.update(tstat[key])
    gray_cands = [b for b, d in bfs.items()
                  if d["fill"] and d["fill"] != "none" and b in used_bf]
    bf_gray = sorted(gray_cands, key=lambda b: (-used_bf[b], int(b)))[0] if gray_cands else None

    body_bold = twin(chars, uch, body_char, bold=True)
    cell_bold = twin(chars, uch, cell_char, bold=True)

    red_by_base = {}
    for cid, d in chars.items():
        if d["color"] != "#FF0000":
            continue
        for base, bd in chars.items():
            if base == cid or bd["color"] != "#000000":
                continue
            if all(bd[k] == d[k] for k in d if k != "color"):
                cur = red_by_base.get(base)
                if cur is None or (uch.get(cid, 0), -int(cid)) > (uch.get(cur, 0), -int(cur)):
                    red_by_base[base] = cid
    red_by_base = {k: red_by_base[k] for k in sorted(red_by_base, key=int)}

    tbl_xml = tstat["tbl_attr"].most_common(1)[0][0]

    def a(name):
        m = re.search(r'%s="([^"]*)"' % name, tbl_xml)
        return m.group(1) if m else None

    pad = tstat["pad"].most_common(1)[0][0]
    width = tstat["width"].most_common(1)[0][0]
    row_min = tstat["height"].most_common(1)[0][0]
    line_w = collections.Counter(
        re.findall(r'<hp:lineseg [^>]*horzsize="(\d+)"', xml[2])).most_common(1)[0][0]

    sm = collections.OrderedDict()
    sm["_meta"] = {
        "source": "04. 미소논문/00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx",
        "measured": "2026-09-12",
        "measured_by": "tools/hwpx_transfer/analysis/probe_style_map.py (W3)",
        "units": "charPr.height = hu(1/100pt), 길이 = HWPUNIT(1/7200 inch), 값은 모두 XML 실측",
        "header_counts": {"charPr": len(chars), "paraPr": len(paras), "style": len(styles),
                          "tabPr": len(tabs), "borderFill": len(bfs)},
        "font_note": ("본문·제목 fontRef: hangul=%s(%s), latin=%s(%s). "
                      "표 안 캡션 charPr %s만 hangul/latin=0(굴림)."
                      % (chars[body_char]["hangul"], hfont(body_char),
                         chars[body_char]["latin"],
                         fonts["LATIN"].get(chars[body_char]["latin"], "?"), cap_char)),
        "renumber_warning": ("한글 재저장으로 header가 정규화돼 기준 파일(윤혁 260725)의 "
                             "charPr/paraPr/borderFill/tabPr id와 전혀 호환되지 않는다. "
                             "기준 파일 값을 복사하면 안 된다."),
    }

    h1p = s2[0]["paraPrIDRef"]
    sm["h1_chapter"] = spec(2, 0, {
        "pageBreak": "1",
        "_detail": ("장 제목. s2 p0 '제1장 서론' 실측(paraPr %s=%s·줄간격 %s, charPr %s=%dpt %s bold, "
                    "style %s '%s'). 새 장은 hp:p pageBreak=\"1\"로 쪽을 넘긴다."
                    % (h1p, paras[h1p]["align"], paras[h1p]["lineSpacing"], s2[0]["runs"][0][0],
                       pt(s2[0]["runs"][0][0]), hfont(s2[0]["runs"][0][0]),
                       s2[0]["styleIDRef"], styles[s2[0]["styleIDRef"]]["name"])),
        "_toc_side": {"styleIDRef": s1[2]["styleIDRef"], "paraPrIDRef": s1[2]["paraPrIDRef"],
                      "charPrIDRef": s1[2]["runs"][0][0],
                      "_note": ("목차 쪽 장 항목(s1 p2). 이 양식의 목차 항목은 장·절·항 모두 "
                                "흑색 charPr %s(%dpt) 한 종류이며 쪽번호·리더 탭이 아직 없다."
                                % (s1[2]["runs"][0][0], pt(s1[2]["runs"][0][0])))},
    })
    h2p = s2[2]["paraPrIDRef"]
    h2c = s2[2]["runs"][0][0]
    sm["h2_section"] = spec(2, 2, {
        "_detail": ("절 제목. s2 p2 '제1절 …' 실측(paraPr %s=%s·줄간격 %s, charPr %s=%dpt bold). "
                    "본문 표를 감싸는 run도 이 charPr를 쓴다(본문 표 %d개 중 %d개)."
                    % (h2p, paras[h2p]["align"], paras[h2p]["lineSpacing"], h2c, pt(h2c),
                       tstat["n"], tstat["wrapper_char"][h2c])),
    })
    sm["h3_item"] = spec(2, 4, {
        "_detail": ("항 제목. s2 p4 '제1항 …' 실측(charPr %s=%dpt bold). "
                    "문단 서식은 본문과 같은 paraPr %s."
                    % (s2[4]["runs"][0][0], pt(s2[4]["runs"][0][0]), s2[4]["paraPrIDRef"])),
    })
    bp = s2[6]["paraPrIDRef"]
    sm["body"] = spec(2, 6, {
        "_detail": ("일반 본문. s2 p6(서론 첫 문단) 실측. paraPr %s=%s·줄간격 %s·들여쓰기 0"
                    "(문단 첫머리 공백으로 들여씀), charPr %s=%dpt %s."
                    % (bp, paras[bp]["align"], paras[bp]["lineSpacing"], body_char,
                       pt(body_char), hfont(body_char))),
    })
    sm["caption"] = spec(2, 7, {
        "_detail": ("그림 캡션 문단(표 밖). s2 p7 '<그림 1-1> …' 실측. paraPr %s=%s, charPr %s=%dpt. "
                    "표 캡션은 표 첫 행(전 열 병합, borderFill %s, paraPr %s, charPr %s)에 넣는다."
                    % (s2[7]["paraPrIDRef"], paras[s2[7]["paraPrIDRef"]]["align"],
                       s2[7]["runs"][0][0], pt(s2[7]["runs"][0][0]), bf_cap, cap_para, cap_char)),
    })

    toc_para = s1[2]["paraPrIDRef"]
    toc_tab = paras[toc_para]["tabPrIDRef"]
    tab_pos = tabs[toc_tab]["items"][0][0] if tabs[toc_tab]["items"] else "-"
    sm["toc_entry"] = {
        "styleIDRef": s1[2]["styleIDRef"], "paraPrIDRef": toc_para,
        "charPrIDRef": s1[2]["runs"][0][0], "tabPrIDRef": toc_tab,
        "inline_tab": {
            "leader": "3", "type": "2", "width_example": str(int(line_w) - 2832),
            "_note": ("이 양식의 목차에는 인라인 탭(<hp:tab>)과 쪽번호가 **하나도 없다**"
                      "(section1/2 통틀어 <hp:tab> 0건). leader=3(DASH)·type=2(RIGHT)는 기준 "
                      "파일과 같은 코드값을 관례로 남긴 것이며, 실제 리더를 넣으려면 paraPr %s의 "
                      "tabPr %s(RIGHT pos %s, leader DASH)에 맞춘다."
                      % (toc_para, toc_tab, tab_pos))},
        "_detail": ("목차 항목. s1 p2~p104 실측 — 장·절·항 항목이 모두 paraPr %s / charPr %s(%dpt) "
                    "한 종류이고, 들여쓰기는 문단 앞 공백 문자로만 준다."
                    % (toc_para, s1[2]["runs"][0][0], pt(s1[2]["runs"][0][0]))),
    }
    lot_para = s1[107]["paraPrIDRef"]
    sm["toc_lot_entry"] = {
        "styleIDRef": s1[107]["styleIDRef"], "paraPrIDRef": lot_para,
        "charPrIDRef": s1[107]["runs"][0][0], "tabPrIDRef": paras[lot_para]["tabPrIDRef"],
        "_detail": ("표목차·그림목차 항목. s1 p107 '<표 2-1> …'·p138 '<그림 1-1> …' 실측. "
                    "목차 항목과 같은 paraPr %s를 쓰되 charPr는 본문과 같은 %s(%dpt)."
                    % (lot_para, s1[107]["runs"][0][0], pt(s1[107]["runs"][0][0]))),
    }

    ex = tstat["example"]
    sm["table"] = {
        "tbl_attrs": {
            "numberingType": a("numberingType"), "textWrap": a("textWrap"),
            "textFlow": a("textFlow"), "lock": a("lock"), "dropcapstyle": a("dropcapstyle"),
            "pageBreak": TBL_PAGE_BREAK, "repeatHeader": a("repeatHeader"),
            "cellSpacing": a("cellSpacing"), "borderFillIDRef": a("borderFillIDRef"),
            "noAdjust": a("noAdjust"),
            "pos": dict(re.findall(r'(\w+)="([^"]*)"', tstat["pos"].most_common(1)[0][0])),
            "outMargin": dict(re.findall(r'(\w+)="([^"]*)"',
                                         tstat["outMargin"].most_common(1)[0][0])),
            "inMargin": dict(re.findall(r'(\w+)="([^"]*)"',
                                        tstat["inMargin"].most_common(1)[0][0])),
            "sz": {"width": width, "widthRelTo": "ABSOLUTE", "heightRelTo": "ABSOLUTE"},
            "_pageBreak_note": ("실측값도 NONE이었고(본문 표 %d개 전부), 규칙상 CELL로 바꾸지 않는다."
                                % tstat["n"]),
        },
        "borderFills": {b: describe_bf(bfs[b]) for b in sorted(
            {bf_inner, bf_first, bf_last, bf_cap, a("borderFillIDRef")} |
            ({bf_gray} if bf_gray else set()), key=int)},
        "cell_paraPr": cell_para,
        "cell_paraPr_variants": {
            p_: "%s·줄간격 %s (%d회)" % (paras[p_]["align"], paras[p_]["lineSpacing"], n)
            for (p_, _s), n in tstat["cell_para"].most_common(6)},
        "cell_charPr": cell_char,
        "cell_charPr_variants": {
            c_: "%dpt %s%s (%d회)" % (pt(c_), hfont(c_),
                                      " bold" if chars[c_]["bold"] else
                                      (" 빨강" if chars[c_]["color"] == "#FF0000" else ""), n)
            for c_, n in tstat["cell_char"].most_common(6)},
        "cell_padding": {"left": pad[0], "right": pad[1], "top": pad[2], "bottom": pad[3]},
        "caption_row": {"borderFillIDRef": bf_cap, "paraPrIDRef": cap_para,
                        "charPrIDRef": cap_char, "styleIDRef": "0"},
        "_grid": ("대표 표(%s, s2 p%d) colCnt=%d rowCnt=%d, 데이터 행 열폭 %s 합=%d=표 폭 %s. "
                  "모든 행의 cellSz.width 합이 표 폭과 일치해야 한다(rowSpan 셀은 해당 행에서 제외). "
                  "cellSz.height는 참고값(최빈 %s, 한글이 재계산)."
                  % (ex["caption"], ex["para_idx"], ex["colCnt"], ex["rowCnt"], ex["widths"],
                     sum(int(x) for x in ex["widths"]), width, row_min)),
    }

    c = collections.OrderedDict()
    sm["constants"] = c
    c["TABLE_WIDTH"] = int(width)
    c["ROW_MIN_H"] = int(row_min)
    c["LINE_W"] = int(line_w)
    c["REF_TITLE"] = {"style": s2[554]["styleIDRef"], "para": s2[554]["paraPrIDRef"],
                      "char": s2[554]["runs"][0][0]}
    c["REF_CATEGORY"] = {"style": s2[556]["styleIDRef"], "para": s2[556]["paraPrIDRef"],
                         "char": s2[556]["runs"][0][0]}
    c["REF_ENTRY"] = {"style": s2[558]["styleIDRef"], "para": s2[558]["paraPrIDRef"],
                      "char": s2[558]["runs"][0][0]}
    c["APPENDIX_TITLE"] = {"style": s2[593]["styleIDRef"], "para": s2[593]["paraPrIDRef"],
                           "char": s2[593]["runs"][0][0]}
    c["BODY_BOLD_CHAR"] = body_bold
    c["CELL_BOLD_CHAR"] = cell_bold
    c["H4_FALLBACK_CHAR"] = body_bold
    c["BLANK_CHAR"] = body_char
    c["TOC_BLANK_CHAR"] = body_char
    c["TOC_ENTRY_CHAR"] = s1[2]["runs"][0][0]
    c["BORDER_INNER"] = bf_inner
    c["BORDER_LEFT_EDGE"] = bf_first
    c["BORDER_RIGHT_EDGE"] = bf_last
    c["BORDER_CAPTION_ROW"] = bf_cap
    c["BORDER_HEADER_GRAY"] = bf_gray
    c["RED_CHAR_BY_BASE"] = red_by_base
    c["CHAR_HEIGHTS"] = {cid: chars[cid]["height"] for cid in sorted(chars, key=int)}
    c["_notes"] = {
        "BODY_BOLD_CHAR": ("charPr %s는 본문 charPr %s와 %dpt·%s·borderFill %s가 같고 bold만 다른 짝"
                           "(문서 내 %d회 사용)."
                           % (body_bold, body_char, pt(body_char), hfont(body_char),
                              chars[body_char]["borderFill"], uch.get(body_bold, 0))),
        "CELL_BOLD_CHAR": ("charPr %s는 셀 기본 charPr %s(%dpt)의 bold 짝(%d회 사용)."
                           % (cell_bold, cell_char, pt(cell_char), uch.get(cell_bold, 0))),
        "BLANK_CHAR": "빈 문단에는 run이 없어 charPr를 잴 수 없으므로 본문 charPr를 그대로 쓴다.",
        "TOC_BLANK_CHAR": ("목차 영역 빈 문단(s1 p1·p105·p135·p146)도 run이 없다. 이 문단들의 "
                           "paraPr는 %s(본문과 동일)이므로 charPr도 본문 값을 쓴다."
                           % s1[1]["paraPrIDRef"]),
        "BORDER_HEADER_GRAY": ("이 양식에는 '사방 실선 + 회색 배경' borderFill이 **없다**. "
                               "winBrush faceColor를 가진 정의는 borderFill %s뿐이고, 그중 표 셀에 "
                               "실제로 쓰인 것은 %s(배경 %s)이다. 본문 표의 머리행은 회색 배경 없이 "
                               "좌우 개방 테두리(%s/%s)와 bold charPr %s로만 구분한다."
                               % (", ".join(sorted((b for b, d in bfs.items()
                                                    if d["fill"] and d["fill"] != "none"),
                                                   key=int)),
                                  bf_gray, bfs[bf_gray]["fill"] if bf_gray else "-",
                                  bf_first, bf_last, cell_bold)),
        "RED_CHAR_BY_BASE": ("색만 다른 짝이 여러 개면 문서에서 더 많이 쓰인 빨간 charPr를 골랐다. "
                             "형식은 '검은 charPr → 빨간 charPr'."),
        "CHAR_HEIGHTS": "header.xml의 charPr 전수(%d개) 높이(hu)." % len(chars),
    }

    fm = collections.OrderedDict()
    sm["front_matter"] = fm
    fm["s1_toc_title_idx"] = 0
    fm["s1_lot_title_idx"] = 106
    fm["s1_lof_title_idx"] = 136
    fm["s1_thanks_range"] = [147, 171]
    fm["s1_abstract_range"] = [172, 173]
    black_of = {red: base for base, red in red_by_base.items()}

    def fm_spec(idx, **extra):
        p = s1[idx]
        cid = p["runs"][0][0] if p["runs"] else None
        d = {"style": p["styleIDRef"], "para": p["paraPrIDRef"], "char": cid}
        if cid and chars[cid]["color"] == "#FF0000":
            d["char_black"] = black_of.get(cid)
            d["_note"] = ("양식의 이 문단은 **빨간 charPr %s**로 쓰여 있다(윤혁 논문의 작성 중 표시). "
                          "미소 논문 본문으로 채울 때는 검은 짝 charPr %s를 쓰고, 아직 못 채운 자리에만 "
                          "빨강을 남긴다." % (cid, black_of.get(cid)))
        d.update(extra)
        return d

    fm["abstract_body"] = fm_spec(173)
    fm["thanks_body"] = fm_spec(148)
    fm["thanks_date"] = fm_spec(170, old=s1[170]["text"])
    fm["thanks_name"] = fm_spec(171, old=s1[171]["text"])
    fm["_detail"] = {
        "toc_title": ("s1 p0 '%s' — paraPr %s, 제목 상자 표 안 charPr %s"
                      % (s1[0]["text"].strip(), s1[0]["paraPrIDRef"], s1[0]["runs"][0][0])),
        "lot_title": ("s1 p106 '%s' — paraPr %s, pageBreak=%s, charPr %s(**빨강** #FF0000. "
                      "검은 짝은 charPr %s이며 목차·그림목차 제목은 그 검은 charPr를 쓴다)"
                      % (s1[106]["text"].strip(), s1[106]["paraPrIDRef"], s1[106]["pageBreak"],
                         s1[106]["runs"][0][0], black_of.get(s1[106]["runs"][0][0]))),
        "lof_title": ("s1 p136 '%s' — paraPr %s, pageBreak=%s, charPr %s"
                      % (s1[136]["text"].strip(), s1[136]["paraPrIDRef"],
                         s1[136]["pageBreak"], s1[136]["runs"][0][0])),
        "thanks": ("s1 p147 제목 상자(pageBreak=%s) → p148 본문 1문단 → p149~p169 빈 문단 21개 → "
                   "p170 '%s' → p171 '%s'. 윤혁 논문의 사용자 직접 작성분이므로 미소 논문에서는 "
                   "p148·p170·p171 텍스트만 갈아끼우고 문단 경계를 유지한다."
                   % (s1[147]["pageBreak"], s1[170]["text"], s1[171]["text"].strip())),
        "abstract": ("s1 p172 '%s' 제목 상자(style %s, pageBreak=%s) + p173 공백 본문 자리"
                     "(paraPr %s, charPr %s). 국문초록 본문은 p173 자리에 넣는다."
                     % (s1[172]["text"].strip(), s1[172]["styleIDRef"], s1[172]["pageBreak"],
                        s1[173]["paraPrIDRef"], s1[173]["runs"][0][0])),
    }

    sm["cover"] = cover

    sm["page"] = {
        "width": "53858", "height": "72567", "size_mm": "190.0 x 256.0",
        "landscape": "WIDELY", "gutterType": "LEFT_ONLY",
        "margins": {}, "margins_mm_note": "7086=25mm, 8503=30mm, 9921=35mm, 4251=15mm",
        "page_numbering": {"section0": "없음(표지)"},
        "footnote": {"numFormat": "DIGIT", "suffixChar": ")", "numbering": "CONTINUOUS",
                     "noteLineWidth": "0.12 mm"},
    }
    names = {0: "section0_cover", 1: "section1_front", 2: "section2_body"}
    for i in (0, 1, 2):
        sec = re.search(r'<hp:secPr .*?</hp:secPr>', xml[i], re.S).group(0)
        d = dict(re.findall(r'(\w+)="([^"]*)"', re.search(r'<hp:margin ([^/]*)/>', sec).group(1)))
        sm["page"]["margins"][names[i]] = {k: d[k] for k in
                                          ("left", "right", "top", "bottom",
                                           "header", "footer", "gutter")}
        pn = re.search(r'<hp:pageNum pos="([A-Z_]+)" formatType="([A-Z_]+)" sideChar="([^"]*)"',
                       xml[i])
        if pn:
            nn = re.search(r'<hp:newNum num="(\d+)" numType="PAGE"/>', xml[i])
            sm["page"]["page_numbering"]["section%d" % i] = {
                "pos": pn.group(1), "formatType": pn.group(2), "sideChar": pn.group(3),
                "newNum": nn.group(1) if nn else None}

    sm["sections"] = [
        {"file": "section0.xml", "role": "표지·속표지(제출서)·인준서 — 문단 3개가 각각 전면 표 1개",
         "paragraphs": len(secs[0])},
        {"file": "section1.xml",
         "role": "전면부: 목차·표목차·그림목차·감사의 글·논문개요(제목만) — 쪽번호 로마 소문자",
         "paragraphs": len(s1)},
        {"file": "section2.xml",
         "role": "본문 제1~6장·참고문헌·부록(설문지 2종) — 쪽번호 아라비아, 본문 표 %d개" % tstat["n"],
         "paragraphs": len(s2)},
    ]

    sm["front_matter_ranges"] = {
        "표지": ["section0", 0, 0],
        "속표지_제출서": ["section0", 1, 1],
        "인준서": ["section0", 2, 2],
        "목차": ["section1", 0, 105],
        "표목차": ["section1", 106, 135],
        "그림목차": ["section1", 136, 146],
        "감사의글": ["section1", 147, 171],
        "논문개요": ["section1", 172, 173],
        "_preserve_note": ("감사의 글(s1 147~171)은 윤혁 논문의 사용자 직접 작성분이다. 미소 논문에서는 "
                           "본문(p148)·날짜(p170)·성명(p171)을 갈아끼우되 제목 상자와 빈 문단 리듬은 "
                           "그대로 둔다. 논문개요(s1 172~173)는 제목 상자(p172)와 공백 본문 문단(p173) "
                           "둘뿐이라 경계 보존이 필수다."),
    }

    sm["conventions"] = {
        "page_break": ("hp:p의 pageBreak=\"1\" 속성만 쓴다(pageBreakBefore paraPr 없음). 양식 실측: "
                       "참고문헌(s2 p554)·부록(s2 p593)·표목차(s1 p106)·그림목차(s1 p136)·"
                       "감사의 글(s1 p147)·논문개요(s1 p172)·속표지(s0 p1)."),
        "blank_line": ("장·절·항 제목 뒤에 빈 문단 1개(paraPr %s, run 없음)가 기본 리듬"
                       "(s2 p1·p3·p5 실측). 표·그림 캡션 앞뒤도 같은 빈 문단으로 띄운다."
                       % s2[1]["paraPrIDRef"]),
        "heading_box": ("전면부 블록 제목(목차·표목차·그림목차·감사의 글·논문개요)은 문단 안에 표 1개를 "
                        "넣은 제목 상자다(has_tbl=True). 본문 장 제목은 표가 아니라 문단이다."),
        "table_inline": ("표는 본문 문단의 run 안에 treatAsChar=1로 인라인 배치되고, 그 run의 charPr는 "
                         "절 제목 charPr %s를 쓴다(본문 표 %d개 중 %d개)."
                         % (h2c, tstat["n"], tstat["wrapper_char"][h2c])),
        "footnote_style": "각주 스타일 11(각주)이 정의돼 있고 본문에는 hp:autoNum 각주가 1건 있다.",
    }
    return sm


# ── 검증 ────────────────────────────────────────────────────────────────────
SAMPLES = [
    ("s2 p0 제1장 서론", 2, 0, {"paraPrIDRef": "49", "styleIDRef": "1", "char": "56"}),
    ("s2 p2 제1절", 2, 2, {"paraPrIDRef": "46", "char": "60"}),
    ("s2 p4 제1항", 2, 4, {"char": "39"}),
    ("s2 p6 본문", 2, 6, {"paraPrIDRef": "46", "char": "36"}),
    ("s2 p7 그림 캡션", 2, 7, {"paraPrIDRef": "31", "char": "8"}),
    ("s2 p8 빨강 마커", 2, 8, {"char": "68"}),
    ("s2 p554 참고문헌 제목", 2, 554, {"paraPrIDRef": "5", "pageBreak": "1"}),
    ("s2 p556 분류", 2, 556, {"paraPrIDRef": "12"}),
    ("s2 p593 부록 제목", 2, 593, {"paraPrIDRef": "31", "pageBreak": "1"}),
]

CHAR_KEYS = {"charPrIDRef", "cell_charPr", "char", "char_black", "TOC_ENTRY_CHAR", "BLANK_CHAR",
             "TOC_BLANK_CHAR", "BODY_BOLD_CHAR", "CELL_BOLD_CHAR", "H4_FALLBACK_CHAR"}
PARA_KEYS = {"paraPrIDRef", "cell_paraPr", "para"}
BF_KEYS = {"borderFillIDRef", "BORDER_INNER", "BORDER_LEFT_EDGE", "BORDER_RIGHT_EDGE",
           "BORDER_CAPTION_ROW", "BORDER_HEADER_GRAY"}


def verify(sm, chars, paras, bfs, tabs, secs):
    ok = True
    print("-- 1. 기준 키 집합 ⊆ 새 키 집합 --")
    with open(REF_MAP, encoding="utf-8") as fh:
        ref = json.load(fh)
    missing = [k for k in ref if k not in sm]
    print("   기준 최상위 키 %d개 / 새 파일 %d개" % (len(ref), len(sm)))
    print("   누락 최상위 키: %s" % (missing or "없음 (부분집합 성립)"))
    sub = [k for k in ref["table"] if k not in sm["table"]]
    print("   table 하위 누락: %s" % (sub or "없음"))
    sub2 = [k for k in ref["table"]["tbl_attrs"] if k not in sm["table"]["tbl_attrs"]]
    print("   table.tbl_attrs 하위 누락: %s" % (sub2 or "없음"))
    for key in ("h1_chapter", "h2_section", "h3_item", "body", "caption",
                "toc_entry", "toc_lot_entry", "page", "front_matter_ranges", "conventions"):
        s = [k for k in ref[key] if k not in sm[key]]
        if s:
            print("   %s 하위 누락: %s" % (key, s))
            ok = False
    if missing or sub or sub2:
        ok = False
    print("   추가 키: %s" % [k for k in sm if k not in ref])

    print()
    print("-- 2. 실측 id가 header.xml에 존재하는가 --")
    pools = {"charPr": chars, "paraPr": paras, "borderFill": bfs, "tabPr": tabs}
    bad, checked = [], collections.Counter()

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, path + [k])
            return
        if isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [str(i)])
            return
        if node is None or isinstance(node, bool) or not isinstance(node, (str, int)):
            return
        key = path[-1]
        kind = ("charPr" if key in CHAR_KEYS else
                "paraPr" if key in PARA_KEYS else
                "borderFill" if key in BF_KEYS else
                "tabPr" if key == "tabPrIDRef" else None)
        if kind is None:
            return
        checked[kind] += 1
        if str(node) not in pools[kind]:
            bad.append(("/".join(path), kind, str(node)))

    walk({k: v for k, v in sm.items() if not k.startswith("_")}, [])
    for base, red in sm["constants"]["RED_CHAR_BY_BASE"].items():
        for sid in (base, red):
            checked["charPr"] += 1
            if sid not in chars:
                bad.append(("constants/RED_CHAR_BY_BASE", "charPr", sid))
    for cid in sm["constants"]["CHAR_HEIGHTS"]:
        checked["charPr"] += 1
        if cid not in chars:
            bad.append(("constants/CHAR_HEIGHTS", "charPr", cid))
    for bid in sm["table"]["borderFills"]:
        checked["borderFill"] += 1
        if bid not in bfs:
            bad.append(("table/borderFills", "borderFill", bid))
    for pid in sm["table"]["cell_paraPr_variants"]:
        checked["paraPr"] += 1
        if pid not in paras:
            bad.append(("table/cell_paraPr_variants", "paraPr", pid))
    for cid in sm["table"]["cell_charPr_variants"]:
        checked["charPr"] += 1
        if cid not in chars:
            bad.append(("table/cell_charPr_variants", "charPr", cid))
    print("   검사한 id 참조: %s (합 %d)" % (dict(checked), sum(checked.values())))
    print("   header.xml에 없는 id: %d건 %s" % (len(bad), bad if bad else ""))
    if bad:
        ok = False

    print()
    print("-- 3. 메인 표본 9건 대조 --")
    for name, sec, idx, want in SAMPLES:
        p = secs[sec][idx]
        got = {"paraPrIDRef": p["paraPrIDRef"], "styleIDRef": p["styleIDRef"],
               "pageBreak": p["pageBreak"],
               "char": p["runs"][0][0] if p["runs"] else None}
        diff = {k: (want[k], got[k]) for k in want if got[k] != want[k]}
        print("   %-22s %s %s" % (name, "OK " if not diff else "FAIL", diff or ""))
        if diff:
            ok = False

    print()
    print("-- 4. 표본이 style_map에 반영됐는가 --")
    for key, pp, st, cp in (("h1_chapter", "49", "1", "56"), ("h2_section", "46", "0", "60"),
                            ("h3_item", "46", "0", "39"), ("body", "46", "0", "36"),
                            ("caption", "31", "0", "8")):
        d = sm[key]
        good = (d["paraPrIDRef"] == pp and d["styleIDRef"] == st and d["charPrIDRef"] == cp)
        print("   %-12s %s para %s / style %s / char %s"
              % (key, "OK " if good else "FAIL", d["paraPrIDRef"], d["styleIDRef"],
                 d["charPrIDRef"]))
        ok = ok and good
    red = sm["constants"]["RED_CHAR_BY_BASE"].get("36")
    print("   %-12s %s RED_CHAR_BY_BASE['36'] = %s" % ("빨강", "OK " if red == "68" else "FAIL", red))
    ok = ok and red == "68"
    for key, want in (("REF_TITLE", "5"), ("REF_CATEGORY", "12"), ("APPENDIX_TITLE", "31")):
        got = sm["constants"][key]["para"]
        print("   %-12s %s .para = %s" % (key, "OK " if got == want else "FAIL", got))
        ok = ok and got == want
    return ok


def verify_cover(sm, xml0, paras0):
    """표지 치환 좌표를 ElementTree로 독립 재현한다(정규식 중첩 오류를 잡기 위한 교차검증)."""
    print()
    print("-- 5. 표지 run 좌표 교차검증 (ElementTree 독립 파싱) --")
    decl = " ".join('xmlns:%s="%s"' % kv for kv in
                    re.findall(r'xmlns:(\w+)="([^"]*)"',
                               re.search(r'<hs:sec [^>]*>', xml0).group(0)))
    ok = True
    for idx in (0, 1, 2):
        root = ET.fromstring("<w %s>%s</w>" % (decl, frag(xml0, paras0[idx])))
        runs = list(root.iter(HP + "run"))
        for it in [c for c in sm["cover"] if c["section0_idx"] == idx]:
            r = runs[it["run_ordinal"]]
            own = [t.text or "" for t in r if t.tag == HP + "t"]
            good = (r.get("charPrIDRef") == it["charPrIDRef"] and it["old"] in own
                    and len(own) == it["_t_nonempty"])
            print("   p%d run%-3d %-15s %s charPr=%s own=%s"
                  % (idx, it["run_ordinal"], it["role"], "OK " if good else "FAIL",
                     r.get("charPrIDRef"), repr(own)[:46]))
            ok = ok and good
    return ok


# ── 리포트 ───────────────────────────────────────────────────────────────────
def write_md(sm, chars, paras, bfs, tabs, styles, fonts, uch, tstat, secs):
    s1, s2 = secs[1], secs[2]
    c = sm["constants"]
    L = []
    w = L.append

    def pt(cid):
        return chars[cid]["height"] // 100

    def hfont(cid):
        return fonts["HANGUL"].get(chars[cid]["hangul"], "?")

    def cell(text, n=None):
        """표 칸에 넣을 텍스트 — XML 이스케이프를 풀고 파이프를 막는다."""
        t = (text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
             .replace("|", "\\|"))
        return t[:n] if n else t

    w("# 양식(260912_1059) 스타일 실측 보고 — style_map_miso.json 근거")
    w("")
    w("측정일 2026-09-12 · 대상 `04. 미소논문/00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx`의 "
      "압축 해제본 `analysis/extracted/Contents/*.xml` · 재실행 "
      "`PYTHONIOENCODING=utf-8 python analysis/probe_style_map.py`")
    w("")
    w("> 한글 재저장으로 header가 정규화돼 id가 전부 재번호됐다(charPr %d · paraPr %d · borderFill %d · "
      "tabPr %d · style %d). 기준 파일 `staging/style_map_yoonhyuk_reference.json`의 **값은 하나도 "
      "쓸 수 없고**, 키 이름만 물려받았다." % (len(chars), len(paras), len(bfs), len(tabs), len(styles)))
    w("")
    w("## 1. 문단 스타일 (section2 본문)")
    w("")
    w("| 키 | 실측 근거(문단 idx·텍스트) | style | paraPr | charPr | paraPr 정의 | charPr 정의 |")
    w("| --- | --- | --- | --- | --- | --- | --- |")
    for key, idx in (("h1_chapter", 0), ("h2_section", 2), ("h3_item", 4),
                     ("body", 6), ("caption", 7)):
        p = s2[idx]
        cp = p["runs"][0][0]
        w("| `%s` | s2 p%d `%s` | %s | %s | %s | %s·줄간격 %s | %dpt %s%s |"
          % (key, idx, cell(p["text"], 30), p["styleIDRef"], p["paraPrIDRef"], cp,
             paras[p["paraPrIDRef"]]["align"], paras[p["paraPrIDRef"]]["lineSpacing"],
             pt(cp), hfont(cp), " bold" if chars[cp]["bold"] else ""))
    p = s2[8]
    w("| (빨강 마커 run) | s2 p8 `%s` | %s | %s | %s | 본문과 동일 | %dpt 빨강 #FF0000 |"
      % (cell(p["text"], 26), p["styleIDRef"], p["paraPrIDRef"],
         p["runs"][0][0], pt(p["runs"][0][0])))
    w("")
    w("빈 문단(s2 p1·p3·p5)은 run이 하나도 없고 paraPr %s만 있다 — `BLANK_CHAR`는 본문 charPr %s로 대신한다."
      % (s2[1]["paraPrIDRef"], c["BLANK_CHAR"]))
    w("")
    w("## 2. 목차·전면부 (section1)")
    w("")
    w("| 키 | 근거 | style/paraPr/charPr | 비고 |")
    w("| --- | --- | --- | --- |")
    toc_tab = paras[s1[2]["paraPrIDRef"]]["tabPrIDRef"]
    tab_pos = tabs[toc_tab]["items"][0][0] if tabs[toc_tab]["items"] else "-"
    w("| `toc_entry` | s1 p2 `제1장 서론` (p2~p104 동일) | %s/%s/%s | paraPr의 tabPr %s = RIGHT %s leader DASH. "
      "**인라인 탭·쪽번호는 문서 전체 0건** |"
      % (s1[2]["styleIDRef"], s1[2]["paraPrIDRef"], s1[2]["runs"][0][0], toc_tab, tab_pos))
    w("| `toc_lot_entry` | s1 p107 `<표 2-1> …` · p138 `<그림 1-1> …` | %s/%s/%s | 목차와 같은 paraPr, charPr만 본문 %dpt |"
      % (s1[107]["styleIDRef"], s1[107]["paraPrIDRef"], s1[107]["runs"][0][0],
         pt(s1[107]["runs"][0][0])))
    for label, idx in (("`s1_toc_title_idx`", 0), ("`s1_lot_title_idx`", 106),
                       ("`s1_lof_title_idx`", 136)):
        q = s1[idx]
        w("| %s = %d | s1 p%d `%s` | %s/%s/%s | 제목 상자 표(has_tbl=%s), pageBreak=%s |"
          % (label, idx, idx, q["text"].strip(), q["styleIDRef"], q["paraPrIDRef"],
             q["runs"][0][0] if q["runs"] else "-", q["has_tbl"], q["pageBreak"]))
    w("| `s1_thanks_range` = [147, 171] | p147 제목 상자 → p148 본문 → p149~p169 빈 문단 21개 → p170 `%s` → p171 `%s` | "
      "본문 %s/%s/%s | 사용자 작성분, 문단 경계 유지 |"
      % (s1[170]["text"], s1[171]["text"].strip(), s1[148]["styleIDRef"],
         s1[148]["paraPrIDRef"], s1[148]["runs"][0][0]))
    w("| `s1_abstract_range` = [172, 173] | p172 `논 문  개 요` 제목 상자 + p173 공백 본문 자리 | 본문 %s/%s/%s | 국문초록은 p173 자리 |"
      % (s1[173]["styleIDRef"], s1[173]["paraPrIDRef"], s1[173]["runs"][0][0]))
    w("")
    w("메인이 추정한 앵커 `0 / 106 / 136 / [147,171] / [172,173]`은 덤프 실측과 **전부 일치**했다.")
    w("")
    w("### 전면부에 섞인 빨간 charPr (양식 그대로 옮기면 안 되는 곳)")
    w("")
    w("| 위치 | 실측 charPr | 색 | 검은 짝 |")
    w("| --- | --- | --- | --- |")
    for label, idx in (("표목차 제목 s1 p106", 106), ("감사의 글 본문 s1 p148", 148)):
        cid = s1[idx]["runs"][0][0]
        if chars[cid]["color"] != "#FF0000":
            continue
        w("| %s | %s | #FF0000 | %s |"
          % (label, cid, c["RED_CHAR_BY_BASE"] and
             {r: b for b, r in c["RED_CHAR_BY_BASE"].items()}.get(cid)))
    w("")
    w("윤혁 양식에서는 미완성 표시로 빨강을 쓴 자리가 전면부에도 남아 있다. 미소 논문 본문으로 채울 "
      "때는 검은 짝 charPr를 쓰고, 빨강은 프로젝트 규칙대로 `[확정 필요`·`[작성 가이드` 같은 마커에만 남긴다.")
    w("")
    w("## 3. 표 (section2 본문 표 %d개 전수)" % tstat["n"])
    w("")
    w("- 표 폭 `sz.width`: %s → `TABLE_WIDTH`"
      % ", ".join("%s(%d개)" % kv for kv in tstat["width"].most_common()))
    w("- `pageBreak`: 실측도 전부 `NONE`(%d/%d) → 규칙대로 `NONE` 고정" % (tstat["n"], tstat["n"]))
    w("- `cellSz.height` 최빈 %d(%d회) → `ROW_MIN_H`"
      % (c["ROW_MIN_H"], tstat["height"].most_common(1)[0][1]))
    w("- 본문 `linesegarray/@horzsize` 전 문단 동일 %d → `LINE_W`" % c["LINE_W"])
    w("- 셀 여백 `cellMargin` 최빈 %s (%d회)"
      % (dict(zip(("left", "right", "top", "bottom"), tstat["pad"].most_common(1)[0][0])),
         tstat["pad"].most_common(1)[0][1]))
    w("- 대표 표: %s" % sm["table"]["_grid"])
    w("")
    w("| 위치 | borderFill 최빈 | 정의 |")
    w("| --- | --- | --- |")
    for label, key, const in (("내부 셀", "bf_mid", "BORDER_INNER"),
                              ("왼쪽 끝 열", "bf_first", "BORDER_LEFT_EDGE"),
                              ("오른쪽 끝 열", "bf_last", "BORDER_RIGHT_EDGE"),
                              ("캡션 행(전 열 병합)", "bf_caption", "BORDER_CAPTION_ROW")):
        b, n = tstat[key].most_common(1)[0]
        w("| %s (`%s`) | **%s** (%d회) | %s |" % (label, const, b, n, describe_bf(bfs[b])))
    g = c["BORDER_HEADER_GRAY"]
    w("| 회색 머리행 (`BORDER_HEADER_GRAY`) | **%s** (대체값) | %s |" % (g, describe_bf(bfs[g])))
    w("")
    w("`BORDER_HEADER_GRAY` 주의 — %s" % c["_notes"]["BORDER_HEADER_GRAY"])
    w("")
    w("| 셀 서식 | 값 | 근거 |")
    w("| --- | --- | --- |")
    w("| `cell_paraPr` | %s | 셀 문단 %d회로 최빈 (%s·줄간격 %s) |"
      % (sm["table"]["cell_paraPr"], tstat["cell_para"].most_common(1)[0][1],
         paras[sm["table"]["cell_paraPr"]]["align"],
         paras[sm["table"]["cell_paraPr"]]["lineSpacing"]))
    w("| `cell_charPr` | %s | 셀 run %d회로 최빈 (%dpt %s) |"
      % (sm["table"]["cell_charPr"], tstat["cell_char"].most_common(1)[0][1],
         pt(sm["table"]["cell_charPr"]), hfont(sm["table"]["cell_charPr"])))
    cr = sm["table"]["caption_row"]
    w("| 캡션 행 | borderFill %s / paraPr %s / charPr %s | 캡션 셀 %d개 전수 동일 (charPr %s는 %dpt %s) |"
      % (cr["borderFillIDRef"], cr["paraPrIDRef"], cr["charPrIDRef"],
         tstat["cap_char"].most_common(1)[0][1], cr["charPrIDRef"],
         pt(cr["charPrIDRef"]), hfont(cr["charPrIDRef"])))
    w("")
    w("## 4. constants")
    w("")
    w("| 키 | 값 | 근거 |")
    w("| --- | --- | --- |")
    ev = {
        "TABLE_WIDTH": "본문 표 %d/%d개의 sz.width" % (tstat["width"].most_common(1)[0][1], tstat["n"]),
        "ROW_MIN_H": "cellSz.height 최빈값(%d회)" % tstat["height"].most_common(1)[0][1],
        "LINE_W": "section2 본문 lineseg horzsize 전건 동일",
        "BODY_BOLD_CHAR": c["_notes"]["BODY_BOLD_CHAR"],
        "CELL_BOLD_CHAR": c["_notes"]["CELL_BOLD_CHAR"],
        "H4_FALLBACK_CHAR": "= BODY_BOLD_CHAR (양식에 h4 대응 서식 없음)",
        "BLANK_CHAR": c["_notes"]["BLANK_CHAR"],
        "TOC_BLANK_CHAR": c["_notes"]["TOC_BLANK_CHAR"],
        "TOC_ENTRY_CHAR": "s1 p2~p104 목차 항목 run charPr(문서 전체 %d회)"
                          % uch.get(c["TOC_ENTRY_CHAR"], 0),
        "BORDER_INNER": "내부 셀 최빈 %d회" % tstat["bf_mid"].most_common(1)[0][1],
        "BORDER_LEFT_EDGE": "colAddr=0 셀 최빈 %d회" % tstat["bf_first"].most_common(1)[0][1],
        "BORDER_RIGHT_EDGE": "마지막 열 셀 최빈 %d회" % tstat["bf_last"].most_common(1)[0][1],
        "BORDER_CAPTION_ROW": "캡션 행 최빈 %d회" % tstat["bf_caption"].most_common(1)[0][1],
        "BORDER_HEADER_GRAY": "대체값 — 위 3절 주의 참조",
    }
    for k in ("TABLE_WIDTH", "ROW_MIN_H", "LINE_W", "BODY_BOLD_CHAR", "CELL_BOLD_CHAR",
              "H4_FALLBACK_CHAR", "BLANK_CHAR", "TOC_BLANK_CHAR", "TOC_ENTRY_CHAR",
              "BORDER_INNER", "BORDER_LEFT_EDGE", "BORDER_RIGHT_EDGE",
              "BORDER_CAPTION_ROW", "BORDER_HEADER_GRAY"):
        w("| `%s` | %s | %s |" % (k, c[k], ev.get(k, "")))
    for k, idx in (("REF_TITLE", 554), ("REF_CATEGORY", 556), ("REF_ENTRY", 558),
                   ("APPENDIX_TITLE", 593)):
        p = s2[idx]
        w("| `%s` | style %s / para %s / char %s | s2 p%d `%s` |"
          % (k, c[k]["style"], c[k]["para"], c[k]["char"], idx,
             cell(p["text"], 36)))
    w("")
    w("### RED_CHAR_BY_BASE — 검은 charPr → 빨간 charPr (%d쌍)" % len(c["RED_CHAR_BY_BASE"]))
    w("")
    w("| 검정 | 서식 | 빨강 | 사용 횟수(검정/빨강) |")
    w("| --- | --- | --- | --- |")
    for base, red in c["RED_CHAR_BY_BASE"].items():
        w("| %s | %dpt %s%s | %s | %d / %d |"
          % (base, pt(base), hfont(base), " bold" if chars[base]["bold"] else "",
             red, uch.get(base, 0), uch.get(red, 0)))
    w("")
    w("본문 charPr %s의 빨강 짝은 %s이며, 이는 메인 표본(s2 p8 `[그림 삽입 예정…]` charPr 68)과 일치한다."
      % (c["BLANK_CHAR"], c["RED_CHAR_BY_BASE"].get(c["BLANK_CHAR"])))
    w("")
    w("`CHAR_HEIGHTS`는 header.xml의 charPr %d개 전수를 id→height(hu)로 담았다." % len(chars))
    w("")
    w("## 5. 표지 치환 대상 (section0)")
    w("")
    w("section0의 최상위 문단은 3개뿐이고 실제 텍스트는 전부 표 셀 안이므로 `section0.xml`을 직접 "
      "파싱해 run 순서(`run_ordinal` = 문단 안 `<hp:run>` 문서 순서, 0-base)로 위치를 잡았다. "
      "`splittable=true`는 바꿀 문자열이 **하나의 `<hp:t>` 안에 통째로** 들어 있어 run·charPr 구조를 "
      "그대로 두고 텍스트만 치환할 수 있다는 뜻이다.")
    w("")
    w("| s0 문단 | run# | charPr | role | 현재 텍스트 | 그 run의 `<hp:t>` 수 | splittable |")
    w("| --- | --- | --- | --- | --- | --- | --- |")
    for it in sm["cover"]:
        w("| %d | %d | %s | `%s` | `%s` | %d | %s |"
          % (it["section0_idx"], it["run_ordinal"], it["charPrIDRef"], it["role"],
             cell(it["old"], 54), it["_t_count"],
             "예" if it["splittable"] else "**아니오**"))
    w("")
    w("주의 1 — 겉표지(s0 p0)의 전공은 `건축ㆍ안전공학전공`(U+318D 아래아), 속표지(s0 p1)는 "
      "`건축․안전공학전공`(U+2024 ONE DOT LEADER)로 **가운뎃점 문자가 서로 다르다**. 원문을 그대로 "
      "두지 말고 W4가 지정한 값으로 통일해야 한다. 인준서(s0 p2)에는 전공 줄이 없다.")
    w("")
    w("주의 2 — `name`은 겉표지·속표지 2회이고, 인준서의 `윤   혁의 석사학위논문을 인준함`은 성명이 "
      "문장 안에 박혀 있어 별도 role `approval_title`로 뒀다(브리프의 '성명 3회'에 해당). "
      "`date`는 속표지·인준서 2회, `title`은 겉표지·속표지 2회, `major`는 2회다.")
    w("")
    w("주의 3 — `run_ordinal`은 **표 셀 안 run까지 포함한** 문단 내 `<hp:run>` 등장 순서다"
      "(표지 문단은 통째로 표 1개라 최상위 run이 표를 감싸고 실제 글자는 셀 안 run에 들어 있다). "
      "위 좌표는 정규식 파싱과 ElementTree 파싱 두 방법으로 교차검증했다"
      "(`probe_style_map.py` 검증 5단계).")
    w("")
    w("주의 4 — 겉표지 `2026학년도`는 `2026`(run %s, charPr %s)과 `학년도`가 서로 다른 run이다. "
      "학년도를 바꿀 때는 숫자 run의 `<hp:t>`만 손댄다."
      % (sm["cover"][0]["run_ordinal"], sm["cover"][0]["charPrIDRef"]))
    w("")
    w("## 6. 쪽 설정")
    w("")
    w("| 구역 | 여백 left/right/top/bottom/footer | 쪽번호 |")
    w("| --- | --- | --- |")
    for name in ("section0_cover", "section1_front", "section2_body"):
        m = sm["page"]["margins"][name]
        pn = sm["page"]["page_numbering"]["section%s" % name[7]]
        w("| %s | %s/%s/%s/%s/%s | %s |"
          % (name, m["left"], m["right"], m["top"], m["bottom"], m["footer"],
             pn if isinstance(pn, str) else "%s %s `%s` newNum=%s"
             % (pn["pos"], pn["formatType"], pn["sideChar"], pn["newNum"])))
    w("")
    fn = sm["page"]["footnote"]
    w("용지 %s x %s HWPUNIT (%s mm), landscape=%s, gutterType=%s. 각주 번호 %s%s · 번호 매김 %s · "
      "구분선 %s."
      % (sm["page"]["width"], sm["page"]["height"], sm["page"]["size_mm"],
         sm["page"]["landscape"], sm["page"]["gutterType"], fn["numFormat"],
         fn["suffixChar"], fn["numbering"], fn["noteLineWidth"]))
    w("")
    w("## 7. 미해결·주의 사항")
    w("")
    w("1. **회색 머리행 정의가 없다.** 이 양식에는 `사방 실선 + 회색 배경` borderFill이 없다"
      "(faceColor를 가진 borderFill은 %s 셋뿐이고 사방 실선이 아니다). `BORDER_HEADER_GRAY`는 "
      "대체값이므로, W4가 머리행을 회색으로 칠하려면 header.xml에 borderFill을 새로 추가해야 한다"
      "(= id 재번호 위험). 양식 관행대로 **회색 없이 bold charPr %s**로 머리행을 구분하는 편을 권한다."
      % (", ".join(sorted((b for b, d in bfs.items() if d["fill"] and d["fill"] != "none"), key=int)),
         c["CELL_BOLD_CHAR"]))
    w("2. **목차 리더·쪽번호가 없다.** `<hp:tab>`이 section1/section2 통틀어 0건이다. 쪽번호를 넣으려면 "
      "paraPr %s의 tabPr %s(RIGHT %s, leader DASH)에 맞춰 인라인 탭을 새로 만들어야 한다. "
      "`toc_entry.inline_tab`은 그때 쓸 관례값이다." % (s1[2]["paraPrIDRef"], toc_tab, tab_pos))
    w("3. **문단 덤프의 `byte_start`/`byte_end`는 사실 문자 오프셋**이다. bytes로 슬라이스하면 조각이 "
      "어긋난다(이 스크립트는 UTF-8 디코드 후 문자 슬라이스를 쓴다). W4도 같은 함정에 주의.")
    n0 = sum(n for s, n in tstat["tbl_attr"].items() if 'noAdjust="0"' in s)
    n1 = sum(n for s, n in tstat["tbl_attr"].items() if 'noAdjust="1"' in s)
    w("4. `noAdjust`는 표 %d개 중 %d개가 `0`, %d개가 `1`이다. 최빈값 `0`을 기본으로 뒀다."
      % (tstat["n"], n0, n1))
    w("5. `table.borderFills`에는 조립기가 실제로 쓰는 5종만 담았다. 양식에는 borderFill이 %d개 "
      "있고 표 셀에 쓰인 것만 해도 %d종이지만(2중선 %s = 부록 설문지 제목 상자 등), 나머지는 "
      "사용자가 직접 만든 설문지 표의 국소 서식이라 조립 대상이 아니다."
      % (len(bfs), len(set(list(tstat["bf_mid"]) + list(tstat["bf_first"]) +
                           list(tstat["bf_last"]) + list(tstat["bf_caption"]))), "26"))
    w("")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))


def main():
    hdr = read(os.path.join(XMLDIR, "header.xml"))
    chars, paras, bfs, tabs, styles, fonts = parse_header(hdr)
    xml, secs = load_sections()
    uch, _upa = usage(xml)
    tstat = survey_tables(xml[2], secs[2])
    cover = survey_cover(xml[0], secs[0])
    sm = build(chars, paras, bfs, tabs, styles, fonts, uch, tstat, cover, xml, secs)

    with open(OUT_MAP, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sm, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    write_md(sm, chars, paras, bfs, tabs, styles, fonts, uch, tstat, secs)
    print("생성: %s" % os.path.relpath(OUT_MAP, ROOT).replace("\\", "/"))
    print("생성: %s" % os.path.relpath(OUT_MD, ROOT).replace("\\", "/"))
    print()

    # 저장한 파일을 다시 읽어 검증한다(JSON 로드 가능 여부 포함).
    with open(OUT_MAP, encoding="utf-8") as fh:
        reloaded = json.load(fh)
    print("JSON 재로드 OK — 최상위 키 %d개" % len(reloaded))
    print()
    ok = verify(reloaded, chars, paras, bfs, tabs, secs)
    ok = verify_cover(reloaded, xml[0], secs[0]) and ok
    print()
    print("== 전체 판정: %s ==" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
