"""Claude Code CLI backend."""

from __future__ import annotations

from council_cli.backends.base import CLIBackend
from council_cli.config import BACKENDS


class ClaudeBackend(CLIBackend):
    """Wrapper for Anthropic's Claude Code CLI (claude -p)."""

    name = "claude"
    command = "claude"

    def __init__(self, model: str | None = None) -> None:
        spec = BACKENDS["claude"]
        self.default_model = model or spec.default_model

    def build_args(self, prompt: str, *, model: str | None = None) -> list[str]:
        effective_model = model or self.default_model
        return [
            "claude",
            "-p", prompt,
            "--model", effective_model,
        ]
