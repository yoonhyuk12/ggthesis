# 워커 공통 규칙 (모든 브리프에 적용)

작업 루트는 저장소 루트 `C:/Users/User/Documents/2026 개발관련/03. 경기대 논문` 이고, 이 작업의 영역은 그 아래 `04. 미소논문/` 이다. 아래 경로는 모두 `04. 미소논문/` 기준 상대경로다.

## 입력 자료 (읽기 전용)
- `01.docs/*.md` — 미소 논문 MD 원고(00.목차, 01.서론 … 06.결론, 07.부록, 07-2. 설문근거, 08.참고문헌), `01.docs/그림/*.png`
- `00. hwpx/양식원본_260912_1059_윤혁작성본.hwpx` — 양식. **직접 열지 말 것.** 대신 아래 덤프를 읽는다
- `tools/hwpx_transfer/analysis/extracted/Contents/{header,section0,section1,section2}.xml` — 양식 압축 해제본
- `tools/hwpx_transfer/analysis/section{0,1,2}_paras.json` — 문단 덤프 `{idx, byte_start, byte_end, paraPrIDRef, styleIDRef, pageBreak, has_tbl, text, runs[[charPrIDRef,text]]}`. 문단 번호는 이 `idx`만 쓴다(표 셀 문단 제외, 최상위 문단 순서)
- `tools/hwpx_transfer/staging/style_map_yoonhyuk_reference.json`, `analysis/template_analysis_yoonhyuk_reference.md`, `staging/references_yoonhyuk_reference.json` — 이전 논문(윤혁) 기준 파일. **id 값은 무효**(양식 header가 재저장으로 정규화돼 charPr 81·paraPr 64·borderFill 29·tabPr 6으로 재번호됨). 형식·키 이름만 참고한다
- 상위 저장소 `../tools/hwpx_transfer/`, `../.claude/skills/hwpx-thesis-editing/SKILL.md`, `../03.plan/260912_0837_hwpx노하우_동기이관_가이드.md` — 참고용, 수정 금지

## 금지 사항 (서브에이전트 write guard)
- `git add/commit/push` 등 git 쓰기 금지
- hwpx MCP 도구(`mcp__hwpx__*`) **읽기·쓰기 전부 금지**(2.2MB 본문에 40분 멈춤 사고). rhwp MCP 쓰기 금지(읽기 `hwp_open`/`hwp_doc_search`/`hwp_doc_text`는 허용하나 덤프 JSON이 있으므로 불필요)
- `00. hwpx/`의 파일을 수정·덮어쓰기 금지. 조립 결과는 `tools/hwpx_transfer/staging/test_out/` 에만 쓴다
- 상위 저장소(`../`)의 파일, `MEMORY.md`, `CLAUDE.md`, `.claude/**`, `../03.plan/**` 수정 금지
- 브리프에 적힌 산출물·파일 외에는 만들거나 고치지 않는다. 원고 MD(`01.docs/*.md`)는 **절대 수정하지 않는다**
- 인용을 지어내지 않는다. 근거 없는 서지는 `[CITE_TODO: …]`로 남긴다

## 실행 환경 함정
- 파이썬 실행은 항상 `PYTHONIOENCODING=utf-8 python …` (cp949 콘솔에서 줄표 출력 시 죽는다)
- bash 환경변수 이름에 `GROUPS`를 쓰지 않는다
- 파일 쓰기는 UTF-8(BOM 없음), 줄바꿈 LF
- 표준 라이브러리만 쓴다(추가 pip 설치 금지). 이미지 크기는 PNG IHDR 청크를 직접 읽는다

## 완료 보고 (worker_done)
- 산출물 경로, 검증 명령과 그 출력(요약), 결정 사항·미해결 사항을 세 문장 요약 + 상세는 산출물 리포트 파일에 적는다
- 판단이 필요한 질문은 프리앰블의 `ask` 명령으로 코디네이터에게 묻는다. 로컬 질문 TUI를 열지 않는다
