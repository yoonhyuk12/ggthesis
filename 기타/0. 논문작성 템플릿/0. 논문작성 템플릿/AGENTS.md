# Codex Project Instructions

## Canonical project guidance

Before starting work in this repository, read [CLAUDE.md](./CLAUDE.md) completely and treat it as the canonical project-level guidance.

- Apply every relevant instruction from CLAUDE.md throughout the task.
- If CLAUDE.md changes, follow the updated file; do not rely on a stale summary.
- Do not duplicate the full contents of CLAUDE.md here. CLAUDE.md is the single source of truth for the research workflow, installed infrastructure, academic standards, and HWPX handling.
- Higher-priority system, developer, user, security, sandbox, and tool instructions always take precedence.

## Codex compatibility mapping

Some instructions in CLAUDE.md use Claude Code terminology. Adapt them to the capabilities available in the current Codex session:

- “Advisor” means the primary Codex agent.
- “Worker”, “Agent tool”, “subagent_type”, and model names such as “opus” mean an available Codex sub-agent or parallel worker. Delegate only when the current session instructions permit delegation and the work is concrete and independently verifiable.
- If a requested Claude-specific agent, slash command, hook, MCP server, or skill is unavailable, inspect the referenced local documentation and use the closest available Codex workflow. State any material limitation instead of pretending the capability exists.
- Paths under .claude may contain useful project assets and instructions, but they are not automatically Codex skills. Read the relevant instruction files before using them.
- Verify delegated work directly by inspecting changes and running appropriate checks, as required by CLAUDE.md.

## Academic work defaults

For academic research and writing tasks:

- Respond and write deliverables in Korean unless the user requests another language.
- Follow the evidence hierarchy, citation-verification, contradiction-reporting, and AI-disclosure rules in CLAUDE.md.
- Route full research or paper-production workflows through the Academic Research Skills guidance described in CLAUDE.md when those local resources are usable.
- Use the narrower claude-research tools or instructions for focused literature, bibliography, review, reproducibility, and document-quality tasks.
- Never invent a citation, DOI, bibliographic field, quotation, statistic, or source finding. Clearly label unverified or inferred information.

## HWPX files

Follow the HWPX rules in CLAUDE.md:

- Use the configured HWPX MCP tools for .hwpx files when they are available.
- Read and inspect before modifying.
- Do not open or edit .hwpx as plain text or treat it as a normal text file.
- Preserve the original when requested and verify generated or modified output.
- Do not claim that binary .hwp is supported by the HWPX workflow.
