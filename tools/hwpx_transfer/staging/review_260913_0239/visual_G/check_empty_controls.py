import zipfile,xml.etree.ElementTree as E,json
from pathlib import Path
b=Path('tools/hwpx_transfer/staging/review_260913_0239'); ns={'h':'http://www.hancom.co.kr/hwpml/2011/paragraph'}
ids={str(x['id']) for x in json.loads((b/'visual_G/header_fix_plan.json').read_text(encoding='utf-8'))}; result=[]
with zipfile.ZipFile(b/'final.hwpx') as z:
 root=E.fromstring(z.read('Contents/section2.xml'))
 for t in root.findall('.//h:tbl',ns):
  if t.get('id') not in ids: continue
  tags={e.tag.split('}')[-1] for r in t.findall('h:tr',ns)[1:3] for e in r.iter()}
  result.append({'id':t.get('id'),'removed_rows_descendant_tags':sorted(tags)})
(b/'visual_G/empty_row_controls.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
