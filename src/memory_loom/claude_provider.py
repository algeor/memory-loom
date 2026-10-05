from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from memory_loom.runner import ModelRequest, ModelResponse


class ClaudeCliAdapter:
    provider = "claude-cli"

    def __init__(
        self,
        model: str,
        *,
        executable: str = "claude",
        timeout_seconds: float = 180,
        working_directory: Path | None = None,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.model = model
        self._executable = executable
        self._timeout = timeout_seconds
        self._working_directory = working_directory or Path(tempfile.gettempdir())
        self._runner = runner

    def generate(self, request: ModelRequest) -> ModelResponse:
        command = self._command(request)
        completed = self._runner(
            command,
            input=request.user_prompt,
            capture_output=True,
            text=True,
            check=False,
            timeout=self._timeout,
            cwd=self._working_directory,
        )
        if completed.returncode != 0:
            raise RuntimeError("Claude CLI provider request failed")
        try:
            document = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("Claude CLI returned invalid JSON") from error
        if document.get("is_error") is True or document.get("subtype") != "success":
            raise RuntimeError("Claude CLI provider request failed")
        output = document.get("result")
        if not isinstance(output, str) or not output:
            raise RuntimeError("Claude CLI response contained no output text")

        model_usage = document.get("modelUsage")
        usage_rows = (
            list(model_usage.values()) if isinstance(model_usage, dict) else []
        )
        input_tokens = sum(_usage_int(row, "inputTokens") for row in usage_rows)
        output_tokens = sum(_usage_int(row, "outputTokens") for row in usage_rows)
        actual_models = {
            row.get("canonicalModel")
            for row in usage_rows
            if isinstance(row, dict) and isinstance(row.get("canonicalModel"), str)
        }
        return ModelResponse(
            output_text=output,
            response_id=_optional_string(document.get("session_id")),
            provider_model=(next(iter(actual_models)) if len(actual_models) == 1 else None),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=_optional_float(document.get("total_cost_usd")),
        )

    def _command(self, request: ModelRequest) -> Sequence[str]:
        return (
            self._executable,
            "-p",
            "--output-format",
            "json",
            "--model",
            request.model,
            "--safe-mode",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--tools",
            "",
            "--system-prompt",
            request.system_prompt,
            "--no-session-persistence",
        )


def _usage_int(row: object, key: str) -> int:
    if not isinstance(row, dict):
        return 0
    value = row.get(key)
    return value if isinstance(value, int) and value >= 0 else 0


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return None
