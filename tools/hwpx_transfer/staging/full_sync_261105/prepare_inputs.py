from pathlib import Path
import sys,json,re,hashlib,subprocess
O=Path('tools/hwpx_transfer/staging/full_sync_261105');sys.path.insert(0,'tools/hwpx_transfer')
import patch_from_fresh as p
base=Path('00. hwpx/261105_1345_경기공학_건축안전_윤혁_논문.hwpx')
import zipfile
with zipfile.ZipFile(base) as z:
 for s in range(3):
  raw=z.read(f'Contents/section{s}.xml').decode(); u=p.Units(raw,set())
  (O/f'base_section{s}.json').write_text(json.dumps([dict(index=i,text=v['text'],xml=v['xml']) for i,v in enumerate(u.items)],ensure_ascii=False,indent=2),encoding='utf8')
  if s==2:
   a=u.appendix_start(); e=next(i for i,v in enumerate(u.items) if v['text']=='Abstract')
  if s==1:
   ta=next(i for i,v in enumerate(u.items) if p.nows(v['text'])=='감사의글' and '<hp:tab' not in v['xml']);te=next(i for i,v in enumerate(u.items) if p.nows(v['text'])=='논문개요' and '<hp:tab' not in v['xml'])
trans={'감사의글':{'source_hwpx':base.as_posix(),'section':1,'range':[ta,te-1],'append_red_note':''},'부록1_설문지':{'source_hwpx':base.as_posix(),'section':2,'range':[a,e-1],'replace_appendix':'부 록 — 설문지','keep_until':'부 록 — 설문지','drop_heading':True}}
(O/'transplant.json').write_text(json.dumps(trans,ensure_ascii=False,indent=2),encoding='utf8')
info={'path':base.as_posix(),'sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'md_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('01.docs').glob('*.md')}}
(O/'base_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
raw=subprocess.check_output(['git','show','ba33381:00. hwpx/건설현장 안전시설물 설치와 떨어짐 사고위험의 관계-논문전체(김정년) 261002.hwpx']);assert hashlib.sha256(raw).hexdigest()=='9bf1980a60d3a98328758e10a5b3e358dc5fbfd74e6006d3552f8424ba1dfff3';(O/'template.hwpx').write_bytes(raw)
# Reuse established bibliography extraction with present MD, not obsolete v3 JSON.
src=Path('tools/hwpx_transfer/staging/fullsync_261104/prepare_fresh.py').read_text(encoding='utf8');start=src.index('refmd=');end=src.index('shutil.copy2')
ROOT=Path.cwd();OUT=O
exec(src[start:end])
print('refs', {k:len(v) for k,v in categories.items()},'appendix range',a,e,'thanks',ta,te)
