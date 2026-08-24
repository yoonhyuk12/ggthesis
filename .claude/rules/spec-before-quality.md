---
paths:
  - "논문구조/**"
  - "학회논문/**"
---

# Rule: Spec Compliance Before Quality Review

## Principle

**Validate that the specification is met before assessing quality.** A beautifully written paper with the wrong 연구모형 is worse than a rough draft with the right one. Spec compliance is a prerequisite for quality review — never reverse the order.

## The Two-Stage Gate

| Stage | Question | Check against | Blocks if failed |
|-------|----------|--------------|-----------------|
| **1. Spec compliance** | "Did we do what was asked?" | 확정 연구모형·가설·작성 규칙 | Yes — quality review is meaningless on wrong spec |
| **2. Quality review** | "Did we do it well?" | 문장·논리·형식 품질 | Depends on severity |

## What Counts as "Spec"

| Context | The spec is... |
|---------|---------------|
| 논문 원고 | `논문구조/04_연구설계.md`의 확정 변수·가설, `논문구조/00_목차.md`의 장·절 구조, 박종용 교수님 논문작성요령 |
| 분석 작업 | `논문구조/04_연구설계.md` 제5절의 분석 설계 (design-before-results 규칙과 연동) |
| 일반 작업 | `plan/`의 승인된 계획 or the user's explicit instructions |

## How to Apply

1. Before a quality review, ask: **"Is there a locked spec for this work?"**
2. If yes, verify the output matches it (변수 정의가 맞는가? 장·절 구조를 따르는가? 요령의 규칙을 지키는가?)
3. If spec is violated, **stop and flag** — do not proceed to quality review
4. If spec is met, proceed to quality review normally

## When to Skip

- No spec exists yet (exploratory/discovery phase) — quality review alone is fine
- The task is mechanical (formatting, bibliography) — no spec to validate
- The user explicitly says "just check quality, spec is fine"

## Why This Matters

Quality review on the wrong spec legitimises scope creep. A reviewer who grades polish on a paper with the wrong 연구모형 implicitly validates it. Separating the two stages catches design drift before it's buried under layers of editorial polish.
