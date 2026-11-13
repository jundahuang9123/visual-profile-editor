"""LLMClient: validation with one corrective retry, audit records, replay cache. No network."""
import pytest
from pydantic import BaseModel

from profile_extensioner.contracts import LLMSettings
from profile_extensioner.llm.base import Completion, LLMInvalidOutput, LLMRefusal, strict_json_schema
from profile_extensioner.llm.client import LLMClient
from profile_extensioner.llm.registry import Credentials, provider_status
from profile_extensioner.store.blackboard import Store


class Answer(BaseModel):
    verdict: str
    score: int = 0
    note: str | None = None


class ScriptedProvider:
    """Returns the scripted texts in order and remembers the prompts it was given."""

    name = "scripted"

    def __init__(self, texts):
        self.texts = list(texts)
        self.prompts = []

    def default_model(self):
        return "scripted-1"

    def complete(self, *, system, user, schema, model, settings, context=None):
        self.prompts.append(user)
        text = self.texts.pop(0)
        if isinstance(text, Exception):
            raise text
        return Completion(text=text, model=model, input_tokens=10, output_tokens=5)

    def list_models(self):
        return ["scripted-1"]


def client(provider, store=None, **kwargs):
    return LLMClient(provider, LLMSettings(provider="mock"), store=store, project_id="p1", **kwargs)


def test_valid_answer_is_parsed_and_recorded():
    store = Store()
    provider = ScriptedProvider(['{"verdict": "ok", "score": 3}'])
    parsed, record = client(provider, store).generate(system="s", user="u", schema=Answer, purpose="propose", subject_id="a1")
    assert parsed.verdict == "ok" and parsed.score == 3
    assert record.status == "ok" and record.input_tokens == 10 and record.id
    calls = store.list_llm_calls("p1", subject_id="a1")
    assert len(calls) == 1 and calls[0].user_prompt == "u" and calls[0].model == "scripted-1"


def test_invalid_answer_gets_one_corrective_retry():
    provider = ScriptedProvider(['{"score": "many"}', '{"verdict": "fixed"}'])
    parsed, record = client(provider).generate(system="s", user="u", schema=Answer, purpose="propose")
    assert parsed.verdict == "fixed"
    assert "did not fit the required schema" in provider.prompts[1]
    assert record.input_tokens == 20  # both attempts are accounted for


def test_two_invalid_answers_raise_and_are_recorded():
    store = Store()
    provider = ScriptedProvider(["not json", "{}"])
    with pytest.raises(LLMInvalidOutput):
        client(provider, store).generate(system="s", user="u", schema=Answer, purpose="propose")
    assert store.list_llm_calls("p1")[0].status == "invalid_output"


def test_refusal_is_recorded_and_propagates():
    store = Store()
    provider = ScriptedProvider([LLMRefusal("declined")])
    with pytest.raises(LLMRefusal):
        client(provider, store).generate(system="s", user="u", schema=Answer, purpose="propose")
    assert store.list_llm_calls("p1")[0].status == "refused"


def test_replay_cache_and_vote_variants():
    store = Store()
    provider = ScriptedProvider(['{"verdict": "first"}', '{"verdict": "second"}'])
    llm = client(provider, store)
    first, _ = llm.generate(system="s", user="u", schema=Answer, purpose="propose")
    again, record = llm.generate(system="s", user="u", schema=Answer, purpose="propose")
    assert again.verdict == first.verdict == "first" and record.cached is True
    other, _ = llm.generate(system="s", user="u", schema=Answer, purpose="propose", variant=1)
    assert other.verdict == "second"  # a different vote is a different request


def test_strict_schema_requires_every_property():
    schema = strict_json_schema(Answer)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"verdict", "score", "note"}
    assert "default" not in schema["properties"]["score"]


def test_credentials_never_leave_as_text():
    credentials = Credentials()
    credentials.set("anthropic", "sk-ant-secret")
    status = provider_status(credentials)
    assert "sk-ant-secret" not in repr(status)
    assert next(item for item in status if item["provider"] == "anthropic")["key_source"] == "workbench"
    credentials.clear("anthropic")
