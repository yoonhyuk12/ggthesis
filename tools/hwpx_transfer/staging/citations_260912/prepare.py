from pathlib import Path
import sys,re,json,zipfile,hashlib,shutil,difflib
from lxml import etree as E
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import md_to_blocks as md
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
def norm(t):return re.sub(r'\s+','',t).replace('ㆍ','·')
def units(path):
 old=md.SRC_DIR;md.SRC_DIR=path.parent
 _,bs,*_=md.parse_file(path.name);md.SRC_DIR=old
 result=[]
 for b in bs:
  if b['type']=='table':
   result.extend(b['header'])
   for row in b['rows']:result.extend(row)
  elif 'runs' in b:result.append(''.join(r['text'] for r in b['runs']))
  elif 'text' in b:result.append(b['text'])
 return result
def main():
 src=sorted((ROOT/'00. hwpx').glob('*.hwpx'),reverse=True)[0]
 base=HERE/'base.hwpx'
 if not base.exists():
  shutil.copy2(src,base)
  publish=ROOT/'00. hwpx/260912_2237_경기공학_건축안전_윤혁_논문_서지수정본.hwpx'
  assert not publish.exists();shutil.copy2(src,publish)
  (HERE/'source.json').write_text(json.dumps({'source':str(src.relative_to(ROOT)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output':str(publish.relative_to(ROOT))},ensure_ascii=False,indent=2),encoding='utf-8')
 rows=[]
 with zipfile.ZipFile(base) as z:
  for name in z.namelist():
   if re.fullmatch(r'Contents/section\d+.xml',name):
    sec=E.fromstring(z.read(name))
    for i,p in enumerate(sec.iter(P+'p')):
     rows.append({'section':name,'idx':i,'text':own(p),'parent':E.QName(p.getparent()).localname,'runs':[(r.get('charPrIDRef'),''.join(''.join(t.itertext()) for t in r.findall(P+'t'))) for r in p.findall(P+'run')]})
 (HERE/'base_paras.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 (HERE/'base_paras.txt').write_text('\n'.join(f"{r['section']}:{r['idx']}:{r['parent']} {r['text']}" for r in rows if r['text']),encoding='utf-8')
 changes=[]
 for path in sorted((ROOT/'01.docs').glob('*.md')):
  if path.name.startswith(('00_','07_','설문')):continue
  before=ROOT/'03.plan/260912_2214_MD반영_evidence/before'/path.name
  a,b=units(before),units(path)
  sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
  for kind,ai,aj,bi,bj in sm.get_opcodes():
   if kind=='equal':continue
   olds,news=a[ai:aj],b[bi:bj]
   change={'file':path.name,'kind':kind,'old':olds,'new':news}
   change['matches']=[[{'section':r['section'],'idx':r['idx'],'text':r['text'],'parent':r['parent']} for r in rows if norm(r['text'])==norm(s)] for s in olds]
   changes.append(change)
 (HERE/'md_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
 print('paragraphs',len(rows),'changes',len(changes))
 for c in changes:
  print(c['file'],c['kind'],len(c['old']),len(c['new']),[len(m) for m in c['matches']],str(c['old'])[:90])
if __name__=='__main__':main()
