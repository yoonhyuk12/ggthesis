from pathlib import Path
import difflib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
TOOL=ROOT/'tools/hwpx_transfer'
a=json.loads((OUT/'integrity.json').read_text(encoding='utf-8'))
stats=json.loads((OUT/'patch_stats.json').read_text(encoding='utf-8'))
patch=(OUT/'patch_report.md').read_text(encoding='utf-8')
manual=patch.split('## 수동 재적용 필요\n',1)[1].split('\n## 로그',1)[0].strip()
tests=(OUT/'tests.txt').read_text(encoding='utf-8-sig')
verification=(OUT/'verification.txt').read_text(encoding='utf-8-sig')
code_paths=['md_to_blocks.py','kjn_profile.py','patch_from_fresh.py','image_grid.py','tests/test_image_grid.py']
diff=[]
for name in code_paths:
    before=OUT/(name+'.before')
    old=before.read_text(encoding='utf-8').splitlines(True) if before.exists() else []
    new=(TOOL/name).read_text(encoding='utf-8').splitlines(True)
    diff.extend(difflib.unified_diff(old,new,fromfile='before-worker/'+name,tofile='tools/hwpx_transfer/'+name))
(OUT/'worker_changes.diff').write_text(''.join(diff),encoding='utf-8')
assert (OUT/'blocks_to_hwpx.py.before').read_bytes()==(TOOL/'blocks_to_hwpx.py').read_bytes()

report=['# HWPX 반입 워커 보고','',
'워커 범위의 패치·코드·정적 검증은 완료했다. `patched.hwpx`는 한글 재조판 전 스크래치이며 최종 한글 산출물이 아니다. 한글 COM·PDF 출력·인쇄 쪽수 갱신은 실행하지 않았다.','',
'## 산출물과 변경 코드','',
'- 패치본: `tools/hwpx_transfer/staging/hwpx_261031/patched.hwpx`',
'- 조립 비교본: 같은 디렉터리 `assembled.hwpx`; 보고: `report.md`, `patch_report.md`',
'- 증거: `tests.txt`, `verification.txt`, `integrity.json`, `image_grid_plan.json`, `base_paragraphs.json`, `survey_targets.json`, `worker_changes.diff`',
'- 코드 변경: `tools/hwpx_transfer/md_to_blocks.py`, `kjn_profile.py`, `patch_from_fresh.py`; 신설 `image_grid.py`, `tests/test_image_grid.py`',
'- 작업 시작 전 도구 수정분은 `.before`로 보존했다. `blocks_to_hwpx.py`는 워커가 수정하지 않았으며 시작 시 바이트와 동일하다. 기존 table_merges 관련 수정은 유지했다.',
'- git 쓰기, `00. hwpx/` 쓰기, `01.docs/`·`03.plan/`·`.claude/` 수정, 한글 COM, HWPX MCP를 실행하지 않았다. 산출물·임시 파일은 지정 staging 안에만 썼다.','',
'## MD 반입과 사용자 편집 보존','',
'기본 patch_from_fresh는 부록 뒤를 통째로 보존하고 BinData를 복사하지 않으며, 제4장 재구성 22구간을 수동 처리로 남겼다. 기본 동작을 유지한 채 새 부록·이미지 반입과 과거 MD 검증 기반 구조 반입 옵션을 추가했다.',
'기준본 본문과 표의 텍스트가 `93aa8fb` 시점 MD를 조립한 `previous/body.xml`에 모두 존재함을 공백 정규화 후 확인했다. 이 검증에서 사용자 고유 추가 텍스트는 0건이었다. 불일치가 있으면 새 구조 반입 경로는 ValueError로 중단한다. `base_vs_previous_unknown.json`과 `base_vs_previous_tables.json`은 모두 빈 배열이다.',
f'- 본문·참고문헌의 기존 최상위 항목 {stats["equal"]}개는 정확한 XML을 재사용했다. 이 가운데 내용 동일 표 {a["unchanged_main_tables_exact_XML"]}개는 병합·열폭·정렬·캐시를 포함한 기준본 XML이 그대로다.',
f'- 현행 MD의 변경·새 항목 {stats["replace_fresh"]}개를 반입했다(표·그림 앵커 포함 최상위 항목 기준). 부록 2·3 최상위 문단은 추가 {stats["insert"]}개다.',
f'- 본문·참고문헌의 비어 있지 않은 항목 {a["main_body_nonempty_units"]}개는 현행 조립본과 순서까지 일치한다. 새 부록 2·3의 텍스트도 현행 MD 조립본과 일치한다.',
f'- 설문 두 벌은 {a["survey_replacement_occurrences"]}회 타깃 치환만 했다. 전체 설문 XML을 기준본에 같은 치환만 적용한 기대값과 대조해 일치했다. 표지 제목 2곳도 타깃 치환했다.',
'- 변경 문단과 표 앵커 캐시만 제거했다. 변경된 표 셀의 형제 셀 캐시는 보존하는 타깃 치환 회귀 테스트를 추가했다. 새 그림 표에는 linesegarray가 없다.',
'- 참고문헌 v3 JSON은 10월 8일 스냅샷이라 jamovi 서지가 빠져 있었다. 최신 기준본의 7개 분류를 재사용하고 현행 MD에 추가된 산업안전보건법 시행령 항목만 더해 과거 서지로 되돌아가지 않게 했다.',
'- `images.json`의 오래된 연구 모형 경로를 그대로 쓰지 않았다. 현행 MD가 명시한 `figure_4-1_research_model_261029.png`를 사용했고 바이트 일치를 검사했다. 연구 흐름도도 현행 연결 이미지로 갱신했다. 기존 이미지 4개는 바이트 그대로이며 2개는 갱신된 내용으로 같은 6개 위치에 반입했다.',
'- 그림과 같은 바이트인 부록 PNG가 두 칸 존재한다. 칸별 그림 47개 규칙을 지키기 위해 서로 다른 입력 item은 중복 제거하지 않았다.',
'- `00_목차.md`의 표·부표 캡션 51개가 본문과 표 목차에 모두 존재한다. 부록 2·3 목차 항목도 포함된다. 인쇄 쪽수는 임시 0이며 실제 쪽수로 갱신해야 한다.','',
'## 단위 테스트와 무결성 검사','',
'명령: `python -m unittest discover -s tools/hwpx_transfer/tests -p "test_*.py" -v` (PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1, TEMP/TMP는 지정 staging). 기존 김정년 조립 회귀 21건을 포함하여 전체 46건 통과했다.','',
'```text',tests.strip(),'```','',
'```text',verification.strip(),'```','',
f'- ZIP 엔트리 {a["zip_entries"]}개, 모든 XML/HPF {len(a["xml_parsed"])}개 파싱 성공, ZIP CRC·중복 경로·mimetype 저장 형식 확인.',
'- BinData 53개 = 기존 그림 위치 6 + 부록 그림 47. manifest 53개와 실제 hc:img 참조 53개가 일치한다. 모든 부록 PNG는 원본 바이트 그대로다.',
f'- section 내 charPr·paraPr·borderFill·style 참조 모두 유효. pageBreak="CELL" 0건. 빨강 마커 {a["red_markers_verified"]}건 및 검정 숫자·양식 대괄호 {a["black_numeric_or_form_brackets_verified"]}건 확인.',
'- `git diff --check`는 변경된 추적 코드에서 오류 없이 종료했다.','',
'## 부록 3 표별 폭 정합','',
'아래 행 수는 Markdown의 빈 구조용 머리행을 제외한 실제 그림 행 수다. 한 행의 빈 후속 칸은 앞 그림 칸에 가로 병합했다. 예를 들어 3-3의 134.2mm 그림은 2열을 차지하고 3-4의 첫 두 행 둘째 그림은 2·3열을 차지한다. 원본 그림의 행·수치·픽셀은 전혀 자르지 않았다.',
'전체 폭은 기존 표 관례 39684 HWPUNIT(약 140mm)을 따랐다. 열폭 합·각 행의 셀 폭 합·병합 점유 격자의 중복/누락을 검사했고 모두 일치했다. 일반 좌우 여백은 각 142 HWPUNIT이며 3-5만 0이다. 3-5 그림은 143.2mm에서 실제 본문 폭 약 140mm로 비례 축소했다.','',
'| 부표 | 행 × 열 | 열폭 HWPUNIT | 전체 폭 / 각 행 폭 합 | 쪽 나눔 |',
'|---|---:|---|---:|---|']
for g in a['appendix3_grids']:
    report.append(f'| {g["caption"].split(">")[0]+">"} | {g["rows"]} × {g["cols"]} | {g["column_widths"]} | {g["total_width"]} | {g["pageBreak"]} |')
report+=['','### 칸별 인쇄 그림 크기','',
'| 파일 | 행·열 / colspan | 셀 폭 HWPUNIT | 그림 폭 × 높이 mm |',
'|---|---|---:|---|']
for g in a['appendix3_grids']:
    for c in g['cells']:
        report.append(f'| {c["file"]} | {c["row"]}행 {c["col"]}열 / {c["colSpan"]} | {c["width"]} | {c["image_width_mm"]} × {c["image_height_mm"]} |')
report+=['','## 수동 재적용 필요 — patch_report 전문','',manual,'',
'이 23건은 내용 미반입 목록이 아니다. 내용이 바뀐 본문 표 22개와 교체한 전면부 1개의 서식 재확인 목록이다. 현행 MD 내용은 이미 반입되어 있다.','',
'## 기준본 SHA256','',
'- 기준본: `00. hwpx/261028_0757_경기공학_건축안전_윤혁_논문.hwpx`',
f'- 작업 전: `{a["base_sha256_before"]}`',f'- 작업 후: `{a["base_sha256_after"]}`',
'- 동일: **예**. staging/base.hwpx도 같은 SHA256이다.',
f'- 패치본 SHA256: `{a["sha256"]}`','',
'## 남은 검증과 알려진 제한','',
'1. 메인이 patched.hwpx를 한글 COM으로 실제 Open하고 재조판 SaveAs해야 한다. 스크래치의 ZIP/XML 통과는 한글 개방 또는 인쇄 배치 성공을 의미하지 않는다.',
'2. 전 표 PDF 검증과 부록 3 쪽 육안 검사가 필요하다. 행 높이는 최소값·추정치이며, TABLE로 나뉜 부표의 행 연속성·라벨과 그림의 같은 셀 배치·꼬리말 침범·표 뒤 본문을 확인해야 한다. 구조용 빈 머리행은 출력하지 않아 repeatHeader=0이며 모든 그림 행의 header=0이다.',
'3. 라벨은 기존 한양신명조 9pt 스타일을 적용했다. Windows GDI는 한양신명조 대신 굴림을 반환하여 라벨 줄 수 계산은 굴림 실측 대체값이다. 그림 폭은 manifest로 정확히 정했지만 한글의 실제 라벨 줄바꿈은 재조판으로 확인해야 한다.',
'4. `부록3_jamovi_원출력.md`의 “모든 출력은 같은 배율로 실었다”는 문장에는 브리프의 3-5 축소 예외가 표현되지 않았다. MD 수정은 금지되어 그대로 두었다. 필요하면 메인이 예외 문구를 판단한다.',
'5. 목차/표 목차/그림 목차는 PDF의 실제 인쇄 쪽수로 갱신하고, 다시 저장·출력하여 목차 변경에 따른 이동까지 확인해야 한다.',
'6. section1은 fresh로 교체했으므로 목차 장평·자간 등 사용자가 적용한 서식은 확인·재적용이 필요하다. 감사의 글 텍스트는 최신 기준본에서 이식했다.','',
'## 재현 순서','',
'`PYTHONIOENCODING=utf-8`을 설정하고 저장소 루트에서 실행한다. 아래 작업은 모두 staging 산출물만 생성하며 COM을 호출하지 않는다.','',
'```powershell',
"$env:PYTHONIOENCODING='utf-8'",
"$env:PYTHONDONTWRITEBYTECODE='1'",
'python tools/hwpx_transfer/md_to_blocks.py --out-dir tools/hwpx_transfer/staging/hwpx_261031',
'python tools/hwpx_transfer/staging/hwpx_261031/assemble.py',
'python tools/hwpx_transfer/staging/hwpx_261031/patch.py',
'python tools/hwpx_transfer/staging/hwpx_261031/verify.py',
'```','',
'`previous/`는 93aa8fb의 1~5장 MD를 git show로 읽어 만든 비교 자료이며 원고가 아니다. 기준본·양식 추출본·단계별 JSON도 모두 스크래치다.']
(OUT/'worker_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
# Fix the old fixed file-count prose in the already generated coverage report.
parse=(OUT/'parse_report.md').read_text(encoding='utf-8').replace('8개 원고 MD','9개 원고 MD').replace('8개 파일 전체','9개 파일 전체')
(OUT/'parse_report.md').write_text(parse,encoding='utf-8')
print('worker_report.md written; worker_changes.diff isolates this dispatch changes')
