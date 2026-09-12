# -*- coding: utf-8 -*-
import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
RUN_BLOCK_RE = re.compile(
    r"<(?:\w+:)?run\b[^>]*?/>|<(?:\w+:)?run\b[^>]*?(?<!/)>.*?</(?:\w+:)?run>", re.S)
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')


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


with zipfile.ZipFile(r"tools/hwpx_transfer/staging/scratch_cite/out.hwpx") as zf:
    xml = zf.read("Contents/section2.xml").decode("utf-8")
spans = paragraph_spans(xml)

for i in (70, 484, 634):
    seg = own_segment(xml, spans[i], spans)
    print(f"\n===== {i} =====")
    print(para_text(seg))
    print("--- runs ---")
    for m in RUN_BLOCK_RE.finditer(seg):
        block = m.group(0)
        ref = CHARPR_REF_RE.search(block[:block.find(">") + 1])
        text = "".join(T_TEXT_RE.findall(block))
        if text:
            print(f"  {ref.group(1) if ref else '-'}: {text}")

# marker census
print("\nCITE_TODO count", xml.count("[CITE_TODO"))
print("new markers:")
for s in [
    "[CITE_TODO: 라벨 데이터 부재 근거 — ref54 부적합]",
    "[CITE_TODO: 화재검출 문헌 서지]",
    "[CITE_TODO: 한소은 2026 서지 확인]",
    "[CITE_TODO: 국토안전관리원 2024 가이드라인 서지]",
]:
    print(f"  {s}: {xml.count(s)}")
