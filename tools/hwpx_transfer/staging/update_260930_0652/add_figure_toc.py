from pathlib import Path
from copy import deepcopy
import sys,zipfile,json
from lxml import etree as E
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q.parent/'intro_260912'))
from apply_intro import elements,raw_zip_patch
P='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
source=Q/'toc2_saved.hwpx'
with zipfile.ZipFile(source) as z:
 raw=z.read('Contents/section1.xml');body=E.fromstring(z.read('Contents/section2.xml'))
def own(p):return ''.join(''.join(t.itertext()) for r in p.findall(P+'run') for t in r.findall(P+'t'))
caption=next(own(p).strip() for p in body.iter(P+'p') if own(p).strip().startswith('<그림 1-1>'))
root=E.fromstring(raw);ps=list(root.iter(P+'p'))
template=next(p for p in ps if own(p).startswith('<그림 3-1>'))
p=deepcopy(template);p.set('id','3100000000')
t=p.find('.//'+P+'t');t.text=caption
for n in p.findall(P+'linesegarray'):p.remove(n)
t.find(P+'tab').tail='5'
node=[n for n in elements(raw) if n['name']=='hp:p'][ps.index(template)]
new=raw[:node['start']]+E.tostring(p,encoding='UTF-8',with_tail=False)+raw[node['start']:]
(Q/'toc3.hwpx').write_bytes(raw_zip_patch(source.read_bytes(),{'Contents/section1.xml':new}))
targets=json.loads((Q/'toc_targets.json').read_text(encoding='utf-8'))
assert not any(t['body_text']==caption for t in targets)
idx=next(i for i,t in enumerate(targets) if t['kind']=='figure')
targets.insert(idx,dict(body_text=caption,toc_title=caption,kind='figure'))
(Q/'toc_targets.json').write_text(json.dumps(targets,ensure_ascii=False,indent=2),encoding='utf-8')
print('Added',caption,'targets',len(targets))
