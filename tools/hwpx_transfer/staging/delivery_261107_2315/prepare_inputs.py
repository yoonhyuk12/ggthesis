"""JSON-only preparation and dump audit. Does not open/write HWPX files."""
from pathlib import Path
import sys,json,re,hashlib,difflib,html
import xml.etree.ElementTree as E
O=Path(__file__).resolve().parent
ROOT=O.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import md_to_blocks as m, table_merges as tm, kjn_profile as k
HP='{'+k.NS['hp']+'}'
def norm(s):return re.sub(r'\s+','',html.unescape(re.sub(r'<br\s*/?>','',s))).replace('\\[','[').replace('\\]',']')
def paras(t):return [re.sub(r'\*\*|`','',x.strip()) for x in re.split(r'\n\s*\n',t) if x.strip() and not x.lstrip().startswith(('#','>','---'))]
def bt(b):return k.normalize_heading_number(b.get('text',k.runs_text(b)))
def changes(old,new):
 return [{'operation':op,'old':old[a:b],'new':new[c:d]} for op,a,b,c,d in difflib.SequenceMatcher(None,[norm(x) for x in old],[norm(x) for x in new],autojunk=False).get_opcodes() if op!='equal']
def dump(name,obj):(O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
original=tm.directive
def directive(line):
 if line.strip().startswith(tm.PREFIX) and line.strip().endswith('-->'):
  spec=json.loads(line.strip()[len(tm.PREFIX):-3])
  if spec.get('caption') and set(spec)<={'caption','merges'} and not spec.get('merges'):return None
 return original(line)
tm.directive=directive
m.OUT_DIR=O
assert m.main([])==0
for _,filename in m.FILES:
 path=O/filename
 obj=json.loads(path.read_text(encoding='utf8'))
 def clean(v):
  if isinstance(v,str):return v.replace('\\[','[').replace('\\]',']')
  if isinstance(v,list):return [clean(x) for x in v]
  if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
  return v
 dump(filename,clean(obj))
units={s:json.loads((O/f'base_section{s}.json').read_text(encoding='utf8')) for s in range(3)}
u1,u2=units[1],units[2]
a=next(i for i,v in enumerate(u2) if norm(v['text']).startswith('부록(도입현장)'))
e=next(i for i,v in enumerate(u2) if v['text']=='Abstract')
ta=next(i for i,v in enumerate(u1) if norm(v['text'])=='감사의글' and '<hp:tab' not in v['xml'])
te=next(i for i,v in enumerate(u1) if norm(v['text'])=='논문개요' and '<hp:tab' not in v['xml'])
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
base=info['base']
trans={'감사의글':{'source_hwpx':base,'section':1,'range':[ta,te-1],'append_red_note':''},'부록1_설문지':{'source_hwpx':base,'section':2,'range':[a,e-1],'replace_appendix':'부 록 — 설문지','keep_until':'부 록 — 설문지','drop_heading':True}}
dump('transplant.json',trans)
audit={key:[] for key in ['paragraphs','tables','figures','front','appendix','force_fresh','unresolved','commands']}
for n in range(1,6):
 blocks=json.loads((O/f'ch{n:02}.blocks.json').read_text(encoding='utf8'))['blocks']
 start=next(i for i,v in enumerate(u2) if norm(v['text'])==norm(bt(blocks[0])))

 end=next(i for i in range(start+1,a) if norm(u2[i]['text'])==('참고문헌' if n==5 else norm(bt(json.loads((O/f'ch{n+1:02}.blocks.json').read_text(encoding='utf8'))['blocks'][0]))))
 old=[v['text'] for v in u2[start:end] if v['text'].strip() and not v['tbl']]
 new=[bt(b) for b in blocks if b['type'] in ('p','h1','h2','h3','h4','table_caption','figure_caption') and not k.image_md(b)]
 audit['paragraphs'].append({'chapter':n,'changes':changes(old,new)})
 cap=''
 for b in blocks:
  if b['type']=='table_caption':cap=re.match(r'<표\s*\d+-\d+>',b['text'])[0].replace(' ','')
  if b['type']=='table':
   old=next((v for v in u2[:a] if v['tbl'] and v['cap']==cap),None)
   grid=[b['header']]+b['rows']; diffs=[]
   if old:
    root=E.fromstring(k._wrap(old['xml']));tbl=next(root.iter(HP+'tbl'));nr,nc=int(tbl.get('rowCnt')),int(tbl.get('colCnt'))
    covered={}; oldcells=[]
    for cell in tbl.findall(HP+'tr/'+HP+'tc'):
     addr=cell.find(HP+'cellAddr');span=cell.find(HP+'cellSpan');r,c=int(addr.get('rowAddr')),int(addr.get('colAddr'));txt=''.join(t.text or '' for t in cell.iter(HP+'t'));oldcells.append([r,c,txt])
     for rr in range(r,r+int(span.get('rowSpan'))):
      for cc in range(c,c+int(span.get('colSpan'))):covered[rr,cc]=(r,c,txt)
     want=grid[r][c] if r<len(grid) and c<len(grid[r]) else None
     if want is None or norm(txt)!=norm(want):diffs.append({'row':r,'col':c,'old':txt,'new':want})
    for r,row in enumerate(grid):
     for c,txt in enumerate(row):
      owner=covered.get((r,c))
      if owner is None or ((r,c)!=owner[:2] and norm(txt) not in ('',norm(owner[2]))):diffs.append({'row':r,'col':c,'old':None,'new':txt})
    structure=(nr,nc)!=(len(grid),len(grid[0]))
   else:structure=True;nr=nc=None;diffs=[{'new':grid}]
   state='structural_replace' if structure else ('text_only' if diffs else 'preserve')
   audit['tables'].append({'caption':cap,'status':state,'base_shape':[nr,nc],'md_shape':[len(grid),len(grid[0])],'changes':diffs})
   if structure:audit['force_fresh'].append(cap)
 for fig in k.group_figures(blocks):
  if fig.get('type')=='_figure':audit['figures'].append({'caption':fig.get('caption'),'image':fig.get('image_md'),'status':'main must compare image pixels; dump contains references only'})
front=(ROOT/'01.docs/00_목차.md').read_text(encoding='utf8')
kr=paras(front.split('## 2. 국문초록',1)[1].split('---',1)[0]);en=paras(front.split('## 6. Abstract',1)[1])
thanks=paras((ROOT/'01.docs/감사의_글.md').read_text(encoding='utf8'))
for label,old,new in [('thanks',[v['text'] for v in u1[ta+1:te] if v['text'].strip()],thanks),('korean_abstract',[v['text'] for v in u1[te+1:] if v['text'].strip()],kr),('english_abstract',[v['text'] for v in u2[e+1:] if v['text'].strip()],en)]:
 ds=changes(old,new);audit['front'].append({'part':label,'changes':ds})
 if label=='thanks':assert not ds,'Thanks differs; transplant must be reviewed'
apx=json.loads((O/'apx1.blocks.json').read_text(encoding='utf8'))['blocks'];aptext=norm(''.join(v['text'] for v in u2[a:e]));missing=[]
for b in apx:
 texts=([x for row in b['rows'] for x in row] if b['type']=='table' else [bt(b)] if b['type']=='p' else [])
 for t in texts:
  if norm(t) and norm(t) not in aptext:missing.append(t)
audit['appendix']={'range':[a,e-1],'missing_fragments':missing,'status':'preserve exact baseline XML; check fragments below'}
if missing:audit['unresolved'].append({'appendix_missing':missing})
dump('md_hashes.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'01.docs').glob('*.md')})
audit['commands']=['python '+(O/filename).relative_to(ROOT).as_posix() for filename in ('prepare_inputs.py','assemble.py','resolve_patch.py')]
audit['unresolved'].append('Main execution: image pixel comparison, COM resave/reopen, all-table PDF check, printed TOC refresh and final PDF recheck remain required.')
dump('change_audit.json',audit)
print('Changed tables:',[(x['caption'],x['status']) for x in audit['tables'] if x['status']!='preserve'])
print('Appendix unmatched fragments:',len(missing))
