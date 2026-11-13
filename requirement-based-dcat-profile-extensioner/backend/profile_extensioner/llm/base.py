"""Provider-neutral interface of the model layer.

A provider turns (system prompt, user prompt, output schema) into JSON text.
Everything else (schema validation, the corrective retry, call records, the
replay cache) lives in ``LLMClient`` so that it behaves the same for every
provider, including the offline mock.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from ..contracts import LLMSettings


class LLMError(Exception):
    """Base class of everything the model layer raises."""


class LLMUnavailable(LLMError):
    """No usable provider: not configured, bad credentials, unknown model, or unreachable."""


class LLMRefusal(LLMError):
    """The model declined to answer."""


class LLMInvalidOutput(LLMError):
    """The model answered, but not with JSON that fits the requested schema."""


@dataclass
class Completion:
    text: str                      # the answer as JSON text
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    stop_reason: str = ""
    notes: list[str] = field(default_factory=list)


class Provider(Protocol):
    """One model backend. Implementations must be safe to call from several threads."""

    name: str

    def default_model(self) -> str: ...

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
        """Return JSON text for ``schema``. ``context`` is a machine-readable copy of what the
        prompt says; hosted providers ignore it, the offline mock answers from it."""
        ...

    def list_models(self) -> list[str]: ...


def strict_json_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema of a pydantic model in the "strict" dialect most structured-output
    endpoints want: every property required, no additional properties, no defaults."""

    def visit(node: Any) -> Any:
        if isinstance(node, list):
            return [visit(item) for item in node]
        if not isinstance(node, dict):
            return node
        node = {key: visit(value) for key, value in node.items() if key != "default"}
        if node.get("type") == "object" or "properties" in node:
            properties = node.get("properties", {})
            node["required"] = list(properties.keys())
            node["additionalProperties"] = False
        return node

    return visit(copy.deepcopy(schema.model_json_schema()))
