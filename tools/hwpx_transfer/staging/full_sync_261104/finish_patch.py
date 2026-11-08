from pathlib import Path
import sys,json,re,zipfile,hashlib
sys.path.insert(0,'tools/hwpx_transfer');import patch_from_fresh as p,kjn_profile as k
O=Path('tools/hwpx_transfer/staging/full_sync_261104')
pt=p.Patcher(str(O/'patched.hwpx'),str(O/'fresh.hwpx'),[],None)
pt.s1=p.replace_literal_text(pt.s1,'연구 가설','연구가설',2)
pt.s1=p.LINESEG_RE.sub('',pt.s1) if False else pt.s1
# Only two changed TOC paragraphs lose cache.
u=p.Units(pt.s1,set())
for v in u.items:
 if '<hp:tab' in v['xml'] and ('연구 문제 및 연구가설' in v['text'] or '<표 4-2>' in v['text']):pt.s1=pt.s1.replace(v['xml'],p.LINESEG_RE.sub('',v['xml']),1)
# The patcher's block alignment removed the blank before a changed section title: restore baseline blank and heading layout.
base=json.loads((O/'base_section2.json').read_text(encoding='utf8'));u=p.Units(pt.s2,set())
b=next(i for i,v in enumerate(base) if v['text']=='제 2 절 연구 문제 및 연구 가설');v=next(v for v in u.items if v['text']=='제 2 절 연구 문제 및 연구가설')
heading=p.replace_literal_text(base[b]['xml'],'연구 가설','연구가설',1);heading=p.LINESEG_RE.sub('',heading)
pt.s2=pt.s2.replace(v['xml'],base[b-1]['xml']+heading,1)
pt.write(str(O/'ready.hwpx'))
# Image byte matches use real package references, not integer IDs.
from lxml import etree as E
with zipfile.ZipFile(O/'ready.hwpx') as z:
 manifest=E.fromstring(z.read('Contents/content.hpf'));items={e.get('id'):e.get('href') for e in manifest.iter() if e.tag.endswith('}item')}
 r=E.fromstring(z.read('Contents/section2.xml'));pics=[]
 for pic in r.findall('.//{'+k.NS['hp']+'}pic'):
  img=pic.find('.//{'+k.NS['hc']+'}img');bid=img.get('binaryItemIDRef');data=z.read(items[bid]);pics.append(hashlib.sha256(data).hexdigest())
 mappings=json.loads((O/'images.json').read_text(encoding='utf8'))['mapping'];imagecheck=[{'caption':v['caption_prefix'],'match':hashlib.sha256(Path(v['source']).read_bytes()).hexdigest() in pics} for v in mappings]
 (O/'image_checks.json').write_text(json.dumps(imagecheck,ensure_ascii=False,indent=2),encoding='utf8');print(imagecheck)
