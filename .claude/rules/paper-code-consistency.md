---
paths:
  - "논문구조/**"
  - "학회논문/**"
---

# Rule: Manuscript-vs-Data Consistency Check

## Principle

**Before committing edits to 연구방법·분석결과 sections, check the prose claim against the actual source (분석 출력, 설문 설계, 시스템 명세).** 원고-데이터 drift surfaces at 심사 time as a "soundness" objection; by then the fix is harder than catching it at edit time.

## When this applies

- Editing 3장(연구방법)·4장(분석결과) — 표본 수, 측정 문항 수, 분석 모형, 계수·p값·신뢰구간을 기술하는 문단
- Editing a paragraph that describes 설문 구성 (문항 수, 척도, 하위요인) — `docs/02-연구모형.md`의 확정 측정도구와 일치해야 한다
- Editing 시스템 기술 문단 (X1~X4 운영적 정의, 아키텍처) — `프로그램 기술분석서.md`·`docs/03-연구대상시스템.md`와 일치해야 한다
- 표와 본문이 같은 수치를 말하는지 — 표를 고치면 본문도, 본문을 고치면 표도 확인
- MD를 수정한 뒤 hwpx에 반영할 때 — 두 원고의 해당 문단이 같은 수치·주장을 담는지

## When to skip

- 참고문헌, 이론적 배경의 순수 문헌 서술 (no data claims)
- Trivial polish: rewording without changing claims

## Check protocol (≈60 s per claim)

1. **For every quantitative claim in the prose** (표본 수, 문항 수, 계수, p값, 부트스트랩 횟수, 신뢰구간), open the source that produces it — SPSS/PROCESS 출력, 설문 원자료, 확정 연구모형 문서. The values must match exactly.
2. **For every "시스템은 X를 수행한다" claim**, confirm X actually appears in `프로그램 기술분석서.md` (실제 구현된 기능인지, 계획 단계 기능인지 구분).
3. **가설 번호·변수 기호(X/M/W/Y)**가 `docs/02-연구모형.md`의 확정 정의와 어긋나지 않는지 확인한다.

## Failure modes prevented

- 본문은 5점 척도라 쓰고 설문지는 7점 척도인 경우
- 표의 N과 본문의 N이 다른 경우
- 분석 재실행 후 본문에 이전 실행의 수치가 남는 경우 (stale numbers)
- MD는 고쳤는데 hwpx에 옛 수치가 남는 경우

## Anti-Patterns

- **Don't** treat "the output probably says what the paragraph says" as a check. "Probably" lies.
- **Don't** assume that because the prose reads well, the claims in it are still valid after a re-analysis.
