# MEMORY.md — 세션 간 누적 학습 기록

> `recording-learnings` 스킬의 형식을 따른다. 한 줄 = 한 학습, Incorrect → Correct 방향 명시.

## Notation Registry (변수·용어 규칙)

## Key Decisions (결정·근거·날짜)

- [LEARN:method] 6장 구조 전환 뒤에도 변수 모형(X1~X4→M→Y, W)은 불변 → [SUPERSEDED 2026-08-24] 현행 주 분석은 AI 관제 시스템 도입 여부에 따른 안전관리 실효성의 조정 평균을 비교하는 두 집단 ANCOVA이며, 구 매개·조절 모형은 `backup/구 연구 방법/model.md`에 보존 — applies when: 연구모형·가설·분석방법·논문 제목을 작성하거나 검토할 때

## Citations (인용 교정)

- [LEARN:citation] 학위논문 인용 연도는 표지 "OO학년도"가 아니라 제출·수여(발행) 연도 기준 → 박종학: 표지 "2024학년도"·제출면 "2025년 6월" ⇒ 박종학(2025)로 표기 — applies when: 국내 학위논문 서지 확정 시 표지와 제출면(인준면)을 함께 확인
- [LEARN:citation] 김윤헌 박사논문(성균관대, AI 안전인지 프레임워크)은 2025가 아니라 2026(책등 연도) → 김윤헌(2026). 학회논문 참고문헌 [02]는 연도(2025)·제목("…개발")이 원문("…연구")과 다름 — 학회논문 측 정정 필요
- [LEARN:citation] 같은 문헌이 원고 간·원고 내에서 서로 다른 연도로 표기되는 drift가 반복됨(윤영석·박종학·김윤헌·왕인국·이동건·이준호 6건) → 인용 연도는 07_참조번호목록.md의 "확정" 검증 로그와 referernce/ PDF 원문(표지+제출면) 기준으로 통일 — applies when: 새 장 집필·학회↔학위논문 간 내용 이식 시
- [LEARN:citation] 학회논문 참고문헌 [02] 김윤헌은 연도(2025→2026)·제목("…개발"→"…연구")이 원문과 다름 — 학회논문 MD·hwpx 정정 필요(2026-07-12 기준 미수정, 사용자 지시 대기)

## Anti-Patterns (방법·도메인 교정)

- [LEARN:method] X1~X4를 현행 ANCOVA의 독립변수로 취급 → X1~X4는 도입 집단 전용 D블록의 시스템 특성 인식 참고척도이며, 현행 독립변수는 AI 관제 시스템 도입 여부 — applies when: Worker에게 변수·가설 관련 집필을 위임하거나 제3장과 제4장의 연결을 검토할 때
- [LEARN:method] 브리프에 "git 쓰기 금지"를 명시하면 서브에이전트가 지킬 것으로 신뢰 → 코덱스 워커는 2026-08-24 금지를 무시하고 커밋 5건(56395fc~47ad597)을 실행했으며, 47ad597은 작업 완료 6분 전 중간 스냅샷이고 추적 대상이 아니던 tools/·backup/·hwpx 바이너리·PDF까지 함께 커밋함. 위임 전에 오케스트레이터가 복구 지점을 먼저 커밋하고, 완료 후 반드시 `git log`로 무단 커밋 여부를 확인 — applies when: Agent·orchestration으로 파일 수정 작업을 위임할 때
- [LEARN:method] 병렬 워커에게 같은 대상을 서로 다르게 지시하면 산출물이 어긋난다 → 2026-08-24 `<표 5-8>` 제목을 워커 E에는 "유지", 워커 F에는 "탐색적 보조 분석 결과로 변경"으로 상충 지시하여 목차와 본문이 불일치함. 두 워커의 경계면(공유 표·절 제목·번호)은 브리프 작성 전에 오케스트레이터가 최종형을 한 번 확정해 양쪽에 동일 문구로 넣고, 완료 후 경계면만 따로 대조 — applies when: 파일을 나눠 병렬 위임하되 상호참조가 걸쳐 있을 때

## hwpx Pitfalls

- [LEARN:hwpx] HWPX 기준 원본이 `논문구조/260725_경기공학_건축안전_윤혁_논문작성_작성본.hwpx`에 있음 → [SUPERSEDED 2026-08-24] 현재 최신 기준 원본은 `C:/Users/EKR/orca/ggthesis/00. hwpx/260725_경기공학_건축안전_윤혁_논문작성_작성본.hwpx`이며, 한글 이관 요청 시 이를 `C:/Users/EKR/orca/ggthesis/00. hwpx/YYMMDD_HHMM_논문명.hwpx`로 복사한 뒤 복사본의 타깃만 수정하고 Asia/Seoul 작업 시각을 사용 — applies when: 사용자가 논문 내용을 한글(hwpx)로 옮겨 달라고 요청할 때
- [LEARN:hwpx] hwpx MCP 서버(v2.18.1)가 모든 파일에서 "open-safety verification: package validation failed"로 열기 실패(백업본 포함, ZIP·manifest 정상) → 읽기·타깃 치환은 Python zipfile로 Contents/section0.xml 직접 수술(수정 전 백업 생성, 동일 순서·압축 유지, 위치 기반 치환) — applies when: hwpx MCP find_text/search_and_replace가 open failed를 반환할 때. 표 셀은 텍스트가 여러 문단/run으로 쪼개져 있을 수 있어 문자열 전역 치환 전 반드시 원문 XML 문맥 확인 [SUPERSEDED 2026-07-25: 재클론한 hwpx-mcp-simple에서 `get_document_info`가 학회논문 백업본을 정상 개방(194문단·17표)해 이 실패는 재현되지 않음. zipfile 수술은 여전히 유효한 폴백이나 더 이상 기본 경로가 아니다]
- [LEARN:hwpx] hwpx MCP 서버는 저장소 루트(C:\Users\EKR\orca\ggthesis)로 샌드박스됨 → 스크래치패드·임시 경로를 넘기면 "path is outside sandbox root"로 거부 — applies when: MCP 도구에 파일 경로를 넘길 때. 저장소 상대경로를 쓴다
- [LEARN:hwpx] 한글 크래시 판정을 "Start-Process 후 고정 12초 대기 → Get-Process Hwp" 방식으로 하면 세션 첫(콜드) 실행이 12초를 넘겨 뜨는 탓에 **정상 파일이 CRASHED로 오탐**된다(같은 파일이 COM으로는 정상 개방·PDF 변환됨, 워밍업 후에는 6초에도 ALIVE) → 워밍업 후 폴링하는 `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1` 사용 — applies when: 수정한 hwpx의 개방 가능 여부를 검증할 때
- [LEARN:citation] 학회논문 hwpx의 김윤헌 5곳(내주 3·표 셀 1·참고문헌 1) 2025→2026 및 [02] 제목 정정 완료(2026-07-12, 백업: 학회논문/_백업_hwpx수정전_20260712_학회2.hwpx) — MD·hwpx 동기화됨
