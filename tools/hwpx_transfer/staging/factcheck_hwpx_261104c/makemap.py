from pathlib import Path
import re,json
s=Path('tools/hwpx_transfer/staging/factcheck_hwpx_261104c')
b=Path('03.plan/261104_1937_부분뒷받침_잔여반영_hwpx반입_코덱스브리프.md').read_text(encoding='utf-8')
r=json.loads((s/'paras.json').read_text(encoding='utf-8'))
changes=[];m={}
for old,new in re.findall(r'`([^`]+)` → `([^`]+)`',b):
 if old.startswith('…'):old=old.lstrip('…');new=new.lstrip('…')
 hits=[x for x in r if old in x['text']]
 entry={'old':old,'new':new,'hits':hits,'status':'applied' if hits else 'held'}
 if hits:m[old]=new
 changes.append(entry)
# caption twice by design; unique paragraph keys separately to satisfy preflight
old='<표 3-5> 정·오탐 라벨링 기준(혼동행렬 정의; 이기수, 2024)'
new='<표 3-5> 정·오탐 라벨링 기준'
# raw key matches two occurrences, supported; retain and document
for x in r:
 if x['section']=='Contents/section2.xml' and x['i'] in [1788,1789,1790]:
  old=x['text'].split(' ',2)[0]+' '+x['text'].split(' ',2)[1]
  n=int(old[1:3]);new=f'[{n-1:02d}]'+old[4:]
  m[old]=new;changes.append({'old':old,'new':new,'hits':[x],'status':'applied'})
(s/'map.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
(s/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
md='\n'.join(p.read_text(encoding='utf-8') for p in Path('01.docs').glob('*.md'))
for x in changes:print(x['status'],len(x['hits']),x['old'][:65], 'MDnew=',x['new'] in md)
