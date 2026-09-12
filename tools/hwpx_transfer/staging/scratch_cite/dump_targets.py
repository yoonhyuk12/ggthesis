# -*- coding: utf-8 -*-
"""Dump hwpx paragraphs relevant to citation/ref edits."""
import hashlib
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

P_TOKEN_RE = re.compile(r"<(?:\w+:)?p\b[^>]*?>|</(?:\w+:)?p>")
T_TEXT_RE = re.compile(r"<(?:\w+:)?t>(.*?)</(?:\w+:)?t>", re.S)
RUN_BLOCK_RE = re.compile(
    r"<(?:\w+:)?run\b[^>]*?/>|<(?:\w+:)?run\b[^>]*?(?<!/)>.*?</(?:\w+:)?run>", re.S)
CHARPR_REF_RE = re.compile(r'charPrIDRef="(\d+)"')
CHARPR_TAG_RE = re.compile(r"<(?:\w+:)?charPr\b[^>]*?>")
ATTR_ID_RE = re.compile(r'\bid="(\d+)"')
ATTR_COLOR_RE = re.compile(r'\btextColor="([^"]*)"')
ATTR_HEIGHT_RE = re.compile(r'\bheight="(\d+)"')
LINESEG_RE = re.compile(r"<(?:\w+:)?linesegarray[\s>]")


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


def run_texts(xml):
    out = []
    for m in RUN_BLOCK_RE.finditer(xml):
        block = m.group(0)
        ref = CHARPR_REF_RE.search(block[:block.find(">") + 1])
        text = "".join(T_TEXT_RE.findall(block))
        out.append((ref.group(1) if ref else None, text, block[: min(200, len(block))]))
    return out


KEYS = [
    "라벨 데이터가 사실상 존재하지 않는다",
    "Kim et al.(2025)",
    "한소은(2026)",
    "국토안전관리원(2024)",
    "오탐과 미탐을 모두 감소시킴을 검증하였다",
    "이형도",
    "참고문헌",
    "김윤헌",
    "Brown",
    "Wilson",
    "Ultralytics",
    "조도빈",
    "이기수",
    "김석기",
    "CITE_TODO",
    "학위논문",
    "학술지",
    "국내문헌",
    "국외문헌",
    "표준",
    "기술자료",
]


def main():
    path = r"tools/hwpx_transfer/staging/scratch_cite/base.hwpx"
    with zipfile.ZipFile(path) as zf:
        header = zf.read("Contents/header.xml").decode("utf-8")
        print("=== RED CHARPR ===")
        for tag in CHARPR_TAG_RE.findall(header):
            color = ATTR_COLOR_RE.search(tag)
            ident = ATTR_ID_RE.search(tag)
            height = ATTR_HEIGHT_RE.search(tag)
            if color and ident and color.group(1).upper() == "#FF0000":
                print(f"  id={ident.group(1)} height={height.group(1) if height else '?'} tag={tag[:180]}")

        xml = zf.read("Contents/section2.xml").decode("utf-8")
        print(f"\nsection2.xml bytes={len(xml.encode('utf-8'))} sha256={hashlib.sha256(xml.encode('utf-8')).hexdigest()[:16]}")

        spans = paragraph_spans(xml)
        paras = []
        for i, span in enumerate(spans):
            seg = own_segment(xml, span, spans)
            text = para_text(seg)
            paras.append((i, span, seg, text))

        print(f"paragraphs={len(paras)}")

        print("\n=== MATCHING PARAS ===")
        for i, span, seg, text in paras:
            if not text.strip():
                continue
            if any(k in text for k in KEYS):
                print(f"\n----- para {i} len={len(text)} lineseg={bool(LINESEG_RE.search(seg))} -----")
                print(text[:800].replace("\n", "\\n"))
                if len(text) > 800:
                    print("...[truncated]...")
                runs = run_texts(seg)
                # only print runs if short or relevant
                if any(k in text for k in [
                    "라벨 데이터가 사실상 존재하지 않는다",
                    "Kim et al.(2025)",
                    "한소은(2026)",
                    "국토안전관리원(2024)",
                    "오탐과 미탐을 모두 감소시킴을 검증하였다",
                ]):
                    print("  RUNS:")
                    for ref, t, raw in runs:
                        if t:
                            print(f"    charPr={ref!s:4} | {t[:200]!r}")

        # bibliography region: find heading
        print("\n=== BIBLIOGRAPHY REGION (last 80 non-empty paras) ===")
        nonempty = [(i, text) for i, _, _, text in paras if text.strip()]
        for i, text in nonempty[-80:]:
            print(f"[{i}] {text[:180].replace(chr(10), ' ')}")


if __name__ == "__main__":
    main()
