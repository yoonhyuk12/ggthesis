# QA_back: 부록 표지 표 42(도입) vs 49(미도입) 셀 문단 서식 비교(읽기 전용)
import zipfile, sys
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'; HH='{http://www.hancom.co.kr/hwpml/2011/head}'
z=zipfile.ZipFile('reflowed.hwpx')
r=etree.fromstring(z.read('Contents/section2.xml')); h=etree.fromstring(z.read('Contents/header.xml'))
pp={p.get('id'):p for p in h.iter(HH+'paraPr')}
def ls(pid):
    p=pp[pid]; l=p.find('.//'+HH+'lineSpacing'); m=p.find('.//'+HH+'margin')
    return f"ls={l.get('type')}:{l.get('value')}"
T=list(r.iter(HP+'tbl'))
for i in (42,49):
    t=T[i]; sz=t.find(HP+'sz'); print('table',i,'sz',sz.attrib.get('height'))
    for tr in t.findall(HP+'tr'):
        for tc in tr.findall(HP+'tc'):
            cs=tc.find(HP+'cellSz')
            for p in tc.iter(HP+'p'):
                lsa=p.find(HP+'linesegarray'); segs=lsa.findall(HP+'lineseg') if lsa is not None else []
                print('  h',cs.get('height'),'pp',p.get('paraPrIDRef'),ls(p.get('paraPrIDRef')),'segs',len(segs),[ (s.get('vertpos'),s.get('vertsize'),s.get('spacing')) for s in segs[:2]], ''.join(p.itertext())[:25])
    # anchor paragraph + previous
    anc=[a for a in t.iterancestors(HP+'p')][-1]; body=[p for p in r if p.tag==HP+'p']; k=body.index(anc)
    for j in (k-2,k-1,k,k+1):
        p=body[j]; print('  body',j,'pp',p.get('paraPrIDRef'),'pageBreak',p.get('pageBreak'),repr(''.join(x for x in p.itertext())[:30]) if j!=k else '[ANCHOR]')
