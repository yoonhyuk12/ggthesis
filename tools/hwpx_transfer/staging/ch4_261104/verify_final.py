from pathlib import Path
import json,re,zipfile,html,hashlib
import fitz,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
final=ROOT/sys.argv[1]
prior=fitz.open(OUT/'resaved2.pdf');pdf=fitz.open(OUT/'final.pdf')
assert len(prior)==len(pdf)
norm=lambda s:re.sub(r'\s+','',s)
changes=[]
for i in range(len(pdf)):
 a=norm(prior[i].get_text());b=norm(pdf[i].get_text())
 if a!=b:
  assert i<11,('body page changed',i+1)
  changes.append(i+1)
m=json.loads((OUT/'toc_pages_completed.json').read_text(encoding='utf8'));want={t:v for d in m.values() for t,v in d.items()};used={};count=0
with zipfile.ZipFile(final) as z:
 assert z.testzip() is None;s=z.read('Contents/section1.xml').decode()
 for para in re.findall(r'<hp:p\b.*?</hp:p>',s,re.S):
  if '<hp:tab' not in para:continue
  before,after=para.split('<hp:tab',1);title=html.unescape(''.join(re.findall(r'<hp:t(?:\s[^>]*)?>([^<]*)',before))).strip()
  actual=re.search(r'/>([^<]*)</hp:t>',after).group(1).strip();value=want[title];i=used.get(title,0);used[title]=i+1
  expected=value[min(i,len(value)-1)] if isinstance(value,list) else value
  assert actual==str(expected),(title,actual,expected)
  count+=1
with zipfile.ZipFile(final) as z:
 raw={n:z.read(n) for n in z.namelist()}
 import xml.etree.ElementTree as E
 h=E.fromstring(raw['Contents/content.hpf']);items={e.get('id'):e.get('href') for e in h.iter() if e.tag.endswith('}item') and e.get('href','').startswith('BinData/')}
 refs=set()
 for name,v in raw.items():
  if re.match(r'Contents/section\d+\.xml',name):refs.update(re.findall(r'binaryItemIDRef="([^"]+)"',v.decode()))
 unused=set(items)-refs
 assert not unused,unused
source=json.loads((OUT/'targeted_report.json').read_text(encoding='utf8'));sha=hashlib.sha256((ROOT/source['base']).read_bytes()).hexdigest();assert sha==source['base_sha256']

r={'final':str(final.relative_to(ROOT)),'pdf_pages':len(pdf),'changed_pdf_pages':changes,'only_toc_changed':True,'unused_images':0,'toc_entries_verified':count,'base_sha256_unchanged':sha,'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
(OUT/'final_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
