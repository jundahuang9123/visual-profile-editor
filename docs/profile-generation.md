# RQ2: Requirements-Driven DCAT-AP Profile Generation

This document describes how reviewed RQ1 requirements become a reviewable
DCAT/DCAT-AP application profile extension. For RQ1 (extraction and
representation) see [requirement-extraction.md](requirement-extraction.md).

## Boundary between RQ1 and RQ2

- **RQ1 does not generate the final profile.** It produces reviewed,
  structured, evidence-traceable requirements with *candidate* metadata
  actions.
- **RQ2 does not redo requirement extraction.** It consumes requirements with
  `status = approved` only and turns them into profile change proposals,
  reusable term choices, constraints, and a generated profile draft.
- **Nothing mutates the active profile silently.** Every stage produces a
  reviewable proposal; the generated draft is merged into the visual editor
  only by explicit user action.

## Pipeline

```text
Approved RQ1 RequirementSet
        ↓ POST /generate-profile-changes
ProfileChangeSet                      (reviewable proposals; accept/reject in UI)
        ↓ POST /generate-profile-draft
LinkML profile draft + SHACL shapes   (generated from accepted changes only)
        ↓ POST /export-rq2-package
RQ2 package (draft + SHACL + provenance mapping)
        ↓ explicit user action in the workbench
Visual editor merge
```

## ProfileChangeSet — the explainable intermediate model

Requirements are never converted directly into LinkML slots. The intermediate
`ProfileChangeSet` (normative schema:
[`requirement-reuse-service/schema/profile_change.linkml.yaml`](../requirement-reuse-service/schema/profile_change.linkml.yaml))
makes the RQ1 → RQ2 transition reviewable and explainable. Each
`ProfileChange` carries:

- `change_type`: `reuse_property | specialize_property |
  create_extension_property | create_profile_class | add_constraint |
  add_usage_note | add_controlled_vocabulary`;
- `target_class` (`dcat:Dataset`, `dcat:Distribution`, `dcat:Catalog`,
  `dcat:DataService`), term URI, slot name, range, obligation level,
  required/multivalued flags;
- **provenance**: `source_requirement_ids` and `evidence_ids` back to the RQ1
  records and evidence units;
- `review_status` (`candidate | accepted | rejected | needs_review`) and
  per-change warnings.

Generation rules:

- the **term registry** (`term_registry.py`) resolves candidate terms in
  reuse-priority order (DCAT/DCAT-AP/DCTERMS, then PROV/SKOS/FOAF, then `cx:`
  extensions), expands/compacts URIs, and checks domain compatibility
  (e.g. `dcat:mediaType` belongs on `dcat:Distribution`);
- unknown terms, non-`cx:` extension proposals, and domain mismatches mark the
  change `needs_review` with a visible warning — such changes are excluded
  from generation until a reviewer resolves or accepts them;
- duplicate requirements proposing the same slot on the same class are folded
  into one change (strongest obligation wins, requirement/evidence ids merge).

## Generated artifacts

**LinkML profile draft.** Profile classes are generated only for targeted base
classes (`ConstructionDatasetProfile is_a DcatDataset`, distribution/catalog/
data-service analogues), each annotated with `profile_of`, `profile_base`, and
`generated_from_requirements`. Slots carry `term_kind`
(`profile`/`extension`), `source_vocabulary`, `obligation_level`, `rationale`,
`source_requirement_ids`, and `source_evidence_ids` annotations.

**SHACL.** Generated from the *same* change set: one node shape per profile
class (`cx:ConstructionDatasetProfileShape sh:targetClass dcat:Dataset`),
obligation mapped to severity (`mandatory` → `sh:minCount 1` +
`sh:Violation`; `recommended` → `sh:Warning`; `optional` → `sh:Info`),
`sh:nodeKind sh:IRI` for URI-valued ranges, and requirement provenance in
`sh:description`.

**RQ2 package** (`rq2-profile-generation-package-v1`): change set, LinkML
draft, SHACL, warnings, validation notes, and a `provenance_mapping` table
(`requirement_id` → `profile_element` → `change_id` → `evidence_unit_ids`).

## Endpoints

Proxied through the main app under `/api/requirements/...`:

| Endpoint | Purpose |
| --- | --- |
| `POST /generate-profile-changes` | approved requirements → `ProfileChangeSet` |
| `POST /generate-profile-draft` | reviewed change set → LinkML draft + SHACL |
| `POST /generate-shacl-from-profile-changes` | SHACL only, from the same change set |
| `POST /export-rq2-package` | full reproducibility package |

The legacy `POST /generate-shacl` (recommendation-based) remains for backward
compatibility but the change-set pipeline above is the primary path.

## Workbench flow

1. **Requirement Review** — approve/reject/edit/merge/split (all edits logged
   to `provenance.editor_history`).
2. **Profile changes** button — refuses to run with zero approved
   requirements; server warnings (unverified evidence, missing actions) are
   shown, not hidden.
3. **Profile Changes tab** — accept/reject each proposed change; source
   requirements and evidence counts are visible per change.
4. **Generated Profile tab** — LinkML + SHACL preview with validation notes;
   `Merge Draft` is the only action that touches the active editor model.
5. **Export** — RQ1 dataset, RQ2 package, SHACL, LinkML.

## Example outputs

Generated from `examples/requirement-corpus` (rules strategy, simulated
review): see `examples/rq2-exports/` — `rq2-profile-package-example.json`,
`generated-profile.linkml.yaml`, `generated-shacl.ttl`.
