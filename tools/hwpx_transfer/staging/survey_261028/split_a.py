from pathlib import Path
import sys,copy,re,zipfile,xml.etree.ElementTree as E
sys.path.insert(0,str(Path('tools/hwpx_transfer').resolve()))
import kjn_profile as k
W=Path('tools/hwpx_transfer/staging/survey_261028'); H='{'+k.NS['hp']+'}';HH='{'+k.NS['hh']+'}'
for pre,uri in k.NS.items():E.register_namespace(pre,uri)
z=zipfile.ZipFile(W/'patched_apx.hwpx');raw=z.read('Contents/section2.xml').decode();r=E.fromstring(raw)
hd=z.read('Contents/header.xml').decode();head=E.fromstring(hd)
def text(p):return ''.join(''.join(t.itertext()) for t in p.iter(H+'t'))
def clear(p):
 for q in p.iter(H+'p'):
  for x in q.findall(H+'linesegarray'):q.remove(x)
fills=head.find('.//'+HH+'borderFills');bf=next(x for x in fills if x.get('id')=='5');nextid=max(int(x.get('id')) for x in fills)+1
newfills=[]
for typ in ['first','middle','last']:
 q=copy.deepcopy(bf);q.set('id',str(nextid));nextid+=1
 for side in ['top','bottom']:
  if (side=='top' and typ!='first') or (side=='bottom' and typ!='last'):q.find(HH+side+'Border').set('type','NONE')
 newfills.append(q)
ids=[x.get('id') for x in newfills]
oldcount=int(fills.get('itemCnt'));hd=hd.replace('</hh:borderFills>',''.join(E.tostring(x,encoding='unicode') for x in newfills)+'</hh:borderFills>')
hd=re.sub(r'(<hh:borderFills itemCnt=")\d+',lambda m:m.group(1)+str(oldcount+3),hd)
changed={}
for i,p in enumerate(r):
 if not any(re.match(r'\s*A-6\)',text(q)) for q in p.iter(H+'p')):continue
 tb=next(p.iter(H+'tbl'));row=tb.find(H+'tr');cell=row.find(H+'tc');sub=cell.find(H+'subList');groups=[[]]
 for q in sub:
  if re.match(r'\s*A-[1-9]\)',text(q)):groups.append([])
  groups[-1].append(copy.deepcopy(q))
 assert len(groups)==10
 tb.remove(row);tb.set('rowCnt','10');tb.set('pageBreak','TABLE');tb.set('repeatHeader','1')
 if '--floating' in sys.argv:tb.find(H+'pos').set('treatAsChar','0')
 for j,ps in enumerate(groups):
  tr=E.SubElement(tb,H+'tr');tc=copy.deepcopy(cell);ss=tc.find(H+'subList')
  for q in list(ss):ss.remove(q)
  ss.extend(ps);tc.set('header','1' if j==0 else '0');tc.set('borderFillIDRef',ids[0 if j==0 else 2 if j==9 else 1]);tc.find(H+'cellAddr').set('rowAddr',str(j));tc.find(H+'cellSz').set('height','1600');tr.append(tc)
 clear(p);changed[i]=E.tostring(p,encoding='unicode')
# Coordinator: identical Part A tables for both forms, including cached sizes.
ai=list(changed);first=next(r[ai[0]].iter(H+'tbl'));second=next(r[ai[1]].iter(H+'tbl'));parent=next(x for x in r[ai[1]].iter() if second in list(x));q=copy.deepcopy(first)
for j,x in enumerate(q.iter()):
 if 'id' in x.attrib and x.get('id').isdigit():x.set('id',str(2300000000+j))
parent.insert(list(parent).index(second),q);parent.remove(second);clear(r[ai[1]]);changed[ai[1]]=E.tostring(r[ai[1]],encoding='unicode')
spans=k.split_paragraphs(raw);out=raw[:spans[0][0]]+''.join(changed.get(i,raw[a:b]) for i,(a,b) in enumerate(spans))+raw[spans[-1][1]:]
E.fromstring(out);E.fromstring(hd)
with zipfile.ZipFile(W/'patched_layout.hwpx','w') as dest:
 for info in z.infolist():
  data=out.encode() if info.filename=='Contents/section2.xml' else hd.encode() if info.filename=='Contents/header.xml' else z.read(info.filename)
  if info.filename=='Contents/section1.xml':
   s=data.decode();assert s.count('Part A. 인구통계학적 특성')==2
   def titlefix(m):
    p=m.group(0)
    if 'Part A. 인구통계학적 특성' in p:p=re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>','',p,flags=re.S).replace('Part A. 인구통계학적 특성','Part A. 인구통계학적 특성 및 현장 운영 특성')
    return p
   data=re.sub(r'<hp:p\b.*?</hp:p>',titlefix,s,flags=re.S).encode()
  dest.writestr(info,data)
print('Split A tables',len(changed),'floating','--floating' in sys.argv)
