"""Coordinator-only application of validated manifests; preserves unrelated ZIP bytes."""
from pathlib import Path
import sys,json,re,zipfile,html,copy,hashlib
from lxml import etree as E
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,raw_zip_patch
from surgical_ops import Surgical
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
C='{http://www.hancom.co.kr/hwpml/2011/core}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def load(n):return json.loads((HERE/n).read_text(encoding='utf8'))
def norm(t):return re.sub(r'\s+','',t).replace('·','ㆍ')

def main():
 ed=Surgical(HERE/'base.hwpx');manifests=[load(n) for n in ['prose_A.json','prose_B.json','main_changes.json']];tc=load('tables_C.json')
 reps={};dels={};queues={};custom={};tablelog=[]
 for man in manifests:
  for r in man.get('replace',[]):
   key=(r['section'],r['idx']);assert key not in reps;assert own(ed.paras[key[0]][key[1]])==r['old'];reps[key]=r['new']
  for r in man.get('delete',[]):dels[(r['section'],r['idx'])]=r['old']
 for r in tc['cell_replace']:
  key=(r['section'],r['idx']);assert key not in reps;assert own(ed.paras[key[0]][key[1]])==r['old'];reps[key]=r['new']
 b=manifests[1];seq=next(x['sequence'] for x in b['coverage'] if x.get('status')=='assembly_order' and x['file'].startswith('05'))
 byblock={s['new_block']:s for s in seq};ranks={}
 for s in seq:
  for loc in s.get('locations',[]):
   if loc['kind']=='insert_after':ranks[(loc['section'],loc['idx'],loc['text_offset'])]=s['new_block']
 def qadd(key,rank,xml):queues.setdefault(key,[]).append((rank,xml))
 for man in manifests:
  for item in man.get('insert_after',[]):
   key=(item['section'],item['idx'])
   for j,text in enumerate(item['texts']):qadd(key,ranks.get((*key,j),j),ed.edit_paragraph(item['section'],item['template_idx'],text,new=True))
 for g in tc['replace_table']:
  sec=g['section'];is5=g['caption'].startswith('<표 5-');panel0=g['panels'][0]
  caption_in=g['caption_location']=='merged_first_cell'
  preceding_caption=panel0['after_new_md_text']==g['caption']
  standalone_caption=caption_in and not preceding_caption
  for ti in g['all_old_table_indices']:
   anchor=next(a for a in ed.tables[sec][ti].iterancestors() if a.tag==P+'p');idx=ed.paras[sec].index(anchor);custom[(sec,idx)]=b''
  if standalone_caption:
   original=ed.tables[sec][g['table_idx']];captionp=next(p for p in original.iter(P+'p') if own(p).startswith('<표'))
   cidx=ed.paras[sec].index(captionp);custom[(sec,g['old_anchor_idx'])]=ed.edit_paragraph(sec,cidx,g['caption'],new=True)
  for j,panel in enumerate(g['panels']):
   ti=panel.get('table_idx');template_ti=ti if ti is not None else g['table_idx']
   cap=g['caption'] if caption_in and preceding_caption and j==0 else None
   rawtbl=ed.table_fragment(sec,template_ti,panel['header'],panel['rows'],panel['width_weights'],caption=cap)
   anchor=panel.get('old_anchor_idx') if ti is not None else g['old_anchor_idx']
   wrapped=ed.wrap_table(sec,anchor,rawtbl,new=ti is None)
   if not is5 or (j==0 and preceding_caption):custom[(sec,g['old_anchor_idx'])]=wrapped
   else:
    prev=byblock[panel['after_new_md_block_idx']];locs=prev.get('locations',[]);assert len(locs)==1,(g['caption'],panel,prev)
    loc=locs[0];qadd((loc['section'],loc['idx']),panel['md_block_idx'],wrapped)
   if panel.get('note'):
    loc=byblock[panel['after_new_md_block_idx']]['locations'][0] if is5 and not preceding_caption else {'section':sec,'idx':g['old_anchor_idx']}
    qadd((loc['section'],loc['idx']),panel['md_block_idx']+.1,ed.edit_paragraph(sec,751,panel['note'],new=True))
   root=E.fromstring(rawtbl);tablelog.append({'caption':g['caption'],'panel':j,'new_block':panel['md_block_idx'],'width':root.find(P+'sz').get('width'),'rows':len(panel['rows'])+1,'cols':len(panel['header']),'texts':[panel['header']]+panel['rows'],'pageBreak':root.get('pageBreak')})
 modified={};oplog=[]
 for sec in ['Contents/section2.xml']:
  raw=ed.data[sec];ns=elements(raw);ps=[n for n in ns if n['name']=='hp:p'];patches=[];ancestor_cache=set()
  for (s,idx),text in reps.items():
   if s!=sec:continue
   assert (s,idx) not in custom;node=ps[idx];patches.append((node['start'],node['end'],ed.edit_paragraph(sec,idx,text)))
   parent=node['parent']
   while parent:
    if parent['name']=='hp:p':ancestor_cache.add(parent['start'])
    parent=parent['parent']
   oplog.append({'kind':'replace','section':s,'idx':idx,'new':text})
  for (s,idx),old in dels.items():
   if s!=sec:continue
   assert own(ed.paras[s][idx])==old;node=ps[idx];patches.append((node['start'],node['end'],b''));oplog.append({'kind':'delete','section':s,'idx':idx})
  for (s,idx),value in custom.items():
   if s!=sec:continue
   node=ps[idx];patches.append((node['start'],node['end'],value));oplog.append({'kind':'table_anchor_replace','section':s,'idx':idx})
  for (s,idx),items in queues.items():
   if s!=sec:continue
   value=b''.join(v for _,v in sorted(items,key=lambda x:x[0]));patches.append((ps[idx]['end'],ps[idx]['end'],value));oplog.append({'kind':'insert_after','section':s,'idx':idx,'count':len(items)})
  # Replace just the two research images, with identical source pixel dimensions.
  for n in ns:
   if n['name']=='hp:linesegarray' and n['parent']['start'] in ancestor_cache:patches.append((n['start'],n['end'],b''))
  cursor=0;chunks=[]
  for a,b,value in sorted(patches,key=lambda x:(x[0],x[1])):
   assert a>=cursor,('overlap',a,b,cursor);chunks.extend([raw[cursor:a],value]);cursor=b
  chunks.append(raw[cursor:]);modified[sec]=b''.join(chunks);E.fromstring(modified[sec])
 # New figure bitmaps have exactly the old canvas geometry; object position and crop remain unchanged.
 with zipfile.ZipFile(HERE/'base.hwpx') as z:
  for item,name in [('image3','flow_current.png'),('image8','model_current.png')]:
   path=next(n for n in z.namelist() if n.startswith('BinData/'+item+'.'))
   from PIL import Image
   import io
   oldsize=Image.open(io.BytesIO(z.read(path))).size;newsize=Image.open(HERE/name).size;assert oldsize==newsize,(path,oldsize,newsize)
   modified[path]=(HERE/name).read_bytes()
 # TOC title changes keep existing tabs, font and folio runs. Page numbers are updated after reflow.
 targets=load('toc_targets.json');raw=ed.data['Contents/section1.xml'];ns=elements(raw);ps=[n for n in ns if n['name']=='hp:p'];patches=[]
 for t in targets:
  idx=t['toc_idx'];p=ed.paras['Contents/section1.xml'][idx];old=fragment(raw,ps[idx]);n=copy.deepcopy(p)
  texts=[x for r in n.findall(P+'run') for x in r.findall(P+'t')]
  prior=[]
  for x in texts:
   prior.append(x)
   if x.find(P+'tab') is not None:break
  assert prior,(idx,'no pretab text');lead=re.match(r'^\s*',own(p))[0]
  prior[0].text=lead+t['body_text']
  for x in prior[1:]:x.text=''
  for x in list(n.findall(P+'linesegarray')):n.remove(x)
  patches.append((ps[idx]['start'],ps[idx]['end'],E.tostring(n,encoding='utf8')))
 for a,b,value in sorted(patches,reverse=True):raw=raw[:a]+value+raw[b:]
 modified['Contents/section1.xml']=raw
 modified['Contents/header.xml']=ed.header_bytes()
 result=raw_zip_patch((HERE/'base.hwpx').read_bytes(),modified);(HERE/'candidate.hwpx').write_bytes(result)
 (HERE/'patch_manifest.json').write_text(json.dumps({'operations':oplog,'tables':tablelog,'changed_parts':list(modified)},ensure_ascii=False,indent=2),encoding='utf8')
 print('Candidate written:',len(result),'bytes;',len(reps),'paragraph replacements;',len(tablelog),'new table panels')
if __name__=='__main__':main()
