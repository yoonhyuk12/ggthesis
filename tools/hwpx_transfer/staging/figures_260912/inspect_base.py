from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as E,shutil
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=sorted((ROOT/'00. hwpx').glob('*.hwpx'),reverse=True)[0]
base=HERE/'base_snapshot.hwpx'
if not base.exists():shutil.copy2(source,base)
result={'base':str(base.relative_to(ROOT)),'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'sections':{}}
with zipfile.ZipFile(base) as z:
 for name in z.namelist():
  if name.startswith('Contents/section'):
   root=E.fromstring(z.read(name)); rows=[]
   for i,p in enumerate(root.findall(P+'p')):
    text=''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
    rows.append({'i':i,'text':text,'attrs':p.attrib})
   result['sections'][name]=rows
(HERE/'base_paras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for name,rows in result['sections'].items():
 if name.endswith('section2.xml'):
  for row in rows:
   if row['text'].startswith(('<그림','[그림')):
    print(row['i'],row['text'][:120])
