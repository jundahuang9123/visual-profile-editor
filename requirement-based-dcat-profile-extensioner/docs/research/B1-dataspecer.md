# B1. Dataspecer and the Data Specification Vocabulary (DSV)

Research input for **requirement-based-dcat-profile-extensioner**. It answers: what "resemble Dataspecer" means in concrete features, what exactly a DSV file must contain so that Dataspecer accepts it, how Dataspecer's SHACL looks, whether Dataspecer checks that a profile refines its base (it does not), and how its diagram is drawn.

Everything below was read from source or measured with scripts written for this study. No Dataspecer code was executed and no import into a running Dataspecer instance was performed.

## 0. Sources, markers, headline findings

| Tag | Local path | Commit | Content |
|---|---|---|---|
| `DS/` | `/home/user/refs/dataspecer__dataspecer` | `ece634b8c52539339e95d6815b85650787a35fc7`, 2026-11-12, `main` | Dataspecer monorepo |
| `DSV/` | `/home/user/refs/mff-uk__data-specification-vocabulary` | `5c1d6555755f641179022aadb250e17474fc36a4`, 2026-04-02 | DSV 1.0.1, DSV-DAP 1.0.1, the three code lists, examples |
| `SPEC/` | `/home/user/refs/mff-uk__specifications` | `833685ef1f5efc845e8901c4ac43e68e0a8b1c98`, 2026-06-30 | Cloned for this study (sparse: `dcat-ap`, `dcat-ap-hvd`, `dcat-dap`). Dataspecer-generated DSV, SHACL and HTML of DCAT-AP 3.0.1, DCAT-AP HVD 3.0.0 and DCAT 3 DAP |
| spike | `/home/user/vpe-rq2-branch/docs/dataspecer-spike.md` | read at 6b22dd14 | Earlier spike; not repeated here, extended in 0.2 |

Markers: **(inferred)** = my conclusion from code, not stated by the source. **verify:** = not confirmed, needs a run against Dataspecer or an external document. Line numbers refer to the commits above.

"Experiment" means a script of mine in `artefacts/verify/` (it re-implements a rule; it never runs repository code). The scripts use the same parser libraries as Dataspecer: `n3` 2.13.12, `jsonld` 9.0.0, `node-html-parser` 9.0.7 (Dataspecer declares `n3 ^2.13.7`, `jsonld ^9.0.0`, `node-html-parser ^9.0.4` in `DS/services/backend/package.json:33-39`), plus `rdflib` 7.6.0 and `pyshacl` 0.40.2.

### 0.1 Ten findings that shape the design

1. **Dataspecer does not write the DSV that is published.** The published vocabulary defines `dsv:range` and `dsv:datatype` (`DSV/dsv/model.owl.ttl:109-125`). Dataspecer writes and reads `dsv:objectPropertyRange` and `dsv:datatypePropertyRange` instead (`DS/packages/data-specification-vocabulary/src/semantic-model/vocabulary.ts:56-57`, `dsv-to-rdf.ts:252,281`, `rdf-to-dsv.ts:288,319`). A file that uses only the published names loses every property profile on import. Details in 3.5.
2. **DCAT-AP exists as DSV.** The Dataspecer team republishes DCAT-AP 3.0.1 as application profile `https://mff-uk.github.io/specifications/dcat-ap#` (34 class profiles, 131 property profiles, `SPEC/dcat-ap/dsv.ttl`). An extension that Dataspecer should recognise as an extension of DCAT-AP has to point its `dsv:profileOf` at these term profiles. A ready lookup is in `artefacts/dcat-ap-dsv-index.json`.
3. **A real extension of DCAT-AP in DSV exists: DCAT-AP HVD** (`SPEC/dcat-ap-hvd/dsv.ttl`). It tightens cardinalities (0..n to 1..n) and adds a new reused property. It is the template for our Compile step (3.7).
4. **Import is by URL of an HTML page** with one embedded JSON-LD block; a bare `.ttl` is imported as a vocabulary, never as a profile (spike, confirmed). The exact resource roles and `conformsTo` values are in 3.8.
5. **An extension needs its own class profiles for every domain and range.** `dsv:domain` and the range of an object property profile must be class profiles of the same application profile (3.6, rule R5).
6. **DSV has four cardinalities only**: 0..1, 0..n, 1..1, 1..n. A lower bound above 1 or an upper bound above 1 cannot be published (3.4).
7. **Dataspecer does not check that a profile refines what it profiles.** The rule exists only as a code comment; the editor accepts any cardinality; the DSV class `dsv:InvalidTermProfile` is never produced (section 5). This check is a genuine addition of our tool.
8. **Dataspecer's SHACL loses tightened lower bounds and ignores requirement levels.** When the base profile says 0..n and the extension says 1..n, the generated shape has no `sh:minCount` (section 4.4, reproduced on the published HVD shapes). Requirement level never becomes a constraint or a severity.
9. **Dataspecer has a review screen for proposed profile changes** (application `history`, "change propagation"): items with a severity, a preselected default choice, dependencies and a "resolve manually" option. It is the closest existing pattern for "LLM decides, human reviews" (1.2.11).
10. **The conceptual-model-editor is a React Flow application** (`@xyflow/react ^12.11.2`, `DS/applications/conceptual-model-editor/package.json:42`), like the Visual Profile Editor. Its visual language (section 6) can be reproduced with custom nodes and edges.

### 0.2 What this adds to the spike

| Spike statement | Status now |
|---|---|
| SHACL is generated from profiles; "Verify: how faithful for maxCount, `sh:in`, nested shapes" | Answered. `sh:maxCount` is written when the bound is 0 or 1. `sh:in`, `sh:node`, `sh:or`, `sh:minLength` and similar are never written: the generator's SHACL vocabulary has only the terms listed in `DS/packages/shacl-v2/src/vocabulary.ts:32-57`. Lower bounds are lost on profile chains (4.4). |
| "Verify: whether SHACL is generated from an imported DSV profile" | By code yes: generation works on stored models regardless of origin (`DS/packages/specification/src/specification.ts:505-576`). verify: by running. |
| Import through HTML with embedded metadata | Confirmed, now with the exact contract, a tested example and four pitfalls (3.8). |
| HTTP routes | Same routes; two additions that matter: `POST /new/application-profile` creates an application profile of given specification URLs with optional auto-profiling (`DS/services/backend/src/routes/new.ts:32-319`), and `POST /resources/reload` re-imports and records the difference as a reviewable branch (`import.ts:737-844`). When a base name is configured the API lives under `<base>/api` (`DS/services/backend/src/main.ts:50-66`; the Docker image is built with `BACKEND=/<base path>/api`, `DS/Dockerfile:23`); no authentication middleware is registered in `main.ts`. The backend accepts `--in-memory-db` (`main.ts:38-45`). |
| No LLM features | Not re-checked beyond the packages read here; nothing LLM-related was seen in them. |

## 1. Feature inventory (Q1)

### 1.1 Applications in the monorepo

| Application | Path | What a user does there |
|---|---|---|
| Specification manager | `DS/applications/manager` | Tree of packages ("specifications") and their models. Per package: open the conceptual editor ("Edit vocabularies and application profiles"), open the structure editor ("Edit data structures"), open "History and change propagation", add a model, export all artefacts as ZIP, show the generated documentation, edit the documentation template, "Profile dataspec from URL", manage controlled vocabularies, backup, rename, tag, auto layout, edit raw JSON, delete (`src/Dir.tsx:91-262`). At root: search by title, filter by tag, **Import** (URL list or backup ZIP, `src/dialog/add-imported.tsx:49,90`) and the **project wizard** with three starts: Vocabulary, Application Profile, Data Schema (`src/dialog/project-wizard/project-wizard.tsx:45-80`). |
| Conceptual-model-editor (CME) | `DS/applications/conceptual-model-editor` | Diagram editor for vocabularies and application profiles. Section 1.2. |
| Data-specification-editor (DSE), also called structure editor or schema editor | `DS/applications/data-specification-editor` | Builds data structures (trees) on top of a semantic model: choose a root class, add attributes and associations from the model, set cardinality, datatype, regular expression, examples, technical labels, XML and JSON specifics (`src/editor/operations/*.ts`). Configures and generates the technical artefacts (`src/manager/artifacts/configuration/tabs/*.tsx`: artifact names, CSV, JSON, XML, modeling, **shacl-v2**). |
| History and change propagation | `DS/applications/history` | Shows the operation log of a project and the **evolution review**: when a profiled vocabulary or profile changed, lists proposed reactions for the dependent profile and lets the user accept them (`src/pages/evolution/*`). Section 1.2.11. |
| Controlled vocabulary manager | `DS/applications/controlled-vocabulary-manager` | Records metadata of controlled vocabularies (title, IRI pattern, concept scheme, distribution) for use in class profiles (`README.md:1-7`). |
| API specification | `DS/applications/api-specification` | Form-based OpenAPI generation from data structures (`README.md:1-20`). Not relevant here. |
| Backend | `DS/services/backend` | REST storage, import, generation (spike section 3; additions in 0.2). |

Project wizard, application-profile start (`DS/applications/manager/src/dialog/project-wizard/profile.tsx:49-76`): the user gives one or more specification URLs, a name, a base IRI (default `https://example.com/profile/vocabulary#`) and a switch "Autoprofile" (on by default: "Automatically create default profile of all concepts from profiled specifications including all structures, if any", `locales/en/project-wizard.json:12`). The backend imports the URLs, creates a profile model with `subType` `https://w3id.org/dsv#ApplicationProfile`, optionally creates a default profile of every entity, creates a visual model and redirects into the CME (`DS/services/backend/src/routes/new.ts:88-229`).

### 1.2 The conceptual-model-editor in detail

Layout: header (package save, "Save and leave", view selection, language, export menu), a catalogue on the left, the canvas on the right (`docs/main.md:25-31`; header labels in `src/application/localization-translations-en.ts:256-265`).

#### 1.2.1 Semantic models (vocabularies) versus profile models

- A package holds several **models**. A model is either a vocabulary (classes, relationships, generalizations) or a profile model (class profiles, relationship profiles, generalizations between profiles). Both are stored as "semantic models"; a model counts as a profile when its main entity has `subType` `https://w3id.org/dsv#ApplicationProfile` or when it contains at least one profile entity (`DS/packages/core-v2/src/semantic-model/profile/concepts/is-model-profile.ts:10-17`, `profile.ts:10`).
- Vocabularies come from three sources: a Turtle (or RDF/XML, JSON-LD) file by URL, parsed by the RDFS adapter (`DS/packages/rdfs/src/adapter/adapter.ts:23-32`: classes are `rdfs:Class`/`owl:Class`, properties are `rdf:Property`/`owl:ObjectProperty`/`owl:DatatypeProperty`, names from `rdfs:label` then `skos:prefLabel`, descriptions from `rdfs:comment` then `skos:definition`); a list of 19 well-known vocabulary files offered in the "Add vocabulary" dialog (ADMS, LOCN, Core Location, DCAT 3, the DCAT-AP `r5r` vocabulary, DCMI Terms, ELI, FOAF, GeoSPARQL and Simple Features, ODRL, OWL, PROF, RDF, RDFS, SKOS, SPDX, OWL-Time, vCard; `src/dialog/semantic-model/create-semantic-model/create-semantic-model-dialog-controller.tsx:7-79`); or a new empty vocabulary created in the editor.
- Imported vocabularies and imported base profiles are read-only; only local models are writable. A new profile is always placed into a writable model (`src/dialog/base-entity-profile/base-entity-profile-dialog-state.ts:222-229`).
- Entity identifiers of imported vocabulary terms and of imported profiles are their IRIs (`DS/packages/rdfs/src/adapter/adapter.ts:113-127`; `DS/services/backend/src/routes/import.ts:459-469`), which is why cross-specification references resolve by IRI.

#### 1.2.2 Class profiles and relationship (attribute, association) profiles

The data model is small (`DS/packages/core-v2/src/semantic-model/profile/concepts/`):

| Entity | Fields | File |
|---|---|---|
| Class profile | `iri`, `profiling[]` (ids of profiled classes or class profiles; several allowed), `name` + `nameFromProfiled`, `description` + `descriptionFromProfiled`, `usageNote` + `usageNoteFromProfiled`, `externalDocumentationUrl`, `tags[]` (class role), `controlledVocabularies[]`, `order` | `class-profile.ts:7-26`, `profile.ts:16-45`, `named-thing-profile.ts:6-24` |
| Relationship profile | two `ends` (domain end, range end). The range end carries everything: `iri`, `profiling[]`, name, description, usage note with their `...FromProfiled`, `concept` (range class profile or datatype IRI), `cardinality` `[min, max or null]` or `null`, `tags[]` (requirement level), `externalDocumentationUrl`. The domain end carries `concept` (domain class profile) and a cardinality. | `relationship-profile.ts:11-48` |
| Generalization between profiles | `child`, `parent` | `generalization-profile.ts:3-10` |
| Controlled vocabulary assignment | `classProfile`, `vocabulary`, `qualifier` (`must`, `at-least-one`, `recommended`, `may`), `replaces` | `controlled-vocabulary-assignment.ts:66-103` |

An attribute profile is a relationship profile whose range is a datatype; an association profile has a class profile as range. The datatype list is closed: 18 XSD types, `rdf:langString`, `rdfs:Literal`, three GeoSPARQL literals and one Czech type (`DS/packages/core-v2/src/semantic-model/datatypes/datatypes.ts:1-46`; the full list is in `artefacts/manifest.json`). Any other range IRI is treated as a class.

#### 1.2.3 How a "profile of" something is created

1. One entity: the magnet button on a node (`src/diagram/node/entity-node.tsx:242`, title "Create class profile") or the profile action of a catalogue row (`src/catalog-v3/catalog-action.ts:60,86,112,138`). It opens the profile dialog pre-filled from the profiled entity (`src/action/open-create-profile-dialog.ts:53-147`). Any class, class profile, attribute, association or their profiles can be profiled; generalizations cannot (`:141-144`).
2. Defaults of a new profile (`src/dialog/base-entity-profile/base-entity-profile-dialog-state.ts:140-217`): IRI = relative IRI taken from the profiled entity; name and description are **not** overridden (inherited from the first profiled entity); the usage note is inherited when the profiled entity is itself a profile.
3. A whole model: "Profile model" dialog with a source model and a target model (`src/dialog/profile-model/profile-model/profile-model-dialog-view.tsx:10-41`; catalogue action `catalog-action.ts:28`).
4. A whole specification at project creation: "Autoprofile" (1.1). The bulk operation is `profileEntities` (`DS/packages/profile-model/src/operations/complex/profile-entities.ts:79-131`): classes first, then relationships (domain and range re-pointed to the new class profiles), then generalizations. The IRI of each new profile is the last segment of the profiled IRI (`:66-73,169`); the cardinality of the profiled relationship is copied (`:301`); requirement-level tags are not copied for relationships (`:303`).
5. "Profile of" is editable afterwards: the dialog has a multi-select "Profile of" (`src/dialog/class-profile/edit-class-profile-dialog.tsx:42-50`).

IRI conventions suggested by the editor (`src/configuration/default-configuration.ts:28-48`): class profile `UpperCamelCase`, relationship `lowerCamelCase`, relationship profile `<DomainName>.<propertyName>`. Published data follow them: `https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint`.

#### 1.2.4 Reused versus overridden values (name, definition, usage note)

- Storage: for each of the three texts there is a pair *value* / *valueFromProfiled*. When `...FromProfiled` holds an entity id, the own value is ignored and the text is read from that entity (`named-thing-profile.ts:10-22`, `profile.ts:32-38`).
- Dialog: every text field has a checkbox **"Change in profile"** (`src/dialog/components/checkbox-override.tsx:3-20`, label at `localization-translations-en.ts:408`). Unchecked: the field is disabled and shows the inherited text; when the profile profiles several entities a selector chooses the source (`src/dialog/components/profiled-value.tsx:31-81`). Checked: the profile stores its own text. Domain cardinality and range cardinality have the same checkbox (`src/dialog/association-profile/edit-association-profile-dialog.tsx:137-175`).
- Resolution: an aggregator computes the effective entity (`DS/packages/core-v2/src/semantic-model/profile/aggregator/semantic-relationship-profile-aggregator.ts:34-166`, class counterpart in `semantic-class-profile-aggregator.ts`). The diagram and the documentation read the aggregated entity (`src/visualization.tsx:240,254,273`).
- DSV: an inherited text is written as a `dsv:PropertyValueReuse` node, an overridden one as a literal on the profile (`DS/packages/data-specification-vocabulary/src/semantic-model/entity-model-to-dsv.ts:448-494`).
- Documentation: each profile gets a table with "Profiled class IRI(s)", "IRI", "Label", "Definition", "Hierarchy", "Usage note"; the hierarchy row lists the chain "profiles class profile X ... profiles class Y", and prints the definition of a profiled entity only when it differs from the inherited one (`DS/packages/documentation/src/default-configuration.ts:281-398` for classes, `:536-655` for properties).

#### 1.2.5 Cardinalities

- Editor choices for a profile: `0..*`, `0..1`, `1..*`, `1..1`; "inherit" is the unchecked "Change in profile" box and is stored as `null` (`src/dialog/utilities/dialog-utilities.ts:519-556`, `base-relationship-profile-dialog-state.ts:150-165`).
- Effective cardinality in the aggregated view = **intersection** of the own value and all profiled values: largest lower bound, smallest upper bound (`semantic-relationship-profile-aggregator.ts:132-135,173-195`).
- Shown as `[min..max]` with `*` for unbounded (`src/util/relationship-utils.ts:124-129`).
- Three different computations exist side by side; a comparison must know which one it looks at:

| Consumer | Rule | Source |
|---|---|---|
| Diagram, documentation | intersection along the profile chain | aggregator, above |
| DSV export | the value declared on this profile only; nothing when inherited | `entity-model-to-dsv.ts:543`, `dsv-to-rdf.ts:257-258` |
| SHACL | smallest lower bound and smallest upper bound along the chain | `DS/packages/shacl-v2/src/semantic-adapter/structure-model/structure-model-factory.ts:410-473`, section 4.4 |

#### 1.2.6 Requirement level and class role

- Requirement level ("Mandatory level" in the dialog): Undefined, Mandatory, Recommended, Optional (`base-relationship-profile-dialog-state.ts:75-91`). Stored as a tag on the range end with the IRI of the code list entry (`DS/packages/profile-model/src/profile-well-known.ts:2-10`).
- Class role: Main, Supportive, stored as a tag on the class profile (`profile-well-known.ts:12-18`). The documentation groups class profiles into "Main class profiles", "Supportive class profiles" and others (`DS/packages/documentation/src/default-configuration.ts:61-92`).
- In the diagram the attribute rows of a node are grouped under titles `<<mandatory>>`, `<<recommended>>`, `<<optional>>`, or `<<undefined>>` (`src/visualization.tsx:478-480,640-663`); an association profile edge shows the level as a second, grey label line (`src/diagram/edge/property-edge.tsx:112-120`).
- Requirement level is independent of cardinality in the model; nothing ties "mandatory" to a lower bound of 1.

#### 1.2.7 Generalisations

- A generalization links a child and a parent of the same kind. Between profiles it is exported as `dsv:specializes` (`entity-model-to-dsv.ts:246-258,288,540`).
- Created by drawing an edge and choosing "generalization", or in the dialog under "specialization of" (`src/dialog/class-profile/edit-class-profile-dialog.tsx:81-89`). The choices are restricted to entities of the same model (`base-entity-profile-dialog-state.ts:165-168`).
- In SHACL the property shapes of every ancestor (through `dsv:specializes`) are added to the shape of the descendant (`DS/packages/shacl-v2/src/semantic-adapter/shacl-semantic-adapter.ts:147-169`).

#### 1.2.8 Visual models and per-vocabulary colours

- A **visual model** is one diagram: nodes with positions, edges with waypoints, groups, and a colour per semantic model (`DS/packages/visual-model/src/concepts/visual-node.ts:10-46`, `visual-relationship.ts:10-45`, `visual-model.ts:63-65`). A package can have several; the header switches between them.
- Colour precedence for a node or edge (`src/visualization.tsx:828-863`): custom colour of the visual entity, else (option) colour of the first profiled vocabulary, else colour of the model the entity belongs to, else `#9fbdffff` (`src/configuration/default-configuration.ts:55`). A new vocabulary gets a random colour from a palette of 17 (`src/util/color-utils.ts:16-242`: `#fc440f #8da266 #1effbc #4dc9ab #e63462 #d4f2d2 #8fab5c #b4e33d #b8a3d3 #ff70a6 #ff9770 #ffb770 #70d6ff #b8d6b8 #ffd670 #ff848b #92bcea`).
- Dialog headers are tinted with the model colour (`src/dialog/class-profile/edit-class-profile-dialog.tsx:28-30`), so the user always sees which model an element belongs to.
- Display options (`src/configuration/options.tsx:43-73`): label = entity label, IRI, or label of the profiled vocabulary term; colour = model or profiled vocabulary; "profile of" line = label, IRI, or hidden; range and cardinality on attribute rows on or off; `<<profile>>` prefix on relationship profile labels on or off (off by default).
- Layout algorithms through `elkjs` (force-directed, force-directed with class profiles, hierarchical, radial, overlap removal, random; `localization-translations-en.ts:540-546`), anchoring of nodes, alignment helpers, groups, minimap.

#### 1.2.9 Catalogue and search

- Six tabs (`src/catalog-v3/catalog.tsx:186-221`): Vocabularies, Classes, Relationship, Attributes, Profiles, Generalizations (labels at `localization-translations-en.ts:372-377`).
- Each tab lists entities per model in collapsible sections; under an entity its profiles and specializations are nested as a tree (`catalog.tsx:296,603,1120`).
- One search field filters the active tab by label; collapse all and expand all (`catalog.tsx:141-178`).
- Row actions (`src/catalog-v3/catalog-action.ts`): show or hide on canvas, focus, detail, edit, delete, create profile, add neighbourhood; on a model: show or hide all, edit (alias, colour, base IRI), delete, create class, association, attribute, profile the whole model.
- Search in an external vocabulary service exists for the Czech government vocabulary only (`src/dialog/external-semantic-model/`).

#### 1.2.10 Validation and warnings

What the editor checks before a dialog can be confirmed:

| Check | Source |
|---|---|
| IRI not empty | `src/dialog/base-entity/base-entity-dialog-validation.ts:4-17` |
| Domain set, range set | `src/dialog/base-relationship/base-relationship-dialog-validation.ts:4-21` |
| Controlled vocabularies: no second assignment next to a `must`; no vocabulary assigned twice; a usage qualifier cannot be weaker than the inherited one | `src/dialog/controlled-vocabularies/select-controlled-vocabularies-state.ts:68-102`, `src/dialog/components/select-qualifier.tsx:60-78` |

That is all. There is one severity (`ERROR`, `src/dialog/utilities/validation-utilities.ts:18-20`). The cardinality validation slots of the profile dialog are constants "no problem" (`base-relationship-profile-dialog-state.ts:152,163`) and are not part of the confirm condition (`edit-association-profile-dialog.tsx:215-217`). The texts "Change of cardinality may introduce a breaking change in the profile." exist as translation keys (`localization-translations-en.ts:412-415`) but nothing references them at this commit (searched all `.ts`/`.tsx` of `applications` and `packages`). `src/visualization-validation.ts` only keeps the diagram consistent with the model (removes edges whose ends disappeared, adds missing profile edges); it does not validate semantics.

#### 1.2.11 Review of proposed changes (history application)

When an imported vocabulary or base profile is reloaded, the backend records the difference as a branch instead of applying it (`import.ts:835-840`). `analyzeEvolution` / `analyzeProfileEvolution` turn the difference into **evolution items** for the dependent profile (`DS/packages/profile-model/src/hooks/semantic-model.ts:26-38`, `profile-model.ts:48-64`, `evolution-items.ts:52-241`):

- kinds: `create-class-profile`, `create-relationship-profile`, `create-generalization-profile`, `modify-profile` (one independent decision per changed field: name, description, usage note, cardinality, concept, external documentation URL), `delete-profile` (`evolution-items.ts:162-226`);
- severity: `automatic` (flows through inheritance, nothing to do), `decision` (safe default preselected), `attention` (real conflict, no safe default) (`:52-64`);
- each decision offers named choices with ready-made operations and a `defaultChoiceId`, for example `inherit`, `freeze-old`, `adopt-new`, `keep-own`, `drop-override`, `keep-override` (`:75-96,617-679,685-735`);
- items can depend on other items (`dependsOn`), for example a relationship profile on a class profile that is itself only proposed (`:153-160`).

The review screen (`DS/applications/history/src/pages/evolution/review-state.ts`, `item-card.tsx`) shows one card per item with a checkbox, the choices as buttons, a status badge (pending, applied, manual, unchecked; `review-state.ts:59`), automatic propagation of dependencies when an item is checked or unchecked (`review-state.ts:103-140`), a "resolve manually" choice that turns the item into a to-do (`:11-12`), and one "Accept update & apply selected" action (described in `DS/www/content/en/papers/iswc2026.md:73-85`).

This is not requirement-driven and has no LLM, but the structure (typed change items, severity, preselected default, dependencies, manual escape, apply selected) is exactly what a human-in-the-loop review of a `ProfileChangeSet` needs.

### 1.3 Generated artefacts

Specification level, written by `generateSpecification` (`DS/packages/specification/src/specification.ts`):

| File | Content | Source lines |
|---|---|---|
| `dsv.ttl` | Application profile in DSV (when the primary model has profiles) | 451-452, 505-549 |
| `model.owl.ttl` | RDFS/OWL vocabulary (when the primary model has classes or relationships) | 451-452, 462-502 |
| `shacl.ttl`, `shacl-<key>.ttl` | SHACL for the application profile, one file per configuration entry | 551-575 |
| `dsv.ldes.ttl`, `model.owl.ldes.ttl` | Operation log as a Linked Data Event Stream (proof of concept) | 578-597 |
| `<structure>/structure.ttl` | Data structures | 605-635 |
| `generator-configuration.ttl` | Generator configuration | 637-666 |
| `controlled_vocabulary_catalog.ttl` | DCAT catalogue of the controlled vocabularies | 668-694 |
| `<visual model id>.svg`, or `<package id>.svg` generated automatically when there is no diagram | Diagrams | 696-760 |
| `en/index.html`, `cs/index.html` | ReSpec documentation with the embedded JSON-LD specification metadata | 762-843 |

Per data structure (`DS/packages/specification/src/v1/schema-artifacts.ts:19-199`): `schema.json` (JSON Schema), `example.json`, `context.jsonld` (JSON-LD context), `schema.xsd`, `lifting.xslt`, `lowering.xslt`, `schema.csv-metadata.json` (CSV on the Web), `rdf-to-csv/`, `query.sparql`, `shacl-shapes.ttl` (older, structure-based SHACL generator `DS/packages/shacl`), `validation.shex`, `validation.shexmap`, `openapi-specification.yaml`.

In the CME itself a menu exports the current diagram as SVG, RDFS/OWL, DSV and SHACL (`src/header/export-management.tsx:162-179`).

## 2. Necessary Dataspecer functionality for our workbench (Q2)

Priority: M = must, S = should, C = could. The same items are in the structured `checklist`.

| # | Dataspecer feature | What our workbench does | Pri | Evidence |
|---|---|---|---|---|
| 1 | Layered models: read-only vocabularies, read-only base profile, one writable profile model | Three layers: vocabulary index (read-only), DCAT-AP base profile (read-only), the extension (the only thing a `ProfileChange` may touch). Every element shows its layer by colour. | M | 1.2.1, 1.2.8 |
| 2 | Profile entities with `profiling[]`; class profile and property profile as separate things from classes and properties | The extension model stores class profiles and property profiles, each with "profile of" (a base term profile) or "profiled term" (a vocabulary class or property). A `ProfileChange` creates or modifies exactly one of them. | M | 1.2.2 |
| 3 | Domain and range of a property profile are class profiles of the same profile model | Compile adds a pass-through class profile of the extension for every class used as domain or range (role "supportive", all texts reused), and Verify rejects a change whose domain or range has none. | M | 3.6 R5, `SPEC/dcat-ap-hvd/dsv.ttl:217-282` |
| 4 | Reuse or override per text (name, definition, usage note), with the source visible; "Change in profile" checkbox | Each text of a profile element is either "reused from <IRI>" or "overridden"; the default is reuse. The detail panel shows the inherited text greyed and a toggle. Compile maps reuse to `dsv:PropertyValueReuse`. | M | 1.2.4 |
| 5 | Cardinality from four values or inherited; requirement level from three values or undefined; class role main or supportive | The typed `ProfileChange` record uses exactly these enumerations. A requested cardinality outside 0..1, 0..n, 1..1, 1..n is kept for LinkML and SHACL but flagged "not expressible in DSV". | M | 1.2.5, 1.2.6, 3.4 |
| 6 | Canvas language: header in model colour, "profile of X" line, prefixed IRI, attribute rows grouped by requirement level with `[min..max]`, four edge styles | Reuse the language so that a Dataspecer user reads our canvas without a legend; add a badge with the covered requirement atoms. | M | section 6 |
| 7 | Aggregated view: inherited texts and intersected cardinalities resolved along the profile chain | Show effective values (base plus extension) next to declared values; the conformance check works on effective values. | M | 1.2.4, 1.2.5 |
| 8 | Catalogue with tabs, per-model sections, nested profiles, one search field | Left panel: Vocabularies, Classes, Properties, Profiles, plus "Requirement atoms". Search over label and IRI. Profiles nested under what they profile. | S | 1.2.9 |
| 9 | Create a profile of one entity, of a model, or of a whole specification ("Autoprofile") | Start an extension from the base profile without copying it: profile only what a requirement touches (as DCAT-AP HVD does: 29 property profiles against 131 in DCAT-AP). Offer "profile this base element" manually on any base node. | S | 1.2.3, 3.7 |
| 10 | Review of proposed changes: item kinds, severity, preselected default, dependencies, manual escape, apply selected | The review of a `ProfileChangeSet` uses the same structure: change items with severity from Verify, the LLM proposal preselected, alternatives from Repair as further choices, dependency propagation (a property profile depends on its domain class profile), "decide manually", "apply selected". | M | 1.2.11 |
| 11 | One model, many deterministic artefacts: `dsv.ttl`, `model.owl.ttl`, `shacl.ttl`, documentation, diagram, ZIP | Compile LinkML, SHACL, DSV, the vocabulary of minted terms and the HTML wrapper from one accepted change set; byte-stable output. | M | 1.3 |
| 12 | Publication contract: HTML page with JSON-LD metadata, roles and `conformsTo`, relative artefact URLs | Compile emits the wrapper of 3.8 next to the Turtle files; a "publish check" replays the import logic (`artefacts/verify/wrapper_import_check.cjs`). | M | 3.8 |
| 13 | Usage note and external documentation link per profile | Keep both fields. The usage note is the only text that reaches SHACL (`sh:description`) and the documentation. | S | 4.1 |
| 14 | Generalization between profiles (`dsv:specializes`) | Support as a change kind only when a requirement needs a subclass profile; otherwise out of scope for the first version. | C | 1.2.7 |
| 15 | Controlled vocabulary assignment with usage qualifier | Out of scope for the first version; its DSV terms are unpublished placeholders (3.3). | C | `vocabulary.ts:82-88,102-111` |

Not in Dataspecer and therefore our contribution: requirement atoms and their trace to profile elements; LLM proposals; checks of legal refinement, term existence and reuse-before-mint; a conformance verdict against the base profile.

## 3. DSV precisely (Q3)

### 3.1 Namespaces

| Prefix (as Dataspecer writes it) | IRI | Defined in |
|---|---|---|
| `dsv:` | `https://w3id.org/dsv#` | `DSV/dsv/model.owl.ttl:14-33` (version 1.0.1, `owl:versionIRI <https://w3id.org/dsv/1.0.1#>`) |
| `cardinality:` | `https://w3id.org/dsv/cardinality#` | `DSV/cardinality/cardinality.ttl` |
| `requirement:` | `https://w3id.org/dsv/requirement-level#` | `DSV/requirement-level/requirement-level.ttl` |
| `role:` | `https://w3id.org/dsv/class-role#` | `DSV/class-role/class-role.ttl` |
| `dsv-dap:` | `https://w3id.org/dsv-dap#` | `DSV/dsv-dap/dsv.ttl:20-41` (the application profile of DSV, itself written in DSV) |
| `prof:` | `http://www.w3.org/ns/dx/prof/` | W3C Profiles Vocabulary, used for the profile node and the specification metadata |
| `dct:` `skos:` | `http://purl.org/dc/terms/`, `http://www.w3.org/2004/02/skos/core#` | membership and texts |

Default prefixes of Dataspecer's writer: `rdf rdfs dct dsv owl skos vann cardinality requirement role prof`, plus the empty prefix for the profile IRI (`dsv-to-rdf.ts:69-71,99-116`). In the specification metadata `role:` means something else: `http://www.w3.org/ns/dx/prof/role/` (3.8).

### 3.2 Classes

| Class | Meaning (published `rdfs:comment`, shortened) | Lines in `DSV/dsv/model.owl.ttl` |
|---|---|---|
| `dsv:ApplicationProfile` | Identifies classes and properties from vocabularies, and class and property profiles from application profiles, that are re-used in a usage context, and lets editors adjust their description without creating subclasses or subproperties. The profile node is also a `prof:Profile`. | 39-42 |
| `dsv:TermProfile` | Common superclass. Carries context-dependent label, definition, usage note, cardinalities. | 65-68 |
| `dsv:ClassProfile` | Profile of a class. Subclass of `dsv:TermProfile`. | 87-91 |
| `dsv:PropertyProfile` | Profile of a property: name, definition, usage note, domain, range, cardinality. Subclass of `dsv:TermProfile`. Dataspecer never writes it as a type. | 131-135 |
| `dsv:ObjectPropertyProfile` | Property profile whose range is a class profile. | 104-108 |
| `dsv:DatatypePropertyProfile` | Property profile whose range is a datatype. | 115-119 |
| `dsv:PropertyValueReuse` | States which value of which property of which resource is reused for the current profile (name, definition, usage note). | 43-46 |
| `dsv:InvalidTermProfile` | "A profile, which breaks profile compliance rules. This may be for a good reason such as temporary, to be propagated upstream, inconsistency." Subclass of `dsv:TermProfile`. Not produced or consumed by Dataspecer (section 5). | 126-130 |
| `dsv:ApplicationProfileSpecificationDocument` | Human-readable version of an application profile. Subclass of `prof:ResourceDescriptor`. Used in the specification metadata. | 160-164 |
| `dsv:VocabularySpecificationDocument` | Human-readable version of a vocabulary. Subclass of `prof:ResourceDescriptor`. | 165-169 |

### 3.3 Properties

| Property | Domain, range | Meaning | Lines |
|---|---|---|---|
| `dct:isPartOf` | term profile, application profile | Membership of a term profile in its application profile. Not a DSV term; the DSV-DAP prescribes exactly one (`DSV/dsv-dap/dsv.ttl:543-556`). | - |
| `dsv:profileOf` | TermProfile, TermProfile | "Specifies a parent profile of the current profile." Points at a term profile of the base application profile. | 69-74 |
| `dsv:class` | ClassProfile, `rdfs:Class` | "The profiled class." Points at a vocabulary class. | 98-103 |
| `dsv:property` | PropertyProfile, `rdf:Property` | "The property profiled by the property profile." Points at a vocabulary property. | 136-141 |
| `dsv:specializes` | TermProfile, TermProfile | "Specifies a profile specialized by this profile." Generalization between two profiles of the same application profile. | 81-86 |
| `dsv:domain` | PropertyProfile, ClassProfile | "Class profile, which is the domain of the property profile." | 142-147 |
| `dsv:range` | ObjectPropertyProfile, ClassProfile | Published name of the object range. **Dataspecer uses `dsv:objectPropertyRange`.** | 109-114 |
| `dsv:datatype` | DatatypePropertyProfile, `rdfs:Datatype` | Published name of the datatype range. **Dataspecer uses `dsv:datatypePropertyRange`.** | 120-125 |
| `dsv:cardinality` | PropertyProfile, `skos:Concept` | Cardinality of the property profile (of its range end). Value from the cardinality code list. | 148-153 |
| `dsv:requirementLevel` | PropertyProfile, `skos:Concept` | "Requirement level of the property, typically mandatory, recommended or optional." | 154-159 |
| `dsv:classRole` | ClassProfile, `skos:Concept` | "Class role, e.g. Mandatory, Supportive, etc." The code list has `main` and `supportive`. | 92-97 |
| `dsv:reusesPropertyValue` | TermProfile, PropertyValueReuse | Points to one reuse statement. Dataspecer writes it as a blank node. | 75-80 |
| `dsv:reusedProperty` | PropertyValueReuse, `rdf:Property` | The property **on the source** whose value is reused (`rdfs:label`, `rdfs:comment`, `skos:prefLabel`, `skos:definition`, `skos:scopeNote`). | 53-58 |
| `dsv:reusedAsProperty` | PropertyValueReuse, `rdf:Property` | The property **on this profile** that receives the value. New in 1.0.1. "Expected to be one of skos:prefLabel for preferred label, skos:definition for definition, or skos:scopeNote for usage note" (`DSV/dsv-dap/dsv.ttl:926`). | 59-64 |
| `dsv:reusedFromResource` | PropertyValueReuse, `rdfs:Resource` | The source: a vocabulary term or a term profile. | 47-52 |
| `dsv:externalDocumentation` | any resource | Link to external documentation; "profiles of this resource should preferably link to this URL". | 170-175 |
| `skos:prefLabel`, `skos:definition`, `skos:scopeNote` | term profile, language-tagged literal | Overridden label, definition, usage note. Absent when the value is reused. | `dsv-to-rdf.ts:191-193` |

Terms that exist only in Dataspecer's code, not in the published vocabulary:

| Term | Status | Source |
|---|---|---|
| `dsv:objectPropertyRange`, `dsv:datatypePropertyRange` | The only range predicates Dataspecer writes and reads. Tracked upstream as `mff-uk/data-specification-vocabulary` issue 3 (link in `dsv-model.ts:243`). | `vocabulary.ts:56-57` |
| `dsv:ControlledVocabularyAssignment`, `dsv:classProfile`, `dsv:controlledVocabulary`, `dsv:usageExpectation`, `dsv:replaces`; values `https://w3id.org/dsv/usage-expectation#must`, `#at-least-1`, `#recommended`, `#may` | "placeholders, not yet part of the published dsv namespace" | `vocabulary.ts:82-88,102-111` |
| `dsv:ConceptualModel` | Legacy name of the application profile, still accepted on read | `vocabulary.ts:45`, `rdf-to-dsv.ts:78-80` |
| `dsv:1n`, `dsv:11`, `dsv:0n`, `dsv:01` | Legacy cardinality IRIs, accepted on read | `vocabulary.ts:68-72`, `rdf-to-dsv.ts:410-419` |
| `dsv:nn`, `dsv:n1`, `dsv:n0`, `dsv:10`, `dsv:00` | Written when a bound is neither 0, 1 nor unbounded, or the upper bound is 0. Unpublished; avoid. | `vocabulary.ts:65-73`, `dsv-to-rdf.ts:286-310` |
| `dsv:Structure`, `dsv:StructureConfiguration` | `conformsTo` markers in the specification metadata | `specification-description/well-known.ts:77,82` |

### 3.4 Code lists (all are `skos:Concept` in a `skos:ConceptScheme`)

| List | IRIs | Labels | Source |
|---|---|---|---|
| Cardinality | `https://w3id.org/dsv/cardinality#0n`, `#01`, `#1n`, `#11` | Zero to Many, Zero to One, One to Many, One to One | `DSV/cardinality/cardinality.ttl:7-29` |
| Requirement level | `https://w3id.org/dsv/requirement-level#mandatory`, `#recommended`, `#optional` | Mandatory, Recommended, Optional | `DSV/requirement-level/requirement-level.ttl:7-23` |
| Class role | `https://w3id.org/dsv/class-role#main`, `#supportive` | Main, Supportive | `DSV/class-role/class-role.ttl:7-17` |

Mapping from `[min, max]` used by the writer (`entity-model-to-dsv.ts:630-663`): min 0 or 1 is kept, any other min becomes "n"; max 0 or 1 is kept, anything else (unbounded or greater than 1) becomes "n". So `[1, 3]` is written as `cardinality:1n` and `[2, 5]` as the unpublished `dsv:nn`. DSV cannot carry a bounded maximum above 1.

### 3.5 Published DSV versus the DSV Dataspecer exchanges

| Aspect | Published (DSV 1.0.1, DSV-DAP 1.0.1) | Dataspecer writer and reader | Consequence for our compiler |
|---|---|---|---|
| Object range | `dsv:range`, exactly one (`DSV/dsv-dap/dsv.ttl:448-465`) | `dsv:objectPropertyRange`; the reader ignores `dsv:range` | Write `dsv:objectPropertyRange`. Optionally add `dsv:range` with the same value: the reader looks up fixed predicates and ignores others (inferred from `rdf-to-dsv.ts:98-154`). |
| Datatype range | `dsv:datatype`, exactly one (`:433-446`) | `dsv:datatypePropertyRange` | Same. |
| Profiled class | `dsv:class`, exactly one (`:577-594`) | Absent when the class profile profiles another profile (only `dsv:profileOf` then); several values possible (`DSV/dsv-dap/dsv.ttl:62`) | Follow Dataspecer: `dsv:profileOf` to the base profile, no `dsv:class`. |
| Profiled property | `dsv:property`, exactly one (`:414-431`) | Absent on a profile of a profile | Same. |
| Reuse node | `reusedProperty`, `reusedAsProperty`, `reusedFromResource`, each exactly one | Always all three; a missing `reusedAsProperty` is read as equal to `reusedProperty` (`rdf-to-dsv.ts:353-359`) | Always write `reusedAsProperty`; it must be `skos:prefLabel`, `skos:definition` or `skos:scopeNote`, otherwise the reuse is not recognised (`dsv-to-entity-model.ts:109-127,237-246`). |
| Types | `dsv:ClassProfile` etc. | Each term profile is typed twice: `dsv:TermProfile` and the specific class (`dsv-to-rdf.ts:158,189,251,280`) | Write both types. |

Experiment: Dataspecer's own `SPEC/dcat-ap-hvd/dsv.ttl` validated against the published DSV-DAP shapes `DSV/dsv-dap/shacl.ttl` with pyshacl gives 718 results, among them 29 for the missing `dsv:range`, 30 for the missing `dsv:class`, 24 for the missing `dsv:property`, and hundreds of `sh:class` results because the profiled terms are not typed inside the file (`artefacts/verify/validate_dsv_dap.py`). The DSV-DAP shapes can therefore not serve as an acceptance gate for a DSV file meant for Dataspecer.

### 3.6 Rules of Dataspecer's reader that a DSV compiler must satisfy

| # | Rule | Source |
|---|---|---|
| R1 | Exactly one subject typed `dsv:ApplicationProfile` per file. The importer converts only the first one. | `rdf-to-dsv.ts:173-178`, `DS/services/backend/src/routes/import.ts:458-459` |
| R2 | Every term profile needs `dct:isPartOf <application profile of this file>`; otherwise it is dropped with a console error. | `rdf-to-dsv.ts:260-276` |
| R3 | A property profile without `dsv:domain` is skipped silently. | `rdf-to-dsv.ts:280-283,311-314` |
| R4 | A property profile needs at least one range value in `dsv:objectPropertyRange` or `dsv:datatypePropertyRange`; only the first value is used. | `dsv-to-entity-model.ts:267-285` |
| R5 | Domain and object range must be IRIs of class profiles that the importer can resolve. Dataspecer always uses class profiles of the same application profile (the editor only offers those: `src/dialog/association-profile/edit-association-profile-dialog-state.ts:71-96` with `filterByModel`, `dialog-utilities.ts:625-630`). | also `SPEC/dcat-ap-hvd/dsv.ttl:646-667` |
| R6 | Datatype ranges should come from the closed datatype list (1.2.2). On re-export a range outside the list turns the profile into an object property profile. | `entity-model-to-dsv.ts:596-609`, `datatypes.ts:40-62` |
| R7 | `dsv:profileOf` and `dsv:reusedFromResource` must name entities that are present after the profiled specifications were imported: term profiles of the base (by their IRI) or vocabulary terms (by their IRI). | `import.ts:459-469`, 1.2.1 |
| R8 | Do not put instances typed `dcat:Dataset` into the DSV file. On import every such subject becomes a controlled-vocabulary record. | `import.ts:437`, `DS/packages/controlled-vocabulary-model/src/dcat-rdf.ts:151-155` |
| R9 | Texts are language-tagged literals. A literal without language tag is stored under the empty language. | `rdf-to-dsv.ts:143-152` |
| R10 | Always write `dsv:reusedAsProperty`, with `skos:prefLabel`, `skos:definition` or `skos:scopeNote`. | `rdf-to-dsv.ts:353-359`, `dsv-to-entity-model.ts:109-127,237-246` |

Also: unknown cardinality or requirement-level IRIs are read as "not set" (`rdf-to-dsv.ts:402-441`). The same rules are available as data in `artefacts/manifest.json` (`dsv.readerRules`).

`artefacts/verify/dsv_reader_check.cjs` checks R1 to R5 and R7 (against given base DSV files) and reports cardinality narrowing; it passes on the example below and, as a control, on Dataspecer's HVD file.

### 3.7 Minimal complete example

Scenario: an extension `https://example.org/dcat-ap-ext#` of DCAT-AP 3.0.1 that (a) profiles `dcat:Dataset` through the DCAT-AP class profile and adds the reused property `dcterms:rightsHolder`, mandatory, 1..1; (b) mints `https://example.org/dcat-ap-ext#retentionPeriod` and profiles it, optional, 0..1; (c) tightens `dcat:contactPoint` on Dataset from 0..n recommended (`SPEC/dcat-ap/dsv.ttl`, profile `https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint`) to 1..n mandatory.

How each part follows Dataspecer:

| Part of the example | Writer code | Same pattern in real output |
|---|---|---|
| Prefix block, `<AP> a prof:Profile, dsv:ApplicationProfile.` | `dsv-to-rdf.ts:99-116,128-137` | `SPEC/dcat-ap-hvd/dsv.ttl:1-15` |
| Class profile: `dct:isPartOf`, `a dsv:TermProfile`, texts, `dsv:specializes`, `dsv:profileOf`, reuse nodes, `dsv:externalDocumentation`, then `a dsv:ClassProfile`, `dsv:class`, `dsv:classRole` | `dsv-to-rdf.ts:156-172,187-218` | `SPEC/dcat-ap-hvd/dsv.ttl:16-39` |
| Property profile: shared part, then `dsv:cardinality`, `dsv:property`, `dsv:domain`, `dsv:requirementLevel`, then type and range | `dsv-to-rdf.ts:249-282` | `SPEC/dcat-ap-hvd/dsv.ttl:646-667` (tightened), `:738-753` (new reused property) |
| Reuse from a vocabulary term: `reusedProperty rdfs:label`, `reusedAsProperty skos:prefLabel` | `entity-model-to-dsv.ts:463-473` (the source property is the one the vocabulary really uses, `DS/packages/rdfs/src/adapter/adapter.ts:27-28,196-222`) | `SPEC/dcat-ap-hvd/dsv.ttl:741-746` |
| Reuse from a base profile: `reusedProperty skos:prefLabel`, `reusedAsProperty skos:prefLabel` | same function, default branch | `SPEC/dcat-ap-hvd/dsv.ttl:650-660` |
| (c) carries `dsv:profileOf` and no `dsv:property` | `entity-model-to-dsv.ts:555-578` | `SPEC/dcat-ap-hvd/dsv.ttl:646-667` |
| Statement layout expected by the writer test | `dsv-api-v1.spec.ts:356-409` | - |

File `artefacts/dsv-example.ttl` (114 triples; parses with n3 and rdflib; passes `dsv_reader_check.cjs` against `SPEC/dcat-ap/dsv.ttl`):

```turtle
# Minimal complete DSV application profile: an EXTENSION of DCAT-AP 3.0.1.
#
# Base profile (machine-readable DCAT-AP published by the Dataspecer team):
#   application profile  <https://mff-uk.github.io/specifications/dcat-ap#>
#   specification page    https://mff-uk.github.io/specifications/dcat-ap/
#
# What this file shows
#   (a) :Dataset profiles dcat:Dataset THROUGH the DCAT-AP class profile, and adds a
#       mandatory reused property (dcterms:rightsHolder) with cardinality 1..1.
#   (b) :Dataset.retentionPeriod profiles a property minted in this profile's own
#       namespace (<https://example.org/dcat-ap-ext#retentionPeriod>). The RDFS/OWL
#       definition of the minted term lives in the companion vocabulary file
#       (dsv-example-vocabulary.ttl = Dataspecer's "model.owl.ttl"), not here.
#   (c) :Dataset.contactPoint tightens a property that DCAT-AP already profiles:
#       base 0..n / recommended  ->  here 1..n / mandatory.
#
# Statement order, prefixes and predicate names follow Dataspecer's own writer:
#   dataspecer/packages/data-specification-vocabulary/src/semantic-model/dsv-to-rdf.ts
#     default prefixes ............ lines 99-116
#     application profile node ..... lines 128-137
#     class profile ................ lines 156-172
#     shared term-profile part ..... lines 187-218
#     property-profile part ........ lines 255-276
#     object property range ........ lines 249-253  (dsv:objectPropertyRange)
#     datatype property range ...... lines 278-282  (dsv:datatypePropertyRange)
#     cardinality IRIs ............. lines 286-310 and vocabulary.ts lines 65-77
# Real output of the same writer for a DCAT-AP extension (DCAT-AP HVD):
#   https://github.com/mff-uk/specifications  dcat-ap-hvd/dsv.ttl

@prefix : <https://example.org/dcat-ap-ext#>.
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix dct: <http://purl.org/dc/terms/>.
@prefix dsv: <https://w3id.org/dsv#>.
@prefix owl: <http://www.w3.org/2002/07/owl#>.
@prefix skos: <http://www.w3.org/2004/02/skos/core#>.
@prefix vann: <http://purl.org/vocab/vann/>.
@prefix cardinality: <https://w3id.org/dsv/cardinality#>.
@prefix requirement: <https://w3id.org/dsv/requirement-level#>.
@prefix role: <https://w3id.org/dsv/class-role#>.
@prefix prof: <http://www.w3.org/ns/dx/prof/>.


# ---------------------------------------------------------------------------
# The application profile itself.
# ---------------------------------------------------------------------------

<https://example.org/dcat-ap-ext#> a prof:Profile, dsv:ApplicationProfile.

# ---------------------------------------------------------------------------
# Class profiles.
# A property profile may only point (dsv:domain, dsv:objectPropertyRange) at
# class profiles of THIS application profile, so the domain class and every
# range class need a class profile here, even when nothing about them changes.
# ---------------------------------------------------------------------------

# (a) Profile of dcat:Dataset, reached through the DCAT-AP class profile.
#     Label, definition and usage note are reused unchanged from DCAT-AP.
:Dataset dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    dsv:profileOf <https://mff-uk.github.io/specifications/dcat-ap#Dataset>;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:prefLabel;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Dataset>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:definition;
  dsv:reusedAsProperty skos:definition;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Dataset>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:scopeNote;
  dsv:reusedAsProperty skos:scopeNote;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Dataset>
];
    a dsv:ClassProfile;
    dsv:classRole role:main.

# Range of :Dataset.rightsHolder.
:Agent dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    dsv:profileOf <https://mff-uk.github.io/specifications/dcat-ap#Agent>;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:prefLabel;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Agent>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:definition;
  dsv:reusedAsProperty skos:definition;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Agent>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:scopeNote;
  dsv:reusedAsProperty skos:scopeNote;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Agent>
];
    a dsv:ClassProfile;
    dsv:classRole role:supportive.

# Range of :Dataset.contactPoint.
:Kind dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    dsv:profileOf <https://mff-uk.github.io/specifications/dcat-ap#Kind>;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:prefLabel;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Kind>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:definition;
  dsv:reusedAsProperty skos:definition;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Kind>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:scopeNote;
  dsv:reusedAsProperty skos:scopeNote;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Kind>
];
    a dsv:ClassProfile;
    dsv:classRole role:supportive.

# ---------------------------------------------------------------------------
# Property profiles.
# IRI convention used by Dataspecer: <profile namespace><DomainClass>.<property>
# ---------------------------------------------------------------------------

# (a) NEW in this profile, REUSED term: dcterms:rightsHolder, mandatory, exactly one.
#     dsv:property points at the vocabulary property (there is no base property
#     profile to point at with dsv:profileOf). The label is reused from the
#     vocabulary (rdfs:label there becomes skos:prefLabel here); the definition
#     is overridden with a profile-specific text.
<https://example.org/dcat-ap-ext#Dataset.rightsHolder> dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    skos:definition "The agent that holds the rights over the Dataset."@en;
    skos:scopeNote "Exactly one rights holder has to be given for every Dataset."@en;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty rdfs:label;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource dct:rightsHolder
];
    dsv:cardinality cardinality:11;
    dsv:property dct:rightsHolder;
    dsv:domain :Dataset;
    dsv:requirementLevel requirement:mandatory;
    a dsv:ObjectPropertyProfile;
    dsv:objectPropertyRange :Agent.

# (b) NEW in this profile, MINTED term in the profile's own namespace.
#     Label and definition are reused from the minted property itself
#     (rdfs:label / rdfs:comment in the companion vocabulary file).
<https://example.org/dcat-ap-ext#Dataset.retentionPeriod> dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty rdfs:label;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource :retentionPeriod
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty rdfs:comment;
  dsv:reusedAsProperty skos:definition;
  dsv:reusedFromResource :retentionPeriod
];
    dsv:cardinality cardinality:01;
    dsv:property :retentionPeriod;
    dsv:domain :Dataset;
    dsv:requirementLevel requirement:optional;
    a dsv:DatatypePropertyProfile;
    dsv:datatypePropertyRange <http://www.w3.org/2001/XMLSchema#duration>.

# (c) TIGHTENED: DCAT-AP profiles dcat:contactPoint on Dataset as 0..n / recommended
#     (<https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint>).
#     This profile narrows it to 1..n / mandatory. dsv:profileOf points at the
#     base property profile; dsv:property is not repeated. Label and definition
#     are reused from the base profile, the usage note is overridden.
<https://example.org/dcat-ap-ext#Dataset.contactPoint> dct:isPartOf <https://example.org/dcat-ap-ext#>;
    a dsv:TermProfile;
    skos:scopeNote "At least one contact point has to be given for every Dataset."@en;
    dsv:profileOf <https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint>;
    dsv:reusesPropertyValue [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:prefLabel;
  dsv:reusedAsProperty skos:prefLabel;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint>
], [
  a dsv:PropertyValueReuse;
  dsv:reusedProperty skos:definition;
  dsv:reusedAsProperty skos:definition;
  dsv:reusedFromResource <https://mff-uk.github.io/specifications/dcat-ap#Dataset.contactPoint>
];
    dsv:cardinality cardinality:1n;
    dsv:domain :Dataset;
    dsv:requirementLevel requirement:mandatory;
    a dsv:ObjectPropertyProfile;
    dsv:objectPropertyRange :Kind.
```

Companion vocabulary for the minted term, `artefacts/dsv-example-vocabulary.ttl` (what Dataspecer calls `model.owl.ttl`; writer `DS/packages/lightweight-owl/src/generator.ts:64-74,162-208`; same shape as `DSV/dsv-dap/examples/dsv-voc.ttl`):

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#>.
@prefix prof: <http://www.w3.org/ns/dx/prof/>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix : <https://example.org/dcat-ap-ext#>.

# Companion vocabulary of dsv-example.ttl: the RDFS/OWL definition of the one
# term minted by the extension profile. In a Dataspecer project this is the
# file "model.owl.ttl", written by
#   dataspecer/packages/lightweight-owl/src/generator.ts
#     ontology node ..... lines 64-74   (a owl:Ontology, prof:Profile)
#     property .......... lines 162-208 (types, label, comment, isDefinedBy, domain, range)
#
# Keep the @prefix lines first: when the file is served with a non-RDF content
# type, Dataspecer guesses the syntax from the first character and treats a
# leading "<" as RDF/XML (packages/core/src/io/rdf/http/http-adapter.ts, lines 65-75).

<https://example.org/dcat-ap-ext#> a owl:Ontology, prof:Profile.
:retentionPeriod a rdf:Property, owl:DatatypeProperty;
    rdfs:label "retention period"@en;
    rdfs:comment "The period of time for which the publisher keeps the data of the Dataset available."@en;
    rdfs:isDefinedBy <https://example.org/dcat-ap-ext#>;
    rdfs:domain <http://www.w3.org/ns/dcat#Dataset>;
    rdfs:range <http://www.w3.org/2001/XMLSchema#duration>.
```

Notes on (b), minting:

- Dataspecer keeps minted terms in a vocabulary model and their profiles in a profile model; the two are written to two files (`specification.ts:451-452`). A model that mixes both is not exported correctly at this commit: both outputs get the file name `model.owl.ttl` (`specification.ts:452,487,534`) (inferred from the code, not run).
- The example mints inside the profile namespace, as asked. The term IRI `...#retentionPeriod` and the profile IRI `...#Dataset.retentionPeriod` cannot collide. A minted **class** would collide with its own class profile, because Dataspecer names a class profile after the profiled class (`profile-entities.ts:66-73,169`). Recommendation (our interpretation): give minted terms a namespace of their own, for example `https://example.org/dcat-ap-ext/vocabulary#`, as DCAT-AP does with `http://data.europa.eu/r5r/`.
- With one shared IRI the node `https://example.org/dcat-ap-ext#` is typed `owl:Ontology` in one file and `dsv:ApplicationProfile` in the other. The importer copes (3.8), but it is one more reason for a separate vocabulary IRI.

What the example deliberately leaves out: `dsv:specializes` (see `SPEC/dcat-ap-hvd/dsv.ttl:18`), `dsv:externalDocumentation` (`:36`), controlled vocabulary assignments, several profiled entities on one profile.

### 3.8 The HTML and JSON-LD wrapper

File `artefacts/dsv-wrapper-example.html`. The JSON-LD has the shape Dataspecer writes (`DS/packages/data-specification-vocabulary/src/specification-description/to-rdf.ts:16-180`, context `dsv-context.json:1-96`); the template puts it into the page head as the first `application/ld+json` script (`DS/packages/documentation/src/default-configuration.ts:771-776`). Real pages with the same structure: `SPEC/dcat-ap-hvd/index.html` (an extension of DCAT-AP), `DSV/dsv-dap/index.html`.

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>DCAT-AP extension (example)</title>
    <!--
      Specification-metadata wrapper that lets Dataspecer import a DSV application profile by URL.

      How Dataspecer reads this page (dataspecer/services/backend/src/routes/import.ts):
        1. importFromUrl (lines 651-686) fetches the URL. Only when the response Content-Type
           contains "text/html" is the page treated as a specification; anything else is
           imported as a plain RDFS/OWL vocabulary.
        2. It takes the FIRST script element of type application/ld+json of the page (line 665),
           expands the JSON-LD with the page URL (without fragment) as base IRI (lines 661-669)
           and hands the triples to dsvImport (lines 487-641).
        3. rdfToDSVMetadata (dataspecer/packages/data-specification-vocabulary/src/
           specification-description/from-rdf.ts, lines 19-154) looks for subjects typed
           prof:Profile; the first one is the specification that gets imported.
        4. Every entry of isProfileOf is imported first, recursively, from its
           hasResource/hasArtifact URL (import.ts lines 570-618): an HTML page is imported as a
           specification again, any other document as a vocabulary.
        5. Among the resources of the specification (import.ts lines 537-554):
             role prof:role/vocabulary .................................. RDFS/OWL vocabulary of minted terms
             role prof:role/constraints AND conformsTo dsv:ApplicationProfile
                                        AND conformsTo prof:Profile ...... the DSV application profile
           The SHACL resource (role constraints, conformsTo https://www.w3.org/TR/shacl/) is listed
           for readers and catalogues; the importer does not fetch it.

      The JSON-LD below has the shape Dataspecer writes itself
        (dataspecer/packages/data-specification-vocabulary/src/specification-description/to-rdf.ts
         and dsv-context.json; real output: https://mff-uk.github.io/specifications/dcat-ap-hvd/).
      Relative artefact URLs are resolved against the URL this page is served from, so the
      three Turtle files only have to sit next to this page.
    -->
    <script type="application/ld+json">
      {
        "@id": "https://example.org/dcat-ap-ext/",
        "@type": [
          "dsv:ApplicationProfileSpecificationDocument",
          "adms:AssetDistribution",
          "prof:ResourceDescriptor"
        ],
        "hasArtifact": "",
        "hasRole": "role:specification",
        "format": "filetype:HTML",
        "inSpecificationOf": [
          {
            "@id": "https://example.org/dcat-ap-ext#",
            "@type": [
              "dsv:ApplicationProfile",
              "prof:Profile"
            ],
            "title": {
              "en": "DCAT-AP extension (example)"
            },
            "description": {
              "en": "Example application profile that extends DCAT-AP 3.0.1 with one reused property, one minted property and one tightened cardinality."
            },
            "isProfileOf": [
              {
                "@id": "https://mff-uk.github.io/specifications/dcat-ap#",
                "title": {
                  "en": "DCAT-AP 3.0.1 based on DCAT 3 DAP"
                },
                "hasResource": {
                  "hasArtifact": "https://mff-uk.github.io/specifications/dcat-ap/"
                }
              }
            ],
            "hasResource": [
              {
                "@type": [
                  "adms:AssetDistribution",
                  "prof:ResourceDescriptor"
                ],
                "hasArtifact": "./dsv-example-vocabulary.ttl",
                "hasRole": "role:vocabulary",
                "format": "filetype:RDF_TURTLE",
                "conformsTo": [
                  "http://www.w3.org/2000/01/rdf-schema#",
                  "http://www.w3.org/2002/07/owl"
                ]
              },
              {
                "@type": [
                  "adms:AssetDistribution",
                  "prof:ResourceDescriptor"
                ],
                "hasArtifact": "./dsv-example.ttl",
                "hasRole": "role:constraints",
                "format": "filetype:RDF_TURTLE",
                "conformsTo": [
                  "prof:Profile",
                  "dsv:ApplicationProfile"
                ]
              },
              {
                "@type": [
                  "adms:AssetDistribution",
                  "prof:ResourceDescriptor"
                ],
                "hasArtifact": "./shacl-example-semic-v1.ttl",
                "hasRole": "role:constraints",
                "format": "filetype:RDF_TURTLE",
                "conformsTo": "https://www.w3.org/TR/shacl/"
              },
              {
                "@id": "https://example.org/dcat-ap-ext/",
                "@type": [
                  "dsv:ApplicationProfileSpecificationDocument",
                  "adms:AssetDistribution",
                  "prof:ResourceDescriptor"
                ],
                "hasArtifact": "",
                "hasRole": "role:specification",
                "format": "filetype:HTML"
              }
            ]
          }
        ],
        "@context": {
          "@version": 1.1,
          "prof": "http://www.w3.org/ns/dx/prof/",
          "role": "prof:role/",
          "dsv": "https://w3id.org/dsv#",
          "owl": "http://www.w3.org/2002/07/owl#",
          "adms": "http://www.w3.org/ns/adms#",
          "filetype": "http://publications.europa.eu/resource/authority/file-type/",
          "title": {
            "@id": "http://purl.org/dc/terms/title",
            "@container": "@language"
          },
          "description": {
            "@id": "http://purl.org/dc/terms/description",
            "@container": "@language"
          },
          "conformsTo": {
            "@id": "http://purl.org/dc/terms/conformsTo",
            "@type": "@id",
            "@container": "@set"
          },
          "format": {
            "@id": "http://purl.org/dc/terms/format",
            "@type": "@id"
          },
          "hasRole": {
            "@id": "prof:hasRole",
            "@type": "@id"
          },
          "hasArtifact": {
            "@id": "prof:hasArtifact",
            "@type": "@id"
          },
          "inSpecificationOf": {
            "@reverse": "prof:hasResource",
            "@type": "@id",
            "@context": {
              "title": {
                "@id": "http://purl.org/dc/terms/title",
                "@container": "@language"
              },
              "description": {
                "@id": "http://purl.org/dc/terms/description",
                "@container": "@language"
              },
              "hasToken": {
                "@id": "prof:hasToken",
                "@type": "xsd:token"
              },
              "isProfileOf": {
                "@id": "prof:isProfileOf",
                "@container": "@set",
                "@context": {
                  "title": {
                    "@id": "http://purl.org/dc/terms/title",
                    "@container": "@language"
                  },
                  "hasResource": {
                    "@id": "prof:hasResource",
                    "@container": "@set",
                    "@context": {
                      "hasArtifact": {
                        "@id": "prof:hasArtifact",
                        "@type": "@id"
                      }
                    }
                  }
                }
              },
              "hasResource": {
                "@id": "prof:hasResource",
                "@container": "@set",
                "@context": {
                  "conformsTo": {
                    "@id": "http://purl.org/dc/terms/conformsTo",
                    "@type": "@id",
                    "@container": "@set"
                  },
                  "format": {
                    "@id": "http://purl.org/dc/terms/format",
                    "@type": "@id"
                  },
                  "hasRole": {
                    "@id": "prof:hasRole",
                    "@type": "@id"
                  },
                  "hasArtifact": {
                    "@id": "prof:hasArtifact",
                    "@type": "@id"
                  }
                }
              }
            }
          }
        }
      }
    </script>
  </head>
  <body>
    <h1>DCAT-AP extension (example)</h1>
    <p>
      Application profile <code>https://example.org/dcat-ap-ext#</code>, an extension of
      <a href="https://mff-uk.github.io/specifications/dcat-ap/">DCAT-AP 3.0.1</a>.
    </p>
    <ul>
      <li><a href="./dsv-example.ttl">Application profile (DSV, Turtle)</a></li>
      <li><a href="./dsv-example-vocabulary.ttl">Vocabulary of terms minted by the profile (RDFS/OWL, Turtle)</a></li>
      <li><a href="./shacl-example-semic-v1.ttl">Validation shapes (SHACL, Turtle)</a></li>
    </ul>
  </body>
</html>
```

The contract, as the importer implements it:

| Requirement | Source |
|---|---|
| The URL must answer with `Content-Type` containing `text/html`. | `import.ts:660` |
| The first `script[type="application/ld+json"]` is used; base IRI for relative URLs is the page URL without fragment. | `import.ts:661-669` |
| The specification is the first subject typed `prof:Profile`. Give only the application profile that type; the `isProfileOf` entries must stay untyped. | `from-rdf.ts:26`, `import.ts:491` |
| DSV file: a resource with `prof:hasRole <http://www.w3.org/ns/dx/prof/role/constraints>` and `dct:conformsTo` both `https://w3id.org/dsv#ApplicationProfile` and `http://www.w3.org/ns/dx/prof/Profile`. | `import.ts:543-549`, `well-known.ts:54,67,72` |
| Vocabulary of minted terms: a resource with role `http://www.w3.org/ns/dx/prof/role/vocabulary`. The importer does not look at `conformsTo` here, so do not list a second resource with that role. | `import.ts:541-542` |
| Every resource needs `prof:hasArtifact`; a missing one makes the import fail. | `from-rdf.ts:104` |
| Base specifications: `prof:isProfileOf` entries with `prof:hasResource [ prof:hasArtifact <URL> ]`. Each URL is imported first, recursively: an HTML page as a specification, anything else as a vocabulary. The backend must be able to fetch all of them. | `from-rdf.ts:45-74`, `import.ts:570-618` |
| Role IRIs are lower-case. Old pages with `role:Specification`, `role:Vocabulary`, `role:Guidance` are mapped. | `well-known.ts:29-54`, `from-rdf.ts:85-97,127-137` |
| The SHACL resource, images and the page itself are listed for readers; the importer does not fetch them. | `import.ts:537-554` |

Pitfalls found while testing:

1. Do not write a literal `application/ld+json` script tag inside an HTML comment before the real one; a tolerant extractor may pick the comment.
2. A Turtle vocabulary served with a non-RDF content type is sniffed: a first character `<` means RDF/XML, `{` means JSON-LD (`DS/packages/core/src/io/rdf/http/http-adapter.ts:65-75`). Start the file with `@prefix`, or serve `text/turtle`.
3. `hasToken` in Dataspecer's context refers to an undeclared `xsd:` prefix (`dsv-context.json:47-50`). Do not use `hasToken`.
4. `hasArtifact: ""` for the page itself and `./file.ttl` for the neighbours keep the page relocatable.

Experiment: `artefacts/verify/wrapper_import_check.cjs` replays the import steps with the same libraries. For the example page it finds one specification (`https://example.org/dcat-ap-ext#`, an application profile), the base `https://mff-uk.github.io/specifications/dcat-ap/`, the vocabulary URL and the DSV URL. Run on `SPEC/dcat-ap-hvd/index.html` as a control it finds `dcat-ap-hvd/dsv.ttl` and the two bases.

verify: an actual import. Headless path from the spike plus 0.2: start the container, `POST <base>/api/resources/import?parentIri=http%3A%2F%2Fdataspecer.com%2Fpackages%2Flocal-root&url=<page URL>` (root IRI from `DS/services/backend/src/configuration.ts:44`), then `GET <base>/api/generate?iri=<package>` for the ZIP. The artefact directory can be served as it is; the four files reference each other relatively.

verify: that one specification node listing both a vocabulary and a DSV resource imports both. The code handles both in one call (`import.ts:622-633`, `:297-482`); Dataspecer's own export would describe two specification nodes when vocabulary and profile have different IRIs, and the importer would then take only the first (`import.ts:490-491`).

### 3.9 Where the requirement trace can live

DSV has no term for "covers requirement X because Y". Three places are compatible with Dataspecer; the first is recommended (our interpretation):

1. A sidecar Turtle file next to `dsv.ttl` whose subjects are the term-profile IRIs. Example `artefacts/dsv-example-trace.ttl` (PROV-O, Dublin Core, SKOS only; 20 triples; every traced subject exists in the DSV example):

```turtle
@prefix : <https://example.org/dcat-ap-ext#>.
@prefix req: <https://example.org/dcat-ap-ext/requirements#>.
@prefix prov: <http://www.w3.org/ns/prov#>.
@prefix dct: <http://purl.org/dc/terms/>.
@prefix skos: <http://www.w3.org/2004/02/skos/core#>.

# OUR INTERPRETATION, not part of DSV and not written by Dataspecer.
#
# DSV has no term for "which requirement does this profile element cover, and why".
# This sidecar keeps that trace next to dsv-example.ttl without touching it:
#   * the subjects are the term-profile IRIs of dsv-example.ttl;
#   * only PROV-O, Dublin Core and SKOS terms are used;
#   * Dataspecer ignores the file (it is not listed as a vocabulary or DSV resource),
#     and would also ignore these predicates if they were put into dsv.ttl, because its
#     reader only looks up the predicates it knows
#     (dataspecer/packages/data-specification-vocabulary/src/semantic-model/rdf-to-dsv.ts).
#     They would however be lost when Dataspecer re-exports the profile.
# Never put instances typed dcat:Dataset into dsv.ttl: on import Dataspecer turns every
# such subject into a controlled-vocabulary record
# (dataspecer/packages/controlled-vocabulary-model/src/dcat-rdf.ts, line 155).

req:RA-1 a prov:Entity;
    dct:identifier "RA-1";
    dct:description "A dataset names exactly one holder of the rights over it."@en.

req:RA-2 a prov:Entity;
    dct:identifier "RA-2";
    dct:description "A dataset may state for how long its data is kept available."@en.

req:RA-3 a prov:Entity;
    dct:identifier "RA-3";
    dct:description "A dataset gives at least one contact point."@en.

# (a) added property profile, reused term.
<https://example.org/dcat-ap-ext#Dataset.rightsHolder> prov:wasDerivedFrom req:RA-1;
    skos:editorialNote "Covers RA-1. dcterms:rightsHolder is reused because DCAT-AP does not profile a rights holder on Dataset and Dublin Core already defines the term; 1..1 and mandatory because the atom says 'exactly one'."@en.

# (b) added property profile, minted term.
<https://example.org/dcat-ap-ext#Dataset.retentionPeriod> prov:wasDerivedFrom req:RA-2;
    skos:editorialNote "Covers RA-2. No reusable term for a retention period was found in the vocabularies of the base profile, so the property is minted; 0..1 and optional because the atom says 'may'."@en.

# (c) modified constraint of a property the base profile already has.
<https://example.org/dcat-ap-ext#Dataset.contactPoint> prov:wasDerivedFrom req:RA-3;
    skos:editorialNote "Covers RA-3. The base profile allows 0..n (recommended); the atom requires at least one, so the lower bound is raised to 1 and the level to mandatory. This narrows the base constraint."@en.

# Class profiles that exist only because a property profile needs them as domain or range.
:Dataset prov:wasDerivedFrom req:RA-1, req:RA-2, req:RA-3.
:Agent prov:wasDerivedFrom req:RA-1.
:Kind prov:wasDerivedFrom req:RA-3.
```

2. The same triples inside `dsv.ttl`. The reader ignores predicates it does not look up, but Dataspecer drops them on re-export.
3. A short human sentence in the usage note (`skos:scopeNote`). It survives a round trip and appears in the documentation and as `sh:description`, so it must be written for readers of the profile, not as an audit record.

## 4. Dataspecer's SHACL generation (Q4)

Package `DS/packages/shacl-v2`, entry `semanticModelsToShacl` (`src/semantic-adapter/shacl-semantic-adapter.ts:61-193`), one policy `semic-v1` (`shacl-semantic-policy.ts:82-188`), writer `src/shacl-to-rdf.ts`. Called from `generateShaclApplicationProfile` with the profile IRI as base IRI (`DS/packages/specification/src/utils.ts:158-213`). The style imitates SEMIC's DCAT-AP shapes (`/home/user/refs/SEMICeu__DCAT-AP/releases/3.0.0/shacl/dcat-ap-SHACL.ttl`): shapes graph with `rdfs:member`, shape names `...#dcat:DatasetShape`, property shapes `<node shape>/<hash>`.

### 4.1 Structure

| Element | Rule | Source |
|---|---|---|
| Shapes graph | `<profile IRI> rdfs:member <node shape>, ...` | `shacl-to-rdf.ts:89-100` |
| Which class profiles | Only class profiles of the top profile model; base profiles contribute no shapes of their own | `shacl-semantic-adapter.ts:100-108,130-133` |
| Node shape | One per pair (class profile, RDF class it finally profiles). The RDF classes are collected by following `dsv:profileOf` down to `dsv:class`. `a sh:NodeShape; rdfs:seeAlso <class profile IRI>; sh:closed false; sh:targetClass <RDF class>` | `structure-model-factory.ts:223-225,285-305`; `shacl-semantic-adapter.ts:141-142,382-410`; `shacl-to-rdf.ts:102-118` |
| Property shapes of a node shape | One per property profile whose `dsv:domain` is that class profile, per RDF property it finally profiles, per range type. Plus the property shapes of all `dsv:specializes` ancestors. | `structure-model-factory.ts:76-94`; `shacl-semantic-adapter.ts:147-169,250-268` |
| Datatype property | `sh:nodeKind sh:Literal`, `sh:datatype <range>` | `shacl-semantic-adapter.ts:314-332` |
| Object property | `sh:nodeKind sh:BlankNodeOrIRI`, `sh:class <RDF class of the range class profile>`; one shape per RDF class when the range profile has several | `shacl-semantic-adapter.ts:334-380` |
| Never used as constraint | `rdfs:Resource`, `rdfs:Literal`: the shape is written without `sh:class` or `sh:datatype` | `shacl-semantic-policy.ts:111-114,181-182` |
| Texts | `sh:name` = label of the property profile; `sh:description` = its **usage note**; all languages unless a language filter is configured. A text is resolved through one level of reuse only: from the vocabulary term, or the raw text of the profile it is reused from. | `shacl-semantic-adapter.ts:319-323`; `structure-model-factory.ts:307-335,375-388` |
| Cardinality | `sh:maxCount` when the bound exists; `sh:minCount` only when greater than 0 | `shacl-to-rdf.ts:151-156` |
| Triple order in a property shape | type, `sh:name`, `sh:description`, `sh:nodeKind`, `sh:path`, `sh:maxCount`, `sh:minCount`, `sh:class`, `sh:datatype`, `sh:hasValue`, `sh:severity` | `shacl-to-rdf.ts:120-164` |
| Prefixes in the file | `rdf rdfs sh skos xsd`; everything else as full IRIs | `shacl-to-rdf.ts:56-67` |

### 4.2 Requirement levels, severities, closedness

- **Requirement level is not used.** It is carried into the intermediate model (`structure-model.ts:134`, `structure-model-factory.ts:403`) and never read by the shape builder; property shapes get `severity: null` (`shacl-semantic-adapter.ts:330,378`). A "recommended" property yields the same shape as an "optional" one. Only cardinality creates count constraints.
- `sh:severity` appears only on controlled-vocabulary shapes: `must` gives `sh:Violation`, `at-least-one`, `recommended` and `may` give `sh:Warning` (`shacl-semantic-adapter.ts:444-455`).
- All node shapes are open: `sh:closed false` (`shacl-semantic-adapter.ts:392`).
- Not generated at all: `sh:in`, `sh:node`, `sh:or`, `sh:pattern` on property shapes, `sh:minLength`, `sh:languageIn`, `sh:uniqueLang`, `sh:qualifiedValueShape` (`DS/packages/shacl-v2/src/vocabulary.ts:32-57` lists every SHACL term the package knows).

### 4.3 Shape IRIs

- Node shape: `<base IRI><prefixed RDF class>Shape`. The class IRI is shortened with a prefix table (`dcat dcterms foaf spdx locn time skos prov rdfs vcard eli adms sh xsd`, plus one prefix per model base IRI taken from its last path segment; `shacl-semantic-policy.ts:91-107`, `utils.ts:187-200`). With a base IRI that contains `#` the separator is `:`, otherwise `%3A` (`shacl-semantic-policy.ts:121-135`). A class without known prefix is appended as a full IRI; every `#` after the first is written `%23` (`shacl-semantic-policy.ts:149-165`). Examples from published output: `https://w3id.org/dsv-dap#dsv:ClassProfileShape`, `https://w3id.org/dsv-dap#http://www.w3.org/1999/02/22-rdf-syntax-ns%23PropertyShape` (`DSV/dsv-dap/shacl.ttl:6`).
- Property shape: `<node shape IRI>/<hash>`, hash = 32-bit string hash (`h = h*31 + charCode`, signed) in hexadecimal of `"<class profile IRI>:<path IRI>:<datatype or class IRI or null>"` (`shacl-semantic-policy.ts:137-146,190-198`).
- Controlled vocabulary: `<node shape IRI>/cv-<hash of vocabulary IRI>` and `.../inScheme` (`shacl-semantic-policy.ts:175-180`).

Experiment: `artefacts/verify/semic_hash.cjs` reproduces 7 of 7 sampled property-shape suffixes of `DSV/dsv-dap/shacl.ttl`, for example `-717603cf` for (`https://w3id.org/dsv-dap#ClassProfile`, `https://w3id.org/dsv#class`, `rdfs:Class`).

### 4.4 Cardinality along a profile chain: lower bounds are lost

`collectCardinality` walks from the property profile along `dsv:profileOf` and merges the declared cardinalities like this (`structure-model-factory.ts:410-473`): a 1.. bound sets `min` to 1 only if nothing was set before, otherwise keeps the smaller; a 0.. bound sets `min` to 0 unconditionally; a ..1 bound keeps the smaller `max`. Result: **smallest lower bound and smallest upper bound of the chain.**

| Extension declares | Base declares | Dataspecer SHACL | Intersection (what "profiles narrow" means) |
|---|---|---|---|
| 1..n | 0..n | no `sh:minCount` | `sh:minCount 1` |
| 1..1 | 0..n | `sh:maxCount 1` only | `sh:minCount 1; sh:maxCount 1` |
| 0..1 | 0..n | `sh:maxCount 1` | same |
| 0..n | 1..n (illegal loosening) | no `sh:minCount` | `sh:minCount 1` |
| 1..n, new property (no base profile) | - | `sh:minCount 1` | same |

Evidence beyond the code:

- `SPEC/dcat-ap-hvd/dsv.ttl:646-667` declares `Dataset.applicableLegislation` as `cardinality:1n`, `requirement:mandatory`, profile of the DCAT-AP profile with `cardinality:0n`. The published shape `<https://mff-uk.github.io/specifications/dcat-ap-hvd#dcat:DatasetShape/-563dac1c>` (`SPEC/dcat-ap-hvd/shacl.ttl:2149`) has no `sh:minCount`. `Dataset.hvdCategory` (`dsv.ttl:738-753`), new in HVD, has `sh:minCount 1` (shape `.../2ecdcd12`, `shacl.ttl:2181`).
- `SPEC/dcat-ap/dsv.ttl` declares `Dataset.title` as 1..n mandatory over a 0..n profile in DCAT-DAP; the published `SPEC/dcat-ap/shacl.ttl` has no `sh:minCount` for `dcterms:title` on `dcat:DatasetShape`, and only 4 `sh:minCount` in the whole file.
- Experiment: `artefacts/verify/dsv_to_semic_shacl.cjs` re-implements the rules of 4.1 to 4.4. Run on `SPEC/dcat-ap-hvd/dsv.ttl` with the DCAT-AP and DCAT-DAP files as chain, it regenerates all 29 HVD property shapes with **identical IRIs and identical constraints** (path, node kind, counts, class, datatype, description) as the published file, and all 15 node shapes (`compare_shacl.py`). The same run reports 10 HVD property profiles where the Dataspecer rule gives lower bound 0 and the intersection gives 1.

verify: that the behaviour is unchanged when run at this commit (the published files are from June 2026; the function is as quoted at ece634b). Whether upstream regards it as a defect is unknown.

### 4.5 Configuration options (`shacl-semantic-configuration.ts:5-50`; defaults `DS/packages/specification/src/shacl-v2.ts:23-36`)

| Option | Default | Effect |
|---|---|---|
| `policy` | `semic-v1` | only value |
| `languages` | `[]` | keep only these languages in `sh:name` and `sh:description`; empty keeps all |
| `noClassConstraints` | `false` | drop every `sh:class` (`shacl-transformer.ts:13-25`) |
| `splitPropertyShapesByConstraints` | `false` | one property shape per constraint, IRIs `<shape>/nodeKind`, `/minCount`, `/maxCount`, `/datatype`, `/class`, `/hasValue` (`shacl-transformer.ts:75-147`). This is the layout of SEMIC's own file. |
| `controlledVocabularyPattern` | `true` | `sh:pattern` on a node shape for the IRIs of a controlled vocabulary |
| `controlledVocabularyScheme` | `false` | `skos:inScheme` with `sh:hasValue` |
| `profileSpecializationAsSubClassOf` | `false` | add `rdfs:subClassOf` between the RDF classes of specialized profiles to the shapes graph |

Several files with different options can be generated (`shacl.ttl`, `shacl-<key>.ttl`).

### 4.6 What "comparable SHACL" means for us

`artefacts/shacl-example-semic-v1.ttl` is the expected Dataspecer output for the DSV example (37 triples; isomorphic to the generated graph; valid against SHACL-SHACL with pyshacl; a conforming test dataset passes; a dataset with two rights holders, a plain-string retention period and a dataset without rights holder gives exactly three results). The dataset without contact point passes: the tightened lower bound of (c) is not enforced.

```turtle
# SHACL that Dataspecer's shacl-v2 generator (policy "semic-v1", default configuration)
# is expected to produce for dsv-example.ttl.
#
# NOT produced by running Dataspecer. It was derived by re-implementing the rules read from
#   dataspecer/packages/shacl-v2/src/semantic-adapter/shacl-semantic-adapter.ts
#   dataspecer/packages/shacl-v2/src/semantic-adapter/shacl-semantic-policy.ts
#   dataspecer/packages/shacl-v2/src/semantic-adapter/structure-model/structure-model-factory.ts
#   dataspecer/packages/shacl-v2/src/shacl-to-rdf.ts
# The same re-implementation reproduces all 29 property shapes of the published DCAT-AP HVD
# profile (github.com/mff-uk/specifications, dcat-ap-hvd/shacl.ttl) with identical IRIs and
# identical constraints, so the shape structure below can be used as the comparison target.
#
# Conventions
#   shapes graph ......... <AP IRI> rdfs:member <node shape>, ...
#   node shape IRI ....... <AP IRI><prefix>:<LocalName>Shape      one per (class profile, profiled RDF class)
#   property shape IRI ... <node shape IRI>/<hash>                 hash = 32-bit string hash, in hex, of
#                          "<class profile IRI>:<sh:path>:<sh:datatype or sh:class or 'null'>"
#   rdfs:seeAlso ......... the class profile the node shape was generated from
#   sh:name .............. label of the property profile, sh:description = its USAGE NOTE (not the definition)
#   sh:minCount .......... written only when greater than 0; sh:maxCount only when bounded
#   requirement level .... NOT represented (no sh:severity on property shapes)
#   only property profiles of THIS profile appear; base DCAT-AP constraints stay in the DCAT-AP shapes

@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix sh: <http://www.w3.org/ns/shacl#>.
@prefix skos: <http://www.w3.org/2004/02/skos/core#>.
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

<https://example.org/dcat-ap-ext#> rdfs:member <https://example.org/dcat-ap-ext#dcat:DatasetShape>, <https://example.org/dcat-ap-ext#foaf:AgentShape>, <https://example.org/dcat-ap-ext#vcard:KindShape>.

<https://example.org/dcat-ap-ext#dcat:DatasetShape> a sh:NodeShape;
    rdfs:seeAlso <https://example.org/dcat-ap-ext#Dataset>;
    sh:closed false;
    sh:targetClass <http://www.w3.org/ns/dcat#Dataset>.

# (b) minted datatype property, 0..1 / optional.
<https://example.org/dcat-ap-ext#dcat:DatasetShape/-40517bc8> a sh:PropertyShape;
    sh:name "retention period"@en;
    sh:nodeKind sh:Literal;
    sh:path <https://example.org/dcat-ap-ext#retentionPeriod>;
    sh:maxCount 1;
    sh:datatype <http://www.w3.org/2001/XMLSchema#duration>.

<https://example.org/dcat-ap-ext#dcat:DatasetShape> sh:property <https://example.org/dcat-ap-ext#dcat:DatasetShape/-40517bc8>.

# (a) reused object property, 1..1 / mandatory.
#     sh:name is the label of dcterms:rightsHolder in the DCMI vocabulary (assumed "Rights Holder"@en,
#     the vocabulary file was not reachable when this example was written).
<https://example.org/dcat-ap-ext#dcat:DatasetShape/3bac298e> a sh:PropertyShape;
    sh:name "Rights Holder"@en;
    sh:description "Exactly one rights holder has to be given for every Dataset."@en;
    sh:nodeKind sh:BlankNodeOrIRI;
    sh:path <http://purl.org/dc/terms/rightsHolder>;
    sh:maxCount 1;
    sh:minCount 1;
    sh:class <http://xmlns.com/foaf/0.1/Agent>.

<https://example.org/dcat-ap-ext#dcat:DatasetShape> sh:property <https://example.org/dcat-ap-ext#dcat:DatasetShape/3bac298e>.

# (c) tightened object property, DSV says 1..n / mandatory.
#     Dataspecer writes NO sh:minCount here: its rule takes the smallest lower bound found on the
#     dsv:profileOf chain, and DCAT-AP and DCAT-DAP both declare 0..n for this property.
#     A compiler that implements "profiles narrow" must add:   sh:minCount 1;
#     There is also no sh:name: the label is reused from the DCAT-AP profile, which itself reuses
#     it from DCAT-DAP, and the generator reads only one level of reuse.
<https://example.org/dcat-ap-ext#dcat:DatasetShape/3addd57c> a sh:PropertyShape;
    sh:description "At least one contact point has to be given for every Dataset."@en;
    sh:nodeKind sh:BlankNodeOrIRI;
    sh:path <http://www.w3.org/ns/dcat#contactPoint>;
    sh:class <http://www.w3.org/2006/vcard/ns#Kind>.

<https://example.org/dcat-ap-ext#dcat:DatasetShape> sh:property <https://example.org/dcat-ap-ext#dcat:DatasetShape/3addd57c>.

<https://example.org/dcat-ap-ext#foaf:AgentShape> a sh:NodeShape;
    rdfs:seeAlso <https://example.org/dcat-ap-ext#Agent>;
    sh:closed false;
    sh:targetClass <http://xmlns.com/foaf/0.1/Agent>.

<https://example.org/dcat-ap-ext#vcard:KindShape> a sh:NodeShape;
    rdfs:seeAlso <https://example.org/dcat-ap-ext#Kind>;
    sh:closed false;
    sh:targetClass <http://www.w3.org/2006/vcard/ns#Kind>.
```

Recommendation (our interpretation):

- Emit our SHACL in the same layout (shape IRIs, `rdfs:seeAlso`, `sh:name`, `sh:description`, `sh:nodeKind`, counts, `sh:class`/`sh:datatype`, open shapes), so that a graph difference against Dataspecer's file is small and explainable.
- Compute counts by intersection. The expected differences to Dataspecer are then exactly the tightened lower bounds; `dsv_to_semic_shacl.cjs --min-count dataspecer|intersection` produces both variants and lists the differing profiles.
- An extension's shapes contain only the extension's own property profiles. Data must be validated against the base shapes **and** the extension shapes. Conformance to the extension alone says nothing about, for example, `dcterms:title`.
- If requirement levels should be visible in SHACL (for example `sh:severity sh:Warning` for "recommended"), that is our own extension; keep it switchable so the comparable variant stays available.

## 5. Does Dataspecer check that a profile legally refines what it profiles? (Q5)

**No check was found.** What exists:

| What | Where | Is it a check? |
|---|---|---|
| The intent as comments: range concept "must be descendant or self of the corresponding concept of the used entity"; cardinality "must be stricter or equal to the corresponding cardinality of the profiled entity ... the value should be determined as an intersection" | `DS/packages/core-v2/src/semantic-model/profile/concepts/relationship-profile.ts:30-41` | No. No code enforces either sentence. |
| Aggregation by intersection: "can only restrict the cardinality of the profiled ends" | `.../profile/aggregator/semantic-relationship-profile-aggregator.ts:132-135,173-195`; same helper in `DS/packages/profile-model/src/utilities.ts:7-27`, used by the flattener and the merger | Not a check. A looser declaration is silently overruled in the aggregated view; an empty intersection (lower above upper) is not detected. The DSV export still writes the looser declared value. |
| Profile dialogs | `src/dialog/base-relationship-profile/base-relationship-profile-dialog-state.ts:152,163`; `edit-association-profile-dialog.tsx:215-217` | No. Any of the four cardinalities and any class profile of the model can be chosen. |
| Old user documentation: "Profiles inherit values from their parents by default. You should just specialize their values (eg domain cardinality). We allow you to change it to any direction, proceed with caution." | `DS/applications/conceptual-model-editor/docs/modifications.md:62-64` | States the absence. |
| Unused warning texts "Change of cardinality may introduce a breaking change in the profile." | `src/application/localization-translations-en.ts:412-415` | Not referenced by any code at this commit. |
| `dsv:InvalidTermProfile` | `DSV/dsv/model.owl.ttl:126-130`; TypeScript interface only in `dsv-model.ts:152-157` | The vocabulary has a class for a rule-breaking profile; no code writes or reads it. |
| Evolution analysis | `evolution-items.ts:685-735` | Compares "inherits", "override equals new upstream value", "override differs". Does not test narrowing. |
| Controlled vocabulary qualifier | `src/dialog/components/select-qualifier.tsx:60-78`; `select-controlled-vocabularies-state.ts:68-102` | Yes, the only refinement guard: a qualifier weaker than the inherited one is disabled; `must` excludes further assignments; no duplicates. |
| SHACL generation | section 4.4 | No; it even weakens lower bounds. |

Searched without result in `applications`, `packages`, `services` (`.ts`, `.tsx`): `InvalidTermProfile` beyond the interface, `stricter`, `narrow`, `loosen`, cardinality comparisons in validation code.

The published profiles respect narrowing by convention. Experiment: in DCAT-AP HVD all 24 property profiles that profile a DCAT-AP profile narrow or keep its cardinality; in DCAT-AP all 125 property profiles with a declared cardinality stay inside the DCAT-DAP chain (`dsv_reader_check.cjs`, `build_base_index.py`).

Consequence: the Verify stage of our engine ("may tighten, never loosen") has no counterpart in Dataspecer. The rules to implement, stated on effective values of the base:

- cardinality: `min_ext >= min_base` and `max_ext <= max_base` (unbounded counts as infinity), and `min_ext <= max_ext`;
- range of an object property: the extension's range class profile profiles (directly or through the chain) the base range class profile, or one of its `dsv:specializes` descendants;
- range of a datatype property: equal to the base datatype, or the base is `rdfs:Literal`;
- requirement level: not weaker than the base (mandatory above recommended above optional) (our interpretation; DSV defines no order);
- a profile of a profile must not change the profiled vocabulary term.

## 6. Visual language of the conceptual-model-editor (Q6)

Sources: React components and CSS under `DS/applications/conceptual-model-editor/src/diagram/`, the conversion in `src/visualization.tsx`, and four diagrams exported from the editor and published with the DSV-DAP (`DSV/dsv-dap/626cb.svg`, `8dlkl.svg`, `n4roi.svg`, `80bb66a5-...svg`). The exports are HTML snapshots inside an SVG; rendered with headless Chrome to `artefacts/img/cme-export-dsv-dap-*.png`. Text overlaps in these renders are a font artefact of the render, not of the editor (inferred).

### 6.1 Node (class or class profile)

| Part | Appearance | Source |
|---|---|---|
| Box | White background, 1px black border, minimum 14rem wide. Selected node: background `rgba(238, 58, 115, 1)`. | `node/entity-node.tsx:70`, `node/entity-node.css:1-13` |
| Header band | Filled with the node colour (model colour by default, 1.2.8). First line: the label in black; an anchor sign when the node is pinned. | `entity-node.tsx:74-86` |
| "profile of" line | Only on class profiles, inside the header band, grey text: `profile of` followed by the labels (or IRIs) of the directly profiled entities, one per line. Can be hidden by option. | `entity-node.tsx:153-183`; label text `localization-translations.ts:18` |
| IRI line | Below the header, grey, prefixed where a prefix is known (for example `dcat-ap:Dataset`); hidden when the label already is the IRI. | `entity-node.tsx:87-89`; `visualization.tsx:551-599`; prefix table `configuration/default-configuration.ts:4-23` |
| Attribute rows | `- <label> : <range label> profile of <labels> [min..max]`. Rows are grouped under plain title rows `<<mandatory>>`, `<<recommended>>`, `<<optional>>`, `<<undefined>>` whenever the level changes. | `entity-node.tsx:278-327`; `visualization.tsx:400-480,640-663` |
| Tooltip | The definition, on the header. | `entity-node.tsx:76` |
| Toolbars of a selected node | Top: detail, edit, create profile (magnet), choose visible attributes, duplicate. Right: connection handle. Bottom: hide, delete, anchor, add attribute (or attribute profile), extend selection. | `entity-node.tsx:237-274` |

A vocabulary class and a class profile use the same box. They differ by the colour of their model, by the "profile of" line, and by the dashed edge to what they profile. There is no other marker such as an icon or a stereotype on the node.

### 6.2 Edges

All edges: orthogonal routing with draggable waypoints, stroke width 2, labels on a pale background `#F0FDFA` with rounded corners (`diagram-controller.ts:1858-1876`; `edge/property-edge.tsx:84-131`).

| Edge | Line | Arrowhead | Colour | Label | Source |
|---|---|---|---|---|---|
| Association (vocabulary) | solid | open arrow | model colour | property label; cardinalities `[min..max]` at both ends | `diagram-controller.ts:1879-1905`; `visualization.tsx:696-729` |
| Association profile | solid | open arrow | model colour of the profile | label of the profile, then in parentheses the labels of the profiled entities unless identical, optional first line `<<profile>>` (off by default), second line in grey `#6B7280` with the requirement level; cardinalities at both ends | `edge/property-edge.tsx:139-221`; `visualization.tsx:731-766`; `configuration/options.tsx:72` |
| Generalization | solid | closed triangle | model colour | none | `edge/generalization-edge.tsx`; `visualization.tsx:768-797` |
| Profile of (class profile to profiled class or class profile) | **dashed** (`strokeDasharray: 5`) | closed triangle | **black** `#000000` | `<<profile>>` | `edge/class-profile-edge.tsx:47-50`; `visualization.tsx:802-826`; `localization-translations.ts:19` |

- In the live editor the closed arrowheads are filled light grey `#f1f1f1`, which makes them look hollow (`src/visualization.css:4-8`). In the exported SVGs they appear filled with the edge colour. verify: in the running editor.
- "Profile of" edges exist only between class nodes. That an attribute or association is a profile is visible from its label and from the "profile of" part of the attribute row, not from an edge.
- A profile-of edge is drawn automatically whenever both ends are on the canvas (`src/visualization-validation.ts:138-169`).

What the rendered exports show (`artefacts/img/cme-export-dsv-dap-626cb.png`): teal class profiles with "profile of ..." lines and attribute rows such as `- title profile of Title [1..*]`; two yellow-green vocabulary classes (`prof:ResourceDescriptor`, `prof:Profile`) without such a line; black dashed `<<profile>>` arrows from profiles to these classes; teal solid generalization arrows; teal association profiles labelled `has specification (has resource)` with `[1..1]` and `[1..*]` at the ends.

### 6.3 Mapping to our canvas (our interpretation)

- Keep: box with coloured header, "profile of" line, prefixed IRI, grouped attribute rows with `[min..max]`, the four edge styles.
- Add, because Dataspecer has nothing for it: a badge per node and per row with the covered requirement atoms; a visual state per change (proposed, accepted, rejected); a marker for "tightened relative to base" showing base and new value, for example `[0..*] -> [1..*]`; a marker for minted terms.
- Use three fixed colours for the three layers (vocabulary, base profile, extension) instead of random per-model colours.

## 7. Consequences for the engine (our interpretation, derived from the findings)

| Stage | Consequence |
|---|---|
| Retrieve | Index the base profile from DSV, not only the vocabularies: `artefacts/dcat-ap-dsv-index.json` gives for every base class profile its RDF class, role, and for every property profile the RDF property, range, declared and effective cardinality and requirement level. The well-known vocabulary URLs of the CME (1.2.1) are a ready seed list for the vocabulary index. |
| Propose | Change kinds that map one to one onto DSV: add class profile (of a base profile or of a vocabulary class), add property profile reusing a term, add property profile of a minted term plus the term, refine a base property profile (cardinality, requirement level, range, texts), add specialization. Field values restricted to the DSV enumerations. |
| Verify | Term exists: in the vocabulary index or the base index. Reuse before mint. Legal refinement: the rules of section 5 on effective values. Structural: R1 to R10 of 3.6. DSV-expressible cardinality. Datatype in Dataspecer's list. |
| Compile | DSV per 3.7 with pass-through class profiles for domains and ranges; vocabulary file for minted terms per 3.7; SHACL per 4.6; wrapper per 3.8; trace sidecar per 3.9. Mapping from the LinkML base of the Visual Profile Editor to DSV base IRIs by (class IRI, property IRI) lookup in the index. |
| Conformance to the base | Dataspecer offers none. Ours: (1) every refinement is legal (section 5); (2) example data that satisfy the extension shapes also satisfy the base shapes, checked with both shape graphs. |

## 8. Open points

1. Actual import of the wrapper into a running Dataspecer (container `ghcr.io/dataspecer/ws`), and regeneration of SHACL there, to confirm 3.8 and 4.4.
2. Which base to target: the DSV re-publication `https://mff-uk.github.io/specifications/dcat-ap#` is DCAT-AP 3.0.1 as modelled by the Dataspecer team, with a DCAT-DAP layer below. The Visual Profile Editor uses its own simplified LinkML base (`/home/user/visual-profile-editor/schemas/dcat_ap_base.yaml`, 7 classes). The (class IRI, property IRI) mapping must be checked for every slot of that base; a slot without counterpart needs a decision.
3. Namespace policy for minted terms (3.7): the profile namespace or a separate vocabulary namespace.
4. Whether to add the published `dsv:range` and `dsv:datatype` next to Dataspecer's predicates.
5. Whether to report the lower-bound behaviour of `collectCardinality` upstream.
6. Label of `dcterms:rightsHolder` in the DCMI file was assumed ("Rights Holder"); the file was not reachable.
7. Requirement level in SHACL: comparable with Dataspecer (none) or our own severities.
8. Appearance of closed arrowheads in the live editor.
9. Controlled vocabulary assignments use unpublished DSV terms; revisit when they are published.

## 9. Artefacts

Directory `/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research/artefacts/`

| File | Content |
|---|---|
| `dsv-example.ttl` | The DSV example of 3.7 |
| `dsv-example-vocabulary.ttl` | RDFS/OWL definition of the minted property |
| `dsv-wrapper-example.html` | The HTML and JSON-LD wrapper of 3.8; references the three Turtle files relatively |
| `shacl-example-semic-v1.ttl` | Expected Dataspecer SHACL for the example (4.6) |
| `dsv-example-trace.ttl` | Requirement-trace sidecar (3.9) |
| `dcat-ap-dsv-index.json` | Lookup of the DCAT-AP DSV base: 34 class profiles, 131 property profiles |
| `manifest.json` | Artefact list plus machine-readable constants: DSV namespaces, classes, properties, code lists, datatype list, reader rules R1 to R10, wrapper roles, `semic-v1` shape rules, colours of the visual language |
| `img/cme-export-dsv-dap-*.png` | Four editor diagrams rendered from `DSV/dsv-dap/*.svg` |
| `verify/dsv_reader_check.cjs` | Checks a DSV file against the reader rules, base references and narrowing |
| `verify/wrapper_import_check.cjs` | Replays the import of a specification page |
| `verify/semic_hash.cjs`, `verify/dsv_to_semic_shacl.cjs` | Shape-IRI hash and a re-implementation of the `semic-v1` rules (`--min-count dataspecer` or `intersection`) |
| `verify/compare_shacl.py`, `verify/shacl_smoke.py`, `verify/validate_dsv_dap.py`, `verify/build_base_index.py` | Comparison with published shapes, smoke test, DSV-DAP validation, index builder |

Running the checks: the Node scripts need `NODE_PATH=/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research/tools/node/node_modules`; the Python scripts need `/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research/tools/venv/bin/python`. Each script prints its usage in its first comment lines.
