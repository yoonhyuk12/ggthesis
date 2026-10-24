# 워커 브리프 — patch_from_fresh.py 보강·검증 (계획: 261024_1519_사용자편집본_기준_조립_계획.md 3-1절)

## 목표
사용자가 한글에서 직접 고친 `00. hwpx/261024_1443_경기공학_건축안전_윤혁_논문_분량감축_11월반영본.hwpx`를 기준본(base)으로 둔다. 여기에 현행 MD로 새로 조립한 fresh 본의 변경분만 반입하는 표준 경로를 완성한다. 반입 도구는 `tools/hwpx_transfer/patch_from_fresh.py`이다. 사용자의 서식 편집은 하나도 잃지 않아야 한다.

## 경로
- 저장소 루트: `C:/Users/User/Documents/2026 개발관련/03. 경기대 논문`
- 스크래치: `C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Documents-2026------03--------/8392860f-c21c-4047-953c-5718d944d5c2/scratchpad/base_diff/`
  - `user1443.hwpx`: 기준본 복사본. 이것만 읽는다. `00. hwpx/` 원본은 열지 않는다.
  - `head1431.hwpx`: 사용자 편집 전 조립본. 1443과 다른 점은 표지·인준지·감사의 글 연월뿐이다.
  - `toc_pages_1443.json`: 1443 조립 때 쓴 목차 쪽수
  - `../diff_fmt.py <a> <b>`: 문단 서식·텍스트 차이 비교. `../diff_tbl.py <a> <b>`: 표 병합·열폭 비교. 둘 다 `PYTHONIOENCODING=utf-8 python -I -X utf8`로 실행한다.
  - `diff_head_vs_user.txt`: 사용자 편집 내역. 셀 병합 7표(#10·26·27·30·31·32·35), 열폭 6표, 셀 정렬·줄간격 약 200문단, 본문 줄간격 약 50문단, 쪽 나눔 추가 3, 병합 셀 빈 문단 삭제 약 45
- 조립 명령: CLAUDE.md의 'MD → hwpx 조립 파이프라인' 1·2단계. 출력은 스크래치에 둔다. `--toc-pages`에는 `toc_pages_1443.json`을 준다. 양식 원본은 스크래치에 복사해 `--template`으로 쓴다.

## 할 일
1. 1단계(`md_to_blocks.py`)와 2단계를 실행해 `fresh.hwpx`를 만든다. MD는 1443 조립 이후 `01.docs/00_목차.md` 주제어 끝 `[확정 필요: 5∼7개 최종 선정]` 삭제 1건만 바뀌었다.
2. `patch_from_fresh.py`를 읽고 `--base user1443.hwpx --fresh fresh.hwpx`로 dry-run을 실행한다. 현재 동작과 문제를 파악한다.
3. 보강한다.
   - (a) **셀 병합 표 자동 판정.** base 표의 각 셀 텍스트(공백 무시)가 fresh의 같은 `(rowAddr,colAddr)` 셀과 같고, base에서 병합으로 덮인 fresh 셀이 빈칸이거나 덮은 셀과 같은 텍스트이면 '내용 동일'로 보고 base XML을 유지한다. 그러면 `--protect`를 손으로 적지 않아도 된다. 내용이 실제로 다른 병합 표는 base를 유지하고 보고서에 '수동 재적용 필요'로 남긴다. 덮어쓰지 않는다.
   - '합계'↔'합  계' 같은 공백 차이는 동일로 본다. base 텍스트를 유지한다.
   - (b) **D3 바로잡기 2건.**
     - base의 3장 문단 '…전체 구성은 <그림 3-1>과 같다.<그림 3-1> YOLO-LLM 이중 캐스케이드 시스템 아키텍처'는 사용자가 실수로 문단 경계를 지운 것이다. 출력에서는 fresh처럼 본문 문단과 캡션 문단으로 나눈다. 본문 문단에는 base의 paraPr·charPr을 유지하고, 캡션은 fresh의 캡션 서식을 쓴다. 그림 개체 위치도 확인한다. base에서 그림이 어느 문단에 붙어 있는지 확인하고, 그림이 사라지거나 중복되면 안 된다.
     - section1 표 목차의 '<표 2-2> 시스템 기능–담당자 업무–안전관리 실효성 하위요인 연결' 뒤에 붙은 '17'은 실수다. 원래 목차 항목 형식(점선 탭 + 쪽수)으로 되돌린다.
   - 일반 규칙: base에만 있는 문단은 지우지 않는다. 위 2건만 명시적 예외다.
   - (c) 주제어 문단이 base와 fresh에서 같아졌는지 확인한다.
4. 단위 테스트를 `tools/hwpx_transfer/tests/test_patch_from_fresh.py`로 추가한다. 최소 3건이다: 병합 표의 내용이 같으면 base 유지, 내용이 다르면 base 유지 + 보고, 바뀐 일반 문단은 fresh 반입 + ID 재매핑. 기존 `test_blocks_to_hwpx_kjn.py` 21건도 통과해야 한다. 초록 마커 수 기대치가 바뀌어 실패하면 기대치만 조정하고 그 사실을 보고한다.
5. 실제 실행으로 `patched.hwpx`를 만들고 `diff_fmt.py user1443.hwpx patched.hwpx`·`diff_tbl.py`로 대조한다.
   - 기대: 서식 차이 그룹 0, 표 차이 0.
   - 텍스트 차이는 다음뿐이어야 한다: <그림 3-1> 분리, 표 목차 '17' 제거, (있다면) 목차 쪽수 문자열.
   - 다른 차이가 남으면 원인을 적는다.

## 금지
- `git add/commit/push` 등 git 쓰기를 하지 않는다.
- hwpx MCP 도구는 읽기를 포함해 모두 쓰지 않는다. rhwp 쓰기 도구도 쓰지 않는다. kordoc 쓰기 도구도 쓰지 않는다.
- 한글 COM(`resave-hwpx.ps1` 포함)을 쓰지 않는다. 메인이 한다.
- `00. hwpx/`의 어떤 파일도 쓰지 않는다. 양식 원본은 SHA256 9bf1980a…이고 바뀌면 안 된다.
- `01.docs/`, `MEMORY.md`, `CLAUDE.md`, `.claude/**`, `03.plan/**`를 수정하지 않는다.
- 수정 허용 범위: `tools/hwpx_transfer/patch_from_fresh.py`, `tools/hwpx_transfer/tests/test_patch_from_fresh.py`(신규), `tools/hwpx_transfer/tests/test_blocks_to_hwpx_kjn.py`(기대치 조정만), 1단계가 재생성하는 `tools/hwpx_transfer/staging/*.blocks.json`·`parse_report.md`, 스크래치 폴더.

## 보고(증거 포함)
- 바꾼 코드 요약(diff 요지)
- 테스트 출력(건수와 OK)
- 실행 명령 전문: 메인이 그대로 재사용한다
- `patched.hwpx` 경로와 SHA256
- diff_fmt/diff_tbl 결과 요약(남은 차이와 원인)
- patch_from_fresh 보고서 경로와 '수동 재적용 필요' 목록(없으면 없음)
