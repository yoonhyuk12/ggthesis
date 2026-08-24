# paraPr 여백·줄간격, tabPr 리더, secPr 페이지 설정, 대표 표 XML, 전면부 표 내용을 심층 실측하는 스크립트
import io
import sys
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted\Contents"
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"

def strip(tag):
    return tag.split("}")[1]

def dump_tree(e, indent=0):
    print("    " * indent + f"{strip(e.tag)}: {dict(e.attrib)}")
    for ch in e:
        dump_tree(ch, indent + 1)

header = ET.parse(BASE + r"\header.xml").getroot()

# 1) 글꼴 이름 (utf-8 정상 출력)
print("=== fontfaces (HANGUL) ===")
for ff in header.iter():
    if strip(ff.tag) == "fontface" and ff.get("lang") == "HANGUL":
        for f in ff:
            if strip(f.tag) == "font":
                print(f"  font id={f.get('id')}: {f.get('face')}")

print()
print("=== style names (all 40) ===")
for s in header.iter():
    if strip(s.tag) == "style":
        a = s.attrib
        print(f"  style {a.get('id')}: name={a.get('name')} type={a.get('type')} paraPr={a.get('paraPrIDRef')} charPr={a.get('charPrIDRef')}")

# 2) paraPr 심층 (switch/case 내부 margin·lineSpacing 포함)
print()
print("=== paraPr deep dump (IDs of interest) ===")
PARA_IDS = {"24", "57", "66", "51", "50", "25", "31", "30", "52", "26", "5", "72", "74", "70", "64", "59", "12"}
for p in header.iter():
    if strip(p.tag) == "paraPr" and p.get("id") in PARA_IDS:
        print(f"--- paraPr {p.get('id')} ---")
        dump_tree(p, 1)

# 3) tabPr 심층 (리더점 tabItem)
print()
print("=== tabPr deep dump ===")
for t in header.iter():
    if strip(t.tag) == "tabPr":
        print(f"--- tabPr {t.get('id')} attrs={dict(t.attrib)} ---")
        dump_tree(t, 1)

# 4) 각 섹션 secPr
for i in range(3):
    tree = ET.parse(BASE + rf"\section{i}.xml")
    root = tree.getroot()
    print()
    print(f"=== section{i}.xml secPr ===")
    for e in root.iter():
        if strip(e.tag) == "secPr":
            dump_tree(e, 1)
            break
