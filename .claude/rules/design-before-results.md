---
paths:
  - "논문구조/**"
---

# Rule: Design Before Results

## Principle

**Lock the research design before examining point estimates.** Specify the 연구모형, 가설, and analysis plan before looking at results. This prevents post-hoc rationalisation and keeps the research credible.

## When This Applies

- 분석 설계 논의 (PROCESS macro 모형 번호, 투입 변수, 통제변수, 부트스트랩 설정)
- Setting up robustness checks or sensitivity analyses
- Choosing between competing statistical approaches
- 4장 분석결과 작성 전 설계 확정 여부 확인

## When to Skip

- Read-only tasks (proofreading, literature search)
- 기술통계·데이터 탐색 (design 이전 단계의 EDA)
- Tasks with no empirical component

## What This Means in Practice

**DO:**
- 가설과 분석 모형(집단 변수·공변량 구성, 탐색적 보조 분석의 지위)을 결과를 보기 전에 확정한다
- 공변량은 이론적 근거와 함께 사전에 투입 목록을 정한다 (분석 후 해석하지 않는다 — 교수님 요령)
- 분석 계획은 `논문구조/04_연구설계.md` 제5절에 기록한다 (별도 요약 문서를 만들지 않는다)
- When results are surprising, document the surprise *before* changing the specification

**DON'T:**
- Run the analysis and then decide what the hypothesis was based on which effects are significant
- Add or drop control variables to get a desired p-value
- Present robustness checks only for specifications that "work"

## The Falsifiability Test

Before running any analysis, ask:

> "If I specified my analysis plan before running it, would I change anything about what I'm about to do?"

If the answer is yes, stop and specify the plan first. If the answer is "I don't have a plan yet", write one before proceeding.

## How to Apply

1. When the user asks to "run the analysis" or "check the results", first confirm the specification is locked (`논문구조/04_연구설계.md` 제2·5절 기준)
2. If no analysis plan exists, draft one and get approval before executing
3. Treat specification changes after seeing results as a new analysis requiring justification
