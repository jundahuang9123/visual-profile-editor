"""Claude through the official Anthropic SDK.

Structured output uses the SDK's ``parse`` helper with a pydantic model, so the
answer is constrained to the schema on the server side. Sampling parameters are
not sent (current Claude models reject them); depth is steered with
``output_config.effort``. If a request is declined on policy grounds the API may
re-run it on a fallback model (``fallbacks="default"``); a final refusal is
reported as ``LLMRefusal``.
"""
from __future__ import annotations

from typing import Any

import anthropic
from pydantic import BaseModel

from ..contracts import LLMSettings
from .base import Completion, LLMError, LLMRefusal, LLMUnavailable

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, *, refusal_fallback: bool = True) -> None:
        # With no explicit key the SDK resolves credentials itself (environment or a saved profile).
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._refusal_fallback = refusal_fallback

    def default_model(self) -> str:
        return DEFAULT_MODEL

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
        request: dict[str, Any] = {
            "model": model,
            "max_tokens": settings.max_output_tokens,
            # The system prompt is the stable part of every request of a run: cache it.
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
            "output_format": schema,
            "output_config": {"effort": settings.effort},
        }
        if self._refusal_fallback:
            request["betas"] = [FALLBACK_BETA]
            request["fallbacks"] = "default"
        client = self._client.with_options(timeout=settings.timeout_seconds)
        try:
            response = client.beta.messages.parse(**request)
        except anthropic.AuthenticationError as exc:
            raise LLMUnavailable("Anthropic rejected the API key.") from exc
        except anthropic.PermissionDeniedError as exc:
            raise LLMUnavailable(f"The API key may not use this model or feature: {exc.message}") from exc
        except anthropic.NotFoundError as exc:
            raise LLMUnavailable(f"Unknown model '{model}': {exc.message}") from exc
        except anthropic.RateLimitError as exc:
            raise LLMUnavailable("Anthropic rate limit reached; retry later.") from exc
        except anthropic.BadRequestError as exc:
            raise LLMError(f"Anthropic rejected the request: {exc.message}") from exc
        except anthropic.APIStatusError as exc:
            raise LLMUnavailable(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMUnavailable("Could not reach the Anthropic API.") from exc

        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            category = getattr(details, "category", None) or "unspecified"
            raise LLMRefusal(f"The model declined the request (category: {category}).")
        if response.stop_reason == "max_tokens":
            raise LLMError("The answer was cut off at the output token limit; raise max_output_tokens.")

        parsed = getattr(response, "parsed_output", None)
        text = parsed.model_dump_json() if isinstance(parsed, BaseModel) else ""
        if not text:
            text = "".join(block.text for block in response.content if block.type == "text")
        usage = response.usage
        return Completion(
            text=text,
            model=response.model,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            stop_reason=response.stop_reason or "",
        )

    def list_models(self) -> list[str]:
        try:
            return [model.id for model in self._client.models.list()]
        except anthropic.APIError as exc:
            raise LLMUnavailable(f"Could not list models: {exc}") from exc
