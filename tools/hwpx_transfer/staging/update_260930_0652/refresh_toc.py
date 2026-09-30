"""Main only: map each TOC target to the first ordered body heading and printed folio."""
from pathlib import Path
import sys,json,re,zipfile
from lxml import etree as E
import fitz
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def norm(t):return re.sub(r'\s+','',t).replace('·','ㆍ').replace('−','-')
def mapping(pdf):
 targets=json.loads((Q/'toc_targets.json').read_text(encoding='utf-8'));doc=fitz.open(pdf);pages=[]
 for k,page in enumerate(doc):
  lines=[dict(text=''.join(s['text'] for s in l['spans']),bbox=l['bbox']) for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines']]
  nums=[int(m[1]) for l in lines if l['bbox'][1]>page.rect.height*.88 and (m:=re.fullmatch(r'[-–]\s*(\d+)\s*[-–]',l['text'].strip()))]
  pages.append(dict(physical=k+1,printed=nums[0] if nums else None,lines=lines))
 for k,p in enumerate(pages[:-1]):
  if p['printed'] is None and pages[k+1]['printed']==2 and any(norm(l['text'])==norm('제1장 서론') for l in p['lines']):p['printed']=1
 found=[];missing=[];last={}
 for t in targets:
  goal=norm(t['body_text']);cs=[]
  for p in pages:
   if p['printed'] is None:continue
   lines=p['lines']
   for j,l in enumerate(lines):
    if l['bbox'][1]>700:continue
    value=''
    for line in lines[j:j+16]:
     value+=norm(line['text'])
     if value==goal:cs.append(dict(physical=p['physical'],printed=p['printed'],y=l['bbox'][1]));break
     if len(value)>len(goal):break
  previous=last.get(t['kind'],(0,0));cs=[c for c in cs if (c['physical'],c['y'])>previous]
  if not cs:missing.append(dict(target=t,previous=previous));continue
  best=min(cs,key=lambda c:(c['physical'],c['y']));last[t['kind']]=(best['physical'],best['y']);found.append({**t,**best})
 return dict(entries=found,unresolved=missing,pages=len(doc))
def main(name,out):
 report=mapping(Q/(name+'.pdf'));(Q/(name+'_toc_map.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('mapped',len(report['entries']),'unresolved',len(report['unresolved']))
 if report['unresolved']:
  for item in report['unresolved']:print(item)
  raise SystemExit(1)
 with zipfile.ZipFile(Q/(name+'.hwpx')) as z:raw=z.read('Contents/section1.xml')
 root=E.fromstring(raw);ps=list(root.iter(P+'p'));nodes=[n for n in elements(raw) if n['name']=='hp:p'];indices=[i for i,p in enumerate(ps) if p.find('.//'+P+'tab') is not None]
 assert len(indices)==len(report['entries']);changes=[]
 for idx,t in zip(indices,report['entries']):
  a,b=nodes[idx]['start'],nodes[idx]['end'];part=raw[a:b]
  part,n=re.subn(rb'(<hp:tab\b[^>]*/>)(\d+)(</hp:t>)',lambda m:m[1]+str(t['printed']).encode()+m[3],part);assert n==1
  part=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',part,flags=re.S);changes.append((a,b,part))
 for a,b,v in reversed(changes):raw=raw[:a]+v+raw[b:]
 (Q/out).write_bytes(raw_zip_patch((Q/(name+'.hwpx')).read_bytes(),{'Contents/section1.xml':raw}))
if __name__=='__main__':main(*sys.argv[1:])
