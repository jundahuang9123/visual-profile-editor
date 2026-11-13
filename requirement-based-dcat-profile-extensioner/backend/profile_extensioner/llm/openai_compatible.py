"""Any endpoint that speaks the OpenAI chat-completions dialect (OpenAI, Ollama,
vLLM, LM Studio, university gateways ...). Plain HTTP, no vendor SDK.

Structured output is requested with ``response_format: json_schema``. Endpoints
that do not know it get one retry with ``json_object`` and the schema spelled
out in the system prompt; the answer is validated by ``LLMClient`` either way.
"""
from __future__ import annotations

import json
import time
from typing import Any

import httpx
from pydantic import BaseModel

from ..contracts import LLMSettings
from .base import Completion, LLMError, LLMUnavailable, strict_json_schema


class OpenAICompatibleProvider:
    name = "openai-compatible"

    max_retries = 5

    def __init__(self, base_url: str, api_key: str | None = None, *, default_model: str | None = None) -> None:
        if not base_url:
            raise LLMUnavailable("An OpenAI-compatible provider needs a base URL (for example http://localhost:11434/v1).")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model

    def default_model(self) -> str:
        if not self._default_model:
            raise LLMUnavailable("Choose a model for the OpenAI-compatible provider.")
        return self._default_model

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _post(self, body: dict[str, Any], timeout: float) -> httpx.Response:
        """POST with retries on rate limits (429) and server errors (5xx), honouring Retry-After."""
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(f"{self._base_url}/chat/completions", headers=self._headers(), json=body, timeout=timeout)
            except httpx.TimeoutException as exc:
                if attempt == self.max_retries:
                    raise LLMUnavailable(f"{self._base_url} did not answer in time: {exc}") from exc
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            except httpx.HTTPError as exc:
                raise LLMUnavailable(f"Could not reach {self._base_url}: {exc}") from exc
            if response.status_code != 429 and response.status_code < 500 or attempt == self.max_retries:
                return response
            wait = delay
            retry_after = response.headers.get("retry-after") if hasattr(response, "headers") else None
            if retry_after:
                try:
                    wait = max(wait, float(retry_after))
                except ValueError:
                    pass
            time.sleep(min(wait, 120.0))
            delay = min(delay * 2, 60.0)
        return response

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        model: str,
        settings: LLMSettings,
        context: dict[str, Any] | None = None,
    ) -> Completion:
        json_schema = strict_json_schema(schema)
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": json_schema, "strict": True},
            },
        }
        if settings.temperature is not None:
            body["temperature"] = settings.temperature
        notes: list[str] = []
        response = self._post(body, settings.timeout_seconds)
        if response.status_code == 400:
            # The endpoint may not support json_schema: fall back to json_object + schema in the prompt.
            notes.append("json_schema response format rejected; retried with json_object")
            body["response_format"] = {"type": "json_object"}
            body["messages"][0]["content"] = (
                f"{system}\n\nAnswer with one JSON object that validates against this JSON Schema:\n"
                f"{json.dumps(json_schema)}"
            )
            response = self._post(body, settings.timeout_seconds)
        if response.status_code in (401, 403):
            raise LLMUnavailable("The endpoint rejected the API key.")
        if response.status_code == 404:
            raise LLMUnavailable(f"Unknown model or endpoint ({self._base_url}, model '{model}').")
        if response.status_code == 429:
            raise LLMUnavailable("Rate limit reached; retry later.")
        if response.status_code >= 400:
            raise LLMError(f"Endpoint error {response.status_code}: {response.text[:400]}")
        try:
            data = response.json()
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected response shape from {self._base_url}: {response.text[:400]}") from exc
        usage = data.get("usage") or {}
        return Completion(
            text=_strip_code_fence(text),
            model=data.get("model") or model,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            stop_reason=str(choice.get("finish_reason") or ""),
            notes=notes,
        )

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self._base_url}/models", headers=self._headers(), timeout=20.0)
            response.raise_for_status()
            return sorted(item["id"] for item in response.json().get("data", []) if "id" in item)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise LLMUnavailable(f"Could not list models at {self._base_url}: {exc}") from exc


def _strip_code_fence(text: str) -> str:
    """Some local models wrap JSON in a Markdown fence even when asked not to."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()
