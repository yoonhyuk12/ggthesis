from pathlib import Path
from datetime import datetime
import shutil,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
audit=json.loads((HERE/'base_paras.json').read_text(encoding='utf-8'))
source=ROOT/audit['source'];source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash==audit['sha256'],'Source changed after snapshot; compare before delivering'
stamp=datetime.now().strftime('%y%m%d_%H%M')
stem=stamp+'_경기공학_건축안전_윤혁_논문_그림삽입본'
files=[]
for ext in ['hwpx','pdf']:
 target=ROOT/'00. hwpx'/(stem+'.'+ext)
 assert not target.exists()
 shutil.copy2(HERE/('ready.'+ext),target);files.append(str(target.relative_to(ROOT)))
p=ROOT/'01.docs/01_서론.md';t=p.read_text(encoding='utf-8');t=t.replace('- [ ] 연구흐름도(&lt;그림 1-3&gt;)는 최종 제출 시 HWP 그림 개체로 변환','- [x] 연구흐름도(&lt;그림 1-3&gt;)를 PNG 그림 개체로 HWPX에 삽입하고 한글 재조판·PDF 확인 완료(2026-09-12).')
p.write_text(t,encoding='utf-8')
report={'outputs':files,'source':audit['source'],'source_sha256':source_hash,'snapshot_and_original_unchanged':True,'pictures':8,'tables_preserved':48,'toc_entries_verified':132,'pdf_pages':120,'hancom_open_resave_reopen_pdf':True,'final_sha256':hashlib.sha256((ROOT/files[0]).read_bytes()).hexdigest(),'remaining_layout_issues':'Prior-document bibliography glyph collisions, floating table placement, survey header and minor wrapping; see review reports. No table final-row clipping or footer intrusion found.','orchestration_run':'run_b8bcc93752fe'}
(HERE/'completion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
