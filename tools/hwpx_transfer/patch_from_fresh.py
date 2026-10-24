# 사용자가 한글에서 직접 고친 hwpx에, 현행 MD로 새로 조립한 hwpx의 바뀐 문단·표만 떼어 와 끼워 넣는 부분 패치 도구
"""patch_from_fresh.py — 전체 재조립 없이 MD 변경분을 기존(사용자 편집) hwpx에 반영한다.

사용:
  PYTHONIOENCODING=utf-8 python tools/hwpx_transfer/patch_from_fresh.py \
      --base <사용자 최신본.hwpx> --fresh <현행 MD 조립본.hwpx> --out <출력.hwpx> \
      [--protect "<표 3-3>,<표 3-9>,<표 5-1>"] [--text-replace spec.json] [--appendix spec.json] \
      [--toc-lines spec.json] [--report report.md] [--dry-run]

원리(2026-10-09):
  - section2 본문을 최상위 문단 단위로 양쪽에서 잘라 텍스트로 정렬(difflib)한다. 같은 문단은 base(사용자본)를 그대로 두고,
    새로 생기거나 바뀐 문단·표는 fresh(조립본) XML을 가져오되 charPr/paraPr/borderFill/글꼴 id를 base header에
    맞게 재대응시킨다(kjn_profile.StyleImporter — 한글 재저장으로 id가 바뀌어 프로파일 id를 직접 쓸 수 없다).
  - base에만 있는 문단(fresh에 없음)은 지우지 않는다(사용자 직접 수정분 보존). 보고서에 남긴다.
  - --protect 로 지정한 캡션의 표(사용자가 셀을 합치거나 지운 표)는 셀 텍스트가 달라도 base XML을 유지한다.
  - 부록 영역('부 록 (도입 현장)' 제목부터 끝)은 정렬 대상에서 빼고 base를 유지한다. 부록 설문지의 문항 추가는
    --appendix 스펙으로 기존 문항 문단(예: A-6)을 복제해 넣는다(두 양식 모두).
  - --text-replace: {"old","new","count"} 목록을 section2의 <hp:t> 텍스트에 적용(출현 횟수 검증, 이스케이프 처리).
  - --toc-lines: section1 목차 문단의 제목 치환과 항목 삽입(인접 항목 복제). 쪽수는 이후 toc_pages_from_pdf.py +
    toc_numbers_patch.py 로 갱신한다.
  - 바뀐 문단의 <hp:linesegarray>는 제거해 한글이 재조판하게 한다. 문단·표 id는 충돌하지 않게 새로 매긴다.
완료 판정은 이 도구가 아니라 한글 COM 재조판 저장 + PDF 검증이다(.claude/rules/hwpx-output-verification.md).
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kjn_profile  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

LINESEG_RE = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)
CAPTION_RE = re.compile(r"^<표\s*\d+\s*-\s*\d+>")
ID_RE = re.compile(r'<hp:(p|tbl|pic|container|rect|line|ellipse|arc|polygon|curve|connectLine|ole|equation) id="(\d+)"')


FIG_CAPTION_RE = re.compile(r"^<(그림|표)\s*\d+\s*-\s*\d+>")
HP_NS = kjn_profile.NS["hp"]
HP = "{%s}" % HP_NS


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def nows(text):
    """공백을 모두 지운 비교용 텍스트('합계'와 '합  계'를 같게 본다)."""
    return re.sub(r"\s+", "", text)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── 표 내용 비교(셀 병합 표 자동 판정) ──
def _wrap(xml_text):
    """조각 XML을 ElementTree로 읽게 hp 등 이름공간을 선언한 루트로 감싼다."""
    decl = " ".join('xmlns:%s="%s"' % (k, v) for k, v in kjn_profile.NS.items())
    return ET.fromstring("<wrap %s>%s</wrap>" % (decl, xml_text))


def _t_text(t):
    """hp:t 글자 — 탭·줄바꿈 같은 자식 태그 뒤 글자(tail)까지 문서 순서대로 잇는다."""
    return (t.text or "") + "".join(c.tail or "" for c in t)


def _cell_text(tc):
    # 셀 안 중첩 표가 있어도 셀 전체 글자를 모은다(중첩 표 구조 자체는 바깥 셀 단위로만 비교)
    return "".join(_t_text(t) for t in tc.iter(HP + "t"))


def table_grid(tbl):
    """최상위 셀만 {(row, col): (rowSpan, colSpan, 공백 제거 텍스트)}로 돌려준다."""
    cells = {}
    for tc in tbl.findall(HP + "tr/" + HP + "tc"):
        a, s = tc.find(HP + "cellAddr"), tc.find(HP + "cellSpan")
        rs = int(s.get("rowSpan", "1")) if s is not None else 1
        cs = int(s.get("colSpan", "1")) if s is not None else 1
        cells[(int(a.get("rowAddr")), int(a.get("colAddr")))] = (rs, cs, nows(_cell_text(tc)))
    return cells


def _outside_text(root):
    """표 바깥(문단 자체 run)의 텍스트 — 표 문단에 글이 함께 있으면 그것도 비교한다."""
    inner = set()
    for tbl in root.iter(HP + "tbl"):
        for t in tbl.iter(HP + "t"):
            inner.add(id(t))
    return nows("".join(_t_text(t) for t in root.iter(HP + "t") if id(t) not in inner))


def _top_tables(root):
    """중첩 표를 뺀 최상위 표 목록."""
    nested = set()
    for tbl in root.iter(HP + "tbl"):
        for sub in tbl.iter(HP + "tbl"):
            if sub is not tbl:
                nested.add(id(sub))
    return [t for t in root.iter(HP + "tbl") if id(t) not in nested]


def compare_tables(base_xml, fresh_xml):
    """표 문단 두 개를 셀 단위로 비교한다.

    돌려주는 값: (same, merge_diff, detail)
      same       — base 각 셀 텍스트(공백 무시)가 fresh의 같은 (rowAddr, colAddr) 셀과 같고, base에서 병합으로 덮인
                   fresh 셀이 빈칸이거나 덮은 셀과 같은 텍스트이면 True(내용 동일 → base XML 유지).
      merge_diff — base와 fresh의 병합 구조(셀 시작 위치·rowSpan·colSpan)가 다르면 True(사용자 병합 표).
      detail     — 처음 발견한 차이 설명(보고서용).
    """
    rb, rf = _wrap(base_xml), _wrap(fresh_xml)
    tb, tf = _top_tables(rb), _top_tables(rf)
    if len(tb) != len(tf):
        return False, True, "표 개수 %d≠%d" % (len(tb), len(tf))
    same, merge_diff, detail = True, False, ""
    if _outside_text(rb) != _outside_text(rf):
        same, detail = False, "표 바깥 문단 텍스트가 다름"
    for k, (b, f) in enumerate(zip(tb, tf)):
        gb, gf = table_grid(b), table_grid(f)
        if {p: v[:2] for p, v in gb.items()} != {p: v[:2] for p, v in gf.items()}:
            merge_diff = True
        cover = {}  # base 병합 셀이 덮는 칸 → 덮는 셀 위치
        for (r, c), (rs, cs, _) in gb.items():
            for dr in range(rs):
                for dc in range(cs):
                    cover[(r + dr, c + dc)] = (r, c)
        for pos, (_, _, btxt) in gb.items():
            if pos not in gf or gf[pos][2] != btxt:
                if same:
                    detail = "표%d 셀%s base '%s' ≠ fresh '%s'" % (k, pos, btxt[:20], gf[pos][2][:20] if pos in gf else None)
                same = False
        for pos, (_, _, ftxt) in gf.items():
            if pos in gb:
                continue
            owner = cover.get(pos)
            if owner is None:
                if same:
                    detail = "표%d fresh 셀%s가 base 격자 밖" % (k, pos)
                same = False
            elif ftxt and ftxt != gb[owner][2]:
                if same:
                    detail = "표%d base 병합 셀%s가 덮는 fresh 셀%s에 글 '%s'" % (k, owner, pos, ftxt[:20])
                same = False
    return same, merge_diff, detail


class Units(object):
    """section2의 최상위 문단 목록."""

    def __init__(self, xml_text, protect, allow_tables=None, keep_prefix=()):
        self.xml = xml_text
        self.spans = kjn_profile.split_paragraphs(xml_text)
        self.items = []
        caption = ""
        for a, b in self.spans:
            p = xml_text[a:b]
            text = norm(kjn_profile.plain_texts(p))
            is_tbl = "<hp:tbl" in p
            if not is_tbl and CAPTION_RE.match(text):
                caption = CAPTION_RE.match(text).group(0).replace(" ", "")
            if allow_tables is not None:
                protected = is_tbl and caption not in allow_tables
            else:
                protected = is_tbl and caption in protect
            if not is_tbl and any(text.startswith(k) for k in keep_prefix):
                protected = True  # 사용자 직접 수정 문단: base 유지
            if protected and is_tbl:
                key = "TBL:" + caption
            elif is_tbl:
                # 표는 공백을 지운 글자로 정렬한다. 사용자가 병합하며 지운 빈 셀·셀 안 문단 나눔·'합  계' 같은 공백 차이에
                # 흔들리지 않게 하려는 것이다. 정렬 뒤 compare_tables로 셀 단위 동일성을 다시 확인한다.
                key = "TBLTXT:" + nows(text)
            else:
                key = text
            self.items.append({"xml": p, "text": text, "key": key, "tbl": is_tbl, "cap": caption, "protected": protected})
        self.head = xml_text[: self.spans[0][0]] if self.spans else xml_text
        self.tail = xml_text[self.spans[-1][1]:] if self.spans else ""

    def appendix_start(self):
        for i, it in enumerate(self.items):
            if it["text"].replace(" ", "").startswith("부록(도입현장)"):
                return i
        return len(self.items)


class Patcher(object):
    def __init__(self, base_path, fresh_path, protect, report, allow_tables=None, keep_prefix=()):
        self.base_infos, self.base_raw = kjn_profile.read_package(base_path)
        _, self.fresh_raw = kjn_profile.read_package(fresh_path)
        self.header = kjn_profile.HeaderEditor(self.base_raw["Contents/header.xml"].decode("utf-8"))
        self.importer = kjn_profile.StyleImporter(self.fresh_raw["Contents/header.xml"].decode("utf-8"), self.header)
        self.protect = set(p.replace(" ", "") for p in protect)
        self.allow_tables = None if allow_tables is None else set(p.replace(" ", "") for p in allow_tables)
        self.keep_prefix = tuple(keep_prefix)
        self.report = report
        self.log = []
        self.s2 = self.base_raw["Contents/section2.xml"].decode("utf-8")
        self.s1 = self.base_raw["Contents/section1.xml"].decode("utf-8")
        fresh_s2 = self.fresh_raw["Contents/section2.xml"].decode("utf-8")
        self.next_id = max([int(i) for _, i in ID_RE.findall(self.s2 + self.s1 + fresh_s2)] + [2147483648]) + 1
        self.fresh_s2 = fresh_s2
        self.stats = {"equal": 0, "insert": 0, "replace_fresh": 0, "replace_kept": 0, "delete_kept": 0, "manual": 0,
                      "table_same_kept": 0, "caption_split": 0}
        self.manual = []  # '수동 재적용 필요' 목록(보고서 별도 절)

    def _manual(self, what):
        self.stats["manual"] += 1
        self.manual.append(what)
        self.log.append("MANUAL | " + what)

    # ── 표 쌍 처리 ──
    def _table_pair(self, bu, fu):
        """짝지어진 표 문단 한 쌍 → 출력 XML. 내용이 같으면 base, 병합 표 내용이 다르면 base + 수동 목록, 그 밖은 fresh."""
        if bu["protected"]:
            self.stats["replace_kept"] += 1
            self.log.append("KEEP(protected) | %s" % bu["cap"])
            return bu["xml"]
        same, merge_diff, detail = compare_tables(bu["xml"], fu["xml"])
        if same:
            self.stats["table_same_kept"] += 1
            self.log.append("KEEP(table same content%s) | %s" % (", merged" if merge_diff else "", bu["cap"]))
            return bu["xml"]
        if merge_diff:
            self.stats["replace_kept"] += 1
            self._manual("%s 병합 표 내용 변경 — base 유지, MD 변경분 수동 재적용 필요 (%s)" % (bu["cap"], detail))
            return bu["xml"]
        self.stats["replace_fresh"] += 1
        self.log.append("REPLACE(table) | %s (%s)" % (bu["cap"], detail))
        return self.take_fresh(fu["xml"])

    # ── 본문+캡션이 한 문단으로 합쳐진 경우(사용자가 문단 경계를 지움) ──
    def _split_merged_caption(self, bblock, fblock):
        """base 1문단 = fresh 본문 문단 + fresh 캡션 문단이면, base 문단에서 캡션 글자만 떼고 fresh 캡션 문단을 뒤에 둔다.
        본문 문단은 base의 paraPr·charPr을 그대로 쓴다. 맞지 않으면 None."""
        if len(bblock) != 1 or len(fblock) != 2 or bblock[0]["tbl"] or any(f["tbl"] for f in fblock):
            return None
        bu, f0, f1 = bblock[0], fblock[0], fblock[1]
        if not FIG_CAPTION_RE.match(f1["text"]) or nows(bu["text"]) != nows(f0["text"]) + nows(f1["text"]):
            return None
        if "<hp:pic" in bu["xml"] or "<hp:tbl" in bu["xml"]:
            return None
        cap_plain = kjn_profile.plain_texts(f1["xml"])
        cap_xml = esc(cap_plain)
        pos = bu["xml"].rfind(cap_xml + "</hp:t>")
        if pos < 0:
            return None
        body = bu["xml"][:pos] + bu["xml"][pos + len(cap_xml):]
        if nows(kjn_profile.plain_texts(body)) != nows(f0["text"]):
            return None
        body = LINESEG_RE.sub("", body)
        self.stats["caption_split"] += 1
        self.log.append("SPLIT(merged caption) | base 본문 서식 유지 + fresh 캡션: %s" % f1["text"][:50])
        return [body, self.take_fresh(f1["xml"])]

    # ── 공통 ──
    def renumber(self, xml_text):
        def rep(m):
            self.next_id += 1
            return '<hp:%s id="%d"' % (m.group(1), self.next_id)
        return ID_RE.sub(rep, xml_text)

    def take_fresh(self, xml_text):
        x = self.importer.remap_body(xml_text)
        x = LINESEG_RE.sub("", x)
        return self.renumber(x)

    # ── 본문 정렬 패치 ──
    def _equal_units(self, bunits, funits):
        """키가 같은 구간. 표는 공백 무시 글자만 같을 수 있으므로 셀 단위로 한 번 더 확인한다."""
        out = []
        for bu, fu in zip(bunits, funits):
            if bu["tbl"] and fu["tbl"] and not bu["protected"] and bu["xml"] != fu["xml"]:
                same, merge_diff, detail = compare_tables(bu["xml"], fu["xml"])
                if not same:
                    out.append(self._table_pair(bu, fu))
                    continue
                if bu["text"] != fu["text"] or merge_diff:
                    self.stats["table_same_kept"] += 1
                    self.log.append("KEEP(table same content%s) | %s" % (", merged" if merge_diff else "", bu["cap"]))
            out.append(bu["xml"])
            self.stats["equal"] += 1
        return out

    def patch_body(self):
        base = Units(self.s2, self.protect, self.allow_tables, self.keep_prefix)
        fresh = Units(self.fresh_s2, self.protect, self.allow_tables, self.keep_prefix)
        nb, nf = base.appendix_start(), fresh.appendix_start()
        bkeys = [u["key"] for u in base.items[:nb]]
        fkeys = [u["key"] for u in fresh.items[:nf]]
        out = []
        sm = difflib.SequenceMatcher(None, bkeys, fkeys, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                out.extend(self._equal_units(base.items[i1:i2], fresh.items[j1:j2]))
            elif tag == "insert":
                for u in fresh.items[j1:j2]:
                    if not u["text"] and not u["tbl"]:
                        self.log.append("SKIP(blank insert)")
                        continue
                    out.append(self.take_fresh(u["xml"]))
                    self.stats["insert"] += 1
                    self.log.append("INSERT  | %s" % u["text"][:70])
            elif tag == "delete":
                for u in base.items[i1:i2]:
                    out.append(u["xml"])
                    self.stats["delete_kept"] += 1
                    self.log.append("KEEP(base only) | %s" % u["text"][:70])
            else:
                out.extend(self._replace(base.items[i1:i2], fresh.items[j1:j2]))
        out.extend(u["xml"] for u in base.items[nb:])  # 부록은 base 유지
        self.s2 = base.head + "".join(out) + base.tail

    def _replace(self, bblock, fblock, depth=0):
        out = []
        if [u["text"] for u in bblock if u["text"]] == [u["text"] for u in fblock if u["text"]]:
            # 빈 문단 수만 다르다(사용자가 한글에서 넣은 빈 줄 등) → base 유지
            for bu in bblock:
                out.append(bu["xml"])
            self.stats["replace_kept"] += len(bblock)
            self.log.append("KEEP(blank-only diff) | %s" % next((u["text"][:50] for u in bblock if u["text"]), ""))
            return out
        split = self._split_merged_caption(bblock, fblock)
        if split is not None:
            return split
        if len(bblock) == len(fblock) and all(bu["tbl"] == fu["tbl"] for bu, fu in zip(bblock, fblock)):
            for bu, fu in zip(bblock, fblock):
                if bu["tbl"]:
                    out.append(self._table_pair(bu, fu))
                elif bu["protected"]:
                    out.append(bu["xml"])
                    self.stats["replace_kept"] += 1
                    self.log.append("KEEP(protected) | %s" % bu["text"][:50])
                else:
                    out.append(self.take_fresh(fu["xml"]))
                    self.stats["replace_fresh"] += 1
                    self.log.append("REPLACE | %s  ->  %s" % (bu["text"][:40], fu["text"][:40]))
            return out
        if not any(u["protected"] or u["tbl"] for u in bblock) and depth == 0:
            # base 쪽에 표·보호 문단이 없으면 블록째 fresh로(문단 분리·합침·사이 삽입을 한 번에 처리).
            # base 표가 섞인 블록은 사용자 병합·열폭 편집을 잃지 않도록 아래 안쪽 정렬로 넘긴다.
            for bu in bblock:
                self.log.append("DROP(base, replaced by block) | %s" % bu["text"][:60])
            for fu in fblock:
                out.append(self.take_fresh(fu["xml"]))
                self.stats["replace_fresh"] += 1
                self.log.append("REPLACE(block) | %s" % fu["text"][:60])
            return out
        # 표·보호 문단이 섞인 블록: 안쪽에서 한 번 더 정렬(키 기준), 그래도 못 짝지으면 base 유지 + 수동 목록
        sm = difflib.SequenceMatcher(None, [u["key"] for u in bblock], [u["key"] for u in fblock], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                out.extend(self._equal_units(bblock[i1:i2], fblock[j1:j2]))
            elif tag == "insert":
                for fu in fblock[j1:j2]:
                    out.append(self.take_fresh(fu["xml"]))
                    self.stats["insert"] += 1
                    self.log.append("INSERT(inner) | %s" % fu["text"][:60])
            elif tag == "delete":
                for bu in bblock[i1:i2]:
                    out.append(bu["xml"])
                    self.stats["delete_kept"] += 1
                    self.log.append("KEEP(base only, inner) | %s" % bu["text"][:60])
            elif depth == 0 and ((i2 - i1) == (j2 - j1) or not any(u["protected"] or u["tbl"] for u in bblock[i1:i2])):
                out.extend(self._replace(bblock[i1:i2], fblock[j1:j2], depth + 1))
            else:
                for bu in bblock[i1:i2]:
                    out.append(bu["xml"])
                self._manual("base %d vs fresh %d 문단을 짝짓지 못해 base 유지: %s" % (
                    i2 - i1, j2 - j1, next((u["text"][:50] for u in bblock[i1:i2] if u["text"]), "(빈 문단)")))
        return out

    # ── 텍스트 치환(section2) ──
    def text_replace(self, spec):
        for rep in spec:
            old, new = esc(rep["old"]), esc(rep["new"])
            cnt = self.s2.count(old)
            want = int(rep.get("count", 1))
            if cnt != want:
                raise SystemExit("text-replace 출현 %d ≠ 기대 %d: %s" % (cnt, want, rep["old"][:50]))
            # 바뀐 문단의 linesegarray 제거
            pos = 0
            while True:
                i = self.s2.find(old, pos)
                if i < 0:
                    break
                ps = self.s2.rfind("<hp:p ", 0, i)
                pe = self.s2.find("</hp:p>", i) + len("</hp:p>")
                para = self.s2[ps:pe].replace(old, new)
                para = LINESEG_RE.sub("", para)
                self.s2 = self.s2[:ps] + para + self.s2[pe:]
                pos = ps + len(para)
            self.log.append("TEXT x%d | %s -> %s" % (cnt, rep["old"][:40], rep["new"][:40]))

    # ── 부록 문항 복제 삽입 ──
    def appendix_insert(self, spec):
        """spec: {"label_template": " A-6)", "anchor_startswith": "※ 총공사비는", "count": 2,
                  "items": [{"kind": "label", "label": " A-7)", "text": " 질문"}, {"kind": "option", "text": " ① …"}, {"kind": "note", "text": "※ …"}]}"""
        label_key = "<hp:t>%s</hp:t>" % esc(spec["label_template"])
        hits = [m.start() for m in re.finditer(re.escape(label_key), self.s2)]
        if len(hits) != int(spec.get("count", 2)):
            raise SystemExit("부록 템플릿 '%s' 출현 %d ≠ 기대 %s" % (spec["label_template"], len(hits), spec.get("count", 2)))
        for h in reversed(hits):  # 뒤에서부터 삽입해 앞 오프셋을 보존
            ps = self.s2.rfind("<hp:p ", 0, h)
            spans = []
            pos = ps
            for _ in range(8):
                pe = self.s2.find("</hp:p>", pos) + len("</hp:p>")
                spans.append((pos, pe))
                pos = pe
                nxt = self.s2.find("<hp:p ", pos)
                if nxt != pos:
                    break
                pos = nxt
            paras = [self.s2[a:b] for a, b in spans]
            label_t = LINESEG_RE.sub("", paras[0])
            option_t = LINESEG_RE.sub("", paras[1])
            note_idx = next(i for i, p in enumerate(paras) if kjn_profile.plain_texts(p).startswith(spec["anchor_startswith"]))
            note_t = LINESEG_RE.sub("", paras[note_idx])
            anchor_end = spans[note_idx][1]
            new = []
            for it in spec["items"]:
                if it["kind"] == "label":
                    runs = re.findall(r"<hp:run\b.*?</hp:run>", label_t, re.S)
                    if len(runs) != 2:
                        raise SystemExit("라벨 템플릿 run이 2개가 아니다")
                    r0 = re.sub(r"<hp:t>.*?</hp:t>", "<hp:t>%s</hp:t>" % esc(it["label"]), runs[0], flags=re.S)
                    r1 = re.sub(r"<hp:t>.*?</hp:t>", "<hp:t>%s</hp:t>" % esc(it["text"]), runs[1], flags=re.S)
                    p = label_t.replace(runs[0], r0, 1).replace(runs[1], r1, 1)
                elif it["kind"] == "option":
                    p = re.sub(r"<hp:t>.*?</hp:t>", "<hp:t>%s</hp:t>" % esc(it["text"]), option_t, count=1, flags=re.S)
                else:
                    p = re.sub(r"<hp:t>.*?</hp:t>", "<hp:t>%s</hp:t>" % esc(it["text"]), note_t, count=1, flags=re.S)
                new.append(self.renumber(p))
            self.s2 = self.s2[:anchor_end] + "".join(new) + self.s2[anchor_end:]
            self.log.append("APPENDIX +%d paras after '%s' @%d" % (len(new), spec["anchor_startswith"], h))

    # ── 목차 문단(section1) ──
    def toc_lines(self, spec):
        """spec: {"replace": [{"old": "제목", "new": "제목"}], "insert_after": [{"after": "<표 4-5>", "text": "<표 4-6> …", "page": "0"}]}"""
        paras = re.findall(r"<hp:p\b.*?</hp:p>", self.s1, flags=re.S)
        def title_of(p):
            before = p.split("<hp:tab", 1)[0]
            return html.unescape("".join(re.findall(r"<hp:t(?:\s[^>]*)?>([^<]*)", before))).strip()
        for rep in spec.get("replace", []):
            n = 0
            for p in paras:
                if "<hp:tab" in p and title_of(p) == rep["old"]:
                    q = LINESEG_RE.sub("", p.replace(esc(rep["old"]), esc(rep["new"]), 1))
                    self.s1 = self.s1.replace(p, q, 1)
                    n += 1
            if n != int(rep.get("count", 1)):
                raise SystemExit("목차 제목 '%s' 출현 %d ≠ 기대 %s" % (rep["old"], n, rep.get("count", 1)))
            self.log.append("TOC title x%d | %s -> %s" % (n, rep["old"][:30], rep["new"][:30]))
        paras = re.findall(r"<hp:p\b.*?</hp:p>", self.s1, flags=re.S)
        for ins in spec.get("insert_after", []):
            tmpl = next((p for p in paras if "<hp:tab" in p and title_of(p).startswith(ins["after"])), None)
            if tmpl is None:
                raise SystemExit("목차 삽입 기준 '%s'를 찾지 못했다" % ins["after"])
            before, after = tmpl.split("<hp:tab", 1)
            before2 = re.sub(r"(<hp:t(?:\s[^>]*)?>)[^<]*", lambda m: m.group(1) + esc(ins["text"]), before, count=1)
            after2 = re.sub(r"(/>)([^<]*)(</hp:t>)", lambda m: m.group(1) + str(ins.get("page", "0")) + m.group(3), after, count=1)
            q = self.renumber(LINESEG_RE.sub("", before2 + "<hp:tab" + after2))
            self.s1 = self.s1.replace(tmpl, tmpl + q, 1)
            self.log.append("TOC insert after '%s' | %s" % (ins["after"], ins["text"][:40]))

    # ── 저장 ──
    def write(self, out_path):
        raw = dict(self.base_raw)
        raw["Contents/section2.xml"] = self.s2.encode("utf-8")
        raw["Contents/section1.xml"] = self.s1.encode("utf-8")
        raw["Contents/header.xml"] = self.header.xml.encode("utf-8")
        with zipfile.ZipFile(out_path, "w") as zout:
            for name, ctype, info in self.base_infos:
                zi = zipfile.ZipInfo(name, date_time=info.date_time if info is not None else (1980, 1, 1, 0, 0, 0))
                zi.compress_type = ctype
                if info is not None:
                    zi.external_attr = info.external_attr
                zout.writestr(zi, raw[name])

    def summary(self):
        lines = ["# patch_from_fresh 보고", "", "통계: %s" % json.dumps(self.stats, ensure_ascii=False),
                 "header 추가 항목: %s" % json.dumps(self.importer.added, ensure_ascii=False), "",
                 "## 수동 재적용 필요"]
        lines += ["- " + m for m in self.manual] or ["- 없음"]
        lines += ["", "## 로그"]
        lines += ["- " + l for l in self.log]
        return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--fresh", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protect", default="", help="보호할 표 캡션(쉼표 구분)")
    ap.add_argument("--allow-tables", dest="allow_tables", help="지정하면 이 캡션의 표만 fresh로 바꾸고 나머지 표는 전부 보호")
    ap.add_argument("--keep-prefix", dest="keep_prefix", help="이 접두사로 시작하는 본문 문단은 base 유지(사용자 직접 수정분), JSON 배열 파일 또는 '|' 구분 문자열")
    ap.add_argument("--text-replace", dest="text_replace")
    ap.add_argument("--appendix")
    ap.add_argument("--toc-lines", dest="toc_lines")
    ap.add_argument("--report")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    protect = [p.strip() for p in a.protect.split(",") if p.strip()]
    allow = None if not a.allow_tables else [p.strip() for p in a.allow_tables.split(",") if p.strip()]
    keep = ()
    if a.keep_prefix:
        if os.path.isfile(a.keep_prefix):
            with open(a.keep_prefix, encoding="utf-8") as f:
                keep = tuple(json.load(f))
        else:
            keep = tuple(k for k in a.keep_prefix.split("|") if k)
    pt = Patcher(a.base, a.fresh, protect, a.report, allow_tables=allow, keep_prefix=keep)
    pt.patch_body()
    if a.text_replace:
        with open(a.text_replace, encoding="utf-8") as f:
            pt.text_replace(json.load(f))
    if a.appendix:
        with open(a.appendix, encoding="utf-8") as f:
            pt.appendix_insert(json.load(f))
    if a.toc_lines:
        with open(a.toc_lines, encoding="utf-8") as f:
            pt.toc_lines(json.load(f))
    rep = pt.summary()
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(rep)
    print(rep.split("\n## 로그")[0])
    if not a.dry_run:
        pt.write(a.out)
        print("저장:", a.out)


if __name__ == "__main__":
    main()
