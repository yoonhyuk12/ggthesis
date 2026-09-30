from pathlib import Path
import sys,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=Q/'toc1_saved.hwpx'
with zipfile.ZipFile(source) as z:raw=z.read('Contents/section1.xml')
root=E.fromstring(raw);ps=list(root.iter(P+'p'))
p=next(p for p in ps if '<표 2-6>' in ''.join(p.itertext()))
t=p.find('.//'+P+'t');before,after=t.text.split('실효성',1)
t.text=before;line=E.Element(P+'lineBreak');line.tail='실효성'+after;t.insert(0,line)
for c in p.findall(P+'linesegarray'):p.remove(c)
node=[n for n in elements(raw) if n['name']=='hp:p'][ps.index(p)]
new=raw[:node['start']]+E.tostring(p,encoding='UTF-8',with_tail=False)+raw[node['end']:]
(Q/'toc2.hwpx').write_bytes(raw_zip_patch(source.read_bytes(),{'Contents/section1.xml':new}))
