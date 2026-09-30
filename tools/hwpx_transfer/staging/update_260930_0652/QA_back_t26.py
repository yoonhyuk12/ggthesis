# QA_back: 표 26(<표 5-1>) 행별 텍스트·높이·셀 문단 수(읽기 전용)
import zipfile, sys
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
root=etree.fromstring(zipfile.ZipFile('reflowed.hwpx').read('Contents/section2.xml'))
t=list(root.iter(HP+'tbl'))[int(sys.argv[1]) if len(sys.argv)>1 else 26]
cap=t.find(HP+'caption'); print('caption:', ''.join(cap.itertext()) if cap is not None else None)
print('inMargin', etree.tostring(t.find(HP+'inMargin')) if t.find(HP+'inMargin') is not None else '')
for r in t.findall(HP+'tr'):
    cells=[]
    for c in r.findall(HP+'tc'):
        ad=c.find(HP+'cellAddr'); sp=c.find(HP+'cellSpan'); cs=c.find(HP+'cellSz')
        paras=c.findall('.//'+HP+'p')
        cells.append(f"[{ad.get('rowAddr')},{ad.get('colAddr')} s{sp.get('rowSpan')}x{sp.get('colSpan')} h{cs.get('height')} hdr{c.get('header')} np{len(paras)}] "+'|'.join(''.join(p.itertext()) for p in paras))
    print(' ; '.join(cells))
