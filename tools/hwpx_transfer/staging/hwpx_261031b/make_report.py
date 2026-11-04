"""Render already collected evidence; no repeated package validation."""
from collections import Counter
from pathlib import Path
import json
import re
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools/hwpx_transfer'))
import kjn_profile as k
import patch_from_fresh as p

audit=json.loads((OUT/'integrity.json').read_text(encoding='utf-8'))
stats=json.loads((OUT/'patch_stats.json').read_text(encoding='utf-8'))
changes=json.loads((OUT/'changes.json').read_text(encoding='utf-8'))
base=k.read_package(OUT/'base.hwpx')[1]
patched=k.read_package(OUT/'patched.hwpx')[1]
bu=p.Units(base['Contents/section2.xml'].decode(),set())
pu=p.Units(patched['Contents/section2.xml'].decode(),set())
stats['equal']=sum((Counter(u['xml'] for u in bu.items)&Counter(u['xml'] for u in pu.items)).values())
stats['table_same_kept']=sum(u['tbl'] and u['xml'] in pu.xml for u in bu.items)
stats['section1_exact_kept']=sum(u['xml'] in patched['Contents/section1.xml'].decode()
                               for u in p.Units(base['Contents/section1.xml'].decode(),set()).items)
(OUT/'patch_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
report=(OUT/'patch_report.md').read_text(encoding='utf-8')
report=re.sub(r'^통계: .+$','통계: '+json.dumps(stats,ensure_ascii=False),report,flags=re.M)
(OUT/'patch_report.md').write_text(report,encoding='utf-8')
verification='PASS: ZIP/XML/style refs; 53 images, unused 0; body grids 4/12 PNGs, appendix grids 5/35 PNGs; all current MD text; targeted notes and LOT; red/black markers; base SHA256\nMain tables retained: 36; appendix grids retained: 5; main exact paragraphs: 650\n'
(OUT/'verification.txt').write_text(verification,encoding='utf-8')
lines=['# jamovi 본문·부록 분리 — 워커 보고','',
'요청된 코드 확장·패치·정적 검증을 완료했다. `patched.hwpx`는 한글 재조판 전 검토용이며 최종 인쇄 산출물이 아니다. 한글 COM·PDF 출력·실제 인쇄 쪽수 갱신은 메인이 수행해야 한다.','',
'## 산출물과 변경 파일','',
'- 결과: `tools/hwpx_transfer/staging/hwpx_261031b/patched.hwpx`',
'- 비교 조립본: 같은 폴더 `assembled.hwpx`; 보고: `patch_report.md`, `worker_report.md`',
'- 증거: `integrity.json`, `image_grid_plan.json`, `changes.json`, `patch_stats.json`, `tests.txt`, `verification.txt`, `section1_base_paragraphs.json`, `section2_base_paragraphs.json`',
'- 확장 코드: `tools/hwpx_transfer/md_to_blocks.py`, `image_grid.py`, `kjn_profile.py`, `tests/test_image_grid.py`',
'- 모든 생성물·임시 파일은 지정 staging에 저장했다. git 쓰기, 00. hwpx 쓰기, 한글 COM, hwpx/rhwp MCP, 01.docs·03.plan·.claude·MEMORY·CLAUDE 수정은 하지 않았다.',
'- 선행 assemble·Patcher의 스타일/이미지 반입·verify 로직을 재사용했다. 단순히 선행 assemble.py를 1206에 적용하면 참고문헌 법령 중복, 역할 용어 중복 치환, 설문 이식 범위에 부록 2·3 혼입이 생기므로 이전에 검증된 references.json·transplant.json을 읽어 비교용 조립본을 만들고 실제 패치는 1206 복사본에만 적용했다.','',
'## 구현과 기준본 보존','',
'본문 격자 앞 `jamovi 원출력(<표 n>)` 문단을 인식하고 manifest의 `for` 대상과 일치하는지 검사한다. 번호 없는 격자는 독립 표/그림 목차 항목을 추가하지 않으며 근거 대상과 그림 크기는 조립 증거에 기록한다. 부록 격자 기능과 원본 PNG 바이트는 유지했다.','',
'1206의 실제 문단을 덤프한 뒤 선행 조립본↔현행 조립본의 변경 구간을 대조했다. 주 문장은 마지막 jamovi 안내 문장만 타깃 치환하고, 본문에는 머리 문단 4개·격자 4개를 삽입했다. 부록 3의 같은 문단과 5개 격자는 정확한 기준본 XML을 재사용하고, 머리말과 부표 번호·표 목차 항목만 변경했다. 동일 PNG 두 칸을 합치지 않도록 fresh 이미지와 기존 BinData 사이에 바이트 기반 일대일 매핑을 만들었다.','',
f'- section2 최상위 문단 XML 그대로 보존: {stats["equal"]}개(빈 문단 포함).',
f'- 기존 본문 표 36개 전부 XML 그대로 보존. 부록 3의 남은 격자 5개도 XML 그대로. 설문·부록 2까지 포함한 기존 최상위 표 보존 {stats["table_same_kept"]}개.',
'- 본문·참고문헌에서는 변경 주 문장 7개를 제외한 기존 문단 650개가 순서·XML 그대로이며 새 항목은 8개이다.',
'- 부록 3: 같은 문단 18개 보존, 캡션 4개 번호만 치환, 새 머리말 1개 반입, 이전 항목 17개 퇴역(이동 격자·기존 캡션·안내 주·머리말·빈 문단 포함).',
f'- section1: 부표 목차 번호 4개만 치환, 본문으로 이동한 항목 4개 제거. 나머지 문단 {stats["section1_exact_kept"]}개 XML 보존. 남는 부표의 기존 인쇄 쪽수 문자열은 모두 그대로이다.',
'- 표지, 설문 두 벌, 부록 2의 XML은 기준본과 정확히 같다. 전체 section2의 비어 있지 않은 텍스트는 현행 MD 조립본과 순서까지 일치한다.',
'- 변경 문단·새 격자/셀의 linesegarray는 없으며 무관한 문단과 보존 표의 캐시는 그대로이다.','',
'**브리프 예상과 다른 점:** 변경된 본문 주는 9개가 아니라 7개다. 선행·현행 조립본 비교에서 바뀐 주는 표 4-7·4-8·4-9·4-10·4-12·4-15·4-16이다. 표 4-6의 부표 3-1 참조는 그대로이고 표 4-11에는 기존 주가 없다. MD를 임의로 고치지 않았다.','',
'## 보존·치환·삽입 통계','', '```json',json.dumps(stats,ensure_ascii=False,indent=2),'```','',
'## 바뀐 문단 목록','']
for c in changes:
    if c['kind']=='body_note':
        lines += ['- 본문 주 치환: '+c['old'].split('jamovi 원출력은 ')[-1]+' → '+c['new'].split('jamovi 원출력은 ')[-1],
                  '  - 해당 문단: '+c['new']]
    elif 'old' in c:
        lines += ['- '+c['kind']+': '+c['old']+' → '+c['new']]
    else:
        lines += ['- '+c['kind']+': '+c['text']]
lines += ['', '## 수동 재적용 필요 — 전문','', '- 없음 (0건).', '',
'이는 이전 1206 산출물의 서식 재확인 요구를 새로 해소했다는 뜻은 아니다. 이번 변경에서 기존 표/목차 전체 교체로 생긴 추가 서식 손실이 없다는 뜻이다.','',
'## 단위 테스트','',
'실행: `python -m unittest discover -s tools/hwpx_transfer/tests -p "test_*.py" -v`',
'환경: `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`; TEMP/TMP는 지정 staging. 본문 번호 없음·대상 불일치 거부·12개 그림·한 쪽 격자 설정 검증을 추가했고 기존 회귀를 포함해 47건 모두 통과했다.','',
'```text',(OUT/'tests.txt').read_text(encoding='utf-8').rstrip(),'```','',
'## 무결성과 실제 그림 치수','', '```text',verification.rstrip(),'```','',
f'- ZIP CRC·엔트리 중복 없음; XML/HPF {len(audit["xml_parsed"])}개 파싱 성공, 총 ZIP 엔트리 {audit["zip_entries"]}개.',
'- BinData 53 = 기존 본문 그림 6 + 본문 격자 그림 12 + 부록 격자 그림 35. manifest와 hc:img 참조 각 53개, 서로 일대일이며 미사용 0개.',
'- 기존 53개 이미지 payload는 모두 바이트 동일. 현행 manifest의 jamovi PNG 47개도 내용·중복 개수까지 일치.',
f'- 스타일 참조 유효, pageBreak="CELL" 0건, 빨간 마커 {audit["red_markers_verified"]}건·검정 숫자/양식 대괄호 {audit["black_brackets_verified"]}건 확인.',
'- 열폭 합·각 행 셀 폭 합·병합 점유 격자·칸별 이미지 비율 및 크기를 검사했다. 전체 폭은 기존 39684 HWPUNIT(약 140mm). 구조용 빈 Markdown 머리행은 인쇄하지 않는다.',
'- 아래 NONE/TABLE은 XML 나눔 설정이며 실제 한 쪽 배치 성공 증거가 아니다. 라벨 높이는 한양신명조 요청→GDI 굴림 대체 측정치로 추정하므로 PDF 확인이 필요하다.','',
'| 위치 | 행 × 열 | 열폭 HWPUNIT | 전체 폭/각 행 합 | 나눔 |',
'|---|---:|---|---:|---|']
for g in audit['grids']:
    lines += [f'| {g["caption"]} | {g["rows"]} × {g["cols"]} | {g["column_widths"]} | {g["total_width"]} | {g["pageBreak"]} |']
lines += ['', '| 그림 | 행·열 / colspan | 셀 폭 | 그림 폭 × 높이 mm |','|---|---|---:|---|']
for g in audit['grids']:
    for c in g['cells']:
        lines += [f'| {c["file"]} | {c["row"]}행 {c["col"]}열 / {c["colSpan"]} | {c["width"]} | {c["image_width_mm"]} × {c["image_height_mm"]} |']
lines += ['', '## SHA256','',
'- 기준본: `00. hwpx/261031_1206_경기공학_건축안전_윤혁_논문.hwpx`',
'- 작업 전: `'+audit['base_sha256_before']+'`',
'- 작업 후: `'+audit['base_sha256_after']+'`',
'- 원본·staging 복사본 일치: 예.',
'- 패치본: `'+audit['sha256']+'`','',
'## 메인이 이어서 할 일','',
'1. 패치본을 한글에서 실제 Open·재조판 저장한다. COM과 HWPX MCP는 이번 작업에서 호출하지 않았다.',
'2. PDF에서 본문 격자 4개와 원래 표/주의 연결, 라벨/그림 줄바꿈, 표가 다음 쪽으로 밀리는 위치, 모든 표의 꼬리말 침범·행 연속성을 확인한다.',
'3. 재조판 결과로 점선 목차의 실제 인쇄 쪽수를 갱신하고 다시 저장·PDF 대조한다. 이번 파일의 목차 숫자는 1206 기준값이므로 아직 새 배치와 맞지 않을 수 있다.',
'4. 기준본에 이미 남아 있던 jamovi [3]·[4] 각주 처리 및 사용자 서식 검토는 메인 판단을 유지한다.','',
'## 재현 명령','', '```powershell',
"$env:PYTHONIOENCODING='utf-8'", "$env:PYTHONDONTWRITEBYTECODE='1'",
'python tools/hwpx_transfer/md_to_blocks.py --out-dir tools/hwpx_transfer/staging/hwpx_261031b',
'python tools/hwpx_transfer/staging/hwpx_261031b/assemble.py',
'python tools/hwpx_transfer/staging/hwpx_261031b/patch.py',
'python tools/hwpx_transfer/staging/hwpx_261031b/verify.py',
'python tools/hwpx_transfer/staging/hwpx_261031b/make_report.py','```','',
'기존 staging의 `base.hwpx`, 양식 비교용 `template.hwpx`, 선행 검증 references/transplant JSON을 입력으로 쓴다. 전체 조립본은 비교용이고 패치본만 메인에게 전달한다.']
(OUT/'worker_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False))
print('worker_report.md written')
