# MEMORY.md — 세션 간 누적 학습 기록

> `.claude/rules/learn-tags.md` 형식을 따른다. 한 줄 = 한 학습, Incorrect → Correct 방향 명시.

## Notation Registry (변수·용어 규칙)

## Key Decisions (결정·근거·날짜)

- [2026-07-12] 학위논문을 6장 구조로 재구성(제3장 시스템 개발 신설) — 지도교수 구두 지시("개발 목차 검토") + 사례 박사논문 목차 기준. 변수 모형(X1~X4→M→Y, W)은 불변. 계획: `plan/2026-07-12_개발장신설_목차재구성.md`

## Citations (인용 교정)

- [LEARN:citation] 학위논문 인용 연도는 표지 "OO학년도"가 아니라 제출·수여(발행) 연도 기준 → 박종학: 표지 "2024학년도"·제출면 "2025년 6월" ⇒ 박종학(2025)로 표기 — applies when: 국내 학위논문 서지 확정 시 표지와 제출면(인준면)을 함께 확인
- [LEARN:citation] 김윤헌 박사논문(성균관대, AI 안전인지 프레임워크)은 2025가 아니라 2026(책등 연도) → 김윤헌(2026). 학회논문 참고문헌 [02]는 연도(2025)·제목("…개발")이 원문("…연구")과 다름 — 학회논문 측 정정 필요
- [LEARN:citation] 같은 문헌이 원고 간·원고 내에서 서로 다른 연도로 표기되는 drift가 반복됨(윤영석·박종학·김윤헌·왕인국·이동건·이준호 6건) → 인용 연도는 07_참조번호목록.md의 "확정" 검증 로그와 referernce/ PDF 원문(표지+제출면) 기준으로 통일 — applies when: 새 장 집필·학회↔학위논문 간 내용 이식 시
- [LEARN:citation] 학회논문 참고문헌 [02] 김윤헌은 연도(2025→2026)·제목("…개발"→"…연구")이 원문과 다름 — 학회논문 MD·hwpx 정정 필요(2026-07-12 기준 미수정, 사용자 지시 대기)

## Anti-Patterns (방법·도메인 교정)

- [LEARN:method] 서브에이전트가 X1~X4 변수명을 임의 창작(예: "검출 신뢰성") → 확정 명칭은 docs/02-연구모형.md 기준(X1 시스템 인프라 범용성, X2 1차 탐지(YOLO) 및 제어 안정성, X3 2차 검증(LLM) 오탐 필터링, X4 알림 전파 즉각성) — applies when: Worker에게 변수 관련 집필 위임 시 브리프에 확정 명칭을 명시

## hwpx Pitfalls

- [LEARN:hwpx] hwpx MCP 서버(v2.18.1)가 모든 파일에서 "open-safety verification: package validation failed"로 열기 실패(백업본 포함, ZIP·manifest 정상) → 읽기·타깃 치환은 Python zipfile로 Contents/section0.xml 직접 수술(수정 전 백업 생성, 동일 순서·압축 유지, 위치 기반 치환) — applies when: hwpx MCP find_text/search_and_replace가 open failed를 반환할 때. 표 셀은 텍스트가 여러 문단/run으로 쪼개져 있을 수 있어 문자열 전역 치환 전 반드시 원문 XML 문맥 확인 [SUPERSEDED 2026-07-25: 재클론한 hwpx-mcp-simple에서 `get_document_info`가 학회논문 백업본을 정상 개방(194문단·17표)해 이 실패는 재현되지 않음. zipfile 수술은 여전히 유효한 폴백이나 더 이상 기본 경로가 아니다]
- [LEARN:hwpx] hwpx MCP 서버는 저장소 루트(C:\Users\EKR\orca\ggthesis)로 샌드박스됨 → 스크래치패드·임시 경로를 넘기면 "path is outside sandbox root"로 거부 — applies when: MCP 도구에 파일 경로를 넘길 때. 저장소 상대경로를 쓴다
- [LEARN:hwpx] 한글 크래시 판정을 "Start-Process 후 고정 12초 대기 → Get-Process Hwp" 방식으로 하면 세션 첫(콜드) 실행이 12초를 넘겨 뜨는 탓에 **정상 파일이 CRASHED로 오탐**된다(같은 파일이 COM으로는 정상 개방·PDF 변환됨, 워밍업 후에는 6초에도 ALIVE) → 워밍업 후 폴링하는 `.claude/skills/hwpx-thesis-editing/scripts/verify-hwpx.ps1` 사용 — applies when: 수정한 hwpx의 개방 가능 여부를 검증할 때
- [LEARN:citation] 학회논문 hwpx의 김윤헌 5곳(내주 3·표 셀 1·참고문헌 1) 2025→2026 및 [02] 제목 정정 완료(2026-07-12, 백업: 학회논문/_백업_hwpx수정전_20260712_학회2.hwpx) — MD·hwpx 동기화됨
