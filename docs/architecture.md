# Visual Profile Editor Architecture

This application is a downstream profile editor. The reusable backend functions for LinkML loading, RDF import, SHACL export, RDF export, JSON Schema generation, and generic FastAPI app creation come from `General-Ontology-Editor`.

Construct-DCAT-specific code stays in this repository:

- `schemas/profile.yaml` is the active profile source.
- `profiles/templates/` contains selectable profile starting points.
- `backend/app/profile_*` modules add profile validation and export packaging.
- `frontend/` contains the specialized profile workflow and terminology.

The dependency direction is always:

```text
Visual Profile Editor -> General-Ontology-Editor
```

## Requirement Extraction & Reuse Recommendation Service

The requirement/reuse component is intentionally separated from the profile editor backend:

```text
frontend -> backend proxy (/api/requirements/*) -> requirement-reuse-service
```

This keeps parser dependencies and future LLM/vector-search experiments isolated while preserving a single workbench experience. The first implementation is deterministic and rule-based: it extracts metadata requirements, semantic anchors, reusable term candidates, and draft SHACL/profile artifacts from text, AAS JSON, `.aasx` packages, DCAT metadata, and lightweight IFC evidence.

The service follows a reuse-first ordering:

1. DCAT/DCAT-AP terms
2. existing Construct-DCAT profile terms
3. AAS/BOT/IFC/IDTA semantic resources
4. extension terms only when no reusable term fits

Generated profile and SHACL artifacts are draft outputs. The frontend keeps the user in the loop by requiring recommendation review before merging generated profile elements into the visual editor.
