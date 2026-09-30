# QA_back: base.hwpx vs reflowed.hwpx 표 속성 비교(읽기 전용)
import zipfile, sys
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def info(path):
    r=etree.fromstring(zipfile.ZipFile(path).read('Contents/section2.xml'))
    out=[]
    for t in r.iter(HP+'tbl'):
        pos=t.find(HP+'pos'); sz=t.find(HP+'sz')
        cw={}
        for c in t.iter(HP+'tc'):
            if list(c.iterancestors(HP+'tbl'))[0] is not t: continue
            a=c.find(HP+'cellAddr'); s=c.find(HP+'cellSpan'); z=c.find(HP+'cellSz')
            if s.get('colSpan')=='1': cw.setdefault(int(a.get('colAddr')),int(z.get('width')))
        out.append((t.get('pageBreak'),t.get('repeatHeader'),pos.get('treatAsChar'),sz.get('width'),tuple(cw.get(k) for k in range(int(t.get('colCnt')))),''.join(t.itertext())[:18]))
    return out
b=info('base.hwpx'); n=info('reflowed.hwpx')
print(len(b),len(n))
# 머리글자 텍스트로 매칭
bm={}
for x in b: bm.setdefault(x[5],[]).append(x)
for i,x in enumerate(n):
    if i<16: continue
    cand=bm.get(x[5])
    same = cand and any(c[:5]==x[:5] for c in cand)
    print(i, x[5], 'SAME' if same else ('CHANGED base='+str(cand[0][:5]) if cand else 'NEW/TEXT-CHANGED'), 'new=',x[:5] if not same else '')
