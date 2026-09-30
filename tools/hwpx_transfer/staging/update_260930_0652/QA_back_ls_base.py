# QA_back: base.hwpx의 부록 표지 표 셀 줄간격 및 전체 linesegarray 누락 문단 수(읽기 전용)
import zipfile, sys
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'; HH='{http://www.hancom.co.kr/hwpml/2011/head}'
for path in ('base.hwpx','reflowed.hwpx'):
    z=zipfile.ZipFile(path); r=etree.fromstring(z.read('Contents/section2.xml')); h=etree.fromstring(z.read('Contents/header.xml'))
    pp={p.get('id'):p for p in h.iter(HH+'paraPr')}
    T=[t for t in r.iter(HP+'tbl') if ''.join(t.itertext()).startswith('중소규모 건설현장을 위한 YOLO')]
    for t in T:
        vals=[]
        for p in t.iter(HP+'p'):
            l=pp[p.get('paraPrIDRef')].find('.//'+HH+'lineSpacing'); vals.append(l.get('value'))
        print(path, 'cover table linespacing', vals)
    allp=list(r.iter(HP+'p')); miss=[p for p in allp if p.find(HP+'linesegarray') is None]
    print(path,'paragraphs',len(allp),'without linesegarray',len(miss), [''.join(p.itertext())[:15] for p in miss[:6]])
