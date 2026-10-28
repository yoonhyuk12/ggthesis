"""기준본(사용자 열폭 보존) 표 4-11·4-13·4-14와 본문 2문단의 글자만 조립본(MD) 값으로 바꾼다."""
import zipfile,re,sys,os,html,shutil
d=sys.argv[1]; base=os.path.join(d,'base.hwpx'); fresh=os.path.join(d,'fresh.hwpx'); out=os.path.join(d,'out.hwpx')
sec=lambda p: zipfile.ZipFile(p).read('Contents/section2.xml').decode('utf-8')
bx,fx=sec(base),sec(fresh)
T=re.compile(r'<hp:t(?:\s[^>]*)?>(.*?)</hp:t>',re.S)
BLACK='15'
def grab_tbl(x,start):
    i=x.find('<hp:tbl',start); depth=0; j=i
    while True:
        o=x.find('<hp:tbl',j); c=x.find('</hp:tbl>',j)
        if o!=-1 and o<c: depth+=1; j=o+7
        else:
            depth-=1; j=c+9
            if depth==0: return i,j
def tbl_spans(x,cap,n):
    m=re.search(re.escape(f'<hp:t>&lt;표 {cap}&gt; '),x); k=m.end(); res=[]
    for _ in range(n):
        s,e=grab_tbl(x,k); res.append((s,e)); k=e
    return res
def cellmap(x,s,e):
    d={}
    for m in re.finditer(r'<hp:tc\b.*?</hp:tc>',x[s:e],flags=re.S):
        a=re.search(r'colAddr="(\d+)" rowAddr="(\d+)"',m.group(0)); d[(int(a.group(2)),int(a.group(1)))]=(s+m.start(),s+m.end())
    return d
def rawtext(seg): return ''.join(T.findall(seg))
targets={'4-11':1,'4-13':2,'4-14':3}
edits=[]  # (start,end,new_segment,desc)
log=[]
for cap,n in targets.items():
    bs=tbl_spans(bx,cap,n); fs=tbl_spans(fx,cap,n)
    for ti,((b0,b1),(f0,f1)) in enumerate(zip(bs,fs),1):
        bc=cellmap(bx,b0,b1); fc=cellmap(fx,f0,f1)
        assert set(bc)==set(fc),(cap,ti)
        for rc in sorted(bc):
            bseg=bx[bc[rc][0]:bc[rc][1]]; fseg=fx[fc[rc][0]:fc[rc][1]]
            bt=re.sub(r'\s+',' ',html.unescape(rawtext(bseg))).strip(); ft=re.sub(r'\s+',' ',html.unescape(rawtext(fseg))).strip()
            if bt==ft: continue
            ps=list(re.finditer(r'<hp:p\b[^>]*>.*?</hp:p>',bseg,flags=re.S))
            assert len(ps)==1,(cap,ti,rc,len(ps))
            p=ps[0].group(0); open_tag=re.match(r'<hp:p\b[^>]*>',p).group(0)
            newraw=rawtext(fseg)  # 조립본 escaped 원문
            newp=open_tag+f'<hp:run charPrIDRef="{BLACK}"><hp:t>{newraw}</hp:t></hp:run></hp:p>'
            s=bc[rc][0]+ps[0].start(); e=bc[rc][0]+ps[0].end()
            edits.append((s,e,newp)); log.append(f'표{cap}#{ti} 셀{rc}: {bt[:30]!r} -> {ft[:40]!r}')
        # 앵커 문단(표 뒤) linesegarray 제거
        tail=bx[b1:b1+4000]; m=re.match(r'(\s*</hp:run>\s*)<hp:linesegarray>.*?</hp:linesegarray>',tail,re.S)
        if m: edits.append((b1,b1+m.end(),m.group(1))); log.append(f'표{cap}#{ti}: 앵커 문단 lineseg 제거')
        else: log.append(f'표{cap}#{ti}: 앵커 lineseg 패턴 없음(확인 필요)')
# 본문 2문단
for key in ('주: W의 집단별 범위는 도입 1.50','상호작용은 B=0.309, SE=0.201'):
    k=html.escape(key,quote=False)
    bi=bx.find(k); fi=fx.find(k); assert bi>0 and fi>0,key
    bps=bx.rfind('<hp:p ',0,bi); bpe=bx.find('</hp:p>',bi)+7; p=bx[bps:bpe]
    fps=fx.rfind('<hp:p ',0,fi); fpe=fx.find('</hp:p>',fi)+7; fp=fx[fps:fpe]
    runs=re.findall(r'<hp:run charPrIDRef="(\d+)">',p); assert len(runs)==1,(key,runs)
    newraw=rawtext(fp); open_tag=re.match(r'<hp:p\b[^>]*>',p).group(0)
    newp=open_tag+f'<hp:run charPrIDRef="{runs[0]}"><hp:t>{newraw}</hp:t></hp:run></hp:p>'
    edits.append((bps,bpe,newp)); log.append(f'본문 {key[:14]}: {len(html.unescape(rawtext(p)))}자 -> {len(html.unescape(newraw))}자')
new=bx
for s,e,seg in sorted(edits,key=lambda t:-t[0]): new=new[:s]+seg+new[e:]
import xml.etree.ElementTree as ET; ET.fromstring(new.encode('utf-8'))
zin=zipfile.ZipFile(base); zout=zipfile.ZipFile(out,'w')
for it in zin.infolist():
    data=zin.read(it.filename)
    if it.filename=='Contents/section2.xml': data=new.encode('utf-8')
    zout.writestr(it,data,compress_type=it.compress_type)
zout.close()
print('\n'.join(log)); print('edits',len(edits)); print('OUT',out)
