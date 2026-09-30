"""Build toc_targets.json from the TOC entries (tab-bearing paragraphs) of the given hwpx section1."""
from pathlib import Path
import sys,json,re,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent;P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
with zipfile.ZipFile(Q/sys.argv[1]) as z:root=E.fromstring(z.read('Contents/section1.xml'))
kind='heading';out=[]
for p in root.iter(P+'p'):
 t=own(p);n=re.sub(r'\s','',t)
 if n=='표목차':kind='table'
 elif n=='그림목차':kind='figure'
 if p.find('.//'+P+'tab') is None:continue
 title=re.sub(r'\d+$','',t).rstrip();out.append(dict(body_text=title.strip(),toc_title=title,kind=kind))
(Q/'toc_targets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(out),{k:sum(o['kind']==k for o in out) for k in ('heading','table','figure')})
