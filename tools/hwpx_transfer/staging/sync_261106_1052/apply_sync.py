"""MAIN ONLY: apply reviewed unit plan to copied latest HWPX. Worker does not execute."""
from pathlib import Path
import sys,json,re,zipfile,copy,hashlib,difflib,html
from lxml import etree as E
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p,kjn_profile as k
O=Path(__file__).parent; HP='{'+k.NS['hp']+'}'
def norm(t):return re.sub(r'\s|<br\s*/?>','',html.unescape(t))
def wrap(x):return E.fromstring(k._wrap(x).encode())
def serialize(x):return re.sub(r' xmlns(?::[^= ]+)?="[^"]*"','',E.tostring(x,encoding='unicode'))
def own_t(para):return [t for r in para.findall(HP+'run') for t in r.findall(HP+'t')]
def text(el):return ''.join(''.join(t.itertext()) for t in el.iter(HP+'t'))
def clear(el):
 for n in list(el.iter(HP+'linesegarray')):n.getparent().remove(n)
def edit_nodes(nodes,new):
 """Apply reverse, minimal diffs so unchanged styled characters stay in their runs."""
 assert all(len(t)==0 for t in nodes),'Structured text requires manual review'
 old=''.join(t.text or '' for t in nodes)
 if old==new:return
 if not nodes:raise AssertionError('No text nodes')
 offsets=[];pos=0
 for t in nodes:offsets.append((pos,pos+len(t.text or '')));pos=offsets[-1][1]
 for tag,a,b,c,d in reversed(difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes()):
  if tag=='equal':continue
  value=new[c:d]
  if a==b:
   eligible=[i for i,(s,e) in enumerate(offsets) if s<=a<=e and e>s]
   idx=eligible[-1] if eligible else len(nodes)-1;s,e=offsets[idx]
   t=nodes[idx];cur=t.text or '';local=a-s;t.text=cur[:local]+value+cur[local:]
  else:
   first=True
   for i,(s,e) in enumerate(offsets):
    if e<=a or s>=b:continue
    t=nodes[i];cur=t.text or '';lo=max(0,a-s);hi=min(e,b)-s
    t.text=cur[:lo]+(value if first else '')+cur[hi:];first=False
 assert ''.join(t.text or '' for t in nodes)==new
PID=3009000000
def fresh_ids(el):
 global PID
 for para in el.iter(HP+'p'):para.set('id',str(PID));PID+=1
def set_cell(cell,new):
 current=text(cell)
 if norm(current)==norm(new):return
 if '<br' in new:
  sl=cell.find(HP+'subList');paras=sl.findall(HP+'p');template=paras[0]
  for q in paras:sl.remove(q)
  for part in re.split(r'<br\s*/?>',new):
   q=copy.deepcopy(template);fresh_ids(q);clear(q)
   runs=q.findall(HP+'run');r=copy.deepcopy(runs[0]) if runs else E.Element(HP+'run',charPrIDRef='49')
   for ch in list(r):r.remove(ch)
   E.SubElement(r,HP+'t').text=part
   for ch in list(q):q.remove(ch)
   q.append(r);sl.append(q)
 else:
  nodes=list(cell.iter(HP+'t'))
  if not nodes:
   para=cell.find('.//'+HP+'p');r=E.SubElement(para,HP+'run',charPrIDRef='49');nodes=[E.SubElement(r,HP+'t')]
  edit_nodes(nodes,new)
 clear(cell)
def table_change(root,chg):
 table=next(root.iter(HP+'tbl'));block=chg['block'];grid=[block['header']]+block['rows']
 old_rows=int(table.get('rowCnt'));new_rows=len(grid)
 if old_rows!=new_rows:
  assert chg['unit_index']==365 and new_rows==old_rows+1
  trs=table.findall(HP+'tr');extra=copy.deepcopy(trs[1]);fresh_ids(extra)
  for tr in trs[2:]:
   for cell in tr.findall(HP+'tc'):
    a=cell.find(HP+'cellAddr');a.set('rowAddr',str(int(a.get('rowAddr'))+1))
  for cell in extra.findall(HP+'tc'):cell.find(HP+'cellAddr').set('rowAddr','2')
  table.insert(list(table).index(trs[2]),extra);table.set('rowCnt',str(new_rows))
  sz=table.find(HP+'sz');sz.set('height',str(int(sz.get('height'))+max(int(c.find(HP+'cellSz').get('height')) for c in extra.findall(HP+'tc'))))
  clear(table)
 for tr in table.findall(HP+'tr'):
  for cell in tr.findall(HP+'tc'):
   a=cell.find(HP+'cellAddr');r,c=int(a.get('rowAddr')),int(a.get('colAddr'))
   set_cell(cell,grid[r][c])
 # All own and nested paragraph caches in the changed table are invalidated.
 clear(root)
def apply_unit(raw,chg):
 root=wrap(raw);para=root.find(HP+'p')
 if chg['kind']=='table':table_change(root,chg)
 elif chg['kind']=='nested_paragraphs':
  for replacement in chg['replacements']:
   matches=[q for q in root.iter(HP+'p') if norm(''.join(t.text or '' for t in own_t(q)))==norm(replacement['old'])]
   assert len(matches)==1,(chg['unit_index'],replacement['old'],len(matches))
   edit_nodes(own_t(matches[0]),replacement['new']);clear(matches[0])
  clear(para)
 else:
  nodes=own_t(para);assert norm(''.join(t.text or '' for t in nodes))==norm(chg['old'])
  edit_nodes(nodes,chg['new']);clear(para)
 return ''.join(serialize(x) for x in root)
def clone_para(raw,t):
 root=wrap(raw);q=root.find(HP+'p');fresh_ids(q);q.set('pageBreak','0');q.set('columnBreak','0')
 # Retain the appropriate paragraph/run formatting, without inherited controls.
 runs=q.findall(HP+'run');r=copy.deepcopy(runs[0])
 for ch in list(r):r.remove(ch)
 E.SubElement(r,HP+'t').text=t
 for ch in list(q):q.remove(ch)
 q.append(r)
 return serialize(q)
def main():
 plan=json.loads((O/'md_diff_plan.json').read_text(encoding='utf8'))
 info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
 assert hashlib.sha256(Path(info['base']).read_bytes()).hexdigest()==info['sha256']
 changes={(x['section'],x['unit_index']):x for x in plan['changes']}
 deletes={(x['section'],x['unit_index']) for x in plan['deletions']}
 audit=[];replacements={}
 with zipfile.ZipFile(O/'base.hwpx') as z:
  for s in range(3):
   name=f'Contents/section{s}.xml';source=z.read(name).decode('utf8');u=p.Units(source,set());out=[]
   for i,unit in enumerate(u.items):
    chg=changes.get((s,i))
    if (s,i) not in deletes:
     if chg:
      assert unit['text']==chg['old'];v=apply_unit(unit['xml'],chg)
      assert norm(p.Units('<hs:sec>'+v+'</hs:sec>',set()).items[0]['text'])==norm(chg['new']),(s,i,'result text mismatch')
      out.append(v);audit.append({'section':s,'unit_index':i,'kind':chg['kind']})
     else:out.append(unit['xml'])
    for ins in plan['insertions']:
     if ins['section']!=s or ins['after_unit_index']!=i:continue
     clone=ins.get('clone_unit_index')
     if clone is None:clone=455 if ins['new'].startswith('주:') else 179 if i==175 else i
     out.append(clone_para(u.items[clone]['xml'],ins['new']))
   rebuilt=u.head+''.join(out)+u.tail
   if rebuilt!=source:replacements[name]=rebuilt.encode('utf8')
  dest=O/'patched.hwpx'
  with zipfile.ZipFile(dest,'w') as w:
   for zi in z.infolist():w.writestr(zi,replacements.get(zi.filename,z.read(zi.filename)))
 (O/'apply_sync_audit.json').write_text(json.dumps({'changes':audit,'insertions':plan['insertions'],'deletions':plan['deletions'],'output':dest.as_posix()},ensure_ascii=False,indent=2),encoding='utf8')
 print('Applied',len(audit),'changes;',len(plan['insertions']),'insertions;',len(plan['deletions']),'deletions:',dest)
if __name__=='__main__':main()
