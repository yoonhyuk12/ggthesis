# 각 section*.xml의 문단 인덱스·styleIDRef·paraPrIDRef·charPrIDRef·텍스트를 TSV로 덤프하는 스크립트
import os
import re
import xml.etree.ElementTree as ET

BASE = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted\Contents"
NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
}
HP = NS["hp"]

def para_text(p):
    # 문단 내 모든 hp:t 텍스트를 이어붙인다 (표 내부 포함 여부는 호출부에서 결정)
    texts = []
    for t in p.iter(f"{{{HP}}}t"):
        texts.append("".join(t.itertext()))
    return "".join(texts)

def direct_text(p):
    # 표/그리기 개체 내부를 제외한, 문단 직속 run의 텍스트만
    texts = []
    for run in p.findall(f"{{{HP}}}run"):
        for child in run:
            tag = child.tag.split("}")[1]
            if tag == "t":
                texts.append("".join(child.itertext()))
    return "".join(texts)

def has_child(p, tag):
    return p.find(f".//{{{HP}}}{tag}") is not None

for fname in ["section0.xml", "section1.xml", "section2.xml"]:
    path = os.path.join(BASE, fname)
    tree = ET.parse(path)
    root = tree.getroot()
    paras = root.findall(f"{{{HP}}}p")
    out = os.path.join(os.path.dirname(BASE), "..", fname.replace(".xml", "_paras.tsv"))
    with open(out, "w", encoding="utf-8") as f:
        f.write("idx\tstyleIDRef\tparaPrIDRef\tcharPrIDRefs\ttbl\tpageBreak\ttext\n")
        for i, p in enumerate(paras):
            style = p.get("styleIDRef")
            parapr = p.get("paraPrIDRef")
            pagebreak = p.get("pageBreak")
            charprs = sorted({r.get("charPrIDRef") for r in p.findall(f"{{{HP}}}run")})
            tbl = "T" if p.find(f".//{{{HP}}}tbl") is not None else ""
            txt = direct_text(p).replace("\t", " ").replace("\n", " ")
            if tbl and not txt:
                inner = para_text(p).replace("\t", " ").replace("\n", " ")
                txt = "[TBL] " + inner[:80]
            f.write(f"{i}\t{style}\t{parapr}\t{','.join(x or '-' for x in charprs)}\t{tbl}\t{pagebreak or ''}\t{txt[:120]}\n")
    print(f"{fname}: {len(paras)} paragraphs -> {out}")
