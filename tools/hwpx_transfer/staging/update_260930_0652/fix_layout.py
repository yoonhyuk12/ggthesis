from pathlib import Path
import sys,zipfile
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=sys.argv[1];output=sys.argv[2]
with zipfile.ZipFile(Q/source) as z:raw=z.read('Contents/section2.xml')
root=E.fromstring(raw);tables=list(root.iter(P+'tbl'));table=tables[26]
assert '<표 5-1>' in ''.join(table.itertext())
widths=[4043,9299,4300,4300,4300,4300,4300,4300]
assert sum(widths)==int(table.find(P+'sz').get('width'))
for cell in table.iter(P+'tc'):
 a=cell.find(P+'cellAddr');span=cell.find(P+'cellSpan');c=int(a.get('colAddr'));n=int(span.get('colSpan'))
 cell.find(P+'cellSz').set('width',str(sum(widths[c:c+n])))
anchor=next(table.iterancestors(P+'p'))
for p in anchor.iter(P+'p'):
 for n in p.findall(P+'linesegarray'):p.remove(n)
if '--split' in sys.argv:
 table.set('pageBreak','TABLE');table.set('repeatHeader','1');table.find(P+'pos').set('treatAsChar','0')
 for row in table.findall(P+'tr')[:2]:
  for cell in row.findall(P+'tc'):cell.set('header','1')
idx=list(root.iter(P+'p')).index(anchor);node=[n for n in elements(raw) if n['name']=='hp:p'][idx]
updated=raw[:node['start']]+E.tostring(anchor,encoding='UTF-8',with_tail=False)+raw[node['end']:]
(Q/output).write_bytes(raw_zip_patch((Q/source).read_bytes(),{'Contents/section2.xml':updated}))
print('Adjusted table5-1 widths',widths,'split','--split' in sys.argv)
