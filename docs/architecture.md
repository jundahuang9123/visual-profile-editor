# Construct-DCAT Profile Editor Architecture

This application is a downstream profile editor. The reusable backend functions for LinkML loading, RDF import, SHACL export, RDF export, JSON Schema generation, and generic FastAPI app creation come from `General-Ontology-Editor`.

Construct-DCAT-specific code stays in this repository:

- `schemas/profile.yaml` is the active profile source.
- `profiles/templates/` contains selectable profile starting points.
- `backend/app/profile_*` modules add profile validation and export packaging.
- `frontend/` contains the specialized profile workflow and terminology.

The dependency direction is always:

```text
ConstructDCAT-with-LinkML -> General-Ontology-Editor
```
