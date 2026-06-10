# Requirement Extraction & Representation

This document describes the requirement extraction stage of the
requirement-reuse-service: how profile-design requirements are derived from
heterogeneous domain materials and represented as traceable records
(thesis stage 1 / RQ1).

## Traceable requirement records

Every extracted requirement is a `CandidateRequirement` record connecting:

- **source evidence** — verbatim spans with machine-checkable locators
  (`chars:120-240`, `sentence:3`, JSON paths, IFC references);
- **stakeholder needs / user tasks** — `supports_user_tasks` links to
  expert-provided competency questions and user tasks, enabling
  competency-question coverage evaluation;
- **FAIR relevance** — `fair_dimensions` plus a rationale;
- **candidate metadata actions** — reuse-first term suggestions
  (`dcterms:`, `dcat:`, `prov:`, `skos:` before `cx:` extensions);
- **validation evidence** — placeholder populated by later workflow stages;
- **extraction provenance** — which strategy/model/prompt produced the
  candidate, whether its evidence passed verification, and an
  `editor_history` slot for measuring expert corrections (H1).

The normative schema lives in
[`requirement-reuse-service/schema/requirement_record.linkml.yaml`](../requirement-reuse-service/schema/requirement_record.linkml.yaml)
(LinkML). The Pydantic models in
`requirement_reuse_service/models.py` mirror it; records serialize as JSON over
the API and as YAML in the requirement-set registry.

## Extraction strategies

The `strategy` field on `analyze-artifacts` / `extract-requirements` requests
selects one of three strategies (the comparison conditions of the evaluation
plan, Section 6.2):

| Strategy | Description |
| --- | --- |
| `rules` | Deterministic keyword/structure heuristics (baseline). Always available, no network access. |
| `llm` | LLM-assisted extraction. The model receives evidence-unit records plus user tasks and returns structured requirement records. |
| `hybrid` | LLM records first; rule-based records covering metadata needs the LLM missed are appended. Duplicate detection surfaces overlaps for review. |

If the LLM provider is unavailable or misconfigured, the service falls back to
rule-based results and reports the reason in `warnings` (the response
`strategy` field always states what actually ran).

### Verbatim evidence guard

LLM output is only trusted where it can be verified: every evidence quote must
cite an `evidence_unit_id` and occur verbatim (whitespace-tolerant) inside that
evidence unit's `content`. Verified quotes keep the cited evidence unit id plus
a subspan locator; unknown evidence ids or unverifiable quotes are discarded
with a warning. Requirements left without verified evidence get
`validation_status=missing_evidence`, capped confidence, and
`provenance.evidence_verified=false`. Human review state remains separate in
`status`.

Machine validation also checks candidate terms:

- unknown reused/specialized terms set `validation_status=unknown_term`;
- obvious resource mismatches such as `dcat:mediaType` on `Dataset` set
  `validation_status=resource_mismatch`;
- `create_extension` actions must use `cx:` terms, otherwise they get
  `validation_status=needs_review`.

## LLM provider configuration (plug and play)

The service is provider-agnostic. Configure via environment variables:

| Variable | Meaning |
| --- | --- |
| `RRS_LLM_PROVIDER` | `disabled`, `anthropic`, `openai-compatible`, or `mock` |
| `RRS_LLM_MODEL` | model id (default for anthropic: `claude-opus-4-8`) |
| `RRS_LLM_BASE_URL` | base URL for OpenAI-compatible endpoints |
| `RRS_LLM_API_KEY` | API key for OpenAI-compatible endpoints |
| `ANTHROPIC_API_KEY` | key for the native Anthropic provider |

Examples:

```bash
# Anthropic (native SDK, structured outputs)
export ANTHROPIC_API_KEY=<your-anthropic-api-key>

# Local Ollama model
export RRS_LLM_PROVIDER=openai-compatible
export RRS_LLM_BASE_URL=http://localhost:11434/v1
export RRS_LLM_MODEL=qwen3

# OpenRouter / OpenAI / vLLM / Groq / Mistral / DeepSeek ... — same pattern
export RRS_LLM_PROVIDER=openai-compatible
export RRS_LLM_BASE_URL=https://openrouter.ai/api/v1
export RRS_LLM_API_KEY=<your-openrouter-api-key>
export RRS_LLM_MODEL=meta-llama/llama-3.3-70b-instruct
```

With no provider, key, or base URL configured, the provider resolves to
`disabled`; `llm` and `hybrid` requests fall back to `rules` with a warning.
`mock` is a deterministic offline client used by the test suite and only runs
when `RRS_LLM_PROVIDER=mock`. The `/health` endpoint reports the active
provider and model.

## Requirement-set registry

Reviewed (or freshly extracted) requirement sets persist as git-friendly YAML
files (default directory `requirement-sets/`, override with
`RRS_REQUIREMENT_STORE`). Service endpoints:

- `POST /save-requirement-set` — `{name, description?, analysis | requirements, user_tasks}`
- `POST /list-requirement-sets`
- `POST /load-requirement-set` — `{id}`

All three are proxied by the main app under `/api/requirements/...`.

## RQ1 evaluation export

The registry is a convenience store for reviewed requirement sets; the full
experiment export is `POST /export-rq1-dataset` (proxied as
`/api/requirements/export-rq1-dataset`). It reruns the requested strategy and
returns requirements, evidence units, duplicate groups, user tasks, warnings,
review/editor history, and summary metrics such as counts by type, scope, and
validation status.

## CLI runner

`scripts/extract_requirements.py` runs extraction over a corpus folder and
saves a requirement set — useful for experiments and strategy comparisons:

```bash
# Rule-based baseline over the bundled sample corpus
python scripts/extract_requirements.py examples/requirement-corpus --strategy rules --name baseline

# LLM-assisted run with the same corpus (compare the two saved sets)
ANTHROPIC_API_KEY=... python scripts/extract_requirements.py examples/requirement-corpus \
    --strategy llm --name llm-pilot
```

Files named `*competency*` or `*tasks*` in the corpus are read as user tasks
(one statement per line); everything else becomes an artifact.

## Roadmap (next stages)

- Normalization/duplicate clustering upgrade (embeddings or LLM-assisted) on
  top of the lexical baseline.
- Term-mapping against an indexed local vocabulary collection instead of the
  hardcoded property catalog.
- Workbench UI for correction logging (`provenance.editor_history`) and
  competency-question coverage display.
- Evaluation harness: coverage, traceability completeness, redundancy, and
  expert-agreement metrics over saved requirement sets; gold-annotation format
  for the formative pilot.
