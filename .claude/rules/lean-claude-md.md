---
paths:
  - "CLAUDE.md"
  - "docs/*.md"
  - ".claude/rules/*.md"
---

# Rule: Keep CLAUDE.md Lean

## Principle

**CLAUDE.md is loaded into context every session — every line costs tokens.** It should contain only instructions Claude needs on every entry. Everything else belongs in dedicated files (`docs/*.md`) that Claude reads on demand.

## What Belongs in CLAUDE.md

- Safety rules and file-protection policies (hwpx 보존 규칙 등)
- 작성 경로·수정 순서 같은 항상 적용되는 규칙
- 문서 인덱스 (one-line summaries with relative links)
- 세션 연속성 포인터

## What Does NOT Belong in CLAUDE.md

- 연구모형·측정도구 상세 → `docs/02-연구모형.md`
- 시스템 기술 명세 → `docs/03-연구대상시스템.md`
- 문헌 노트·참조자료 상세 → `docs/05-참조자료.md`
- Long reference lists (>10 entries) → `docs/`
- Anything that duplicates content already in another project file

## The Pointer Pattern

When reference material exists elsewhere, use a one-line summary + link:

```markdown
## 통계 분석

4장 분석 설계, SPSS/PROCESS macro 사용.

Full details: [`docs/07-통계분석.md`](docs/07-통계분석.md)
```

## Thresholds

- **CLAUDE.md > 200 lines:** Review for extractable content.
- **Any section > 15 lines of reference material** (not safety rules or conventions): Extract to `docs/` and replace with a pointer.
- **Duplicated content:** If the same information exists in another file, keep only the pointer in CLAUDE.md.
