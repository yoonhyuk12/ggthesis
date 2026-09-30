"""Coordinator-only fragment edits; original package and unrelated nodes stay intact."""
from pathlib import Path
from copy import deepcopy
import sys,json,re,zipfile,hashlib
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
sys.path.insert(0,str(Q.parent/'review_260913_0239'))
import surgical_ops as S
S.MARK=re.compile(r'\[(?:DATA PENDING|확정 필요|CITE_TODO|그림 삽입 예정|UNVERIFIED)[^\]]*\]|실험전')
P=S.P;H=S.H
def read(f):return json.loads((Q/f).read_text(encoding='utf-8'))
def text(b):return b.get('text',''.join(r['text'] for r in b.get('runs',[])))
def norm(s):return re.sub(r'\s+','',s).replace('ㆍ','·').replace('−','-')
def serial(n):return E.tostring(n,encoding='UTF-8',with_tail=False)

def main():
 ed=S.Surgical(Q/'base.hwpx');ops={};queues={};logs=[]
 def replace(sec,idx,data,kind):
  key=(sec,idx);assert key not in ops,(key,kind,'duplicate')
  ops[key]=data;logs.append(dict(section=sec,idx=idx,kind=kind))
 def insert(sec,idx,pos,order,data):
  assert pos in ('before','after');queues.setdefault((sec,idx,pos),[]).append((order,data))
 for file in ('prose_A.json','prose_B.json'):
  m=read(file)
  for op in m.get('replace',[]):
   sec,idx=op['section'],op['idx'];assert S.own(ed.paras[sec][idx])==op['old'],(file,idx)
   replace(sec,idx,ed.edit_paragraph(sec,idx,op['new']),'replace')
  for op in m.get('delete',[]):
   sec,idx=op['section'],op['idx'];assert S.own(ed.paras[sec][idx])==op['old'],(file,idx)
   S._plain(ed.paras[sec][idx]);replace(sec,idx,b'','delete')
  for op in m.get('remove_object',[]):
   sec,idx=op['section'],op['idx'];assert ed.paras[sec][idx].getparent()==ed.roots[sec]
   replace(sec,idx,b'','remove_approved_object')
  for op in m.get('insert',[]):
   insert(op['section'],op['anchor_idx'],op['position'],op['order'],ed.edit_paragraph(op['section'],op['template_idx'],op['text'],new=True))
 c=read('tables_C.json')
 for op in c.get('cell_replace',[]):
  sec,idx=op['section'],op['idx'];assert S.own(ed.paras[sec][idx])==op['old'],('cell',idx)
  replace(sec,idx,ed.edit_paragraph(sec,idx,op['new']),'cell_replace')
 for op in c.get('replace_table',[]):
  sec=op['section'];xml=ed.table_fragment(sec,op['table_idx'],op['header'],op['rows'],op['weights'],caption=op.get('caption'))
  replace(sec,op['anchor_idx'],ed.wrap_table(sec,op['anchor_idx'],xml),'replace_table')
 for op in c.get('insert_table',[]):
  sec=op['section'];xml=ed.table_fragment(sec,op['template_table_idx'],op['header'],op['rows'],op['weights'],caption=op.get('caption'))
  insert(sec,op['anchor_idx'],op['position'],op['order'],ed.wrap_table(sec,op['template_anchor_idx'],xml,new=True))
 for op in c.get('delete_table',[]):replace(op['section'],op['anchor_idx'],b'','delete_table')
 for op in c.get('move_table',[]):
  sec=op['section'];key=(sec,op['source_anchor_idx'])
  value=ops.pop(key,serial(ed.paras[sec][key[1]]))
  replace(sec,key[1],b'','move_table_source');insert(sec,op['anchor_idx'],op['position'],op['order'],value)
 # Cell edits also invalidate the containing table anchor's cached layout.
 for op in c.get('cell_replace',[]):
  sec=op['section'];p=ed.paras[sec][op['idx']]
  for ancestor in p.iterancestors(P+'p'):
   for cache in ancestor.findall(P+'linesegarray'):
    # Queue only the exact cache range below; enclosing paragraph stays intact.
    cache.set('data-invalidate','1')
 changed={}
 for sec,ps in ed.paras.items():
  raw=ed.data[sec];nodes=[n for n in elements(raw) if n['name']=='hp:p'];spans=[]
  assert len(nodes)==len(ps)
  for idx,p in enumerate(ps):
   if any(n.get('data-invalidate')=='1' for n in p.findall(P+'linesegarray')) and (sec,idx) not in ops:
    # Direct anchor cache follows all runs and nested cell paragraphs.
    caches=[n for n in elements(raw[nodes[idx]['start']:nodes[idx]['end']]) if n['name']=='hp:linesegarray']
    if caches:
     n=caches[-1];spans.append((nodes[idx]['start']+n['start'],nodes[idx]['start']+n['end'],b''))
  for (s,idx),value in ops.items():
   if s==sec:spans.append((nodes[idx]['start'],nodes[idx]['end'],value))
  for (s,idx,pos),items in queues.items():
   if s==sec:
    off=nodes[idx]['start' if pos=='before' else 'end'];spans.append((off,off,b''.join(v for _,v in sorted(items,key=lambda x:x[0]))))
  spans.sort(key=lambda x:(x[0],x[1]));cursor=0;chunks=[]
  for a,b,v in spans:
   assert a>=cursor,('overlap',sec,a,b,cursor);chunks.extend([raw[cursor:a],v]);cursor=b
  if spans:chunks.append(raw[cursor:]);changed[sec]=b''.join(chunks);E.fromstring(changed[sec])
 # Add one blank before section/subsection headings where needed, without touching other nodes.
 sec='Contents/section2.xml';raw=changed.get(sec,ed.data[sec]);root=E.fromstring(raw)
 nodes=[n for n in elements(raw) if n['name']=='hp:p'];ps=list(root.iter(P+'p'));extra=[]
 blank=next(i for i,p in enumerate(ed.paras[sec]) if p.getparent()==ed.roots[sec] and not S.own(p).strip() and not list(p.iter(P+'tbl')) and not list(p.iter(P+'pic')) and not any(E.QName(n).localname in ('secPr','ctrl') for n in p.iter()))
 for p in root.findall(P+'p'):
  if re.match(r'^제\d+[절항]\s',S.own(p).strip()):
   prev=p.getprevious()
   if prev is not None and (S.own(prev).strip() or list(prev.iter(P+'tbl')) or list(prev.iter(P+'pic'))):
    idx=ps.index(p);extra.append((nodes[idx]['start'],ed.edit_paragraph(sec,blank,'',True)))
 for off,v in reversed(extra):raw=raw[:off]+v+raw[off:]
 changed[sec]=raw
 # Refresh TOC titles/ranges using current MD; cover, acknowledgement, abstract remain untouched.
 sec='Contents/section1.xml';raw=ed.data[sec];root=ed.roots[sec];ps=ed.paras[sec];nodes=[n for n in elements(raw) if n['name']=='hp:p']
 blocks=read('new_blocks.json');groups=[[],[],[]]
 for file,bs in blocks.items():
  if not re.match(r'0[1-6]_',file):continue
  for b in bs:
   if b['type'] in ('h1','h2','h3'):
    title=text(b);groups[0].append(dict(body_text=title,toc_title=' '*({'h1':0,'h2':1,'h3':2}[b['type']])+title,kind='heading'))
   elif b['type']=='table_caption':groups[1].append(dict(body_text=text(b),toc_title=text(b),kind='table'))
   elif b['type']=='figure_caption':groups[2].append(dict(body_text=text(b),toc_title=text(b),kind='figure'))
 for idx in range(86,99):
  title=re.sub(r'\d+$','',S.own(ps[idx])).rstrip();groups[0].append(dict(body_text=title.strip(),toc_title=title,kind='heading'))
 template=ps[3];changes=[];targets=[]
 for (start,end),group in zip([(3,98),(102,129),(133,140)],groups):
  items=[]
  for entry in group:
   p=deepcopy(template);p.set('id',ed._id());S._cache(p)
   t=p.find('.//'+P+'t');tab=deepcopy(t.find(P+'tab'));assert tab is not None
   for child in list(t):t.remove(child)
   t.text=entry['toc_title'];tab.tail='0';t.append(tab)
   items.append(serial(p));targets.append(entry)
  changes.append((nodes[start]['start'],nodes[end]['end'],b''.join(items)))
 for a,b,v in reversed(changes):raw=raw[:a]+v+raw[b:]
 changed[sec]=raw
 # Existing unrevised markers (including result placeholders) must also remain red.
 marker_fixes=[]
 for sec in ed.paras:
  raw=changed.get(sec,ed.data[sec]);root=E.fromstring(raw);ps=list(root.iter(P+'p'))
  nodes=[n for n in elements(raw) if n['name']=='hp:p'];fixes=[]
  for idx,p in enumerate(ps):
   value=S.own(p);colors=[]
   for r in p.findall(P+'run'):
    colors.extend([ed.chars[r.get('charPrIDRef')].get('textColor','').upper()]*len(S.own_run(r)))
   if any(any(c!='#FF0000' for c in colors[m.start():m.end()]) for m in S.MARK.finditer(value)):
    fixes.append((nodes[idx]['start'],nodes[idx]['end'],serial(ed._edit(p,value))))
    marker_fixes.append((sec,idx))
  for a,b,v in reversed(fixes):raw=raw[:a]+v+raw[b:]
  if fixes:changed[sec]=raw
 changed['Contents/header.xml']=ed.header_bytes()
 result=raw_zip_patch((Q/'base.hwpx').read_bytes(),changed)
 (Q/'candidate.hwpx').write_bytes(result)
 (Q/'toc_targets.json').write_text(json.dumps(targets,ensure_ascii=False,indent=2),encoding='utf-8')
 (Q/'patch_log.json').write_text(json.dumps(dict(operations=logs,inserted=sum(len(v) for v in queues.values()),blank_insertions=len(extra),marker_fixes=marker_fixes,table_estimates=ed.estimates,changed_entries=list(changed)),ensure_ascii=False,indent=2),encoding='utf-8')
 print('candidate',len(result),'ops',len(logs),'inserts',sum(len(v) for v in queues.values()),'toc',len(targets))
if __name__=='__main__':main()
