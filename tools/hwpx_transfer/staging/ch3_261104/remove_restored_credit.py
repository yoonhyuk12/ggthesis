"""Main-only: preserve user's deletion below figure3-1."""
from pathlib import Path
import sys,zipfile,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import patch_from_fresh as p
src=ROOT/'00. hwpx/261104_0815_경기공학_건축안전_윤혁_논문.hwpx'
with zipfile.ZipFile(src) as z:
 infos=z.infolist();raw={i.filename:z.read(i.filename) for i in infos}
s=raw['Contents/section2.xml'].decode();u=p.Units(s,set())
cap=next(i for i,x in enumerate(u.items) if x['text'].startswith('<그림 3-1>'))
target=next(x for x in u.items[cap+1:cap+7] if x['text']=='자료: 연구자 작성.')
assert s.count(target['xml'])==1
raw['Contents/section2.xml']=s.replace(target['xml'],'',1).encode()
with zipfile.ZipFile(OUT/'credit_preserved.hwpx','w') as z:
 for i in infos:z.writestr(i,raw[i.filename],compress_type=i.compress_type)
print('Removed exactly 1 restored credit below figure3-1; all other entries unchanged')
