# 완성본 hwpx에서 문단·표를 구조 그대로 뽑아 QA 대조에 쓰는 독립 추출기 (조립기 코드 미사용)
"""hwpx_dump.py — hwpx 섹션 XML을 문단/표 구조로 추출한다.

조립 파이프라인(blocks_to_hwpx.py, extract_text.py)과 독립적으로 zipfile +
ElementTree만 써서 다시 구현한 추출기다. 최상위 문단은 텍스트로, 표는
행×열 셀 문자열 2차원 배열로 뽑는다.

    python hwpx_dump.py --input X.hwpx --section 2 --json out.json
    python hwpx_dump.py --input X.hwpx --section 2          # 사람이 읽는 형식
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def sections(path):
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist()
                 if re.match(r"Contents/section\d+\.xml$", n)]
        names.sort(key=lambda n: int(re.search(r"section(\d+)", n).group(1)))
        return [(n, zf.read(n)) for n in names]


def run_text(run):
    """hp:run 하나의 텍스트. hp:t는 그대로, 줄바꿈 컨트롤(hp:lineBreak)은 \n으로."""
    parts = []
    for child in run:
        tag = child.tag
        if tag == HP + "t":
            # hp:t 안에 <hp:lineBreak/> 같은 자식이 있으면 줄바꿈으로 치환
            parts.append(t_text(child))
        elif tag in (HP + "tbl", HP + "ctrl", HP + "pic", HP + "container"):
            continue
        else:
            parts.append("".join(child.itertext()))
    return "".join(parts)


def t_text(t):
    out = [t.text or ""]
    for c in t:
        if c.tag == HP + "lineBreak":
            out.append("\n")
        elif c.tag in (HP + "markpenBegin", HP + "markpenEnd", HP + "titleMark"):
            pass
        else:
            out.append("".join(c.itertext()))
        out.append(c.tail or "")
    return "".join(out)


def para_own_text(p):
    return "".join(run_text(r) for r in p.findall(HP + "run"))


def cell_text(tc):
    """표 셀 텍스트. 셀 안 문단은 \n으로 잇는다(원본 <br> 자리)."""
    sub = tc.find(HP + "subList")
    if sub is None:
        return ""
    lines = []
    for p in sub.findall(HP + "p"):
        lines.append(para_own_text(p))
    return "\n".join(lines)


def table_grid(tbl):
    """표를 행 리스트(각 행은 셀 문자열 리스트)로. colSpan/rowSpan은 span 정보로 별기."""
    rows = []
    spans = []
    for tr in tbl.findall(HP + "tr"):
        row = []
        srow = []
        for tc in tr.findall(HP + "tc"):
            row.append(cell_text(tc))
            span = tc.find(HP + "cellSpan")
            cs = int(span.get("colSpan", "1")) if span is not None else 1
            rs = int(span.get("rowSpan", "1")) if span is not None else 1
            srow.append((cs, rs))
        rows.append(row)
        spans.append(srow)
    return rows, spans


def walk(root):
    """최상위 문단을 순서대로 돌며 {kind: para|table} 항목을 만든다."""
    items = []
    for idx, p in enumerate(root.findall(HP + "p")):
        text = para_own_text(p)
        style = p.get("styleIDRef")
        parapr = p.get("paraPrIDRef")
        if text.strip():
            items.append({"kind": "para", "idx": idx, "style": style,
                          "paraPr": parapr, "text": text})
        for run in p.findall(HP + "run"):
            for tbl in run.findall(HP + "tbl"):
                rows, spans = table_grid(tbl)
                items.append({"kind": "table", "idx": idx,
                              "rowCnt": int(tbl.get("rowCnt", len(rows))),
                              "colCnt": int(tbl.get("colCnt", 0)),
                              "rows": rows, "spans": spans})
    return items


def dump(path, sec_filter=None):
    out = {}
    for name, data in sections(path):
        num = int(re.search(r"section(\d+)", name).group(1))
        if sec_filter is not None and num != sec_filter:
            continue
        out["section%d" % num] = walk(ET.fromstring(data))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--section", type=int, default=None)
    ap.add_argument("--json")
    args = ap.parse_args()
    data = dump(args.input, args.section)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("wrote %s" % args.json)
        for k, v in data.items():
            print("  %s: %d items (para %d, table %d)" % (
                k, len(v), sum(1 for i in v if i["kind"] == "para"),
                sum(1 for i in v if i["kind"] == "table")))
    else:
        for k, v in data.items():
            for i, it in enumerate(v):
                if it["kind"] == "para":
                    print("%s\t%d\tP[%s]\t%s" % (k, i, it["style"], it["text"]))
                else:
                    print("%s\t%d\tTABLE %dx%d" % (k, i, it["rowCnt"], it["colCnt"]))
                    for r in it["rows"]:
                        print("\t\t| " + " | ".join(c.replace("\n", "\\n") for c in r))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
