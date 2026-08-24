# 대표 표(<표 3-1>) 원본 XML 추출, 전면부 표 내용 확인, 목차 탭 구조, 머리말/꼬리말/쪽번호 실측 스크립트
import io
import sys
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted\Contents"
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
ET.register_namespace("hp", HP)

def strip(tag):
    return tag.split("}")[1]

def paras(fname):
    root = ET.parse(BASE + "\\" + fname).getroot()
    return root.findall(f"{{{HP}}}p")

def all_text(e):
    return "".join("".join(t.itertext()) for t in e.iter(f"{{{HP}}}t"))

# 1) section2 para 223 의 표 (<표 3-1> 연구변수의 구성) 원본 XML
s2 = paras("section2.xml")
p223 = s2[223]
tbl = p223.find(f".//{{{HP}}}tbl")
xml_str = ET.tostring(tbl, encoding="unicode")
with open(r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\table_3_1_raw.xml", "w", encoding="utf-8") as f:
    f.write(xml_str)
print(f"table 3-1 raw XML saved, length={len(xml_str)}")
print(f"tbl attrs: {dict(tbl.attrib)}")

# 표 구조 요약: 행·셀·span·크기·셀 문단 스타일
for ch in tbl:
    t = strip(ch.tag)
    if t in ("sz", "pos", "outMargin", "inMargin", "cellzoneList"):
        print(f"  tbl/{t}: {dict(ch.attrib)}")
        for gd in ch:
            print(f"      {strip(gd.tag)}: {dict(gd.attrib)}")

rows = tbl.findall(f"{{{HP}}}tr")
print(f"rows={len(rows)}")
for ri, tr in enumerate(rows[:4]):
    for tc in tr.findall(f"{{{HP}}}tc"):
        addr = tc.find(f"{{{HP}}}cellAddr")
        span = tc.find(f"{{{HP}}}cellSpan")
        csz = tc.find(f"{{{HP}}}cellSz")
        cmg = tc.find(f"{{{HP}}}cellMargin")
        sub = tc.find(f"{{{HP}}}subList")
        cell_paras = sub.findall(f"{{{HP}}}p") if sub is not None else []
        pinfo = []
        for cp in cell_paras[:1]:
            runs = cp.findall(f"{{{HP}}}run")
            pinfo.append(f"paraPr={cp.get('paraPrIDRef')},style={cp.get('styleIDRef')},charPr={[r.get('charPrIDRef') for r in runs]}")
        txt = all_text(tc)[:24]
        print(f"  r{ri} bf={tc.get('borderFillIDRef')} addr=({addr.get('colAddr')},{addr.get('rowAddr')}) span=({span.get('colSpan')},{span.get('rowSpan')}) sz=({csz.get('width')},{csz.get('height')}) margin={dict(cmg.attrib) if cmg is not None else None} {pinfo} txt={txt!r}")

# 행별 셀 폭 합계 (그리드 검증)
print("row width sums:")
for ri, tr in enumerate(rows):
    ws = [int(tc.find(f'{{{HP}}}cellSz').get('width')) for tc in tr.findall(f"{{{HP}}}tc")]
    print(f"  r{ri}: n={len(ws)} sum={sum(ws)} widths={ws}")

# 2) 표 캡션 확인: 표 내부에 캡션 문단이 있는지 (hp:caption) 또는 별도 문단인지
cap = tbl.find(f".//{{{HP}}}caption")
print(f"tbl caption element: {cap is not None}")
# 표 첫 셀 위 문단(=para 222? 아니면 표 앞 문단)의 캡션 후보 확인
for idx in (221, 222, 223):
    p = s2[idx]
    print(f"s2 para {idx}: paraPr={p.get('paraPrIDRef')} style={p.get('styleIDRef')} text={all_text(p)[:60]!r}")

# 표 안 캡션 문단이 서브리스트 밖(같은 문단 run)에 있는지: para223의 run 구조
print("para223 runs:")
for run in s2[223].findall(f"{{{HP}}}run"):
    kinds = [strip(c.tag) for c in run]
    print(f"  run charPr={run.get('charPrIDRef')} children={kinds}")

# 3) section1 전면부: para 0(목차 표), 110(논문개요?) 표 내부 텍스트와 셀 스타일
s1 = paras("section1.xml")
for idx in (0, 78, 82, 85, 110):
    p = s1[idx]
    t = p.find(f".//{{{HP}}}tbl")
    print(f"\ns1 para {idx}: style={p.get('styleIDRef')} paraPr={p.get('paraPrIDRef')} tbl={'Y' if t is not None else 'N'}")
    print(f"  full text: {all_text(p)[:200]!r}")
    if t is not None:
        print(f"  tbl attrs: rowCnt={t.get('rowCnt')} colCnt={t.get('colCnt')} borderFill={t.get('borderFillIDRef')}")

# 4) 목차 항목의 탭 구조: para 7 raw XML
print("\nTOC entry para7 raw XML:")
print(ET.tostring(s1[7], encoding="unicode")[:1500])

# 5) 표 목차 항목 para 80 raw XML
print("\nList-of-tables entry para80 raw XML:")
print(ET.tostring(s1[80], encoding="unicode")[:1200])

# 6) 머리말/꼬리말/쪽번호: 각 섹션에서 header/footer/pageNum/masterPage 검색
for fname in ("section0.xml", "section1.xml", "section2.xml"):
    root = ET.parse(BASE + "\\" + fname).getroot()
    found = []
    for e in root.iter():
        tag = strip(e.tag)
        if tag in ("header", "footer", "pageNum", "pageNumCtrl", "autoNum", "newNum"):
            found.append((tag, dict(e.attrib), all_text(e)[:40]))
    print(f"\n{fname} header/footer/pageNum elements:")
    for f_ in found:
        print(f"  {f_}")

# 7) section0 표지 3개 표의 정체 확인 (각 표 첫 100자)
s0 = paras("section0.xml")
for idx, p in enumerate(s0):
    print(f"\ns0 para {idx}: pageBreak={p.get('pageBreak')} text={all_text(p)[:100]!r}")
