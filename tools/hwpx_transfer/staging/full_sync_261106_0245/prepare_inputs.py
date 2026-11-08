"""Main-only input preparation; execute from repository root."""
from pathlib import Path
import sys,json,re,hashlib,shutil
O=Path(__file__).parent
sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p
info=json.loads((O/'base_info.json').read_text(encoding='utf8'))
base=Path(info['base'])
assert hashlib.sha256(base.read_bytes()).hexdigest()==info['sha256'], 'Baseline changed since snapshot'
units={s:json.loads((O/f'base_section{s}.json').read_text(encoding='utf8')) for s in range(3)}
u1=units[1];u2=units[2]
ta=next(i for i,v in enumerate(u1) if p.nows(v['text'])=='감사의글' and '<hp:tab' not in v['xml'])
te=next(i for i,v in enumerate(u1) if p.nows(v['text'])=='논문개요' and '<hp:tab' not in v['xml'])
a=next(i for i,v in enumerate(u2) if p.nows(v['text']).startswith('부록(도입현장)'))
e=next(i for i,v in enumerate(u2) if v['text']=='Abstract')
trans={'감사의글':{'source_hwpx':base.as_posix(),'section':1,'range':[ta,te-1],'append_red_note':''},'부록1_설문지':{'source_hwpx':base.as_posix(),'section':2,'range':[a,e-1],'replace_appendix':'부 록 — 설문지','keep_until':'부 록 — 설문지','drop_heading':True}}
(O/'transplant.json').write_text(json.dumps(trans,ensure_ascii=False,indent=2),encoding='utf8')
# Preserve baseline metadata and dump files produced by the main context.
mdthanks=Path('01.docs/감사의_글.md').read_text(encoding='utf8')
mdparas=[re.sub(r'\*\*|`','',x.strip()) for x in re.split(r'\n\s*\n',mdthanks) if x.strip() and not x.lstrip().startswith(('#','>','---'))]
baseparas=[v['text'] for v in u1[ta+1:te] if v['text'].strip()]
assert list(map(p.nows,mdparas))==list(map(p.nows,baseparas)), 'Thanks MD differs: review before transplant'
template=Path('tools/hwpx_transfer/staging/full_sync_261105/template.hwpx')
assert hashlib.sha256(template.read_bytes()).hexdigest()=='9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3'
shutil.copy2(template,O/'template.hwpx')
# Established current-bibliography filter, excluding editorial history.
src=Path('tools/hwpx_transfer/staging/fullsync_261104/prepare_fresh.py').read_text(encoding='utf8')
start=src.index('refmd=');end=src.index('shutil.copy2')
ROOT=Path.cwd();OUT=O
exec(src[start:end])
print('refs', {k:len(v) for k,v in categories.items()},'appendix range',a,e,'thanks',ta,te,'thanks MD agrees')
