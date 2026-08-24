# Rule: Audit Before Fix

## Principle

**When running audits, report ALL findings before fixing ANY of them.** Fixing issues one by one without seeing the full picture leads to missed structural problems — redundant files, inconsistent numbering across chapters, or cascading issues that a single fix can't address.

## Protocol

### 1. Scan and collect

Run the full audit (e.g., 원고 전체 점검, MD↔hwpx 대조, 인용·참고문헌 검수). Collect all findings into a single report.

### 2. Classify and present

Present findings grouped by severity:
- **Structural anomalies** — redundant files, missing sections, orphaned drafts, inconsistent 장·절 numbering
- **Consistency gaps** — MD와 hwpx 불일치, 본문 수치와 표 수치 불일치, stale cross-references
- **Convention violations** — files outside `01.docs/`, 인용 표기 형식 위반

### 3. Wait for triage

Let the user review the full list before fixing anything. He may reprioritise, skip some, or flag things Claude missed.

### 4. Fix in order

After triage, fix in the agreed order. Report each fix as completed.

## When This Applies

- Any task that involves "check and fix" or "audit and repair" (원고 점검, 검수 후 수정)
- When Claude notices multiple issues during routine work

## When to Skip

- Single known issue with explicit fix instruction
- The user says "just fix everything you find"

## Why This Matters

Fixing issues before seeing the full picture leads to surface-level fixes while the real structural issue goes unnoticed until the user points it out.
