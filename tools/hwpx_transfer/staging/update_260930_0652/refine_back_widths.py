from pathlib import Path
import sys,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=Q/'layout2_saved.hwpx'
with zipfile.ZipFile(source) as z:raw=z.read('Contents/section2.xml')
root=E.fromstring(raw);ps=list(root.iter(P+'p'));ts=list(root.iter(P+'tbl'));changes=[]
nodes=[n for n in elements(raw) if n['name']=='hp:p']
for i,widths in {33:[7100,4518,4518,4818,4516,4817,4043,4812],39:[5400,4942]+[3600]*8,40:[10600,6391,6100,6100,4243,5708]}.items():
 t=ts[i];assert sum(widths)==int(t.find(P+'sz').get('width'))
 for c in t.iter(P+'tc'):
  a=c.find(P+'cellAddr');s=c.find(P+'cellSpan');col=int(a.get('colAddr'));n=int(s.get('colSpan'))
  c.find(P+'cellSz').set('width',str(sum(widths[col:col+n])))
 anchor=next(t.iterancestors(P+'p'))
 for p in anchor.iter(P+'p'):
  for n in p.findall(P+'linesegarray'):p.remove(n)
 node=nodes[ps.index(anchor)];changes.append((node['start'],node['end'],E.tostring(anchor,encoding='UTF-8',with_tail=False)))
for a,b,v in sorted(changes,reverse=True):raw=raw[:a]+v+raw[b:]
(Q/'layout3.hwpx').write_bytes(raw_zip_patch(source.read_bytes(),{'Contents/section2.xml':raw}))
