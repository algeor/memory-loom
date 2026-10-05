from __future__ import annotations

import json
import subprocess

from memory_loom.claude_provider import ClaudeCliAdapter
from memory_loom.runner import ModelRequest


def test_claude_cli_adapter_isolated_invocation_and_usage() -> None:
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "is_error": False,
                    "subtype": "success",
                    "session_id": "session-001",
                    "result": "Reviewed.",
                    "total_cost_usd": 0.001,
                    "modelUsage": {
                        "claude-haiku-4-5-20251001": {
                            "inputTokens": 100,
                            "outputTokens": 20,
                            "canonicalModel": "claude-haiku-4-5",
                        }
                    },
                }
            ),
            stderr="",
        )

    adapter = ClaudeCliAdapter("haiku", runner=runner)
    response = adapter.generate(_request())

    assert response.output_text == "Reviewed."
    assert response.provider_model == "claude-haiku-4-5"
    assert response.total_tokens == 120
    assert response.estimated_cost_usd == 0.001
    assert captured["input"] == "Review this code."
    command = captured["command"]
    assert "--safe-mode" in command
    assert "--disable-slash-commands" in command
    assert "--strict-mcp-config" in command
    assert command[command.index("--tools") + 1] == ""
    assert "Review this code." not in command


def _request() -> ModelRequest:
    return ModelRequest(
        system_prompt="Follow the current request.",
        user_prompt="Review this code.",
        provider="claude-cli",
        model="haiku",
        seed=0,
        temperature=0,
        top_p=1,
        max_output_tokens=128,
    )
