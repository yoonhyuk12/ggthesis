# header.xml에서 지정 ID의 charPr/paraPr/style/tabPr/borderFill 정의를 실측 요약하는 스크립트
import xml.etree.ElementTree as ET

PATH = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted\Contents\header.xml"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HC = "http://www.hancom.co.kr/hwpml/2011/core"

tree = ET.parse(PATH)
root = tree.getroot()

def strip(tag):
    return tag.split("}")[1]

def find_all(root, local):
    return [e for e in root.iter() if strip(e.tag) == local]

fontfaces = {}
for ff in find_all(root, "fontface"):
    lang = ff.get("lang")
    for f in ff:
        if strip(f.tag) == "font":
            fontfaces[(lang, f.get("id"))] = f.get("face")

charprs = {c.get("id"): c for c in find_all(root, "charPr")}
paraprs = {p.get("id"): p for p in find_all(root, "paraPr")}
styles = {s.get("id"): s for s in find_all(root, "style")}
tabprs = {t.get("id"): t for t in find_all(root, "tabPr")}
borderfills = {b.get("id"): b for b in find_all(root, "borderFill")}

print(f"counts: charPr={len(charprs)} paraPr={len(paraprs)} style={len(styles)} tabPr={len(tabprs)} borderFill={len(borderfills)}")
print(f"fontfaces: {fontfaces}")
print()

def show_charpr(cid):
    c = charprs.get(cid)
    if c is None:
        print(f"charPr {cid}: NOT FOUND"); return
    attrs = dict(c.attrib)
    detail = {}
    for ch in c:
        t = strip(ch.tag)
        detail[t] = dict(ch.attrib)
    print(f"charPr {cid}: {attrs}")
    for k, v in detail.items():
        print(f"    {k}: {v}")

def show_parapr(pid):
    p = paraprs.get(pid)
    if p is None:
        print(f"paraPr {pid}: NOT FOUND"); return
    print(f"paraPr {pid}: {dict(p.attrib)}")
    for ch in p:
        print(f"    {strip(ch.tag)}: {dict(ch.attrib)}")
        for gd in ch:
            print(f"        {strip(gd.tag)}: {dict(gd.attrib)}")

def show_style(sid):
    s = styles.get(sid)
    if s is None:
        print(f"style {sid}: NOT FOUND"); return
    print(f"style {sid}: {dict(s.attrib)}")

def show_tabpr(tid):
    t = tabprs.get(tid)
    if t is None:
        print(f"tabPr {tid}: NOT FOUND"); return
    print(f"tabPr {tid}: {dict(t.attrib)}")
    for ch in t:
        print(f"    {strip(ch.tag)}: {dict(ch.attrib)}")

print("=== styles (all) ===")
for sid in sorted(styles, key=int):
    s = styles[sid]
    a = s.attrib
    print(f"style {sid}: name={a.get('name')!r} engName={a.get('engName')!r} type={a.get('type')} paraPrIDRef={a.get('paraPrIDRef')} charPrIDRef={a.get('charPrIDRef')} nextStyleIDRef={a.get('nextStyleIDRef')}")

print()
print("=== charPr of interest ===")
for cid in ["63", "67", "41", "61", "62", "13", "116", "21", "42", "52", "9", "36", "50", "54"]:
    show_charpr(cid)
    print()

print("=== paraPr of interest ===")
for pid in ["24", "57", "66", "51", "50", "25", "31", "30", "52", "26", "5", "72", "74", "12", "59", "70"]:
    show_parapr(pid)
    print()

print("=== tabPr (all) ===")
for tid in sorted(tabprs, key=int):
    show_tabpr(tid)

print()
print("=== borderFill (all, summary) ===")
for bid in sorted(borderfills, key=int):
    b = borderfills[bid]
    parts = []
    for ch in b:
        t = strip(ch.tag)
        if t in ("leftBorder", "rightBorder", "topBorder", "bottomBorder", "diagonal"):
            parts.append(f"{t}={ch.get('type')}/{ch.get('width')}")
        elif t == "fillBrush":
            for br in ch.iter():
                if strip(br.tag) == "winBrush":
                    parts.append(f"fill={br.get('faceColor')}")
    print(f"borderFill {bid}: threeD={b.get('threeD')} " + " ".join(parts))
