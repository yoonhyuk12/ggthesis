from pathlib import Path
import json,re,sys,zipfile,html
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p,kjn_profile as k
O=Path('tools/hwpx_transfer/staging/full_sync_261105')
with zipfile.ZipFile(O/'resaved2.hwpx') as z:u=p.Units(z.read('Contents/section2.xml').decode(),set())
a=u.appendix_start();e=next(i for i,v in enumerate(u.items) if v['text']=='Abstract');text=p.nows(''.join(v['text'] for v in u.items[a:e]))
blocks=json.loads(Path('tools/hwpx_transfer/staging/apx1.blocks.json').read_text(encoding='utf8'))['blocks'];missing=[];counts=[]
def norm(t):return re.sub(r'\s+','',html.unescape(re.sub(r'<br\s*/?>|\*\*|`','',t))).replace('\\*','*')
for b in blocks:
 if 'runs' in b:b['text']=''.join(v['text'] for v in b['runs'])
 if b['type']=='p':
  t=norm(b['text']);actual=text.count(t)
  if not actual:missing.append(b['text'])
  counts.append({'text':b['text'],'count':actual})
 if b['type']=='table':
  for row in b['rows']:
   if len(row)>1 and re.match('[BCD]-[0-9]',row[0]):
    t=norm(row[1]);counts.append({'text':row[0]+' '+row[1],'count':text.count(t)})
    if text.count(t)!=(2 if row[0].startswith('B') else 1):missing.append(row)
(O/'survey_audit.json').write_text(json.dumps({'counts':counts,'missing':missing},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(missing,ensure_ascii=False))

