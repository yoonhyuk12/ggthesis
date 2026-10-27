"""표 4-7 세 패널: 기준본(사용자 병합·열폭)의 표 XML을 가져와 셀 글자만 패치본(현행 MD) 값으로 바꾼다.
패널 A는 기준본 14행(역할 '기타' 행 포함) → 13행으로 '기타' 행(r8)을 삭제하고 역할 rowSpan 4→3."""
import sys,zipfile,re,html,shutil
import xml.etree.ElementTree as ET
base,pat,out=sys.argv[1:4]
def sec2(p): return zipfile.ZipFile(p).read('Contents/section2.xml').decode('utf-8')
braw,praw=sec2(base),sec2(pat)
nsdecl=dict(re.findall(r'xmlns:(\w+)="([^"]+)"',praw[:3000]))
for k,v in nsdecl.items(): ET.register_namespace(k,v)
HP='{%s}'%nsdecl['hp']
def spans(raw):
    cap=raw.find('&lt;표 4-7&gt;'); end=raw.find('&lt;표 4-8&gt;',cap)
    res=[]; pos=cap
    while True:
        s=raw.find('<hp:tbl ',pos)
        if s<0 or s>end: break
        e=raw.find('</hp:tbl>',s)+len('</hp:tbl>')
        assert raw.find('<hp:tbl ',s+1,e)<0, 'nested table'
        res.append((s,e)); pos=e
    assert len(res)==3,res
    return res
bsp,psp=spans(braw),spans(praw)
wrap=lambda x: ET.fromstring('<root %s>%s</root>'%(' '.join(f'xmlns:{k}="{v}"' for k,v in nsdecl.items()),x))[0]
norm=lambda t: re.sub(r'\s+','',t)
def ptexts(tc): return [''.join(t.text or '' for t in p.iter(HP+'t')) for p in tc.find(HP+'subList').findall(HP+'p')]
def cells(tbl):
    d={}
    for tc in tbl.iter(HP+'tc'):
        a=tc.find(HP+'cellAddr'); s=tc.find(HP+'cellSpan')
        d[(int(a.get('rowAddr')),int(a.get('colAddr')))]=(tc,int(s.get('rowSpan')),int(s.get('colSpan')))
    return d
log=[]; fails=[]
newtbls=[]
for k,((bs,be),(ps,pe)) in enumerate(zip(bsp,psp),1):
    bt=wrap(braw[bs:be]); pt=wrap(praw[ps:pe])
    rowmap=lambda r:r
    if k==1:
        trs=bt.findall(HP+'tr'); assert len(trs)==14
        drop=trs[8]; assert norm('|'.join(ptexts(drop.findall(HP+'tc')[0])))=='기타', ptexts(drop.findall(HP+'tc')[0])
        hdrop=int(drop.find(HP+'tc').find(HP+'cellSz').get('height'))
        bt.remove(drop)
        for tc in bt.iter(HP+'tc'):
            a=tc.find(HP+'cellAddr'); r=int(a.get('rowAddr'))
            if r>=9: a.set('rowAddr',str(r-1))
            if (r,int(a.get('colAddr')))==(5,0):
                sp=tc.find(HP+'cellSpan'); assert sp.get('rowSpan')=='4'; sp.set('rowSpan','3')
        bt.set('rowCnt','13'); sz=bt.find(HP+'sz'); sz.set('height',str(int(sz.get('height'))-hdrop))
        log.append(f't1: 기타 행 삭제(높이 {hdrop}), 역할 rowSpan 4→3, rowCnt 13')
    bc=cells(bt); pc=cells(pt)
    assert bt.get('rowCnt')==pt.get('rowCnt') and bt.get('colCnt')==pt.get('colCnt'),(k,bt.get('rowCnt'),pt.get('rowCnt'))
    changed=0
    for (r,c),(tc,rs,cs) in sorted(bc.items()):
        ftc=pc[(r,c)][0]; ft=ptexts(ftc); btx=ptexts(tc)
        # 병합으로 덮인 fresh 셀 확인
        for rr in range(r,r+rs):
            for cc in range(c,c+cs):
                if (rr,cc)==(r,c): continue
                cov=norm('|'.join(ptexts(pc[(rr,cc)][0])))
                if cov and cov!=norm('|'.join(ft)): fails.append(f't{k} 병합 덮인 셀 ({rr},{cc}) fresh 텍스트 {cov!r} ≠ 앵커 {ft}')
        if norm('|'.join(btx))==norm('|'.join(ft)): continue
        paras=tc.find(HP+'subList').findall(HP+'p')
        if len(paras)!=len(ft): fails.append(f't{k} ({r},{c}) 문단 수 불일치 base {btx} fresh {ft}'); continue
        for p,newt in zip(paras,ft):
            runs=p.findall(HP+'run'); ts=[t for rr in runs for t in rr.findall(HP+'t')]
            if len(runs)!=1 or len(ts)!=1 or len(list(ts[0]))>0: fails.append(f't{k} ({r},{c}) run 구조 복잡 {btx}'); break
            ts[0].text=newt
            la=p.find(HP+'linesegarray')
            if la is not None: p.remove(la)
        changed+=1; log.append(f't{k} ({r},{c}) {"|".join(btx)!r} → {"|".join(ft)!r}')
    s=ET.tostring(bt,encoding='unicode')
    s=re.sub(r'\s+xmlns:\w+="[^"]*"','',s,count=len(nsdecl))
    newtbls.append(s); log.append(f't{k}: 셀 {changed}개 글자 교체')
if fails:
    print('FAIL'); [print(' ',f) for f in fails]; sys.exit(1)
# 패치본 section2에 치환(뒤에서부터) + 앵커 문단 linesegarray 제거
new=praw
for (ps,pe),s in reversed(list(zip(psp,newtbls))):
    tail=new[pe:]
    m=re.match(r'(\s*</hp:run>\s*)<hp:linesegarray>.*?</hp:linesegarray>',tail,re.S)
    tail=(m.group(1)+tail[m.end():]) if m else tail
    new=new[:ps]+s+tail
ET.fromstring(new.encode('utf-8'))  # well-formed 확인
zin=zipfile.ZipFile(pat); zout=zipfile.ZipFile(out,'w')
for it in zin.infolist():
    data=zin.read(it.filename)
    if it.filename=='Contents/section2.xml': data=new.encode('utf-8')
    zout.writestr(it,data, compress_type=it.compress_type)
zout.close()
print('\n'.join(log)); print('OUT',out)
