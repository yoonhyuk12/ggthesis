# Rule: Sub-Agent Write Guard

## Principle

**Sub-agents must not run `git commit`, `git push`, hwpx 쓰기 도구, or any other write/build command without explicit authorisation in the prompt.** The orchestrator (main context) handles all git activity, all hwpx edits, and all file edits outside the assigned scope. This applies even when a sub-agent could plausibly infer that a write is the natural next step.

hwpx는 특히 위험하다: 쓰기 도구는 호출 즉시 저장되고, 병렬 쓰기는 race condition으로 문서를 깨뜨린다. **hwpx 쓰기는 항상 메인 컨텍스트가 단독·순차로 수행한다.**

## What "explicit authorisation" looks like

The sub-agent prompt must contain something like:

> "You are authorised to: edit files matching `논문구조/*.md`. You are NOT authorised to run git commands, hwpx write tools, or edit any other file."

The default is read-only + scoped writes. Explicit affirmation expands the surface.

## Standard forbid-list (paste into prompts that need it)

```
## Scope of action — DO NOT do these things

This sub-agent has a narrow scope. It does NOT inherit the orchestrator's
authorisation for any other action. Do NOT do any of the following, even if
they would seem like a natural next step:

- Do NOT run `git add`, `git commit`, `git push`, or any other git write command.
- Do NOT call any hwpx write tool (search_and_replace, replace_*, apply_*,
  set_*, insert_*, delete_*, add_*, create_* 등 mcp__hwpx__ 쓰기 계열).
  The orchestrator handles all hwpx edits, sequentially.
- Do NOT edit `MEMORY.md`, `CLAUDE.md`, `.claude/**`, `plan/**`, or any project-level
  documentation file.
- Do NOT edit or create any file outside the assigned scope.

If you find yourself wanting to do any of these, stop and include what
you were about to do in your final summary. The orchestrator decides.
```

## Citation forbid-list clause (drafting sub-agents)

Sub-agents that draft 논문 원고 MUST NOT invent citations. Paste this into any drafting sub-agent's prompt (in addition to the standard forbid-list above):

```
You may draft prose, but you must NOT invent citations.
Allowed: (1) cite only papers listed in the brief or in .claude/reference/05-참조자료.md,
exactly as given; (2) if a claim needs a source you don't have, write
[CITE_TODO: 주장 요약] instead of a citation.
Forbidden: inventing plausible 저자(연도) citations; asserting page numbers
you have not seen; silently replacing [CITE_TODO] with a guessed citation.
Return a CITES_USED list and a CITE_TODOS list.
```

## When This Applies

- Every Agent tool dispatch where the sub-agent has `Edit`, `Write`, `Bash`, or MCP write tools available

## When to Skip

- Read-only sub-agents (`subagent_type: Explore`, search-only) — explicit forbid-list optional
- Single-file lookup or grep tasks

## Anti-Patterns

- **Don't** assume "drafted a section → push it into hwpx" is the natural sub-agent flow. It isn't. The orchestrator decides.
- **Don't** rely on the sub-agent reading these rules — they don't auto-load in sub-agent context. Inline the forbid-list.
- **Don't** dispatch multiple sub-agents that write to the same hwpx file. Ever.
