# QA_back: 표 앵커 문단과 직전 문단(제목) 속성 확인(읽기 전용)
import zipfile, sys, re
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HH='{http://www.hancom.co.kr/hwpml/2011/head}'
z=zipfile.ZipFile('reflowed.hwpx')
root=etree.fromstring(z.read('Contents/section2.xml'))
head=etree.fromstring(z.read('Contents/header.xml'))
pp={p.get('id'):p for p in head.iter(HH+'paraPr')}
def ppinfo(pid):
    p=pp.get(pid); 
    if p is None: return pid
    br=p.find(HH+'breakSetting')
    return f"paraPr{pid} "+(' '.join(f'{k}={v}' for k,v in br.attrib.items()) if br is not None else '')
tbls=list(root.iter(HP+'tbl'))
body=[p for p in root if p.tag==HP+'p']
for ti in map(int,sys.argv[1:]):
    t=tbls[ti]; anc=[a for a in t.iterancestors(HP+'p')][-1]
    k=body.index(anc)
    for j in range(k-2,k+2):
        p=body[j]
        txt=''.join(x for x in p.itertext())[:60] if not p.findall('.//'+HP+'tbl') else '[TABLE-ANCHOR] '+''.join(r.text or '' for r in p.iter(HP+'t') if not list(r.iterancestors(HP+'tbl')))[:40]
        print(ti, j, ppinfo(p.get('paraPrIDRef')), 'pageBreak=',p.get('pageBreak'), repr(txt))
    print()
