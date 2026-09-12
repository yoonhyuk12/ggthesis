"""Main-only paragraph pagination repairs found during actual PDF review."""
from pathlib import Path
import copy,json,re,sys
from lxml import etree as E
from surgical_ops import Surgical,P,H,own
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
ed=Surgical(Q/'final2.hwpx');sec='Contents/section2.xml';root=ed.roots[sec]
ps=root.findall(P+'p');allp=ed.paras[sec];raw=ed.data[sec]
lex=[n for n in elements(raw) if n['name']=='hp:p'];changed=set();log=[]
styles={s.get('id'):s for s in ed.header.iter(H+'paraPr')};cache={}
def style(p,**values):
 key=(p.get('paraPrIDRef'),tuple(sorted(values.items())))
 if key not in cache:
  source=styles[key[0]];n=copy.deepcopy(source);new=str(max(map(int,styles))+1);n.set('id',new)
  for k,v in values.items():n.find(H+'breakSetting').set(k,v)
  source.getparent().append(n);styles[new]=n;cache[key]=new
 p.set('paraPrIDRef',cache[key]);changed.add(p)
def blank(p):return not own(p).strip() and p.find('.//'+P+'tbl') is None and p.find('.//'+P+'pic') is None
for i,p in enumerate(ps):
 s=own(p).strip();heading=bool(re.match(r'^(제\d+[장절항]\s|Part [A-E]\.|\d\. (공통부|도입 현장))',s))
 if s.startswith('제2장 '):p.set('pageBreak','1');changed.add(p);log.append('Chapter 2 starts a new page')
 if s.startswith('주:'):
  style(p,keepLines='1')
  if p.get('pageBreak')=='1':p.set('pageBreak','0');log.append('Removed inherited page break from table note')
 if heading or s.startswith('패널 ') or (s.startswith('<표 ') and p.find('.//'+P+'tbl') is None):
  style(p,keepWithNext='1',keepLines='1')
  j=i+1
  while j<len(ps) and blank(ps[j]):style(ps[j],keepWithNext='1');j+=1
 if heading and i and blank(ps[i-1]):style(ps[i-1],keepWithNext='1')
 if p.get('pageBreak')=='1' and i and blank(ps[i-1]):
  # The explicit break belongs before the existing spacing paragraph, avoiding a blank page.
  ps[i-1].set('pageBreak','1');p.set('pageBreak','0');changed.update((p,ps[i-1]));style(ps[i-1],keepWithNext='1')
  log.append('Moved break before existing blank: '+s)
# Apply independently reviewed table layout manifests, if supplied.
extra=Q/'layout_table_ops.json'
if extra.exists():
 for op in json.loads(extra.read_text(encoding='utf8')):
  t=ed.tables[sec][op['table_idx']]
  if op['kind']=='widths':
   widths=op['widths'];assert sum(widths)==int(t.find(P+'sz').get('width'))
   for row in t.findall(P+'tr'):
    for c in row.findall(P+'tc'):
     addr=c.find(P+'cellAddr');span=c.find(P+'cellSpan');start=int(addr.get('colAddr'));count=int(span.get('colSpan'))
     c.find(P+'cellSz').set('width',str(sum(widths[start:start+count])))
  elif op['kind']=='empty_header_rows':
   assert t.get('id')==op['id'];rows=t.findall(P+'tr')
   for row in rows[1:3]:
    assert not any(own(p).strip() for p in row.iter(P+'p'))
    assert all(E.QName(x).localname not in ['tbl','pic','ctrl','equation','ole','shapeObject'] for x in row.iter())
    t.remove(row)
   t.set('rowCnt',str(op['rowCnt_after']))
   title=rows[0].find(P+'tc');assert title.find(P+'cellSpan').get('rowSpan')=='3'
   title.find(P+'cellSpan').set('rowSpan','1');title.find(P+'cellSz').set('height',str(op['new_header_height']))
   for row in rows[3:]:
    for c in row.findall(P+'tc'):
     a=c.find(P+'cellAddr');a.set('rowAddr',str(int(a.get('rowAddr'))-2))
   t.find(P+'sz').set('height',str(op['table_height_after']))
  for p in t.iter(P+'p'):
   for x in list(p.findall(P+'linesegarray')):p.remove(x)
  anchor=t
  while anchor.getparent() is not root:anchor=anchor.getparent()
  changed.add(anchor);log.append(op)
# Statistical units use the same two-paragraph header convention as physical units.
for t in ed.tables[sec]:
 row=t.find(P+'tr')
 if row is None:continue
 for c in row.findall(P+'tc'):
  sub=c.find(P+'subList')
  for p in list(sub.findall(P+'p')):
   m=re.fullmatch(r'(.*?)\s*(\((?:M|SD)\))',own(p).strip())
   if not m or not m[1]:continue
   first=ed._edit(p,m[1]);second=ed._edit(p,m[2],new=True)
   idx=sub.index(p);sub.remove(p);sub.insert(idx,first);sub.insert(idx+1,second)
   anchor=t
   while anchor.getparent() is not root:anchor=anchor.getparent()
   changed.add(anchor);log.append('Split statistical unit header '+m[0])
patches=[]
for p in changed:
 for x in list(p.findall(P+'linesegarray')):p.remove(x)
 idx=allp.index(p);patches.append((lex[idx]['start'],lex[idx]['end'],E.tostring(p,encoding='utf8')))
for a,b,value in sorted(patches,reverse=True):raw=raw[:a]+value+raw[b:]
E.fromstring(raw)
for parent in ed.header.iter(H+'paraProperties'):parent.set('itemCnt',str(len(parent)))
(Q/'layout_input.hwpx').write_bytes(raw_zip_patch((Q/'final2.hwpx').read_bytes(),{sec:raw,'Contents/header.xml':E.tostring(ed.header,encoding='utf8')}))
(Q/'layout_changes.json').write_text(json.dumps({'paragraphs':len(changed),'changes':log},ensure_ascii=False,indent=2),encoding='utf8')
print('Layout paragraphs changed',len(changed),'operations',len(log))
