"""Hosted providers build the right requests (no network: the clients are replaced)."""
from types import SimpleNamespace

import pytest

from profile_extensioner.contracts import LLMSettings
from profile_extensioner.engine.schemas import AttributionOut
from profile_extensioner.llm.anthropic_provider import AnthropicProvider
from profile_extensioner.llm.base import LLMRefusal
from profile_extensioner.llm.openai_compatible import OpenAICompatibleProvider


class FakeMessages:
    def __init__(self, response):
        self.response, self.request = response, None

    def parse(self, **request):
        self.request = request
        return self.response


def anthropic_with(response):
    provider = AnthropicProvider(api_key="sk-ant-dummy")
    messages = FakeMessages(response)
    fake = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    provider._client = SimpleNamespace(with_options=lambda **_: fake)
    return provider, messages


def response(stop_reason="end_turn", parsed=None):
    return SimpleNamespace(
        stop_reason=stop_reason, stop_details=SimpleNamespace(category="cyber"), parsed_output=parsed, content=[],
        model="claude-opus-5-5", usage=SimpleNamespace(input_tokens=11, output_tokens=7, cache_read_input_tokens=3),
    )


def test_anthropic_request_shape():
    parsed = AttributionOut(verdict="supported", explanation="ok", unsupported_facets=[])
    provider, messages = anthropic_with(response(parsed=parsed))
    completion = provider.complete(system="S", user="U", schema=AttributionOut, model="claude-opus-5-5",
                                   settings=LLMSettings(provider="anthropic", effort="high"))
    request = messages.request
    assert request["model"] == "claude-opus-5-5" and request["output_format"] is AttributionOut
    assert request["output_config"] == {"effort": "high"}
    assert request["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert request["fallbacks"] == "default" and request["betas"] == ["server-side-fallback-2026-07-01"]
    assert "temperature" not in request
    assert AttributionOut.model_validate_json(completion.text).verdict == "supported"
    assert (completion.input_tokens, completion.output_tokens, completion.cache_read_tokens) == (11, 7, 3)


def test_anthropic_refusal_is_raised():
    provider, _ = anthropic_with(response(stop_reason="refusal"))
    with pytest.raises(LLMRefusal):
        provider.complete(system="S", user="U", schema=AttributionOut, model="m", settings=LLMSettings(provider="anthropic"))


def test_openai_compatible_falls_back_to_json_object(monkeypatch):
    bodies = []

    def fake_post(url, headers, json, timeout):
        bodies.append(json)
        if json["response_format"]["type"] == "json_schema":
            return SimpleNamespace(status_code=400, text="unsupported")
        content = '```json\n{"verdict": "supported", "explanation": "x", "unsupported_facets": []}\n```'
        return SimpleNamespace(status_code=200, text="", json=lambda: {
            "model": "local", "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2}})

    monkeypatch.setattr("profile_extensioner.llm.openai_compatible.httpx.post", fake_post)
    provider = OpenAICompatibleProvider("http://localhost:11434/v1", None, default_model="qwen")
    completion = provider.complete(system="S", user="U", schema=AttributionOut, model="qwen",
                                   settings=LLMSettings(provider="openai-compatible"))
    assert len(bodies) == 2 and bodies[1]["response_format"] == {"type": "json_object"}
    assert "JSON Schema" in bodies[1]["messages"][0]["content"]
    assert AttributionOut.model_validate_json(completion.text).verdict == "supported"
    assert completion.notes
