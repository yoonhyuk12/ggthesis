# QA_back: reflowed.hwpx section2 표 16~53 속성 덤프(읽기 전용)
import zipfile, sys, json
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
z=zipfile.ZipFile('reflowed.hwpx')
root=etree.fromstring(z.read('Contents/section2.xml'))
tbls=list(root.iter(HP+'tbl'))
out=[]
for i,t in enumerate(tbls):
    if i<16: continue
    pos=t.find(HP+'pos'); sz=t.find(HP+'sz')
    parent_tbl=None
    for a in t.iterancestors(HP+'tbl'):
        parent_tbl=tbls.index(a); break
    rows=t.findall(HP+'tr')
    colw={}; hdr=[]; rowh=[]
    for r in rows:
        rh=0
        for c in r.findall(HP+'tc'):
            ad=c.find(HP+'cellAddr'); sp=c.find(HP+'cellSpan'); cs=c.find(HP+'cellSz')
            ca,ra=int(ad.get('colAddr')),int(ad.get('rowAddr'))
            if sp.get('colSpan')=='1': colw.setdefault(ca,int(cs.get('width')))
            if c.get('header')=='1': hdr.append((ra,ca))
            rh=max(rh,int(cs.get('height')))
        rowh.append(rh)
    txt=''.join(t.itertext())
    d=dict(idx=i,parent=parent_tbl,rows=t.get('rowCnt'),cols=t.get('colCnt'),pageBreak=t.get('pageBreak'),
           repeatHeader=t.get('repeatHeader'),treatAsChar=pos.get('treatAsChar'),width=sz.get('width'),height=sz.get('height'),
           colw=[colw.get(k) for k in range(int(t.get('colCnt')))],header_rows=sorted({r for r,c in hdr}),
           rowh_sum=sum(rowh),exp=txt.count('실험전'),head=txt[:50])
    out.append(d)
    print(json.dumps(d,ensure_ascii=False))
