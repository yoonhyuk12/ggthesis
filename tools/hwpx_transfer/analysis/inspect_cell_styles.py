# 표 셀 내부 문단·글자 스타일(charPr 7/58/89, paraPr 11/75/76, charPr 60) 정의를 실측하는 스크립트
import io
import sys
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PATH = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted\Contents\header.xml"
root = ET.parse(PATH).getroot()

def strip(tag):
    return tag.split("}")[1]

def dump_tree(e, indent=0):
    print("    " * indent + f"{strip(e.tag)}: {dict(e.attrib)}")
    for ch in e:
        dump_tree(ch, indent + 1)

CHAR_IDS = {"7", "58", "89", "92", "60", "68"}
PARA_IDS = {"11", "75", "76", "53", "62"}

for e in root.iter():
    t = strip(e.tag)
    if t == "charPr" and e.get("id") in CHAR_IDS:
        a = e.attrib
        font = e.find(f"{{{e.tag.split('}')[0][1:]}}}fontRef")
        bold = any(strip(c.tag) == "bold" for c in e)
        fr = next((c for c in e if strip(c.tag) == "fontRef"), None)
        print(f"charPr {a['id']}: height={a.get('height')} color={a.get('textColor')} bold={bold} fontRef.hangul={fr.get('hangul') if fr is not None else '?'}")
    elif t == "paraPr" and e.get("id") in PARA_IDS:
        print(f"--- paraPr {e.get('id')} ---")
        dump_tree(e, 1)
