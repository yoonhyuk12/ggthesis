# Rule: Mark Unverified Claims

## Principle

**Never assert a citation, statistic, 법령·고시 기준, or factual claim that hasn't been verified from a primary source.** Mark anything unverified as `[UNVERIFIED]` rather than asserting it. False claims that slip through (특히 학회 투고본·심사 답변서) damage credibility.

## What "unverified" means

A claim is unverified when:

- The citation (저자·연도·제목·게재지) has NOT been confirmed against the actual PDF in `02.reference/` or an academic index (RISS, DBpia, Google Scholar, Crossref)
- The cited page number has NOT been checked against the source PDF — use the `verifying-citation-pages` skill (인쇄 쪽수 vs PDF 페이지 인덱스 함정 주의)
- The statistic has NOT been computed from the survey data / SPSS·PROCESS output, or quoted from a paper just read in this session
- 법령·고시·금액 기준 (산업안전보건법, 고용노동부 고시, 산안비 계상 요율·한도 등) has NOT been re-checked against the current official text — 법령·고시는 매년 바뀐다
- A self-derived quantitative claim (간접효과 크기·부호, 조절효과 방향 등) has NOT been actually computed from the analysis output, only asserted from intuition

## What to do instead

| Instead of | Write |
|---|---|
| "Smith(2024)는 X를 보였다" | "Smith(2024) `[UNVERIFIED]` reportedly showed X" — 검증 후 플래그 제거 |
| "산안비 스마트 안전장비 사용 한도는 X%이다" | 최신 고시 원문 확인 후 기술; 못 했으면 `[UNVERIFIED — 고시 최신본 확인 필요]` |
| "간접효과는 유의하다" | 분석 출력에서 확인 후 기술; 분석 전이면 가설·예상으로 명시 |

The `[UNVERIFIED]` flag is preserved through edits until verification actually happens.

## Verification chains

| Claim type | Primary source |
|---|---|
| 인용 존재·서지 | `02.reference/` PDF 원문; 없으면 RISS·Google Scholar·Crossref 웹 검증 |
| 인용 페이지 | 원문 PDF + `verifying-citation-pages` 스킬 |
| 법령·고시·금액 | 국가법령정보센터·고용노동부 최신 원문 (WebFetch/WebSearch) |
| 통계 수치 | 설문 원자료·SPSS/PROCESS 출력 |
| 시스템 사양 (X1~X4 운영적 정의) | `프로그램 기술분석서.md`, `01.docs/03_시스템개발.md` |

## When This Applies

- Drafting paper sections, abstracts, 심사 답변서
- Producing literature notes, syntheses, reading lists
- Reporting statistics or findings from prior work
- Generating citation lists from memory

## When to Skip

- The user explicitly says "draft fast, I'll verify later"
- Internal notes / brainstorming where verification would slow ideation

## Anti-Patterns

- **Don't** invent a plausible-looking citation — that's a fabrication
- **Don't** assert 법령·고시 내용 from training data — read the current official text
- **Don't** quote a paper from memory without re-checking the actual claim. Hallucinated quotes are a top failure mode
- **Don't** strip `[UNVERIFIED]` flags during editing without actually verifying. The flag is the trail of unfinished work
