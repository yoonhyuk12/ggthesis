# Rule: Read Documentation Before Searching

## Principle

**Never explore when documentation already answers your question.** Broad codebase searches (Glob, Grep, web searches) burn tokens and time. Project docs exist precisely to avoid this.

## On Every New Session

Before doing any work:

1. `CLAUDE.md` — already auto-loaded; follow its 참고 자료 인덱스 pointers
2. 원고 사실은 `논문구조/`에서 찾는다. 그 밖의 참고 자료는 CLAUDE.md 인덱스의 `.claude/reference/` 중 필요한 것만 로드한다
3. 논문 원고 작업이면 박종용 교수님 논문작성요령 전문 (경로는 CLAUDE.md 참조)
4. The latest file in `plan/` (if resuming work)
5. `MEMORY.md` (if it exists) — accumulated corrections and decisions

This takes seconds and prevents minutes of aimless searching.

## Before Any Search

When you need information about the project, check in this order:

1. **`논문구조/` 원고** — 장 구조·변수·가설·문항·수치·분석 설계의 단일 원본이다
2. **CLAUDE.md 참고 자료 인덱스** — PDF 분류, 일정, 스킬 호출, 디펜스 논리, G*Power 조작법
3. **`프로그램 기술분석서.md`** — AI CCTV Viewer 상세 기술 명세
4. **`.claude/reference/05-참조자료.md`** — referernce/ PDF 분류 (원문 PDF를 열기 전에 분류부터)
5. **Only then** use Grep/Glob for targeted searches
6. **Web search is a last resort** — never search the web for something already documented locally (단, 법령·고시 최신본 확인은 예외 — mark-unverified 규칙)

## Anti-Patterns (Do NOT Do These)

- Globbing for `**/*.md` across the entire repo to "find" documentation CLAUDE.md already lists
- Grepping for keywords when CLAUDE.md explicitly lists where things are
- 참고 자료 5종을 전부 열어 "맥락을 파악"하려는 것 — 필요한 하나만 연다
- Opening `referernce/` PDFs before reading `.claude/reference/05-참조자료.md`
