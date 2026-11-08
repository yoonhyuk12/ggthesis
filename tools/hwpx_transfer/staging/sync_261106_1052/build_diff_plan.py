from pathlib import Path
import json,re,difflib,sys,html
from lxml import etree as E
sys.path.insert(0,'tools/hwpx_transfer')
import kjn_profile as k
O=Path(__file__).parent
U={s:json.loads((O/f'base_section{s}.json').read_text(encoding='utf8')) for s in range(3)}
P={'changes':[],'insertions':[],'deletions':[],'notes':[],'coverage':{}}
def norm(t):return re.sub(r'\s|<br\s*/?>','',html.unescape(t))
def bt(b):
 if b['type']=='table':return ' '.join(b['header']+sum(b['rows'],[]))
 return b.get('text') or ''.join(x['text'] for x in b.get('runs',[]))
def change(s,i,t,kind,source,**kw):
 if norm(U[s][i]['text'])!=norm(t):P['changes'].append(dict(section=s,unit_index=i,old=U[s][i]['text'],new=t,kind=kind,md_source=source,**kw))
def insert(s,i,t,source,**kw):P['insertions'].append(dict(section=s,after_unit_index=i,new=t,kind='paragraph',md_source=source,**kw))
M=[]
for n in range(1,6):
 data=json.loads((O/f'ch{n:02}.blocks.json').read_text(encoding='utf8'))
 for bi,b in enumerate(data['blocks']):
  t=bt(b)
  if t and not t.startswith('!['):M.append((t,b,'01.docs/'+data['source'],bi))
end=next(i for i,v in enumerate(U[2]) if norm(v['text'])=='참고문헌')
A=[(v['text'],i) for i,v in enumerate(U[2][:end]) if v['text']]
for op,a,b,c,d in difflib.SequenceMatcher(None,[norm(t[0]) for t in A],[norm(t[0]) for t in M],autojunk=False).get_opcodes():
 if op=='equal':continue
 old,new=A[a:b],M[c:d]
 for ov,nv in zip(old,new):
  t,blk,src,bi=nv
  change(2,ov[1],t,'table' if blk['type']=='table' else 'paragraph',src,block=blk,md_block_index=bi)
 for ov in old[len(new):]:P['deletions'].append(dict(section=2,unit_index=ov[1],old=ov[0],kind='paragraph'))
 for nv in new[len(old):]:
  t,blk,src,bi=nv;anchor=old[-1][1] if old else A[a-1][1]
  insert(2,anchor,t,src,block=blk,md_block_index=bi)
P['coverage']['body']={'MD_blocks':len(M),'HWPX_nonempty_units':len(A),'coverage_missing':0}
def paras(t):return [re.sub(r'\*\*|`','',x.strip()) for x in re.split(r'\n\s*\n',t) if x.strip() and not x.lstrip().startswith(('#','>','---'))]
front=Path('01.docs/00_목차.md').read_text(encoding='utf8')
kr=paras(front.split('## 2. 국문초록',1)[1].split('---',1)[0]);en=paras(front.split('## 6. Abstract',1)[1])
for s,start,ps,src in [(1,142,kr,'01.docs/00_목차.md'),(2,591,en,'01.docs/00_목차.md'),(1,133,paras(Path('01.docs/감사의_글.md').read_text(encoding='utf8')),'01.docs/감사의_글.md')]:
 for j,t in enumerate(ps):change(s,start+j,t,'paragraph',src)
 P['coverage'][src+str(s)]={'paragraphs':len(ps),'base_start':start}
# Current-bibliography presentation filter used by existing assembly. No HWPX I/O.
src=Path('tools/hwpx_transfer/staging/fullsync_261104/prepare_fresh.py').read_text(encoding='utf8')
ROOT=Path.cwd();OUT=O
exec(src[src.index('refmd='):src.index('shutil.copy2')])
editorial_removed=[]
for cat,refs in categories.items():
 for ref in refs:
  original=ref['text']
  starts=list(re.finditer(r'\((?:대표\s+ref\b|번호가 중복된|원전 미보유)',original))
  value=original
  for match in reversed(starts):
   depth=0
   for j in range(match.start(),len(value)):
    if value[j]=='(':depth+=1
    elif value[j]==')':
     depth-=1
     if depth==0:value=value[:match.start()]+value[j+1:];break
  ref['text']=value.strip()
  if ref['text']!=original:editorial_removed.append({'before':original,'after':ref['text']})
  assert not re.search(r'\bref\s*\d|사용자 결정|원전 미보유|파일명으로 식별|확보본|전문.*확보',ref['text']),ref['text']
(O/'references.json').write_text(json.dumps({'categories':categories,'flagged':[]},ensure_ascii=False,indent=2),encoding='utf8')
P['coverage']['bibliography_editorial_filter']={'removed':editorial_removed,'remaining_editorial_markers':0,'actual_fields_preserved':'DOI, ISBN, degree, title, publisher, year, volume, pages and report identifier retained'}
ref_expected=[]
for cat,refs in categories.items():
 heading=next(i for i,x in enumerate(U[2]) if norm(x['text'])==norm(cat))
 finish=next((i for i in range(heading+1,len(U[2])) if re.match(r'^\d+\. ',U[2][i]['text']) or U[2][i]['text'].startswith('부 록')),len(U[2]))
 old=[(i,x['text']) for i,x in enumerate(U[2]) if heading<i<finish and re.match(r'^\[\d+\]',x['text'])]
 def key(t):
  t=re.sub(r'^\[\d+\]\s*','',t)
  return 'Ultralytics' if t.startswith('Ultralytics') else t.split(',')[0].strip()
 om={key(t):(i,t) for i,t in old}; seen=set();anchor=heading
 for n,r in enumerate(refs,1):
  t=f'[{n:02}] '+r['text'];ref_expected.append(t);q=key(t)
  if q in om:
   i,_=om[q];change(2,i,t,'paragraph','01.docs/07_참조번호목록.md');seen.add(i);anchor=i
  else:insert(2,anchor,t,'01.docs/07_참조번호목록.md',clone_unit_index=old[0][0])
 for i,t in old:
  if i not in seen:P['deletions'].append(dict(section=2,unit_index=i,old=t,kind='reference',md_source='01.docs/07_참조번호목록.md'))
P['coverage']['references']={'expected_count':len(ref_expected),'categories':{c:len(v) for c,v in categories.items()}}
# Appendix transformations are deduced from old parsed MD then checked against current dump.
old_apx=json.loads(Path('tools/hwpx_transfer/staging/full_sync_261106_0245/apx1.blocks.json').read_text(encoding='utf8'))['blocks']
new_apx=json.loads((O/'apx1.blocks.json').read_text(encoding='utf8'))['blocks']
apx_maps={}
for op,a,b,c,d in difflib.SequenceMatcher(None,[str(x) for x in old_apx],[str(x) for x in new_apx],autojunk=False).get_opcodes():
 if op=='equal':continue
 assert b-a==d-c==1 and old_apx[a]['type']==new_apx[c]['type']=='p'
 apx_maps[bt(old_apx[a])]=bt(new_apx[c])
HP='{'+k.NS['hp']+'}'
apx_found={x:0 for x in apx_maps}
for i,u in enumerate(U[2]):
 if not 549<=i<590:continue
 root=E.fromstring(k._wrap(u['xml']).encode());repls=[]
 for para in root.iter(HP+'p'):
  ts=[t for run in para.findall(HP+'run') for t in run.findall(HP+'t')]
  old=''.join(''.join(t.itertext()) for t in ts)
  for a,b in apx_maps.items():
   if norm(old)==norm(a):repls.append({'old':old,'new':b});apx_found[a]+=1
 if repls:
  new=u['text']
  for r in repls:
   assert norm(r['old']) in norm(new),(i,r['old']);new=norm(new).replace(norm(r['old']),norm(r['new']))
  change(2,i,new,'nested_paragraphs','01.docs/부록1_설문지_양식.md',replacements=repls)
P['coverage']['appendix']={'MD_blocks':len(new_apx),'changed_text_occurrences':list(apx_found.values()),'assertion':'Each historical MD change matched current HWPX own-paragraph text; unchanged blocks retain prior verified form.'}
assert sorted(apx_found.values())==[1,2,2]
# Cover and table of contents maintain existing wording. Compare heading/caption inventory.
headings=[bt(b) for t,b,src,bi in M if re.match(r'^제\s*\d+\s*[장절항]\s',bt(b)) or (b['type'] in ('table_caption','figure_caption') and len(bt(b))<150)]
toc=''.join(x['text'] for x in U[1][:132])
missing=[t for t in headings if norm(t) not in norm(toc)]
P['coverage']['toc']={'expected_headings_captions':len(headings),'missing':missing}
P['coverage']['cover']={'title_present':norm('건설현장 YOLO-LLM 안전관제 시스템 개발 및 실증 연구') in norm(U[0][0]['text']),'date_present':'2026년 11월' in U[0][0]['text'],'action':'preserve approved cover and endorsement form'}
P['notes'].append('Empty layout paragraphs, page breaks, all unchanged HWPX units retained. Table 4-4 adds one operational-characteristics row by cloning original control row; lower rows shift +1, merged structure remains otherwise unchanged.')
P['notes'].append('Three inherited editorial parentheticals in references are excluded from printed HWPX. Original MD records remain unchanged. Subheadings 1–4 under section4.7 and a paragraph beginning with <표2-2> are not TOC entries; formal chapter/section/subsection and caption inventory is compared instead.')
assert not missing,missing
# Full current appendix text coverage, excluding the MD-only repeated number heading.
changed={c['unit_index']:c['new'] for c in P['changes'] if c['section']==2}
apx_text=norm(''.join(changed.get(i,u['text']) for i,u in enumerate(U[2]) if 549<=i<590))
covered=0;omitted=[]
for bi,b in enumerate(new_apx):
 if b['type']=='p':texts=[bt(b)]
 elif b['type']=='table':texts=b['header']+sum(b['rows'],[])
 else:continue
 for t in texts:
  if not norm(t):continue
  if norm(t) in apx_text:covered+=1
  else:omitted.append({'block':bi,'text':t})
assert all(x['text']=='번호' for x in omitted)
P['coverage']['appendix']['current_MD_text_entries_covered']=covered
P['coverage']['appendix']['form_only_omissions']=omitted
assert len({(x['section'],x['unit_index']) for x in P['changes']})==len(P['changes'])
(O/'md_diff_plan.json').write_text(json.dumps(P,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'changes':len(P['changes']),'insertions':len(P['insertions']),'deletions':len(P['deletions']),'coverage':P['coverage']},ensure_ascii=False))

