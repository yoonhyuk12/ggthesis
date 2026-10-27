"""표 4-12 패널 A 열폭 재배분 + 머리행 '조정 평균·차이'를 '조정'/'평균·차이' 두 문단으로 분리(텍스트 불변, 조판만)."""
import sys,zipfile,re,copy,random
import xml.etree.ElementTree as ET
src,out=sys.argv[1:3]
NEW=[7100,5520,4020,6100,5500,3720,None]  # 마지막 열은 잔차
raw=zipfile.ZipFile(src).read('Contents/section2.xml').decode('utf-8')
nsdecl=dict(re.findall(r'xmlns:(\w+)="([^"]+)"',raw[:3000]))
for k,v in nsdecl.items(): ET.register_namespace(k,v)
HP='{%s}'%nsdecl['hp']
cap=re.search(r'&lt;표 4-12&gt; 안전관리 실효성의 공분산분석',raw).start()
s=raw.find('<hp:tbl ',cap); e=raw.find('</hp:tbl>',s)+len('</hp:tbl>')
assert raw.find('<hp:tbl ',s+1,e)<0
tbl=ET.fromstring('<root %s>%s</root>'%(' '.join(f'xmlns:{k}="{v}"' for k,v in nsdecl.items()),raw[s:e]))[0]
assert tbl.get('rowCnt')=='4' and tbl.get('colCnt')=='7'
total=int(tbl.find(HP+'sz').get('width')); NEW[-1]=total-sum(NEW[:-1]); assert NEW[-1]>=7000,NEW
old={}
ids=set(re.findall(r'<hp:p id="(\d+)"',raw))
for tc in tbl.iter(HP+'tc'):
    a=tc.find(HP+'cellAddr'); r,c=int(a.get('rowAddr')),int(a.get('colAddr'))
    z=tc.find(HP+'cellSz'); old.setdefault(c,int(z.get('width'))); z.set('width',str(NEW[c]))
    sl=tc.find(HP+'subList'); paras=sl.findall(HP+'p')
    for p in paras:
        la=p.find(HP+'linesegarray')
        if la is not None: p.remove(la)
    if (r,c)==(0,4):
        assert len(paras)==1 and ''.join(t.text for t in paras[0].iter(HP+'t'))=='조정 평균·차이'
        p0=paras[0]; p1=copy.deepcopy(p0)
        p0.find('.//'+HP+'t').text='조정'; p1.find('.//'+HP+'t').text='평균·차이'
        nid=str(random.randint(2147490000,2147499999))
        while nid in ids: nid=str(int(nid)+1)
        p1.set('id',nid); sl.insert(list(sl).index(p0)+1,p1)
print('열폭 old→new:',[(old[c],NEW[c]) for c in range(7)],'합',sum(NEW),'=',total)
sx=ET.tostring(tbl,encoding='unicode'); sx=re.sub(r'\s+xmlns:\w+="[^"]*"','',sx,count=len(nsdecl))
tail=raw[e:]; m=re.match(r'(\s*</hp:run>\s*)<hp:linesegarray>.*?</hp:linesegarray>',tail,re.S)
tail=(m.group(1)+tail[m.end():]) if m else tail
new=raw[:s]+sx+tail; ET.fromstring(new.encode('utf-8'))
zin=zipfile.ZipFile(src); zout=zipfile.ZipFile(out,'w')
for it in zin.infolist():
    data=zin.read(it.filename)
    if it.filename=='Contents/section2.xml': data=new.encode('utf-8')
    zout.writestr(it,data,compress_type=it.compress_type)
zout.close(); print('OUT',out)
