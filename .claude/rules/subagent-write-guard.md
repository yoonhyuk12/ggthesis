# Rule: Sub-Agent Write Guard

## Principle

**Sub-agents must not run `git commit`, `git push`, hwpx 쓰기 도구, or any other write/build command without explicit authorisation in the prompt.** The orchestrator (main context) handles all git activity, all hwpx edits, and all file edits outside the assigned scope. This applies even when a sub-agent could plausibly infer that a write is the natural next step.

hwpx는 특히 위험하다: 쓰기 도구는 호출 즉시 저장되고, 병렬 쓰기는 race condition으로 문서를 깨뜨린다. **hwpx 쓰기는 항상 메인 컨텍스트가 단독·순차로 수행한다.**

## What "explicit authorisation" looks like

The sub-agent prompt must contain something like:

> "You are authorised to: edit files matching `01.docs/*.md`. You are NOT authorised to run git commands, hwpx write tools, or edit any other file."

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
- Do NOT call any hwpx MCP **read** tool either (get_document_text,
  get_document_outline, get_paragraph_text, find_text 등 mcp__hwpx__ 전부).
  학위논문 본문은 2.5MB라 이 도구들이 40분 넘게 응답 없이 멈춘다(2026-09-11 실제 발생).
  본문은 오케스트레이터가 넘긴 문단 덤프 JSON(base_paras.json)이나
  Python zipfile+ElementTree로만 읽는다.
- Do NOT call any rhwp MCP **write** tool (`mcp__rhwp__hwp_doc_save`, `hwp_doc_replace_text`,
  `hwp_doc_set_cell`, `hwp_doc_fill_fields`, `hwp_convert_*`, `hwp_scaffold`, `hwp_insert_*`,
  `hwp_delete_*`, `hwp_set_*`, `hwp_apply_*`, `hwp_fit_table`, `hwp_replace_text`, `hwp_fill_fields` 등
  — `.claude/settings.json` deny 목록 111종). rhwp는 저장 시 패키지 전체를 IR에서 재생성해
  사용자 직접 수정분을 지운다. 읽기(`hwp_open`/`hwp_doc_search`/`hwp_doc_text`)·진단(`hwp_layout_anomaly`,
  `hwp_ir_diff`)·내보내기(`hwp_export_*`)만 허용된다.
- Do NOT edit `MEMORY.md`, `CLAUDE.md`, `.claude/**`, `03.plan/**`, or any project-level
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

## hwpx 분석 위임 시 브리프에 반드시 넣을 것 (2026-09-11 사고 재발 방지)

- **문단 덤프를 먼저 만들어 넘긴다.** `Contents/section2.xml`을 파싱해 `{idx, text, runs[[charPrIDRef, text]]}` JSON을 스크래치에 두고 경로를 브리프에 적는다. 워커가 hwpx를 직접 열 이유를 없앤다.
- **산출물 스키마를 JSON으로 고정한다** (`replace[{hwpx_idx, old_hwpx, new}]`, `insert_after`, `headings`, `user_edits` …). "보고서를 써라"만 하면 워커는 자기 번호 체계(표 셀 문단을 뺀 번호 등)로 보고해 다시 시켜야 한다.
- **문단 번호는 덤프의 `idx`(표 셀 문단 포함, 문서 순서)만 쓰라고 명시**한다.
- **bash 환경변수 이름에 `GROUPS`를 쓰지 마라**(bash 내장 읽기전용 변수라 값이 전달되지 않는다).

## 워커 무응답 시 복구 절차

heartbeat만 오고 60분 넘게 산출물이 없으면 `unverifiable`이라도 방치하지 말고 화면을 본다.
1. `orca terminal read --terminal <handle> --screen --json` — grok TUI 화면에서 `Run (Hwpx) Get Document Text 40m…` 같은 멈춘 도구 호출을 확인
2. `orca terminal send --terminal <handle> --interrupt` 로 호출을 끊고
3. `orca terminal send --terminal <handle> --text "<MCP 금지·덤프 사용 지시>" --enter` 로 직접 지시한다 (오케스트레이션 mail은 도구 호출 중인 워커에게 닿지 않는다)

## When This Applies

- Every Agent tool dispatch where the sub-agent has `Edit`, `Write`, `Bash`, or MCP write tools available

## When to Skip

- Read-only sub-agents (`subagent_type: Explore`, search-only) — explicit forbid-list optional
- Single-file lookup or grep tasks

## Anti-Patterns

- **Don't** assume "drafted a section → push it into hwpx" is the natural sub-agent flow. It isn't. The orchestrator decides.
- **Don't** rely on the sub-agent reading these rules — they don't auto-load in sub-agent context. Inline the forbid-list.
- **Don't** dispatch multiple sub-agents that write to the same hwpx file. Ever.
