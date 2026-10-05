from __future__ import annotations

import json
import os
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from memory_loom.runner import ModelRequest, ModelResponse


class OpenAIResponsesAdapter:
    provider = "openai"

    def __init__(
        self,
        model: str,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "https://api.openai.com/v1",
        input_cost_per_million: float | None = None,
        output_cost_per_million: float | None = None,
        timeout_seconds: float = 120,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.model = model
        self._api_key_env = api_key_env
        self._base_url = base_url.rstrip("/")
        self._input_cost = input_cost_per_million
        self._output_cost = output_cost_per_million
        self._timeout = timeout_seconds
        self._opener = opener

    def generate(self, request: ModelRequest) -> ModelResponse:
        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise RuntimeError(f"{self._api_key_env} is required")

        payload = {
            "model": request.model,
            "instructions": request.system_prompt,
            "input": request.user_prompt,
            "max_output_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "store": False,
        }
        http_request = Request(
            f"{self._base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(http_request, timeout=self._timeout) as response:
                document = json.loads(response.read())
        except HTTPError as error:
            detail = (
                "authentication failed"
                if error.code in {401, 403}
                else _http_error_message(error)
            )
            raise RuntimeError(f"OpenAI API returned HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError("OpenAI API request failed") from error

        output_text = _output_text(document)
        usage = document.get("usage") or {}
        input_tokens = _optional_int(usage.get("input_tokens"))
        output_tokens = _optional_int(usage.get("output_tokens"))
        total_tokens = _optional_int(usage.get("total_tokens"))
        return ModelResponse(
            output_text=output_text,
            response_id=document.get("id"),
            provider_model=(
                document.get("model")
                if isinstance(document.get("model"), str)
                else None
            ),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=_estimated_cost(
                input_tokens,
                output_tokens,
                self._input_cost,
                self._output_cost,
            ),
        )


def _output_text(document: dict[str, object]) -> str:
    parts: list[str] = []
    for item in document.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
    if not parts:
        raise RuntimeError("OpenAI response contained no output text")
    return "".join(parts)


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def _estimated_cost(
    input_tokens: int | None,
    output_tokens: int | None,
    input_cost_per_million: float | None,
    output_cost_per_million: float | None,
) -> float | None:
    if (
        input_tokens is None
        or output_tokens is None
        or input_cost_per_million is None
        or output_cost_per_million is None
    ):
        return None
    return (
        input_tokens * input_cost_per_million
        + output_tokens * output_cost_per_million
    ) / 1_000_000


def _http_error_message(error: HTTPError) -> str:
    try:
        document = json.loads(error.read())
        message = document.get("error", {}).get("message")
        if isinstance(message, str) and message:
            return message
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return "request rejected"
