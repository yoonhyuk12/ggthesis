"""Main-only TOC page refresh using ordered body context and printed PDF folios."""
from pathlib import Path
import json,re,zipfile,sys,html
from lxml import etree as E
import fitz
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def norm(s):return re.sub(r'\s+','',s).replace('·','ㆍ').replace('−','-')
def make_targets():
 rows=json.loads((HERE/'base_paras.json').read_text(encoding='utf8'))
 body=[r for r in rows if r['section']=='Contents/section2.xml']
 base_entries=json.loads((HERE.parent/'toc_260912/page_map.json').read_text(encoding='utf8'))['entries']
 reps={}
 for fn in ['prose_A.json','prose_B.json','main_changes.json']:
  for r in json.loads((HERE/fn).read_text(encoding='utf8')).get('replace',[]):reps[norm(r['old'])]=r['new'].strip()
 captions={}
 for bs in json.loads((HERE/'new_blocks.json').read_text(encoding='utf8')).values():
  for b in bs:
   if b['type']=='table_caption':captions[re.search(r'<표\s+(\d+-\d+)>',b['text'])[1]]=b['text']
 with zipfile.ZipFile(HERE/'base.hwpx') as z:
  root=E.fromstring(z.read('Contents/section1.xml'))
  ps=[(i,p) for i,p in enumerate(root.iter(P+'p')) if p.find('.//'+P+'tab') is not None]
 assert len(ps)==len(base_entries),(len(ps),len(base_entries))
 result=[]
 for (idx,p),old in zip(ps,base_entries):
  title=old['body_text'];toc_title=re.sub(r'\d+$','',own(p)).rstrip()
  if old['kind']=='table':
   number=re.search(r'<표\s*(\d+-\d+)>',toc_title)[1];title=captions[number]
  elif norm(title) in reps:title=reps[norm(title)]
  else:
   # Keep current HWPX wording when only space or historical caption differences exist.
   matches=[r['text'].strip() for r in body if norm(r['text'])==norm(title)]
   if matches:title=matches[0]
  result.append({'toc_idx':idx,'old_toc_title':toc_title,'body_text':title,'kind':old['kind']})
 (HERE/'toc_targets.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 return result

def mapping(pdf):
 targets=json.loads((HERE/'toc_targets.json').read_text(encoding='utf8'));doc=fitz.open(pdf);pages=[]
 for k,page in enumerate(doc):
  lines=[{'text':''.join(s['text'] for s in line['spans']),'bbox':line['bbox']} for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines']]
  nums=[int(m[1]) for l in lines if l['bbox'][1]>page.rect.height*.88 and (m:=re.fullmatch(r'[-–]\s*(\d+)\s*[-–]',l['text'].strip()))]
  pages.append({'physical':k+1,'printed':nums[0] if nums else None,'lines':lines})
 # Suppressed first body folio must be corroborated by following printed 2.
 for k,p in enumerate(pages[:-1]):
  if p['printed'] is None and pages[k+1]['printed']==2 and any(norm(l['text'])==norm('제1장 서론') for l in p['lines']):p['printed']=1
 result=[];unresolved=[];last_by_kind={}
 for e in targets:
  target=norm(e['body_text']);candidates=[]
  for p in pages:
   if p['printed'] is None:continue
   ls=p['lines']
   for j,l in enumerate(ls):
    if l['bbox'][1]>700:continue
    text=''
    for n in range(16):
     if j+n>=len(ls):break
     text+=norm(ls[j+n]['text'])
     if text==target:candidates.append({'physical':p['physical'],'printed':p['printed'],'y':l['bbox'][1]})
     if len(text)>len(target):break
  # Headings in repeated appendix forms and chapter 2 must be resolved in reading order.
  prev=last_by_kind.get(e['kind'],(0,0));viable=[c for c in candidates if (c['physical'],c['y'])>prev]
  if not viable:unresolved.append({**e,'candidates':candidates,'previous':prev});continue
  chosen=min(viable,key=lambda c:(c['physical'],c['y']));last_by_kind[e['kind']]=(chosen['physical'],chosen['y'])
  result.append({**e,**chosen,'candidate_count':len(candidates)})
 return {'entries':result,'unresolved':unresolved,'pages':len(doc)}

def update(name):
 report=mapping(HERE/(name+'.pdf'));(HERE/(name+'_toc_map.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print('TOC mapped',len(report['entries']),'unresolved',len(report['unresolved']))
 if report['unresolved']:
  for e in report['unresolved']:print(e['body_text'],e['previous'])
  return False
 with zipfile.ZipFile(HERE/(name+'.hwpx')) as z:raw=z.read('Contents/section1.xml')
 ps=[n for n in elements(raw) if n['name']=='hp:p'];ep=list(E.fromstring(raw).iter(P+'p'));current=[i for i,p in enumerate(ep) if p.find('.//'+P+'tab') is not None]
 assert len(current)==len(report['entries'])
 edits=[]
 for idx,e in zip(current,report['entries']):
  old=fragment(raw,ps[idx]);new,n=re.subn(rb'(<hp:tab\b[^>]*/>)(\d+)(</hp:t>)',lambda m:m[1]+str(e['printed']).encode()+m[3],old);assert n==1,(idx,n)
  new=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',new,flags=re.S);edits.append((ps[idx]['start'],ps[idx]['end'],new))
 for a,b,value in sorted(edits,reverse=True):raw=raw[:a]+value+raw[b:]
 E.fromstring(raw);(HERE/'toc_updated.hwpx').write_bytes(raw_zip_patch((HERE/(name+'.hwpx')).read_bytes(),{'Contents/section1.xml':raw}));return True
if __name__=='__main__':
 if sys.argv[1]=='targets':make_targets()
 else:update(sys.argv[1])
