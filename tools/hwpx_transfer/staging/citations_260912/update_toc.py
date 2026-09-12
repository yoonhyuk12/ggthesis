from pathlib import Path
import sys,re,json,zipfile,html
import xml.etree.ElementTree as E
import fitz
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,owned
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def norm(t):return re.sub(r'\s+','',t).replace('·','ㆍ')
def mapping(pdf):
 doc=fitz.open(pdf); pages=[]
 for k,page in enumerate(doc):
  lines=[{'text':''.join(s['text'] for s in line['spans']),'bbox':line['bbox']} for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines']]
  footer=[re.fullmatch(r'[-–]\s*(\d+)\s*[-–]',l['text'].strip()) for l in lines if l['bbox'][1]>page.rect.height*.88]
  nums=[int(m[1]) for m in footer if m]
  pages.append({'physical':k+1,'printed':nums[0] if nums else None,'lines':lines})
 entries=json.loads((HERE.parent/'toc_260912/page_map.json').read_text(encoding='utf-8'))['entries']
 result=[];unresolved=[]
 for e in entries:
  target=norm(e['body_text'].replace('상용 솔루션 대비 첫해 도입 비용(TCO) 비교','상용 솔루션과 본 시스템의 비용 구성 가정 비교')); candidates=[]
  for p in pages:
   if p['physical']<12:continue
   ls=p['lines']
   for j in range(len(ls)):
    text=''
    for n in range(20):
     if j+n>=len(ls):break
     text+=norm(ls[j+n]['text'])
     if text==target:
      printed=p['printed']
      if printed is None and any(norm(l['text'])==norm('제1장 서론') for l in p['lines']):
       nxt=pages[p['physical']] if p['physical']<len(pages) else {}
       if nxt.get('printed')==2:printed=1
      if printed is not None:candidates.append({'physical':p['physical'],'printed':printed,'bbox':ls[j]['bbox']})
     if len(text)>len(target):break
  unique={c['physical']:c for c in candidates}
  if not unique:unresolved.append(e);continue
  selected=unique[min(unique)]
  result.append({'toc_idx':e['toc_idx'],'title':e['title'],**selected,'matches':list(unique)})
 return {'entries':result,'unresolved':unresolved,'pages':len(pages)}
def main():
 name=sys.argv[1] if len(sys.argv)>1 else 'reflowed'
 report=mapping(HERE/(name+'.pdf'))
 (HERE/(name+'_toc_map.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Mapped',len(report['entries']),'unresolved',len(report['unresolved']))
 if report['unresolved']:
  for e in report['unresolved']:print(e['toc_idx'],e['body_text'])
  return
 with zipfile.ZipFile(HERE/(name+'.hwpx')) as z:infos=z.infolist();data={n:z.read(n) for n in z.namelist()}
 raw=data['Contents/section1.xml'];nodes=[n for n in elements(raw) if n['name']=='hp:p'];ps=list(E.fromstring(raw).iter(P+'p'))
 current_indices=[i for i,p in enumerate(ps) if p.find('.//'+P+'tab') is not None]
 assert len(current_indices)==len(report['entries']),(len(current_indices),len(report['entries']))
 edits=[]
 for e,idx in zip(report['entries'],current_indices):
  node=nodes[idx];old=fragment(raw,node)
  assert '<hp:tab' in old.decode()
  # The existing final tab carries only its printed page number.
  new,n=re.subn(rb'(<hp:tab\b[^>]*/>)(\d+)(</hp:t>)',lambda m:m[1]+str(e['printed']).encode()+m[3],old)
  assert n==1,(idx,n)
  new=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',new,flags=re.S)
  edits.append((node['start'],node['end'],new))
 for start,end,new in sorted(edits,reverse=True):raw=raw[:start]+new+raw[end:]
 E.fromstring(raw);data['Contents/section1.xml']=raw
 with zipfile.ZipFile(HERE/'toc_updated.hwpx','w') as z:
  for info in infos:z.writestr(info,data[info.filename])
if __name__=='__main__':main()
