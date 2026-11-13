"""The one place where a model is called.

``LLMClient.generate`` adds, for every provider alike:

* schema validation of the answer, with ONE corrective retry that shows the
  model its validation errors;
* an audit record per call (prompts, answer, tokens, duration) on the blackboard;
* a replay cache keyed by the full request, so re-running a stage does not pay
  for (or re-roll) answers that were already given. Model output is not
  deterministic even at fixed settings, so the stored answer IS the record of
  what a run decided.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..contracts import LLMCallRecord, LLMSettings
from ..store.blackboard import Store
from .base import LLMError, LLMInvalidOutput, LLMRefusal, Provider

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMClient:
    def __init__(
        self,
        provider: Provider,
        settings: LLMSettings,
        *,
        store: Store | None = None,
        project_id: str = "",
        use_cache: bool = True,
    ) -> None:
        self.provider = provider
        self.settings = settings
        self.store = store
        self.project_id = project_id
        self.use_cache = use_cache

    @property
    def author(self) -> str:
        return f"llm:{self.provider.name}/{self.model_for('')}"

    def model_for(self, purpose: str) -> str:
        return self.settings.step_models.get(purpose) or self.settings.model or self.provider.default_model()

    def generate(
        self,
        *,
        system: str,
        user: str,
        schema: type[ModelT],
        purpose: str,
        subject_id: str = "",
        stage: str = "",
        prompt_version: str = "",
        context: dict[str, Any] | None = None,
        variant: int = 0,
    ) -> tuple[ModelT, LLMCallRecord]:
        """Ask the model for an instance of ``schema``.

        ``variant`` distinguishes otherwise identical requests (independent votes)
        so that each gets its own answer and its own cache slot.
        """
        model = self.model_for(purpose)
        request_hash = _request_hash(
            self.provider.name, model, self.settings.effort, prompt_version, schema.__name__, system, user, variant
        )
        record = LLMCallRecord(
            stage=stage,
            purpose=purpose,
            subject_id=subject_id,
            provider=self.provider.name,
            model=model,
            prompt_version=prompt_version,
            request_hash=request_hash,
            system_prompt=system,
            user_prompt=user,
        )

        if self.use_cache and self.store is not None:
            cached = self.store.find_cached_call(request_hash)
            if cached is not None:
                try:
                    parsed = schema.model_validate_json(cached.response_text)
                except ValidationError:
                    parsed = None
                if parsed is not None:
                    record.response_text = cached.response_text
                    record.cached = True
                    return parsed, self._save(record)

        started = time.monotonic()
        try:
            parsed, completion_text = self._call_and_validate(system, user, schema, model, context, record)
        except LLMRefusal as exc:
            record.status, record.error = "refused", str(exc)
            record.duration_ms = int((time.monotonic() - started) * 1000)
            self._save(record)
            raise
        except LLMInvalidOutput as exc:
            record.status, record.error = "invalid_output", str(exc)
            record.duration_ms = int((time.monotonic() - started) * 1000)
            self._save(record)
            raise
        except LLMError as exc:
            record.status, record.error = "error", str(exc)
            record.duration_ms = int((time.monotonic() - started) * 1000)
            self._save(record)
            raise
        record.response_text = completion_text
        record.duration_ms = int((time.monotonic() - started) * 1000)
        return parsed, self._save(record)

    def _call_and_validate(
        self,
        system: str,
        user: str,
        schema: type[ModelT],
        model: str,
        context: dict[str, Any] | None,
        record: LLMCallRecord,
    ) -> tuple[ModelT, str]:
        prompt = user
        last_error = ""
        for attempt in range(2):
            completion = self.provider.complete(
                system=system, user=prompt, schema=schema, model=model, settings=self.settings, context=context
            )
            record.model = completion.model or model
            record.input_tokens += completion.input_tokens
            record.output_tokens += completion.output_tokens
            record.cache_read_tokens += completion.cache_read_tokens
            try:
                return schema.model_validate_json(completion.text), completion.text
            except ValidationError as exc:
                last_error = _short_validation_error(exc)
                record.response_text = completion.text
                if attempt == 0:
                    prompt = (
                        f"{user}\n\n---\nYour previous answer did not fit the required schema:\n{last_error}\n"
                        "Answer again with one corrected JSON object and nothing else."
                    )
        raise LLMInvalidOutput(f"The answer did not fit schema {schema.__name__}: {last_error}")

    def _save(self, record: LLMCallRecord) -> LLMCallRecord:
        if self.store is not None:
            return self.store.add_llm_call(self.project_id, record)
        return record


def _request_hash(*parts: object) -> str:
    return hashlib.sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _short_validation_error(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors()[:8]:
        location = ".".join(str(part) for part in error.get("loc", ()))
        lines.append(f"- {location or '(root)'}: {error.get('msg', '')}")
    return "\n".join(lines) or str(exc)[:400]
