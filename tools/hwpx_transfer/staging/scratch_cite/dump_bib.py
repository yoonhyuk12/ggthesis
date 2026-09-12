# -*- coding: utf-8 -*-
import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
RUN_BLOCK_RE = re.compile(
    r"<(?:\w+:)?run\b[^>]*?/>|<(?:\w+:)?run\b[^>]*?(?<!/)>.*?</(?:\w+:)?run>", re.S)
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')
PARA_PR_RE = re.compile(r'paraPrIDRef="(\d+)"')
STYLE_RE = re.compile(r'styleIDRef="(\d+)"')


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
    xml = zf.read("Contents/section2.xml").decode("utf-8")

spans = paragraph_spans(xml)
print("=== BIBLIOGRAPHY PARAS 2000-2200 ===")
for i, span in enumerate(spans):
    if i < 2000 or i > 2150:
        continue
    seg = own_segment(xml, span, spans)
    text = para_text(seg).strip()
    if not text:
        continue
    open_tag = xml[span[0]:span[1]]
    ppr = PARA_PR_RE.search(open_tag)
    sty = STYLE_RE.search(open_tag)
    runs = []
    for m in RUN_BLOCK_RE.finditer(seg):
        block = m.group(0)
        ref = CHARPR_REF_RE.search(block[:block.find(">") + 1])
        t = "".join(T_TEXT_RE.findall(block))
        if t:
            runs.append(f"{ref.group(1) if ref else '-'}:{t[:40]}")
    print(f"[{i}] paraPr={ppr.group(1) if ppr else '?'} style={sty.group(1) if sty else '?'} runs={runs[:3]}")
    print(f"    {text[:220]}")

# dump XML of one bib item and heading for cloning
print("\n=== SAMPLE XML para 2009 heading / 2010 item / 2017 last thesis ===")
for i in (2007, 2008, 2009, 2010, 2017, 2018, 2019, 2020):
    span = spans[i]
    seg = own_segment(xml, span, spans)
    print(f"\n----- para {i} xml len={len(seg)} -----")
    print(seg[:1500])
