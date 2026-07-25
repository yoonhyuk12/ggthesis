# Rule: Plan Before Implementing

## When This Applies

- Multi-file edits (touching 3+ files)
- New chapters/sections or significant additions
- Unclear or ambiguous scope
- Restructuring existing 원고 or 문서 구조

## When to Skip

- Single-file fixes (typos, one-line corrections)
- Running existing skills (`verifying-citation-pages` 등)
- Informational questions

## Assumption Check (Medium Tasks)

For tasks that don't need a full plan but involve choices that could go wrong (1-2 files, clear goal, ambiguous *how*). This is the gap where most "wrong approach" friction occurs.

**When this applies:**
- Edits where output location, format, naming, or convention could be ambiguous
- Any task where you're choosing between options without being told which
- Tasks where scope boundaries are fuzzy ("fix this" — just the bug, or also surrounding issues?)

**What to do:**
Before making changes, state in 2-4 lines:
1. What you're about to do and which files you'll touch
2. Key assumptions (target paths, format, scope boundaries — e.g., "MD만 수정, hwpx 반영은 별도 지시 대기")

Then **wait for confirmation**. One word from the user ("yes", "go", "응") is enough.

**Skip the check when:** instruction is fully explicit; direct follow-up where assumptions were already confirmed; the user says "just do it".

## Quick Mode

For experimental/exploratory tasks: skip full planning.

**Triggers:** "quick", "try this", "experiment", "일단 해봐", "그냥 해줘"; single-file exploration.

**What stays:** verification, all safety rules (hwpx 보존 규칙 포함). Kill switch: "stop" any time.

## Protocol

1. **Draft a plan** before making changes
2. **Save the plan** to `plan/YYYY-MM-DD_설명.md` (기존 `plan/` 디렉토리 사용)
3. **Get approval** — present the plan to the user and wait for confirmation
4. **Implement**, noting any deviations from the plan

## Session Recovery

When starting a new session or after context compression:

1. Read the most recent file in `plan/` — where the last plan left off
2. Follow the CLAUDE.md 문서 인덱스 to load only the `docs/*.md` parts needed

## Execution Stall Detector

When a plan already exists (in `plan/` or stated by the user), enforce execution momentum:

- **2-message rule:** If 2 consecutive messages pass after a plan is confirmed and no file has been edited, STOP reading/auditing and start implementing immediately. Print: "Stall detected — starting execution now."
- **No re-planning approved plans:** Do not re-read, re-audit, or re-draft a plan that the user has already approved. Start from step 1 and make changes.
- **File-edit-first:** When implementing, make the first file change within your next response. Read only the files you need to edit, not the entire project.

## Important

- Plans are living documents — update them if scope changes mid-implementation
- Quick plans (3-5 lines) are fine for medium tasks; full format for large ones
