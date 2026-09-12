# -*- coding: utf-8 -*-
import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
CHARPR_TAG_RE = re.compile(r'<(?:\w+:)?charPr\b([^>]*?)>')
ATTR_ID_RE = re.compile(r'\bid="(\d+)"')
ATTR_HEIGHT_RE = re.compile(r'\bheight="(\d+)"')
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


path = r"tools/hwpx_transfer/staging/scratch_cite/base.hwpx"
with zipfile.ZipFile(path) as zf:
    header = zf.read("Contents/header.xml").decode("utf-8")
    xml = zf.read("Contents/section2.xml").decode("utf-8")

print("=== CHARPR 37 / 8 / 70-73 ===")
for tag in CHARPR_TAG_RE.finditer(header):
    attrs = tag.group(1)
    ident = ATTR_ID_RE.search(attrs)
    if ident and ident.group(1) in {"8", "37", "70", "71", "72", "73", "36"}:
        h = ATTR_HEIGHT_RE.search(attrs)
        c = ATTR_COLOR_RE.search(attrs)
        print(f"id={ident.group(1)} height={h.group(1) if h else '?'} color={c.group(1) if c else '?'}")

# count charPr 71 usage
print("charPr 71 count:", xml.count('charPrIDRef="71"'))
print("charPr 70 count:", xml.count('charPrIDRef="70"'))
print("charPr 72 count:", xml.count('charPrIDRef="72"'))
print("charPr 73 count:", xml.count('charPrIDRef="73"'))

spans = paragraph_spans(xml)
# existing CITE_TODO sample (para 61)
print("\n=== EXISTING CITE_TODO XML (para 61 excerpt) ===")
seg = own_segment(xml, spans[61], spans)
idx = seg.find("[CITE_TODO")
print(seg[max(0, idx-250): idx+350])

# anchors
for i in (70, 412, 484, 634, 674):
    span = spans[i]
    seg = own_segment(xml, span, spans)
    text = para_text(seg)
    print(f"\n===== PARA {i} FULL TEXT =====")
    print(text)
    print(f"--- XML around target ---")
    for needle in [
        "오탐과 미탐을 모두 감소시킴을 검증하였다.",
        "(Kim, 2025)",
        "Kim et al.(2025)",
        "한소은(2026)",
        "국토안전관리원(2024)",
    ]:
        p = text.find(needle)
        if p >= 0:
            print(f"  found {needle!r} at textpos {p}")
            # find in xml
            q = seg.find(needle.replace("&", "&amp;") if False else needle)
            # Kim might be in one run
            if needle in seg:
                j = seg.find(needle)
                print(seg[max(0, j-120): j+len(needle)+80])
            else:
                # split across runs? print last 400 of xml t tags
                print("  needle not contiguous in xml")
                print(seg[:800])
