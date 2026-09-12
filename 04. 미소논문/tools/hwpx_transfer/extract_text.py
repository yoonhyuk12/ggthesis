# 완성 hwpx에서 문단·표 셀 텍스트를 문서 순서대로 뽑아 blocks JSON과 대조하는 QA 유틸
"""extract_text.py — hwpx 텍스트 추출 · blocks 대조.

사용 예:
    # 1) 텍스트 단위 목록 출력 (TSV: 섹션<TAB>순번<TAB>종류<TAB>텍스트)
    python tools/hwpx_transfer/extract_text.py --input out.hwpx

    # 2) blocks JSON의 모든 텍스트가 순서대로 들어갔는지 대조 (누락 목록 출력)
    python tools/hwpx_transfer/extract_text.py --input out.hwpx \
        --verify-blocks ch01.blocks.json apx1.blocks.json

    # 3) zip · XML 무결성 검사
    python tools/hwpx_transfer/extract_text.py --input out.hwpx --check-integrity

zipfile + ElementTree(표준 라이브러리)만 쓴다.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

# blocks_to_hwpx.py가 셀 텍스트에 적용하는 변환과 같은 규칙(대조 기준을 맞추기 위함).
CELL_LINEBREAK_TOKEN = "<br>"
EMSP_TOKEN = "&emsp;"
EMSP_CHAR = " "


def section_names(zf):
    names = [n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n)]
    return sorted(names, key=lambda n: int(re.search(r"section(\d+)", n).group(1)))


def para_text(p):
    """hp:p 요소의 직속 run 텍스트만 모은다(중첩 표·각주 subList는 제외)."""
    out = []
    for run in p.findall(HP + "run"):
        for child in run:
            if child.tag in (HP + "tbl", HP + "ctrl"):
                continue
            out.append("".join(child.itertext()))
            if child.tail:
                out.append(child.tail)
    return "".join(out)


def walk_paragraph(p, section, index, out, kind="p"):
    """문단 텍스트를 내보내고, 문단 안 표는 셀 문단을 문서 순서대로 이어서 내보낸다."""
    text = para_text(p)
    if text.strip():
        out.append((section, index, kind, text))
    for run in p.findall(HP + "run"):
        for tbl in run.findall(HP + "tbl"):
            for tr in tbl.findall(HP + "tr"):
                for tc in tr.findall(HP + "tc"):
                    sub = tc.find(HP + "subList")
                    if sub is None:
                        continue
                    for cp in sub.findall(HP + "p"):
                        walk_paragraph(cp, section, index, out, kind="cell")


def iter_text_units(path):
    """(섹션명, 최상위 문단 순번, 종류, 텍스트) 목록을 문서 순서대로 돌려준다."""
    units = []
    with zipfile.ZipFile(path) as zf:
        for name in section_names(zf):
            root = ET.fromstring(zf.read(name))
            for idx, p in enumerate(root.findall(HP + "p")):
                walk_paragraph(p, name.split("/")[-1], idx, units)
    return units


def check_integrity(path):
    """zip 무결성과 XML 파싱 가능 여부를 확인한다. (문제 목록, 검사한 XML 수)"""
    problems = []
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            problems.append("zip CRC 오류: %s" % bad)
        xml_count = 0
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            data = zf.read(name)
            if data.startswith(b"\xef\xbb\xbf"):
                problems.append("UTF-8 BOM 발견: %s" % name)
            try:
                ET.fromstring(data)
                xml_count += 1
            except ET.ParseError as exc:
                problems.append("XML 파싱 실패 %s: %s" % (name, exc))
    return problems, xml_count


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def expected_units(block_paths):
    """blocks JSON에서 hwpx에 들어가야 할 텍스트 단위를 순서대로 만든다."""
    expected = []
    for path in block_paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for b in data["blocks"]:
            kind = b["type"]
            if kind in ("h1", "h2", "h3", "h4", "table_caption",
                        "figure_caption", "figure_placeholder"):
                expected.append((path, kind, b["text"]))
            elif kind == "figure_image":
                # 그림은 BinData PNG로 들어가 텍스트가 없다 — 대조 대상에서 제외한다.
                continue
            elif kind == "p":
                expected.append((path, kind, "".join(r.get("text", "") for r in b["runs"])))
            elif kind == "table":
                for row in [b["header"]] + b["rows"]:
                    for cellrec in row:
                        for line in cellrec.split(CELL_LINEBREAK_TOKEN):
                            if line.strip():
                                expected.append((path, "cell", line))
            else:
                raise SystemExit("알 수 없는 블록 타입: %r" % kind)
    # 조립기와 같은 규칙으로 &emsp;를 전각 공백으로 바꿔 놓아야 대조 기준이 일치한다
    return [(p, k, t.replace(EMSP_TOKEN, EMSP_CHAR))
            for p, k, t in expected if normalize(t)]


def verify(units, expected):
    """추출 텍스트 흐름이 기대 텍스트를 순서대로 포함하는지 확인한다. 누락 목록을 돌려준다."""
    haystack = [normalize(t) for _, _, _, t in units]
    missing = []
    cursor = 0
    for path, kind, text in expected:
        needle = normalize(text)
        found = -1
        for i in range(cursor, len(haystack)):
            if needle in haystack[i]:
                found = i
                break
        if found < 0:
            missing.append((path, kind, text))
        else:
            cursor = found + 1
    return missing


def main(argv=None):
    ap = argparse.ArgumentParser(description="hwpx 텍스트 추출 · blocks 대조 QA 유틸")
    ap.add_argument("--input", required=True, help="검사할 hwpx")
    ap.add_argument("--verify-blocks", nargs="+", help="대조할 blocks JSON (본문 순서대로)")
    ap.add_argument("--check-integrity", action="store_true", help="zip·XML 무결성만 검사")
    ap.add_argument("--limit", type=int, default=0, help="TSV 출력 줄 수 제한(0=전체)")
    args = ap.parse_args(argv)

    exit_code = 0
    if args.check_integrity or args.verify_blocks:
        problems, xml_count = check_integrity(args.input)
        print("무결성: XML %d개 파싱 성공, 문제 %d건" % (xml_count, len(problems)))
        for p in problems:
            print("  - " + p)
        if problems:
            exit_code = 1

    units = iter_text_units(args.input)
    print("추출 텍스트 단위: %d" % len(units))

    if args.verify_blocks:
        expected = expected_units(args.verify_blocks)
        missing = verify(units, expected)
        print("대조 대상 텍스트: %d, 누락: %d" % (len(expected), len(missing)))
        for path, kind, text in missing:
            print("  [누락] %s %s: %s" % (path, kind, text[:120]))
        if missing:
            exit_code = 1
    elif not args.check_integrity:
        for i, (sec, idx, kind, text) in enumerate(units):
            if args.limit and i >= args.limit:
                break
            print("%s\t%d\t%s\t%s" % (sec, idx, kind, text))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
