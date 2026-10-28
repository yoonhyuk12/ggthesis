from pathlib import Path
import sys, re, copy, zipfile, json, difflib, collections, xml.etree.ElementTree as E
sys.path.insert(0, str(Path('tools/hwpx_transfer').resolve()))
import kjn_profile as k
W=Path('tools/hwpx_transfer/staging/survey_261028')
H='{'+k.NS['hp']+'}'
for prefix,uri in k.NS.items(): E.register_namespace(prefix,uri)
base=next(Path('00. hwpx').glob('261028_0644*'))
z=zipfile.ZipFile(W/'patched.hwpx'); raw=z.read('Contents/section2.xml').decode()
r=E.fromstring(raw); br=E.fromstring(zipfile.ZipFile(base).read('Contents/section2.xml'))
orig=list(r); before=[E.tostring(p) for p in r]
md=Path('01.docs/부록1_설문지_양식.md').read_text(encoding='utf-8')
def clean(s): return s.replace('**','').replace('&emsp;',' ').strip()
lines=[clean(s) for s in md.splitlines()]
def ml(prefix): return next(s for s in lines if s.startswith(prefix))
def txt(p): return ''.join(''.join(t.itertext()) for t in p.findall(H+'run/'+H+'t'))
def alltxt(p): return ''.join(''.join(t.itertext()) for t in p.iter(H+'t'))
changes=[]; uid=2200000000
def clear(p):
 for q in p.iter(H+'p'):
  for a in q.findall(H+'linesegarray'): q.remove(a)
 if p.tag==H+'p':
  for a in p.findall(H+'linesegarray'): p.remove(a)
def settext(p,s):
 old=txt(p)
 if old.strip()==s.strip(): return
 runs=p.findall(H+'run'); template=next((x for x in runs if x.find(H+'t') is not None),runs[0])
 styles=[]
 for run in runs:
  value=''.join(''.join(t.itertext()) for t in run.findall(H+'t'))
  styles.extend([run.get('charPrIDRef')]*len(value))
 default=collections.Counter(styles).most_common(1)[0][0] if styles else template.get('charPrIDRef')
 newstyles=[default]*len(s)
 for op,a,b,c,d in difflib.SequenceMatcher(None,old,s,autojunk=False).get_opcodes():
  if op=='equal':newstyles[c:d]=styles[a:b]
  elif op=='replace' and styles[a:b]:newstyles[c:d]=[collections.Counter(styles[a:b]).most_common(1)[0][0]]*(d-c)
 chunks=[]
 for ch,style in zip(s,newstyles):
  if chunks and chunks[-1][0]==style:chunks[-1][1]+=ch
  else:chunks.append([style,ch])
 for run in runs: p.remove(run)
 for i,(style,value) in enumerate(chunks):
  q=E.Element(H+'run',dict(template.attrib));q.set('charPrIDRef',style);E.SubElement(q,H+'t').text=value;p.insert(i,q)
 clear(p);changes.append((old,s))
def clone(p,s):
 global uid
 q=copy.deepcopy(p);uid+=1;q.set('id',str(uid));q.set('pageBreak','0');settext(q,s);clear(q);return q
def para(prefix,root=r): return [p for p in root.iter(H+'p') if txt(p).strip().startswith(prefix)]
def table(cap,root):
 seen=False
 for p in root:
  if txt(p).strip().startswith(cap): seen=True;continue
  if seen:
   ts=list(p.iter(H+'tbl'))
   if ts:return p,ts[0]
bp,bt=table('<표 4-11>',br);pp,pt=table('<표 4-11>',r)
def grid(t):return [(c.find(H+'cellAddr').attrib,c.find(H+'cellSpan').attrib) for c in t.findall(H+'tr/'+H+'tc')]
assert grid(bt)==grid(pt)
for b,c in zip(bt.findall(H+'tr/'+H+'tc'),pt.findall(H+'tr/'+H+'tc')): c.find(H+'cellSz').set('width',b.find(H+'cellSz').get('width'))
assert bt.find(H+'sz').get('width')==pt.find(H+'sz').get('width');clear(pp)
start=next(i for i,p in enumerate(r) if '부   록 (도입 현장)' in txt(p))
ap=list(r)[start:]
aps=[p for top in ap for p in top.iter(H+'p')]
def apfind(prefix):return [p for p in aps if txt(p).strip().startswith(prefix)]
def replace(prefix,new):
 ps=apfind(prefix);assert ps,prefix
 for p in ps:settext(p,new)
replace('응답에는 정답이 없으며',ml('응답에는 정답이 없으며'))
replace('배포코드와 성명은',ml('전자 설문 첫 섹션'))
replace('Google 계정 로그인과',ml('Google 계정 로그인과'))
replace('Part A. 인구통계학적 특성',ml('## Part A.')[3:])
replace('※ 다음은 응답자의 일반적',ml('※ 다음은 응답자의 일반적'))
replace('※ 다음 Part B의',ml('※ 다음 Part B의'))
replace('※ Part D는',ml('※ Part D는'))
replace('※ Part E에서는',ml('※ Part E에서는'))
for p in apfind('배포코드:'):
 i=list(r).index(p)
 strings=[ml('- 현장 구분')[2:],ml('- 현장명:')[2:],ml('- 현재 담당')[2:],ml('- 예시 :')[2:]]
 for offset,s in enumerate(strings):r.insert(i+offset,clone(p,s))
 r.remove(p)
for p in apfind('A-4)'):settext(p,ml('A-4)'))
for p in apfind('※ 여러 현장이나'):settext(p,ml('※ 1년 미만은'))
for p in aps:
 if '개월' in txt(p) and txt(p).strip().startswith('('):settext(p,' 만 (   )년')
 # MD option differs by a space in the original printed other field.
 if '④ 기타 (' in txt(p):settext(p,txt(p).replace('④ 기타 (','④ 기타('))
for top in ap:
 if not any(txt(p).strip().startswith('A-6)') for p in top.iter(H+'p')):continue
 parent={c:p for p in top.iter() for c in p}
 label=next(p for p in top.iter(H+'p') if txt(p).strip().startswith('A-6)'))
 note=next(p for p in top.iter(H+'p') if txt(p).strip().startswith('※ 총공사비'))
 container=parent[note]; opt=list(container)[list(container).index(label)+1]
 begin=lines.index(ml('A-7)'));end=lines.index('---',begin)
 new=[]
 for s in lines[begin:end]:
  if not s:continue
  template=label if re.match('A-[789]\\)',s) else note if s.startswith('※') else opt
  new.append(clone(template,s))
 for j,q in enumerate(new):container.insert(list(container).index(note)+1+j,q)
 clear(top)
for p in apfind('Part D.')+apfind('Part E.'):
 template=apfind('※ Part D는')[0];r.insert(list(r).index(p)+1,clone(template,ml('다음은 CCTV')))
# Every Likert question must match MD. Preserve existing cells and all 5 option glyphs.
questions={}
for s in lines:
 if re.match(r'\| [BCDE]-\d+ \|',s):
  a=[v.strip() for v in s.strip('|').split('|')];questions[a[0]]=a[1]
for top in ap:
 for tb in top.iter(H+'tbl'):
  rows=tb.findall(H+'tr')
  if not rows:continue
  codes=[alltxt(tr.findall(H+'tc')[0]).strip() for tr in rows if tr.findall(H+'tc')]
  if not any(c in questions for c in codes):continue
  for tr in rows[1:]:
   cs=tr.findall(H+'tc');code=alltxt(cs[0]).strip()
   if code in questions:
    ps=list(cs[1].iter(H+'p'));settext(ps[0],questions[code])
  # Fill two blank scale headings from the MD; other three already have line breaks.
  heads=rows[0].findall(H+'tc')
  for j,s in [(2,'그렇지 않다'),(4,'그렇다')]:
   if not alltxt(heads[j]).strip():settext(next(heads[j].iter(H+'p')),s)
  if any(c.startswith(('D-','E-')) for c in codes):
   tb.set('colCnt','7')
   for row in rows:
    cs=row.findall(H+'tc');removed=cs[-1];assert '비해당' in alltxt(removed)
    extra=int(removed.find(H+'cellSz').get('width'));row.remove(removed)
    for c in cs[:-1]:
     addr=c.find(H+'cellAddr');sp=c.find(H+'cellSpan');old=int(addr.get('colAddr'))
     if old>=2:addr.set('colAddr',str(2+(old-2)//2));sp.set('colSpan','1')
     if old in (0,1) and (old==1 or int(sp.get('colSpan'))==2):
      sz=c.find(H+'cellSz');sz.set('width',str(int(sz.get('width'))+extra))
    assert sum(int(c.find(H+'cellSz').get('width')) for c in row.findall(H+'tc'))==int(tb.find(H+'sz').get('width'))
  clear(top)
# Record the full concrete text diff before writing the new HWPX.
report=['# 설문지 동기화 작업 보고','', '## A. 본문 반입', '561 블록, 누락 0. equal 675 / replace_fresh 9(본문 7, 표 2) / manual 0 / table_same_kept 6. 문단 합침으로 1개 감소. 표 4-11 격자 동일 확인 후 기준본 셀 폭 재적용.','', '## B. 전수 대조표','부록의 Google Forms·Google 계정 언급은 실제 배포본 재현 지시에 따라 MD대로 유지한다. MD의 관리용 인용 블록과 내부 대조표는 제외한다.','D/E는 실제 XML colCnt 14(척도 열마다 2칸 병합)에서 논리 7열로 정규화하고 비해당 폭 3500을 문항 열에 더한다. B/C는 기존 격자를 보존하고 비어 있던 ②·④ 머리글을 MD대로 채운다.','', '| 항목 | 기준본 문구 | MD 문구 | 처리 |','|---|---|---|---|']
for i,(a,b) in enumerate(changes):report.append(f'| {i+1} | {a.replace(chr(10)," ")} | {b} | 반영 |')
report+=['','## C. 검증','XML 작성 전. 한글 재조판 및 PDF 검증은 후속 단계.']
(W/'report.md').write_text('\n'.join(report),encoding='utf-8')
# Preserve raw bytes of unrelated top-level paragraphs.
spans=k.split_paragraphs(raw);mapping={id(p):raw[a:b] for p,(a,b) in zip(orig,spans)}
serialized=[]
for p in r:
 if p in orig and E.tostring(p)==before[orig.index(p)]:serialized.append(mapping[id(p)])
 else:serialized.append(E.tostring(p,encoding='unicode'))
out=raw[:spans[0][0]]+''.join(serialized)+raw[spans[-1][1]:]
E.fromstring(out)
with zipfile.ZipFile(W/'patched_apx.hwpx','w') as dest:
 for info in z.infolist():dest.writestr(info,out.encode() if info.filename=='Contents/section2.xml' else z.read(info.filename))
zz=zipfile.ZipFile(W/'patched_apx.hwpx');assert zz.infolist()[0].filename=='mimetype' and zz.infolist()[0].compress_type==0
for name in zz.namelist():
 if name.endswith('.xml'):E.fromstring(zz.read(name))
(W/'apx_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print('changes',len(changes),'XML/ZIP PASS')
