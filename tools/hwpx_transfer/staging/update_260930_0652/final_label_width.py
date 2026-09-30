from pathlib import Path
import sys,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=Q/'final_saved.hwpx'
with zipfile.ZipFile(source) as z:raw=z.read('Contents/section2.xml')
root=E.fromstring(raw);ps=list(root.iter(P+'p'));table=list(root.iter(P+'tbl'))[39]
widths=[5800,4542]+[3600]*8
assert sum(widths)==int(table.find(P+'sz').get('width'))
for c in table.iter(P+'tc'):
 a=c.find(P+'cellAddr');s=c.find(P+'cellSpan');col=int(a.get('colAddr'));n=int(s.get('colSpan'))
 c.find(P+'cellSz').set('width',str(sum(widths[col:col+n])))
anchor=next(table.iterancestors(P+'p'))
for p in anchor.iter(P+'p'):
 for n in p.findall(P+'linesegarray'):p.remove(n)
node=[n for n in elements(raw) if n['name']=='hp:p'][ps.index(anchor)]
raw=raw[:node['start']]+E.tostring(anchor,encoding='UTF-8',with_tail=False)+raw[node['end']:]
(Q/'final2.hwpx').write_bytes(raw_zip_patch(source.read_bytes(),{'Contents/section2.xml':raw}))
