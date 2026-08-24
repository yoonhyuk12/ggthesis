---
paths:
  - "01.docs/**"
  - "02.reference/**"
  - ".claude/reference/05-참조자료.md"
---

# Rule: Verify Every Reference Before Writing

## Principle

**Never write any paper reference to any output file without verifying the paper exists.** This applies to every format — 참고문헌 목록, 내주, 문헌 요약 노트. The sequence is always: find → verify existence → write.

Hallucinated papers are worse than missing papers. A missing citation is an honest gap; a fabricated citation undermines the entire document's credibility.

## Paper Existence Protocol

Before writing any paper reference:

1. **First check `02.reference/`** — 이 프로젝트의 선행연구 PDF 44종 (분류는 `.claude/reference/05-참조자료.md`). 보유 PDF에서 인용하는 것이 기본이다.
2. **보유하지 않은 문헌을 인용해야 하면 존재를 검증하라** — RISS, DBpia, Google Scholar, Crossref 중 최소 1곳에서 실제 검색 결과를 확인한다 (WebSearch/WebFetch). Zero hits = the paper does not exist.
3. **Only write verified references** — never record a reference you cannot find, regardless of how confident you are it exists.

## Hallucination Red Flags

Drop the paper immediately (do not write, do not flag as "unverified") if ANY of these are true:

- **Publication date is in the future** or the current year with no database record
- **Zero hits** across the indexes above
- **Title is suspiciously tailored** to the exact research question (real papers have broader or tangential titles)
- **Authors cannot be found** via search with their name + field
- **Venue does not exist** or the paper is not in the venue's proceedings/issue

When a paper is dropped, do not include it with a caveat — omit it entirely.

## When This Applies

- 참고문헌 목록 작성·수정
- 본문 내주 추가
- Any task that produces a list of references
- **Any context where you are about to cite a paper from memory** — if you haven't verified it in this session, verify before writing

## When to Skip

- Reading or summarising papers in `02.reference/` (existence already confirmed)
- Informal conversation about papers where no file is being written

## Cross-Reference

인용 페이지가 실제로 해당 내용을 담고 있는지는 `verifying-citation-pages` 스킬로 검증한다. 이 규칙은 "존재 검증", 그 스킬은 "페이지 검증"이다.
