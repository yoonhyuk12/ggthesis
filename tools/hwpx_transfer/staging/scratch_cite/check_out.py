# -*- coding: utf-8 -*-
import re, sys, zipfile, hashlib
sys.stdout.reconfigure(encoding="utf-8")

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
RUN_BLOCK_RE = re.compile(
    r"<(?:\w+:)?run\b[^>]*?/>|<(?:\w+:)?run\b[^>]*?(?<!/)>.*?</(?:\w+:)?run>", re.S)
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')
LINESEG_RE = re.compile(r"<(?:\w+:)?linesegarray[\s>]")
CHARPR_TAG_RE = re.compile(r"<(?:\w+:)?charPr\b[^>]*?>")
ATTR_ID_RE = re.compile(r'\bid="(\d+)"')
ATTR_COLOR_RE = re.compile(r'\btextColor="([^"]*)"')


def paragraph_spans(xml):
    stack, spans = [], []
    for m in P_TOKEN_RE.finditer(xml):
        tok = m.group(0)
        if tok.startswith("</"):
            if stack:
                s0, e0 = stack.pop()
                spans.append((s0, e0, m.start(), m.end()))
        elif tok.endswith("/>"):
            spans.append((m.start(), m.end(), m.start(), m.end()))
        else:
            stack.append((m.start(), m.end()))
    spans.sort()
    return spans


def own_segment(xml, span, spans):
    s0, e0, s1, _ = span
    inner = [c for c in spans if c[0] > s0 and c[3] <= s1]
    outermost = []
    for child in inner:
        if not any(m[0] < child[0] and child[3] <= m[3] for m in outermost):
            outermost.append(child)
    parts, pos = [], e0
    for child in outermost:
        parts.append(xml[pos:child[0]])
        pos = child[3]
    parts.append(xml[pos:s1])
    return xml[s0:e0] + "".join(parts)


def para_text(seg):
    return "".join(T_TEXT_RE.findall(seg))


def run_texts(seg):
    out = []
    for m in RUN_BLOCK_RE.finditer(seg):
        block = m.group(0)
        ref = CHARPR_REF_RE.search(block[:block.find(">") + 1])
        text = "".join(T_TEXT_RE.findall(block))
        out.append((ref.group(1) if ref else None, text))
    return out


base = r"tools/hwpx_transfer/staging/scratch_cite/base.hwpx"
outp = r"tools/hwpx_transfer/staging/scratch_cite/out.hwpx"

with zipfile.ZipFile(base) as za, zipfile.ZipFile(outp) as zb:
    ia, ib = za.infolist(), zb.infolist()
    print("entry names equal", [e.filename for e in ia] == [e.filename for e in ib])
    print("compress_type equal", [e.compress_type for e in ia] == [e.compress_type for e in ib])
    for e in ia:
        ha = hashlib.sha256(za.read(e.filename)).hexdigest()
        hb = hashlib.sha256(zb.read(e.filename)).hexdigest()
        if ha != hb:
            print(f"DIFF {e.filename}")
    xml_a = za.read("Contents/section2.xml").decode("utf-8")
    xml_b = zb.read("Contents/section2.xml").decode("utf-8")
    header = za.read("Contents/header.xml").decode("utf-8")

red_ids = set()
for tag in CHARPR_TAG_RE.findall(header):
    color = ATTR_COLOR_RE.search(tag)
    ident = ATTR_ID_RE.search(tag)
    if color and ident and color.group(1).upper() == "#FF0000":
        red_ids.add(ident.group(1))
print("red ids", sorted(red_ids, key=int))

spans = paragraph_spans(xml_b)
print("out paras", len(spans), "base paras", len(paragraph_spans(xml_a)))

needles = [
    "라벨 데이터가 사실상 존재하지 않는다(Kim, 2025)",
    "Kim et al.(2025)이 화재",
    "한소은(2026)",
    "국토안전관리원(2024)",
    "오탐과 미탐을 모두 감소시킴을 검증하였다.",
    "가. 학위논문",
    "나. 학술지",
    "마. 기타",
]
print("\n=== TARGET PARAS ===")
for i, span in enumerate(spans):
    seg = own_segment(xml_b, span, spans)
    text = para_text(seg)
    if any(n in text for n in needles) or any(
        x in text for x in [
            "김석기, 「소규모", "이기수, 「건설현장의 안전", "이형도, 「객체탐지",
            "조도빈, 「국내 소규모", "Brown et al.", "Wilson, E. B.",
            "Ultralytics, [Computer Software]",
        ]
    ):
        print(f"\n[{i}] lineseg={bool(LINESEG_RE.search(seg))} text={text[:220]}")
        if any(n in text for n in [
            "라벨 데이터가", "Kim et al.(2025)이 화재", "한소은(2026)",
            "국토안전관리원(2024)", "오탐과 미탐",
        ]):
            for ref, t in run_texts(seg):
                if t:
                    flag = " RED" if ref in red_ids else ""
                    print(f"    run {ref}{flag}: {t[:120]!r}")

# bibliography sequence around 가/나/마
print("\n=== BIB SEQUENCE ===")
in_bib = False
for i, span in enumerate(spans):
    text = para_text(own_segment(xml_b, span, spans)).strip()
    if text == "참고문헌":
        in_bib = True
    if in_bib:
        if text:
            print(f"  [{i}] {text[:160]}")
        if text.startswith("부") and "록" in text:
            break
