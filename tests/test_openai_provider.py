from __future__ import annotations

import json

import pytest

from memory_loom.openai_provider import OpenAIResponsesAdapter
from memory_loom.runner import ModelRequest


class FakeResponse:
    def __init__(self, document: dict[str, object]) -> None:
        self._body = json.dumps(document).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_openai_adapter_uses_responses_api_and_captures_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def opener(request, *, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "id": "resp_test",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "Reviewed."}],
                    }
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                },
            }
        )

    monkeypatch.setenv("TEST_OPENAI_KEY", "secret-test-value")
    adapter = OpenAIResponsesAdapter(
        "gpt-test",
        api_key_env="TEST_OPENAI_KEY",
        base_url="https://example.test/v1/",
        input_cost_per_million=2,
        output_cost_per_million=10,
        opener=opener,
    )

    result = adapter.generate(_request())

    assert result.output_text == "Reviewed."
    assert result.response_id == "resp_test"
    assert result.total_tokens == 120
    assert result.estimated_cost_usd == pytest.approx(0.0004)
    assert captured["url"] == "https://example.test/v1/responses"
    assert captured["body"]["store"] is False
    assert captured["body"]["instructions"] == "Follow the current request."
    assert captured["headers"]["Authorization"] == "Bearer secret-test-value"


def test_openai_adapter_requires_configured_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MISSING_OPENAI_KEY", raising=False)
    adapter = OpenAIResponsesAdapter("gpt-test", api_key_env="MISSING_OPENAI_KEY")

    with pytest.raises(RuntimeError, match="MISSING_OPENAI_KEY is required"):
        adapter.generate(_request())


def _request() -> ModelRequest:
    return ModelRequest(
        system_prompt="Follow the current request.",
        user_prompt="Review this code.",
        provider="openai",
        model="gpt-test",
        seed=0,
        temperature=0,
        top_p=1,
        max_output_tokens=128,
    )
