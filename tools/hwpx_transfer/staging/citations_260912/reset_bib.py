from pathlib import Path
import sys,zipfile,re,json
from lxml import etree as E
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'intro_260912'))
from apply_intro import elements,fragment,raw_zip_patch,owned
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
src=(HERE/'final.hwpx').read_bytes()
with zipfile.ZipFile(HERE/'final.hwpx') as z:raw=z.read('Contents/section2.xml')
ps=[n for n in elements(raw) if n['name']=='hp:p'];ep=list(E.fromstring(raw).iter(P+'p'));active=False;edits=[]
for n,p in zip(ps,ep):
 t=owned(p)
 if t=='참고문헌':active=True
 if t.startswith('부   록'):active=False
 if active:
  frag=fragment(raw,n);new=re.sub(rb'<hp:linesegarray\b.*?</hp:linesegarray>',b'',frag,flags=re.S)
  if new!=frag:edits.append((n['start'],n['end'],new))
for a,b,v in sorted(edits,reverse=True):raw=raw[:a]+v+raw[b:]
(HERE/'bib_reflow.hwpx').write_bytes(raw_zip_patch(src,{'Contents/section2.xml':raw}))
print('Bibliography paragraphs with layout cache reset:',len(edits))
