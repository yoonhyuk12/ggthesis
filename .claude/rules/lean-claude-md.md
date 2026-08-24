---
paths:
  - "CLAUDE.md"
  - ".claude/reference/*.md"
  - ".claude/rules/*.md"
---

# Rule: Keep CLAUDE.md Lean

## Principle

**CLAUDE.md is loaded into context every session — every line costs tokens.** It should contain only instructions Claude needs on every entry. Everything else lives where the fact itself lives, and CLAUDE.md points at it.

## 원본은 하나만 둔다 (가장 중요)

**요약본을 만들지 마라.** 같은 사실을 두 곳에 두면 원본이 바뀔 때 반드시 어긋난다. 편의를 위한 요약이 가장 흔한 사고 원인이다.

- 원고 사실(장 구조·변수·가설·문항·수치·분석 설계)의 단일 원본은 `논문구조/`다. CLAUDE.md에도, `.claude/reference/`에도 사본을 만들지 않는다.
- 참고 자료는 **원고에 담을 수 없는 것만** `.claude/reference/`에 둔다 (PDF 분류, 일정, 스킬 호출법, 디펜스 논리, 도구 조작법).
- 이미 있는 문서를 가리키는 한 줄 링크는 사본이 아니다. 그 문서의 내용을 옮겨 적은 순간 사본이 된다.

> 2026-08-24 실제 사고. `docs/02-연구모형.md`가 04장의 변수·가설·문항을 복제하고 있었고, 04장이 ANCOVA로 두 번 바뀌는 동안 따라오지 못해 폐기된 매개모형을 서술하고 있었다. `docs/07-통계분석.md`는 "현행은 jamovi SEM"이라는 **정정 문구 자체가 낡은** 상태였다. 중복 5종을 삭제해 해결했다.

## What Belongs in CLAUDE.md

- Safety rules and file-protection policies (hwpx 보존 규칙, 빨간색 표기 규칙 등)
- 작성 경로·수정 순서 같은 항상 적용되는 규칙
- 참고 자료 인덱스 (one-line summaries with relative links)
- 세션 연속성 포인터

## What Does NOT Belong in CLAUDE.md

- 연구모형·가설·측정도구 상세 → `논문구조/04_연구설계.md`
- 장·절 구성표 → `논문구조/00_목차.md`
- 시스템 기술 명세 → `논문구조/03_시스템개발.md`, `프로그램 기술분석서.md`
- 문헌 노트·참조자료 상세 → `.claude/reference/05-참조자료.md`
- Long reference lists (>10 entries)
- Anything that duplicates content already in another project file

## The Pointer Pattern

When the material exists elsewhere, use a one-line summary + link — 내용을 옮겨 적지 않는다.

```markdown
## 분석 설계

도입/미도입 두 집단 ANCOVA. 단일 원본은 [`논문구조/04_연구설계.md`](논문구조/04_연구설계.md) 제5절.
```

## Thresholds

- **CLAUDE.md > 200 lines:** Review for extractable content.
- **Any section > 15 lines of reference material** (not safety rules or conventions): 원본이 어디인지 찾아 포인터로 바꾼다. 새 요약 문서를 만들어 옮기는 것이 아니다.
- **Duplicated content:** If the same information exists in another file, keep only the pointer in CLAUDE.md.
