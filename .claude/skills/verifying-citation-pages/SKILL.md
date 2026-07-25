---
name: verifying-citation-pages
description: Use when checking whether a thesis/paper reference's 인용 페이지 (cited page numbers) actually contain the content the body attributes to it — cross-referencing 06_참고문헌.md entries against source PDFs in referernce/. Critical when a citation's page seems to land on a title page, blank page, or wrong section (the printed page vs PDF page-index trap).
---

# Verifying Citation Pages (인용 페이지 원문 대조)

## Overview

Each entry in `학회논문/06_참고문헌.md` ends with 〔인용 페이지: …〕 — the **printed page numbers** (인쇄본 쪽번호) of the source where the cited content appears. This skill verifies those page numbers actually contain what the body attributes to the reference.

**Core trap:** 인용 페이지 is the **printed page number** (the footer like `- 3 -`), NOT the PDF reader's page index. Front matter (겉표지·속표지·목차·초록·그림목차) shifts them apart by a fixed offset. Reading "PDF page 3" when the citation says "p.3" lands you on a title page and produces a false "citation is wrong" conclusion.

**Always derive the offset before judging a page.**

## When to Use

- User says "참고문헌 하나씩 확인하자" / "인용 페이지 맞는지 대조해줘"
- A cited page appears to show a title page, blank, or unrelated section
- Auditing 06_참고문헌.md against source PDFs before submission

## Procedure

1. **Read the citation entry** in `학회논문/06_참고문헌.md` — note the reference `[NN]`, author/year, and 〔인용 페이지〕.
   - No 〔인용 페이지〕 = 원문 미확보 (외부 논문·법령·웹자료). Nothing to verify against a PDF; skip.

2. **Find what the body attributes to it.** Grep the body for the author surname or `[NN]`:
   ```
   Grep "[01]|김석기" in 학회논문/  → 02_문헌고찰.md, etc.
   ```
   Record the *specific claim* (e.g. "BERTopic+GPT-4o 사고 패턴 분석, 사후 분석, 실시간 경보 불가"). This is what must be supported.

3. **Locate the source PDF** in `referernce/` (filename starts with its download-order number, unrelated to `[NN]`). Match by title.

4. **Derive the printed↔PDF offset.** Read a few body PDF pages, find a footer page number (e.g. `- 3 -`):
   ```
   offset = (PDF page index) − (printed number in footer)
   ```
   Then: **PDF index to read = printed page + offset.**
   - Example (ref 51): PDF page 13 shows footer `- 3 -` → offset = +10. So printed p.2 → PDF 12, printed p.39 → PDF 49.
   - Offset is per-document; front matter length varies. Never reuse a previous PDF's offset.

5. **Read the target printed pages** (via the computed PDF indices) and confirm the body's claim is actually present there.

6. **Report a dataset table** — one row per cited page: 인용 페이지 | 원문 내용 | 본문 인용과 일치 여부 (✅/⚠️/❌). State clearly whether the page numbers are correct or need fixing.

## Quick Reference

| Symptom | Cause | Fix |
|---|---|---|
| Cited page shows title/blank page | Read PDF index instead of printed page | Derive offset (step 4) |
| Footer number missing on a page | Chapter-opening or figure-only page | Read an adjacent page to anchor the offset |
| PDF filename number ≠ `[NN]` | referernce/ uses download order, 참고문헌 uses citation order | Match by title, not number |
| No 〔인용 페이지〕 in entry | 원문 미확보 문헌 | Skip PDF dual-check |

## Common Mistakes

- **Trusting the PDF page index = printed page.** The #1 error. Always anchor on a footer number first.
- **Reusing an offset across documents.** Each PDF's front matter differs.
- **Verifying the page exists but not the *content*.** The claim in the body must be supported by that exact page, not merely "the paper is about this topic."
- **Confusing referernce/ file numbers with citation `[NN]`.** They are independent numbering schemes.
