# Gemini Project Instructions

## Canonical project guidance

The following file is the single source of truth for this research project and is imported automatically into Gemini CLI's project context:

@./CLAUDE.md

Apply every relevant instruction from the imported file throughout the task. If `CLAUDE.md` changes, use the newly imported content rather than a previous summary. Higher-priority system, developer, user, security, sandbox, and tool instructions always take precedence.

## Gemini compatibility mapping

Some imported instructions use Claude Code terminology. Interpret them as follows when working in Gemini CLI:

- “Advisor” means the primary Gemini agent in the current session.
- “Worker”, “Agent tool”, `subagent_type`, and model names such as “opus” mean an available Gemini sub-agent or delegated worker. Delegate only when the current Gemini environment supports it and the task is concrete, independent, and verifiable.
- If sub-agent delegation is unavailable, perform the work directly and parallelize safe, independent tool calls where possible. Do not claim that a worker was used when none was available.
- Claude slash commands, agents, hooks, MCP servers, and skills are not automatically Gemini capabilities. Inspect the referenced local instruction files and use the closest available Gemini tool or workflow.
- Files under `.claude/` and the `academic-research-skills/` or `claude-research/` directories are project resources. Read the relevant `SKILL.md`, command, rule, or documentation file before adapting it; do not assume it has been registered as a Gemini skill.
- Tool names may differ between Claude Code and Gemini CLI. Use the tool that provides the same function, and report any material limitation instead of simulating unavailable functionality.
- Verify delegated or tool-generated work by inspecting the resulting files and running proportionate checks before reporting completion.

## Academic work defaults

- Respond and write deliverables in Korean unless the user requests another language.
- For manuscript writing, revision, or review, read `3. 기타/박종용교수님_논문작성요령20260707.md` completely before acting and treat it as the highest-priority local manuscript guide.
- Follow the evidence hierarchy, citation verification, contradiction reporting, and AI-disclosure rules imported from `CLAUDE.md`.
- Never invent a citation, DOI, bibliographic field, quotation, statistic, source finding, or verification result. Clearly label information that is unverified or inferred.
- Use the installed academic-research resources according to the routing rules in `CLAUDE.md`; use only the subset relevant to the current request.

## HWPX handling

- Use the configured HWPX MCP tools for `.hwpx` work when those tools are available in the Gemini session.
- Read and inspect a document before modifying it, preserve the original when requested, and verify generated or modified output.
- Do not open, parse, or edit `.hwpx` as ordinary plain text. Do not treat binary `.hwp` as supported by the HWPX workflow.
- If the HWPX MCP server is unavailable, state the limitation and request an appropriate conversion or environment change rather than using an unsafe substitute.

## Context verification

- Gemini CLI should load this root `GEMINI.md` automatically and expand the `@./CLAUDE.md` import.
- After either file changes during an active session, refresh the context with `/memory refresh` (or the equivalent command supported by the installed Gemini CLI version).
- When diagnosing instruction loading, inspect the effective context with `/memory show` and confirm that both `GEMINI.md` and `CLAUDE.md` appear.
