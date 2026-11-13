# requirement-based-dcat-profile-extensioner

An LLM-driven, human-supervised workbench that **extends a DCAT / DCAT-AP
application profile from requirement atoms**, keeps every added class, property
and tightened constraint **traceable to the atoms it covers**, and **checks that
the result still conforms to the base profile**.

```
requirement atoms ─► Intake ─► Retrieve ─► Propose ─► Verify ─► Repair ─► Consolidate ─► Compile ─► Conformance ─► Review & sign-off
   (term-free)      lint +    reusable    LLM fills   V1-V6,    LLM,       one element     SHACL,      static rules +   human has the
                    subject   terms from  typed       trace T1, ≤ N        per class +     LinkML,     pySHACL witness  final say
                    → class   base +      changes     judge T2  rounds     property        DSV, docs   vs official base
                              vocabulary
```

## What it does

* **LLM-based, provider of your choice.** Anthropic (official SDK), any
  OpenAI-compatible endpoint (OpenAI, Ollama, vLLM, gateways), or an offline rules
  provider (no key; used by the tests and as a no-LLM baseline). The API key is
  entered on the workbench (or via environment variable) and kept **in server
  memory only**: it is never written to the blackboard, the logs or any export.
* **The model decides, the human has the final say.** The model proposes one
  typed decision per atom (covered by the base / needs a change / out of scope /
  unclear) and fills typed `ProfileChange` records. It never writes SHACL. Every
  proposal is checked symbolically; what passes and is confident enough is
  *auto-accepted* and stands unless a human overrules it. Everything else is
  repaired (bounded rounds) and then queued for review. Nothing is released
  without a human **sign-off**, and any later change of a decision withdraws it.
* **Traceability is structural.** Every change lists the atoms it covers, with a
  reason and a verbatim quote of the atom, and each constraint it sets or
  tightens has its own justification with the base value next to the new one.
  The trace is carried into every artefact (`prov:wasDerivedFrom` in SHACL and
  DSV, annotations in LinkML, a CSV trace matrix, the documentation).
* **Reuse first.** Retrieval ranks what the base already defines on the atom's
  class first; reuse an existing term > tighten a base constraint > mint a new
  term, and a minted term must say why no candidate fits (check V4).
* **Conformance to the base.** Final rules C1-C7 (see
  [docs/conformance.md](docs/conformance.md)): only legal refinements, no
  contradiction, own namespace for new terms, no invented terms, full trace,
  valid SHACL, and witness data that pySHACL validates against the **official**
  DCAT-AP shapes.
* **Everything stays on the workbench.** An append-only blackboard records what
  every rule, model call and person did; each model call is stored with its full
  prompts, answer and token counts, and can be replayed from a cache.

## The workbench (resembles VPE and Dataspecer)

* **Profile canvas** (React Flow, VPE's visual language): one card per class the
  extension touches; rows show *refine* (tightens the base), *reuse* and *new*
  elements with obligation and cardinality, inherited base properties can be
  expanded. Like Dataspecer's profile model, a class card is a *profile of* a base
  class and each row is a property profile with its own cardinality and
  requirement level.
* **Inspector**: for an element, the plain-language statement, the atoms it
  covers (with quotes), the constraint table (base → new, tightened/added), the
  alternatives and why they were rejected, every check result, provenance and
  the exact model calls. For an atom: lint findings, how the model read it, its
  disposition, the retrieved candidates and the changes covering it.
* **Review queue** with Accept / Reject / Undecided / Edit (an edit becomes a new,
  re-verified version; the old one is kept), atom-level overrides, conflicts, and
  the final sign-off.
* **Conformance** report, **Artefacts** (SHACL, minted vocabulary, LinkML for
  VPE, DSV for Dataspecer, ProfileDelta for the RQ2 evaluator, trace matrix,
  documentation) and the **Blackboard log**.
* **Model & pipeline** panel: provider, key, model, effort; switches for
  retrieval, the judge, automatic acceptance, votes, repair rounds and
  namespaces to hide from the index (leakage control for benchmark runs).

## Run it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
(cd frontend && npm ci && npm run build)
cd backend && uvicorn profile_extensioner.api.app:app --port 8020
# open http://localhost:8020 → New project → example: materials-testing-lab → Run all
```

Use a model: open *Model & pipeline*, choose *Anthropic* (default model
`claude-opus-5-5`) or an *OpenAI-compatible* endpoint, paste the key, save, run.
Or set `ANTHROPIC_API_KEY` / `RBDPE_LLM_API_KEY` + `RBDPE_LLM_BASE_URL` and
`RBDPE_LLM_PROVIDER` before starting the server. Frontend development:
`cd frontend && npm run dev` (port 5175, proxies `/api` to 8020).

Tests never call a model: `pytest -q` (59 tests).

## Layout

| Path | What |
|------|------|
| `backend/profile_extensioner/contracts.py` | All typed records (atoms, changes, trace, checks, blackboard, reports) |
| `backend/profile_extensioner/engine/` | Stages: `intake`, `retrieve`, `propose`, `verify`, `repair`, `consolidate`, `pipeline` (orchestration, decision policy, human actions); prompts and output schemas |
| `backend/profile_extensioner/knowledge/` | Base-profile registry (official SHACL + obligations), SHACL reader, vocabulary index |
| `backend/profile_extensioner/conformance/` | Refinement comparison (shared by check V3 and the final report) and the C1-C7 report |
| `backend/profile_extensioner/compile/` | SHACL, minted vocabulary, LinkML, DSV, documentation, trace matrix, ProfileDelta |
| `backend/profile_extensioner/llm/` | Provider layer, schema-validated client with call records and replay cache, offline provider |
| `backend/profile_extensioner/store/` | SQLite blackboard |
| `backend/profile_extensioner/data/base-profiles/` | DCAT-AP 3.0.0 and 3.0.1 (official SHACL, CC BY 4.0, unmodified) |
| `scripts/build_base_profile.py` | Rebuilds a base profile from a SEMICeu/DCAT-AP checkout |
| `examples/materials-testing-lab/` | Synthetic demo atoms (not benchmark gold) |
| `docs/` | [design](docs/design.md), [conformance rules](docs/conformance.md) |

## Status and limits

Research prototype. Known limits: lexical retrieval only (no embeddings); the
vocabulary index currently holds the terms the base profile uses (vendored
vocabulary files can be added under `data/vocab/` with a `MANIFEST.json`);
controlled-vocabulary usage levels of DCAT-AP 3.0.1 are not modelled; the
offline provider is a lexical baseline, not a modelling authority.

DCAT-AP shapes and specification data: © European Union, CC BY 4.0
(SEMICeu/DCAT-AP). Code: Apache-2.0.
