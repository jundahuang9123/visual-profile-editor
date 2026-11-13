# B2 — What "extension E still conforms to the base DCAT-AP B" means

Research note for the `requirement-based-dcat-profile-extensioner` (Verify step and final conformance check).
Everything below is taken from the primary sources listed in section 0. Text marked **(inferred)** is our reading,
**verify:** marks something that could not be confirmed here, **derived (our interpretation)** marks a rule we
propose that no source states literally. Quotes are verbatim (whitespace normalised) and at most 40 words.

Line numbers refer to the files at the commits listed in section 0.

---

## 0. Sources and provenance

| Short name | Location | Commit / date | Used for |
|---|---|---|---|
| **RG** reuse guidelines, "How to create your DCAT-AP profile" | `/home/user/refs/SEMICeu__DCAT-AP-reuse-guidelines/index.html` (1 684 lines; ReSpec `publishDate: "2026-06-17"`, line 26) | `e958ded83c4c501dd811d6ccbf5ea71b5cf9f69a` | Q1, Q4 |
| **AP301** DCAT-AP 3.0.1 specification | `/home/user/refs/SEMICeu__DCAT-AP/releases/3.0.1/index.html` | `4470b8ea907b7eb9ec55ab22befd1ecd2210ff32` | Q2, Q4 |
| **AP300** DCAT-AP 3.0.0 specification | `.../releases/3.0.0/index.html` | same | Q2 |
| Official SHACL | `.../releases/{1.1,2.0.1,2.1.1,3.0.0,3.0.1}/...` | same | Q3, Q4b |
| **HVD** DCAT-AP HVD 3.0.0 | `.../releases/3.0.0-hvd/index.html` and `html/hvd-SHACL-*.ttl`, `shacl/hvd-SHACL.ttl` | same | Q5, tests |
| DCAT-AP 1.1 / 2.0.1 / 2.1.1 text | PDFs in `.../releases/1.1`, `2.0.1`, `2.1.1` (read with `pdftotext`) | same | Q2 (class obligation history) |
| **GEO** GeoDCAT-AP 3.0.0 / 3.1.0 | shallow clone of `github.com/SEMICeu/GeoDCAT-AP`, `releases/3.1.0/index.html`, `shacl/geodcat-ap-SHACL.ttl` | `7e7d6a82f4bd4491c68f774f185193439881ab42` (2026-04-28) | Q5, tests |
| **MOB** mobilityDCAT-AP 3.0.0 | shallow clone of `github.com/mobilityDCAT-AP/mobilityDCAT-AP`, `src/index.html`, `src/shacl/*` | `3f228c7b9b1c460039b7e18ff1527240a73ee8cd` (2026-11-06) | Q5 |
| **HEALTH** HealthDCAT-AP (archived draft) | shallow clone of `github.com/HealthDCAT-AP/HealthDCAT-AP.github.io`, `OldContent/index.html` | `a155911e9c9ac442e437aa048f608db5bd6f4c58` (2025-09-22) | Q5 |
| **DE** DCAT-AP.de 2.0 | shallow clone of `github.com/GovDataOfficial/DCAT-AP.de`, `Releases/DCAT-AP.de V2.0/spec/06_conformity.md` | `2cc6629fc32b4a0ff0016a063e10066c87c7be2d` (2024-04-17) | Q5, Q4 |
| **ITB** validator configuration | shallow clone of `github.com/ISAITB/validator-resources-dcat-ap`, `resources/config.properties`, `README.md` | `08adbf5955eb1c6c1f09149351135a88420e8601` (2025-12-01) | Q3, Q4b (which files to combine) |
| **STYLE** SEMIC Style Guide | shallow clone of `github.com/SEMICeu/style-guide`, `docs/modules/ROOT/pages/*.adoc` | `6eb6499c44236f8c4fb12dbe358957b760ec0fb1` (2026-06-15) | Q4 (reuse, severity, versioning) |
| **DCAT3** W3C DCAT 3 source | `raw.githubusercontent.com/w3c/dx-dcat/gh-pages/TR/index.html` (branch head `01714554…`) | fetched 2026-11-13 | profile definition. verify: wording against the published Recommendation (w3.org unreachable) |
| **PROF** W3C Profiles Vocabulary source | `raw.githubusercontent.com/w3c/dx-prof/gh-pages/prof/index.html` | fetched 2026-11-13 | `prof:isProfileOf` semantics. verify: against the published Note |
| **SHACL** W3C SHACL source | `raw.githubusercontent.com/w3c/data-shapes/gh-pages/shacl/index.html` (editor's draft of the 2017 Recommendation) | fetched 2026-11-13 | engine semantics. verify: against the published Recommendation |

Working copies of the downloads and clones are under
`/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research/B2-work/` (`refs/`, `dl/`).
Empirical statements were produced with rdflib 7.6.0 and pySHACL 0.40.2 in a private virtualenv; scripts and example
files are in `.../research/B2-artefacts/` (section 9). No code from the cloned repositories was executed.

Not reachable from this session (proxy): `interoperable-europe.ec.europa.eu` (the older SEMIC note "How to extend
DCAT-AP") and `healthdataeu.pages.code.europa.eu` (current HealthDCAT-AP releases). Statements about them are marked verify:.

---

## 1. Twelve findings that decide the design

1. **The rule is one-directional: a profile may tighten, never loosen.** RG: "It is not possible to loosen them under any
   conditions, as the result would no longer be compliant with DCAT-AP." (RG lines 376-379). DCAT-AP.de states the
   instance-level consequence explicitly (section 6.5).
2. **Conformance is relative to one exact base release.** DCAT-AP 3.0.1 itself *relaxed* three cardinalities of 3.0.0
   (`releases/3.0.1/CHANGELOG.md`: `dct:rights` on Catalogue and Distribution, `dcat:spatialResolutionInMeters` on Dataset, to 0..n).
   A profile using `dct:rights` 0..n conforms to 3.0.1 and not to 3.0.0.
3. **The normative base is the specification table, not any SHACL file.** For 3.0.1 the tables hold 131 (class, property)
   rows: 20 Mandatory, 39 Recommended, 72 Optional. Obligation is *not* derivable from cardinality (Recommended rows are
   `0..1` or `0..*`). Machine-readable extraction: `B2-artefacts/dcat-ap-3.0.1-base-table.tsv`.
4. **There are two official SHACL flavours per 3.x release and they disagree.** The "individual constraints" file
   (`shacl/dcat-ap-SHACL.ttl`) matches every cardinality of the 3.0.1 tables but has no recommended level, no temporal
   datatypes and no controlled-vocabulary checks. The legacy set (`html/shacl/*.ttl`) carries those, but the 3.0.1 copy of
   `shapes.ttl` is the 3.0.0 file with one line changed and is stale in at least six facets (section 4.4).
5. **The 3.0.1 "individual constraints" file does not load in pySHACL as published**: two `sh:property` links in
   `dcat:DataServiceShape` point to property shapes that do not exist (lines 564 and 566). `shacl/ranges.ttl` has 206 such links.
   Removing dangling links makes both usable (`B2-artefacts/clean_shapes.py`).
6. **Recommended = `sh:minCount 1` with `sh:severity sh:Warning`**, in a separate file (`shapes_recommended.ttl`).
   Mandatory = `sh:minCount >= 1` with `sh:Violation` (legacy) or no severity (new style, default Violation).
7. **No official shape is closed.** New-style shapes say `sh:closed false`; legacy shapes have no `sh:closed`. Added
   properties never break base validation; only restated properties can.
8. **A delta cannot loosen, it can only contradict.** If E is published as "base shapes + additional shapes" (SHACL
   conjunction, the design mobilityDCAT-AP 3.0.0 adopted), every graph valid under E is valid under B by construction.
   The remaining failure modes are (i) a *documented* loosening in the profile tables, (ii) an unsatisfiable combination,
   (iii) semantic drift. A standalone restatement of the base can loosen by omission.
9. **Official extensions are not perfectly clean.** GeoDCAT-AP 3.1.0 widens three maxima of DCAT-AP 3.0.1
   (`dcat:version`, `dcat:temporalResolution` on Dataset and Distribution, 0..1 to 0..*) and downgrades one Recommended
   property to Optional; HVD 3.0.0 widened `dct:rights` on Distribution against 3.0.0. These are good regression fixtures.
10. **Inference settings change the verdict.** RDFS inference plus the DCAT 3 vocabulary creates false violations
    (`dcat:dataset` is a sub-property chain to `dct:hasPart`; `dcat:mediaType` is a sub-property of `dct:format`). Use no
    inference and mix in only `rdfs:subClassOf` axioms.
11. **XSD subtype narrowing is legal on paper and fails the base shapes.** RG allows "a subtype of the DCAT-AP one";
    SHACL `sh:datatype` is an exact match, so `"25"^^xsd:integer` fails the base `sh:datatype xsd:decimal` (verified).
12. **SHACL-SHACL is necessary and not sufficient.** It catches the dangling links of finding 5 but accepts the legacy
    non-SHACL term `sh:shape` (5 uses in `shapes.ttl`) and the typo `sh:dateTime` (2.0.1). Add a lint for unknown `sh:` terms.

---

## 2. Question 1 — the reuse guidelines, rule by rule

Source: RG. Document title "How to create your DCAT-AP profile", subtitle "A guide for creating new DCAT-AP profiles".
The file contains an empty `<section id="conformance"></section>` (line 133); ReSpec fills it with the RFC 2119 boilerplate
when rendered **(inferred)**. The guidelines use "must", "should", "may" in lower case in running text; upper-case keywords
appear only where they quote DCAT-AP's controlled-vocabulary levels.

### 2.1 Framing

| ID | Rule (our wording) | Quote | Where |
|---|---|---|---|
| RG-01 | Every profile must satisfy the base's requirements and restrictions | "all DCAT-AP profiles must comply with the requirements and restrictions imposed by DCAT-AP, namely mandatory properties and controlled vocabularies that must be used with select properties" | Introduction, lines 100-105 |
| RG-02 | "Profile" and "extension" are synonyms here | "the terms “DCAT‑AP profile” and “DCAT‑AP extension” are used to refer to specifications that build upon DCAT‑AP by reusing, constraining, or extending its classes and properties" | Introduction, lines 110-112 |
| RG-03 | Start from the minimal profile and extend | "The process of creating a new DCAT-AP profile therefore starts from a minimal DCAT-AP profile, gradually extending it to cover the requirements driving the creation of a new profile." | Introduction, lines 105-107 |
| RG-04 | Announce the profile | "We kindly request that newly created DCAT-AP profiles are announced as a DCAT-AP GitHub issue." | Introduction, lines 121-123 |
| RG-05 | Minimal compliance = mandatory classes and their mandatory properties | "we recommend starting with the minimal DCAT-AP compliance requirements, i.e., the mandatory classes and their mandatory properties for DCAT-AP, and therefore for every profile" | Step 1, lines 167-171 |
| RG-06 | Content of the minimum conformant catalogue | Catalogue: title, description, publisher and its name, links to datasets and data services "(if any)"; Dataset: title, description, links to distributions; Distribution: access URL; Data Service: title, endpoint URL, datasets served | Step 1, list at lines 177-236 |
| RG-07 | Use cases justify the design decisions that matter | "Use cases are intended to justify and explain relevant design decisions, in particular those that introduce new elements, tighten existing constraints, or have a significant impact on interoperability." | Step 2 `#step-2`, lines 262-264 |

RG-07 is the official counterpart of "every change states which requirement atom it covers and why": justification is
expected for *new elements*, *tightened constraints* and *interoperability-relevant* decisions, not for every reused element
("rather than documenting each individual profile element", line 265).

### 2.2 What a profile may add

| ID | Rule | Quote | Where |
|---|---|---|---|
| RG-10 | Reuse a term from W3C DCAT, another vocabulary or another DCAT-AP profile when DCAT-AP has none | "Then reuse that approach, given that it does not cause a semantic issue." | `#use-case-not-covered-by-dcat-ap`, line 411 |
| RG-11 | Reused external property: link to its original description | "Reuse property from DCAT in the new DCAT-AP application profile and link to the property description in DCAT" | lines 434-435 |
| RG-12 | Mint only when nothing admissible exists | "Then an original approach needs to be developed, typically supported by a new vocabulary defining new classes and properties." | `#use-case-not-covered-by-any-known-vocabulary`, lines 445-447 |
| RG-13 | Minted terms go in the profile owner's namespace, with label, definition, domain, range | "we create our own in our own namespace, e.g. http://data.europa.eu/930/serviceCategory along with its label, definition and possible domain and range" | lines 471-474 |
| RG-14 | Code lists used by a profile must already be linked data | "a code list that is already published as linked data, which is a prerequisite for code lists to be used with DCAT-AP profiles" | lines 476-479 |
| RG-15 | New subclasses for distinct usage contexts of one base class | "create a subclass of the corresponding DCAT-AP class for each of the contexts" | `#situation-class-usage-scope-change`, lines 1418-1420 |
| RG-16 | New sub-profile when the context spans several classes ("profile of a profile") | "If the usage contexts supersede one class, creating an additional, separate sub-profile for the context is preferred, containing all the affected classes and properties in that context." | lines 1425-1427 |

### 2.3 What a profile may change

| ID | Aspect | Rule | Quote | Where |
|---|---|---|---|---|
| RG-20 | Any constraint | Tighten only | "these adjustments are possible, if they tighten existing constraints. It is not possible to loosen them under any conditions, as the result would no longer be compliant with DCAT-AP." | `#use-case-covered-by-dcat-ap-with-context-specific-adjustments-required`, lines 376-379 |
| RG-21 | Minimum cardinality | May be raised (0..1 to 1..1; 0..* to 1..*) | "the cardinality constraint is tightened from 0..* to 1..*, which is a compliant change" | lines 398-400 |
| RG-22 | Mandatory stays mandatory | | "Then it must be mandatory in the profile as well." | `#situation-property-cardinality-mismatch`, line 1293 |
| RG-23 | Maximum cardinality | At most one stays at most one | "Then in the profile, the property also must have at most one value." | line 1304 |
| RG-24 | Maximum cardinality | Raising the maximum is not compliant; use another property | "meaning cardinality 1..*, this would not be compliant with DCAT-AP Distribution licence and another property would have to be used for this" | lines 367-373 |
| RG-25 | Needed relaxation | Escalate to the base | "If there is a good case to change this on DCAT-AP level, raise an issue." | lines 1305-1306 |
| RG-26 | Stricter is always fine | | "No action required, a profile can be more restrictive than DCAT-AP." | line 1322 |
| RG-27 | Range: class to literal | Not possible | "Reuse not possible. Another property needs to be used." | `#situation-property-range-mismatch`, case 1, line 1066 |
| RG-28 | Range: literal to class | Not possible | "Reuse not possible. Another property needs to be used." | case 2, line 1084 |
| RG-29 | Range: datatype to datatype | Only to a subtype | "Reuse possible, if the profile datatype is a subtype of the DCAT-AP one." | case 3, line 1095 |
| RG-30 | Range: datatype, examples | Subset of the Temporal Literal union is fine, an extra member is not | "A profile may require that only xsd:date is used, which is OK." and "also xsd:gDay can be used. This is, however, not possible" | lines 1106-1108 |
| RG-31 | Range: class to controlled vocabulary | Allowed | "This means a selection from specific instances of the DCAT-AP indicated class, listed in a controlled vocabulary. This is OK." | case 4, lines 1120-1121 |
| RG-32 | Range: class to another class | Allowed when semantically compatible; double typing advised | "If the classes are semantically compatible, then it is OK. For interoperability purposes, it might be good to double type the resources" | case 5, lines 1145-1147 |
| RG-33 | Range, general principle | Narrow, never extend | "Narrowing down the value space will not create any issues but extending it will." | lines 1180-1181 |
| RG-34 | Controlled vocabulary: missing items | First try to extend it at its source | "Try to extend the existing controlled vocabulary at its source." | `#situation-controlled-vocabulary-mismatch`, lines 883-884 |
| RG-35 | CV level MUST (closed) | Separate CV needs a separate property | "The property MUST use the original controlled vocabulary in DCAT-AP" then "Create a separate property" | lines 907-909 |
| RG-36 | CV level "at least one" | Keep one base value, add others | "Use at least one value from the original controlled vocabulary with the original property" | lines 932-934 |
| RG-37 | CV level RECOMMENDED / MAY | A separate CV may be used with the original property | "Use the separate controlled vocabulary with the original property" | lines 940-942 and 948-950 |
| RG-38 | A different CV altogether | Different property | "If another controlled vocabulary is to be used, then it must be used with a different property." | line 962 |
| RG-39 | CV publication | Must meet DCAT-AP's CV requirements | "Ensure that the used controlled vocabulary is published according to the DCAT-AP requirements." | line 986 |
| RG-40 | CV, summary | | "values from other controlled vocabularies are allowed only in addition to the specified one" (at-least-one level) | lines 1011-1014 |
| RG-41 | Labels | Terminological change allowed in the documentation | "the more precise labels can be applied to the HTML documentation" | `#situation-property-class-semantic-mismatch`, line 786 |
| RG-42 | Definitions and usage notes | May be made more specific, never contradict | "that does not contradict the DCAT-AP formulations and only makes them more specific to the context of the new profile, then reuse is still possible" | lines 779-781 |
| RG-43 | Substantial semantic change | Sub-class or sub-property in a new vocabulary | "a subclass or subproperty needs to be created in a new vocabulary and used in the profile" | lines 806-808 |
| RG-44 | Class label per context | Allowed | "the class dcat:Distribution will therefore have the Data Interface label, which will be used throughout the profile document" | lines 1357-1359 |
| RG-45 | Usage notes of reused classes | Improve where necessary to give context | "Improve the usage notes of the reused DCAT-AP classes to provide the readers with an as much precise context as possible" | lines 1401-1402 |

### 2.4 What a profile must not do

| ID | Rule | Quote | Where |
|---|---|---|---|
| RG-50 | Loosen any constraint | see RG-20 | lines 376-379 |
| RG-51 | Reuse a term whose base meaning does not fit | "the class/property cannot be reused, as it would cause confusion with DCAT-AP users. A new class/property needs to be defined and used." | lines 828-830 |
| RG-52 | Leave semantic differences or contradictions | "profile authors must make sure that the labels, definitions and usage notes in DCAT-AP still capture the meaning of the data, even if in a more abstract way" | lines 851-853 |
| RG-53 | Change the kind of range of a reused property | see RG-27, RG-28; "would not be compatible with DCAT-AP" | lines 1046-1048 |
| RG-54 | Use a non-base CV on a property whose base CV level is MUST | "if the property is to be used with that class, even in DCAT-AP profile, it is to be used with the DCAT-AP indicated controlled vocabulary" | lines 999-1001 |
| RG-55 | Block exchange as Linked Data | "the profile should not block the implementation as Linked Data exchange" | `#situation-linked-data-expectations`, line 703 |
| RG-56 | Over-constrain range classes shared across profiles | "do not add any additional formal constraint to the range" (when the referenced description suffices) | `#situation-external-vocabulary-relationships`, line 1612 |

### 2.5 Namespace and URI policy for new terms

| ID | Rule | Quote | Where |
|---|---|---|---|
| RG-60 | Own namespace | see RG-13 | lines 471-474 |
| RG-61 | Persistent URIs for all new properties | "All new properties should be defined according to the Linked Data principles of persistent URIs." | lines 715-716 |
| RG-62 | Dereferenceable with content negotiation (HTML for `text/html`, RDF for RDF media types) | "Dereferenceable with a minimum content negotiation implemented" | lines 734-739 |
| RG-63 | Consequence of non-dereferenceable terms | "Elements which are not dereferenceable in the best case are disregarded or in the worst case the entire dataset might be thrown out." | lines 751-753 |
| RG-64 | Separate, managed supporting vocabulary | "Create if it does not exist yet, or otherwise use a supporting vocabulary in a managed namespace" | `#situation-new-property-assignment`, line 1237 |
| RG-65 | Generic domain in the vocabulary | "Ensure the domain is as open as possible: use dcat:Resource for catalogable resources, or rdfs:Resource for generic resources" | line 1243 |
| RG-66 | Generic range in the vocabulary | "For object properties use rdfs:Resource, or a very generic class" and "For datatype properties use rdfs:Literal, or rdf:langString" | lines 1246-1247 |
| RG-67 | Generic wording of definitions | "do not write as definition: status of the Dataset when the domain is dcat:Resource. Write status of the catalogued resource instead." | line 1253 |
| RG-68 | Context-specific usage belongs in the profile | "a reusable definition of the property in a vocabulary, and then description of its context-specific usage in the profile documentation" | lines 1227-1228 |
| RG-69 | Stable publication URLs; w3id.org is acceptable | "As these URLs need to be as stable as possible not to break references in future, a conscious effort should be invested in their definition." | Step 4, lines 575-577 |

### 2.6 Reuse expectations

Order of preference, from the four "standard situations" of Step 2 (lines 287-486): (1) reuse the DCAT-AP element as-is,
(2) reuse it with a tightening adjustment, (3) reuse from W3C DCAT, another vocabulary or another DCAT-AP profile,
(4) mint. Reuse "as-is" carries everything: "This includes class and property labels, property cardinalities, definitions,
usage notes and mandatory code lists from DCAT-AP, and a link to the reused DCAT-AP class or property." (lines 291-292).
Domain fit is the test for situation 3: `dct:language` may be put on Data Service because "Data Service is a subclass of
Catalogued Resource, so no semantic issue arises" (lines 428-430).

### 2.7 Conformance and "profile of a profile"

* The only conformance clause is RG-01. There is no separate normative conformance section (the element at line 133 is empty).
* A profile of a profile is foreseen: "it is advised to create an additional, separate sub-profile of the currently created
  profile, describing that usage context" (lines 1471-1472), with DCAT-AP HVD as the model: "That is why it is a separate
  profile (annex) of DCAT-AP." (lines 1431-1432).
* Each profile must state its scope: "Each profile must express its motivation to exist." (line 1441) and "A profile without
  a well circumscribed context is subject to the existential question: what does this profile address differently than
  DCAT-AP?" (lines 1388-1390).
* Profiles overlap in practice, so constraints on shared range classes leak across profiles: "As DCAT-AP profiles overlap,
  this requirement is not only for the data exchange in the context of the profile" (lines 1634-1635).

### 2.8 Documentation and SHACL publication

| ID | Rule | Quote | Where |
|---|---|---|---|
| RG-70 | Publish all artefacts at public, stable URLs | "Artifacts of the profile such as the human readable documentation, RDFS vocabulary with definitions of new classes and properties, or SHACL shapes validating defined constraints should be published at publicly accessible URLs." | Step 4, lines 571-575 |
| RG-71 | HTML specification | "A human-readable, HTML-based specification of the application profile." | lines 592-593 |
| RG-72 | The HTML must say how the profile differs | "It should contain the profile usage context, explanation how the profile is distinct from DCAT-AP, and contact information" | lines 596-598 |
| RG-73 | SHACL | "A machine-actionable set of validation rules using SHACL shapes." | lines 612-613 |
| RG-74 | Vocabulary document, when terms were minted | "A separate human-readable document describing the newly created classes and properties." | line 627 |
| RG-75 | Vocabulary RDF, related to existing terms | "These definitions should relate the new classes and properties to existing ones from admissible vocabularies in order to make their intended semantics explicit." | lines 645-646 |
| RG-76 | Reused elements link back to the base documentation | "link to the DCAT-AP description in the HTML documentation of the profile" | lines 315-316 |
| RG-77 | Use cases are tracked publicly | "Each use case from the previous step should be clearly identified e.g. as a GitHub issue." | Step 3, line 530 |
| RG-78 | Consensus process is traceable | "the process of consensus building needs to be transparent, accessible and traceable" | lines 522-524 |

### 2.9 Versioning

The guidelines contain **no versioning rule for profiles**. The only related statements are RG-69 (stable URLs) and
"Considering the DCAT-AP profile and the supporting vocabulary as two distinct specifications, each with their own
lifecycle" (line 1269). All links in the document are pinned to specific base releases (`releases/3.0.1/`, `releases/3.0.0-hvd/`).
Versioning rules therefore have to come from elsewhere:

* STYLE PC-R3: "A consistent version management shall be implemented for the data specification evolution respecting the
  "semantic versioning" principles." (`gc-publication-conventions.adoc`, lines 96-110).
* STYLE PC-R4: "The data specification shall be versioned as a whole and never to atomic elements (concepts, relations or
  constraints)." and "No version information shall be embedded into any artefact URIs unless it is a version URI provided
  via `owl:versionIRI`." (same file, lines 135-162).
* Practice: HVD line 433 "As the publication URL indicates this version of DCAT-AP HVD is based on DCAT-AP 3.0.0."; MOB line 100
  "mobilityDCAT-AP is designed as an extension of [[DCAT-AP-v3.0.1]]".

---

## 3. Question 2 — DCAT-AP 3.0.0 and 3.0.1 specification text

Unless noted, 3.0.0 and 3.0.1 have identical wording; both line numbers are given as `AP300:n / AP301:n`.

### 3.1 Conformance Statement (`<section id="conformance">`, AP300:431-456 / AP301:432-457)

Provider requirements. "In order to conform to this Application Profile, an application that provides metadata MUST:"

1. "Provide a description of the Catalogue, including at least the mandatory properties specified for the class Catalogue."
2. "Provide information for the mandatory properties for Catalogue Records, if descriptions of Catalogue Records are
   provided – please note that the provision of descriptions of Catalogue Records is optional."
3. "Provide descriptions of Datasets in the Catalogue, including at least the mandatory properties for the class Dataset."
4. "Provide descriptions of Distributions, if any, of Datasets in the Catalogue, including at least the mandatory properties
   for the class Distribution."
5. "Provide descriptions of Data Services, if any, of Datasets in the Catalogue, including at least the mandatory properties
   for the class Data Service."
6. "Provide descriptions of all organisations involved in the descriptions of Catalogue and Datasets, including at least the
   mandatory properties for the class Agent."
7. "Apply the publication requirements for the controlled vocabularies as mentioned in section [controlled-vocs]."

Followed by (AP300:448-449 / AP301:449-450): "For the properties listed in the table in section [controlled-vocs], the
associated controlled vocabularies MUST be used. Additional controlled vocabularies MAY be used." and "In addition to the
mandatory properties, any of the recommended and optional properties defined in section [quick-reference] MAY be provided."

Receiver requirements (AP300:450-455 / AP301:451-456). "In order to conform to this Application Profile, an application
that receives metadata MUST be able to:" "Process information for all classes and properties specified in section
[quick-reference]." and "Process information for all controlled vocabularies specified in section [controlled-vocs]."
"Processing" is defined as: "receivers must accept incoming data and transparently provide these data to applications and
services."

Consequences **(inferred)**:

* Provider conformance is what a tightening extension preserves: data valid for E is still data a base provider may send.
* Receiver conformance is *not* inherited. A receiver built for E that ignores base properties E does not list is not a
  conformant base receiver. mobilityDCAT-AP deliberately does not use many optional base properties (section 6.3); that is
  a provider-side narrowing only.
* 2.1.1 still had the sentence "Recommended and optional classes may have mandatory properties, but those only apply if and
  when an instance of such a class is present in a description." (`releases/2.1.1/dcat-ap_2.1.1.pdf`, section 6.1). It is
  absent from 3.0.0 and 3.0.1 (0 matches), although the SHACL still behaves that way (shapes are `sh:targetClass` based).

### 3.2 Mandatory, recommended, optional, deprecated

Only *properties* are defined in 3.0.x, in the appendix "Quick Reference of Classes and Properties"
(`<section id="quick-reference" class="appendix">`, AP300:10554-10557 / AP301:10946-10949):

* "Mandatory property: a receiver MUST be able to process the information for that property; a sender MUST provide the
  information for that property."
* "Recommended property: a receiver MUST be able to process the information for that property; a sender SHOULD provide the
  information for that property if it is available."
* "Optional property: a receiver MUST be able to process the information for that property; a sender MAY provide the
  information for that property but is not obliged to do so."
* "Deprecated property: a receiver SHOULD be able to process information about instances of that property; a sender SHOULD
  NOT provide the information about instances of that property."

Classes. 3.0.x has **no** mandatory / recommended / optional class definitions. Classes are split into "Main Entities"
("those that form the core of the Application Profile", AP301:610) and "Supportive Entities" ("They are included in the
Application Profile because they form the range of properties.", AP301:8522-8523). Class-level obligation follows only from
the Conformance Statement. For the record, the class definitions existed up to 2.0.1 (`releases/1.1/dcat-ap_1.1.pdf` and
`releases/2.0.1/DCAT_AP_2.0.1.pdf`, section 2): "Mandatory class: a receiver of data MUST be able to process information about
instances of the class; a sender of data MUST provide information about instances of the class."; they were dropped in 2.1.x.

Where the obligation of a property is recorded: only in the quick-reference table (column "Property Type"). The per-class
tables give Property, Range, Card, Definition, Usage and a Reuse code. Cardinality notation is inconsistent and must be
normalised: `0..*`, `0..1`, `1..*`, `1` (exactly one) and `1..n`. Counts for 3.0.1 (131 rows, parsed with
`B2-artefacts/spec_tables.py`):

| Obligation | Card | Rows |
|---|---|---|
| Mandatory | `1` | 6 |
| Mandatory | `1..*` | 10 |
| Mandatory | `1..n` | 4 |
| Recommended | `0..*` | 22 |
| Recommended | `0..1` | 17 |
| Optional | `0..*` | 45 |
| Optional | `0..1` | 27 |

(3.0.0: same except Optional `0..*` 42 and `0..1` 30, the three relaxations of 3.0.1.)

The 20 mandatory (class, property) pairs of 3.0.1: `foaf:Agent` `foaf:name`; `dcat:Catalog` `dct:title`, `dct:description`,
`dct:publisher` (exactly 1); `dcat:CatalogRecord` `dct:modified` (1), `foaf:primaryTopic` (1); `spdx:Checksum` `spdx:algorithm` (1),
`spdx:checksumValue` (1); `dcat:DataService` `dct:title`, `dcat:endpointURL`; `dcat:Dataset` `dct:title`, `dct:description`;
`dcat:DatasetSeries` `dct:title`, `dct:description`; `dcat:Distribution` `dcat:accessURL`; `dcat:Relationship` `dcat:hadRole`,
`dct:relation`; `skos:Concept` `skos:prefLabel`; `skos:ConceptScheme` `dct:title`; `adms:Identifier` `skos:notation` (1).

### 3.3 Statements about extensions and profiles of DCAT-AP

| Statement | Quote | Where |
|---|---|---|
| What an application profile is | "An Application Profile is a specification that reuses terms from one or more base standards, adding more specificity by identifying mandatory, recommended and optional elements to be used for a particular application" | Terminology, AP300:466 / AP301:467 |
| Unlisted DCAT properties are optional | "Any property that is mentioned in DCAT applicable to a class but not explicitly is listed DCAT-AP is considered an optional field for DCAT-AP for that class." | Overview, AP300:513 / AP301:521 |
| Unlisted properties carry no expectation | "Properties that are not explicitly listed in this specification have no conformance expectation. From that perspective these are ignored." | AP300:514-515 / AP301:522-523 |
| Freedom on supporting classes | "DCAT-AP leaves a lot of freedom to the implementors to shape them to their needs. Only minimal expectations are expressed by DCAT-AP." | AP300:506 / AP301:514 |
| Extensions may add properties | "In such cases, extensions to DCAT-AP may be defined using additional properties with more specific meanings." | Agent Roles (informative), AP300:10113 / AP301:10468 |
| New properties need a managed namespace | "To enable the use of such properties, they must be defined as RDF properties with URIs in a well-managed namespace." | AP300:10120 / AP301:10475 |
| The base's own minted namespace | "DCAT-AP extends DCAT with a few properties. The used namespace http://data.europa.eu/r5r/." | AP301:501 only |
| Annex model | "These requirements can be expressed as additional constraints and usage notes on DCAT-AP and are collected in an annex dedicated to the implementation of the HVD IR" | AP300:10260 / AP301:10651 |
| Inverse properties | "In a proper DCAT profile the inverse property cannot be used to replace completely the property." | Inverse properties (informative), AP300:10516 / AP301:10907 |
| Profiles and CV level MUST | "All profiles in the ecosystem MUST avoid conflicts by creating subproperties." | AP301:10305 only |
| Profiles and CV level "at least one" | "All profiles in the ecosystem MUST adopt this interpretation in case they want to restrict the value space." | AP301:10311 only |
| Ecosystem list | DCAT-AP HVD, GeoDCAT-AP, StatDCAT-AP, Health DCAT-AP, Mobility DCAT-AP named as "European DCAT-AP profiles" | AP301:10621-10629 only |
| Reuse codes relative to DCAT | "A: reused as-is", "E: reused with additional usage notes or additional restrictions compared to DCAT", "P: DCAT-AP profile specific extension where DCAT had no requirements earlier on specified" | AP300:608-610 / AP301:615-617 |

The A/E/P code is the base's own vocabulary for "how did we treat the parent's element" and is reused by HVD and GeoDCAT-AP
relative to DCAT-AP (section 6). It is a ready-made label for the provenance of each ProfileChange.

### 3.4 Controlled vocabularies: 3.0.1 introduced four usage levels

Section "Controlled Vocabularies" (`id="controlled-vocs"`, marked `class="informative"` in both releases although the
Conformance Statement refers to it with MUST: AP300:9992 / AP301:10278).

3.0.0 has two tables: vocabularies that "MUST be used for the listed properties" (AP300:10010) and one that "MAY be used"
(AP300:10031). 3.0.1 adds "Expected usage of controlled vocabularies" (AP301:10295-10336) with four levels:

| Level | Text | Validation | Where |
|---|---|---|---|
| a | "The property MUST use as range values codes from {codelist}"; "the value space is closed under the codelist" | "Validation systems SHOULD produce errors." | AP301:10302-10305 |
| b | "The property MUST have at least one value from {codelist}"; "makes the value space minimally constrained" | "Validation systems SHOULD produce warnings." | AP301:10308-10312 |
| c | "The property IS RECOMMENDED to use as range values codes from {codelist}"; "other values are tolerated" | "validation systems SHOULD produce warnings" | AP301:10315-10318 |
| d | "The property MAY use as range values codes from {codelist}"; "other values are accepted" | "validation systems MAY produce warnings but users are free to ignore them" | AP301:10321-10326 |

Assignment in 3.0.1 (AP301:10345-10389): level a for `dcat:mediaType`, `dct:accrualPeriodicity`, `dct:format`, `dct:language`,
`adms:status`, `dcatap:availability`, `spdx:algorithm`, compression format, packaging format; level b for `dcat:theme` (Dataset,
Data Service); level c for `dct:type` (Agent, Licence Document) and `dct:accessRights`; level d for `dct:publisher`,
`dct:spatial`, `dct:type` (Dataset). In 3.0.0 `dcat:theme`, `dct:publisher`, `dct:spatial`, `dct:type` (Agent, Licence Document)
and `dct:accessRights` were all in the single MUST table. The CV obligation of a (class, property) pair is therefore
version-dependent, and it is independent of the property's own obligation (`dct:language` on Catalogue is a Recommended
property with a level-a vocabulary). The TSV artefact has both columns.

Requirements for the vocabularies themselves (AP300:9996-10006 / AP301:10283-10292): "Controlled vocabularies SHOULD:" be
"published under an open licence", be "properly documented", "Have terms that are identified by URIs with each URI resolving
to documentation about the term", "Have associated persistence and versioning policies", and others.

### 3.5 Deprecated terms

* Definition: see 3.2 ("a sender SHOULD NOT provide").
* List (AP300:12729-12738 / AP301:13110-13119): "dct:hasVersion is replaced by dcat:hasVersion.", "dct:isVersionOf is
  replaced by dcat:isVersionOf.", "owl:versionInfo is replaced by dcat:version." and "To identify these deprecations, a SHACL
  shape is provided." (`html/shacl/deprecateduris.ttl`).
* Rationale in 3.0.0 (AP300:331-332): "The sole data model impact DCAT 3 creates, is by deprecating the use of some URIs and
  introducing new URIs in the DCAT namespace for the use case of Dataset versioning."
* The quick-reference tables of 3.0.x contain no row typed "Deprecated" (0 of 131).
* The provided shape does not report anything in a standard engine (section 4.4, quirk Q-7).

### 3.6 Validation is declared informative and contextual

* "Each constraint in this specification that could be converted into a SHACL expression has been included." (AP300:10330 / AP301:10721)
* "It is up to the implementers of the data exchange to define the validation they expect." (AP300:10334 / AP301:10725)
* "the provided SHACL shapes provide only a start point for implementers" (AP300:10303 / AP301:10694)
* "For DCAT-AP conformance, it is not mandatory that this happens in a RDF serialisation, but the exchanged format SHOULD be
  unambiguously be transformable into RDF." (AP300:10278 / AP301:10669)
* The new-style file: "the constraints are also provided in a new design where each constraint has got a unique identifier"
  so that "DCAT-AP implementers could cherry pick the constraints they want" (AP300:10371-10372 / AP301:10762-10763).

Status and licence lines: AP300:401 "SEMIC Recommendation published at 2024-06-14"; AP301:402 "SEMIC Draft Specification
published at 2025-07-10" while the repository `README.md` calls 3.0.1 "SEMIC Recommendation v3.0.1" (verify: which label
applies). Licence: AP300:425 / AP301:426, see 4.6.

---

## 4. Question 3 — the official SHACL files

Numbers come from `B2-artefacts/shacl_inventory.py` (rdflib parse of each file).

### 4.1 Inventory

**DCAT-AP 1.1** — two zip archives, same three files in two syntax generations.

| Path | Size | Content |
|---|---|---|
| `releases/1.1/shacl-201608.zip` (6 681 B) → `dcat-ap.shapes.ttl` (15 112 B) | 368 triples | Base shapes for 4 classes (Catalog, CatalogRecord, Dataset, Distribution), cardinality + `sh:class` + node kind. **Pre-Recommendation syntax**: `sh:predicate` (66) instead of `sh:path`, `sh:Shape`, `sh:shape` |
| … → `dcat-ap-mandatory-classes.shapes.ttl` (5 072 B) | 72 triples | "At least one Agent, Catalog, Dataset exists": `sh:targetNode` + `sh:inversePath rdf:type` + `sh:minCount 1` |
| … → `dcat-ap-mdr-vocabularies.shapes.ttl` (13 803 B) | 319 triples | Controlled vocabularies: `skos:inScheme` + `sh:hasValue <scheme>` restriction shapes, `sh:or` for spatial |
| `releases/1.1/shacl-201706.zip` (6 515 B) → same three names (14 842 / 5 084 / 13 760 B) | 369 / 72 / 320 triples | Same content in June-2017 syntax (`sh:path`, `sh:NodeShape`, `sh:node`; 3 leftover `sh:shape`) |

**DCAT-AP 2.0.1** (`releases/2.0.1/`)

| File | Size | Content |
|---|---|---|
| `dcat-ap_2.0.1_shacl_shapes.ttl` | 20 347 B, 617 triples | Base **and** range in one file: 14 `sh:targetClass` shapes, 109 property shapes, 66 `sh:class`, 18 `sh:minCount`, 48 `sh:maxCount`; all `sh:Violation` |
| `dcat-ap_2.0.1_shacl_mdr-vocabularies.shape.ttl` | 13 837 B, 275 triples | Controlled vocabularies for Catalog, Dataset, Distribution, LicenseDocument; 8 Violation, 6 Warning |
| `dcat-ap_2.0.1_shacl_deprecateduris.ttl` | 1 663 B, 11 triples | `schema:startDate` / `schema:endDate` on PeriodOfTime, Warning, no constraint component |

No recommended-level file and no imports file in 2.0.1.

**DCAT-AP 2.1.1** (`releases/2.1.1/`) — first release with the seven-file layout.

| File | Size | Content |
|---|---|---|
| `dcat-ap_2.1.1_shacl_shapes.ttl` | 18 473 B, 559 triples | Existence, cardinality, literal ranges. 14 target classes, 109 property shapes (36 of them path-only) |
| `dcat-ap_2.1.1_shacl_range.ttl` | 12 813 B, 350 triples | Object ranges: 65 property shapes, each one `sh:class` |
| `dcat-ap_2.1.1_shacl_shapes_recommended.ttl` | 9 423 B, 225 triples | Recommended properties: 29 × `sh:minCount 1` + `sh:Warning` |
| `dcat-ap_2.1.1_shacl_mdr-vocabularies.shape.ttl` | 16 088 B, 321 triples | Controlled vocabularies; 10 Violation, 7 Warning |
| `dcat-ap_2.1.1_shacl_deprecateduris.ttl` | 1 664 B | as 2.0.1 |
| `dcat-ap_2.1.1_shacl_imports.ttl` | 1 435 B | `owl:imports` of 10 vocabularies (DCAT 2, DCTERMS, FOAF, LOCN, SPDX, schema.org, PROV-O, OWL-Time, vCard, ADMS) |
| `dcat-ap_2.1.1_shacl_mdr_imports.ttl` | 1 622 B | `owl:imports` of 13 code lists (EU Vocabularies NALs, ADMS SKOS) |

**DCAT-AP 3.0.0 and 3.0.1** — two flavours each.

| File | 3.0.0 size | 3.0.1 size | Content (3.0.1 numbers) |
|---|---|---|---|
| `html/shacl/shapes.ttl` | 20 608 B | 20 619 B | "constraints concerning existence, domain and literal range, and cardinalities" (AP301:10739). 15 target classes, 130 property shapes, 20 `sh:minCount`, 54 `sh:maxCount`, 100 `sh:nodeKind`; 129 Violation, 1 Warning |
| `html/shacl/range.ttl` | 12 490 B | 12 490 B (identical) | "constraints concerning object range" (AP301:10740). 82 property shapes, 84 `sh:class` |
| `html/shacl/shapes_recommended.ttl` | 10 170 B | 10 170 B (identical) | "constraints concerning existence of recommended properties" (AP301:10749). 36 property shapes `sh:minCount 1` + `sh:Warning`, plus one `sh:or` node shape |
| `html/shacl/mdr-vocabularies.shape.ttl` | 17 444 B | 19 592 B | "constraints concerning the usage of controlled vocabularies" (AP301:10741). 7 target classes; 13 Violation, 13 Warning |
| `html/shacl/deprecateduris.ttl` | 4 144 B | 4 144 B (identical) | Deprecated URIs (2.x and 3.x) and the old ADMS status code list |
| `html/shacl/imports.ttl` | 1 435 B | identical | Vocabulary imports (still `dcat2.ttl`) |
| `html/shacl/mdr_imports.ttl` | 1 622 B | identical | Code-list imports |
| `shacl/dcat-ap-SHACL.ttl` | 178 717 B, 1 968 triples | 155 471 B, 1 874 triples | **New style**, "each constraint has got a unique identifier": 33 node shapes (42 in 3.0.0), 292 property-shape links, one constraint per property shape, IRIs such as `<https://semiceu.github.io/DCAT-AP/releases/3.0.1#dcat:DatasetShape/6b72…>`; 20 `sh:minCount`, 50 `sh:maxCount`, 83 `sh:class`, 6 `sh:datatype`, 131 `sh:nodeKind` |
| `shacl/dcat-ap-SHACL.jsonld` | 187 407 B | absent | JSON-LD serialisation of the new-style file (3.0.0 only) |
| `shacl/ranges.ttl` | absent | 80 322 B, 895 triples | New-style range-only extract: 85 `sh:class`, 6 `sh:datatype`; 206 of its 297 `sh:property` links dangle |

Which files the official validator combines (ITB `resources/config.properties`, lines 195-246):

| ITB validation type | Files |
|---|---|
| "Base Zero (no background knowledge)" | `shapes.ttl` |
| "Ranges Zero (no background knowledge)" | `range.ttl` |
| "Base (with background knowledge)" | `shapes.ttl` + `imports.ttl`, `loadImports = true` |
| "Ranges (with background knowledge)" | `range.ttl` + `imports.ttl`, `loadImports = true` |
| "Controlled Vocabularies" | `mdr-vocabularies.shape.ttl` + `mdr_imports.ttl`, `loadImports = true` |
| "Recommendations (with background knowledge)" | `shapes_recommended.ttl` + `imports.ttl` |
| "Full (with background knowledge)" | `shapes.ttl` + `range.ttl` + `shapes_recommended.ttl` + `imports.ttl` + `deprecateduris.ttl` |
| "Full (individual constraints)" | `shacl/dcat-ap-SHACL.ttl` |

Note that for 3.0.1 the ITB configuration fetches the files from `…/gh-pages/releases/3.0.1-draft/…` (lines 196-245), not from
`releases/3.0.1/` (verify: that the draft copies equal the release copies read here).

The ITB README explains why ranges are separate: "these rules should not be executed because they are always valid" when
the receiver trusts the sender's typing (ITB `README.md`, option 2).

### 4.2 How obligation levels are represented

| Level | Legacy flavour | New style |
|---|---|---|
| Mandatory property | `sh:minCount n` (n >= 1) with `sh:severity sh:Violation`, in `shapes.ttl` | `sh:minCount n` in its own property shape, no `sh:severity` (default Violation) |
| Recommended property | `sh:minCount 1` with `sh:severity sh:Warning`, in `shapes_recommended.ttl` (since 2.1.x) | **not represented** (all 39 recommended rows have no shape for it) |
| Optional property | Property shape with range / node kind / `sh:maxCount` only | same |
| Deprecated property | Property shape with `sh:path` + `sh:severity sh:Warning` + `sh:message`, no constraint | not represented |
| CV level a (closed) | `sh:node :XRestriction` + `sh:nodeKind sh:IRI`, `sh:Violation` | not represented |
| CV levels b, c, d | same construct with `sh:Warning` (level d partly not checked) | not represented |
| "Catalogue should list datasets or services" | Node-level `sh:or ( [sh:path dcat:dataset; sh:minCount 1] [sh:path dcat:service; sh:minCount 1] )` with `sh:Warning` (`:Catalog_Shape2`) | not represented |

SHACL itself: "The specific values of sh:severity have no impact on the validation" and "The value of sh:conforms is true if and only if the
validation did not produce any validation results" (SHACL, sections "Severity" and "Validation Report"). A warning-only
report therefore has `sh:conforms false`; the hard verdict must count results of severity `sh:Violation`.

### 4.3 Constructs

| Construct | Legacy flavour (3.0.1) | New style (3.0.1) | Older releases |
|---|---|---|---|
| Targets | `sh:targetClass` on every validating shape | `sh:targetClass` on all 33 | 1.1: **implicit class targets** (shape IRI = class IRI, no `rdfs:Class` triple in the file) and `sh:targetNode` |
| `sh:closed` | absent | `sh:closed false` on all node shapes | absent |
| `sh:or` | datatype union `:DateOrDateTimeDataType_Shape` (date, dateTime, gYear, gYearMonth); class union `:DcatResource_Shape` (Catalog, Dataset, DataService, DatasetSeries); `:Catalog_Shape2`; spatial CV union | none | 1.1 / 2.x: date union with two members |
| `sh:node` | 8 in `shapes.ttl`, 2 in `range.ttl`, 31 in the CV file | none | yes |
| `sh:in` | none | none | none |
| `sh:hasValue` | 15 in the CV file (`skos:inScheme` has value scheme; `dcat:themeTaxonomy` has value data-theme scheme) | none | 2.x: `spdx:algorithm sh:hasValue spdx:checksumAlgorithm_sha1` |
| `sh:pattern` | 3 in the CV file: `^https://sws.geonames.org`, `^http.*://www.iana.org/assignments/media-types/`, `^https://spdx.org/rdf/terms` | none | none |
| Complex paths | `[ sh:inversePath dcat:inSeries ]` on DatasetSeries (Warning) | none | 1.1: `sh:inversePath rdf:type` |
| Qualified value shapes, SPARQL, `sh:not`, `sh:xone`, `sh:and` | none | none | none |
| Property-shape IRIs | blank nodes | IRIs (hash per constraint) | blank nodes |

DCAT-AP HVD 3.0.0 adds, in `html/hvd-SHACL-usagenotes.ttl`: `sh:hasValue <http://data.europa.eu/eli/reg_impl/2023/138/oj>` on
`dcatap:applicableLegislation`; `sh:node` to a scheme restriction for `dcatap:hvdCategory`; node-level `sh:or` of `sh:minCount 1`
alternatives ("licence or rights"); and the path `[ sh:alternativePath ( [ sh:inversePath dcat:servesDataset ] ( dcat:distribution dcat:accessService ) ) ]`.

### 4.4 Known quirks (all verified on the files)

| ID | File | Quirk | Effect |
|---|---|---|---|
| Q-1 | 3.0.1 `shacl/dcat-ap-SHACL.ttl` lines 564, 566 | Two `sh:property` objects (`…#dcat:DataServiceShape/dc08f4dc…` and `…/eb3ac4e4…`) have no triples | pySHACL 0.40.2: `ReportableRuntimeError: … exists but is not a well-formed SHACL PropertyShape`. SHACL-SHACL reports 2 `sh:path` min-count results |
| Q-2 | 3.0.1 `shacl/ranges.ttl` | 206 of 297 `sh:property` links dangle; 7 `rdfs:member` entries are not node shapes | same engine error |
| Q-3 | 3.0.1 `html/shacl/shapes.ttl` | Identical to 3.0.0 except line 515 (`xsd:decimal` → `xsd:nonNegativeInteger` for `dcat:byteSize`); prefix on line 2 still `…/releases/3.0.0/html/shacl/shapes.ttl#` | 3.0.1 relaxations missing: `sh:maxCount 1` kept on `dct:rights` (Catalog, Distribution) and `dcat:spatialResolutionInMeters` (Dataset) |
| Q-4 | 3.0.x `shapes.ttl` | `dct:conformsTo` on CatalogRecord has `sh:maxCount 1`; table says `0..*` | stricter than the specification (also noted in MOB `src/shacl/shapes.ttl`, header comment) |
| Q-5 | 3.0.x `shapes.ttl` | `skos:notation` on `adms:Identifier` has no `sh:minCount`; table says `1` | looser than the specification |
| Q-6 | 3.0.x `shapes.ttl` lines 66, 373, 403, 658, 671 | `sh:shape :DateOrDateTimeDataType_Shape` — `sh:shape` is not a SHACL term | Constraint silently ignored for `dct:modified` (CatalogRecord, Dataset), `dct:issued` (Dataset), `dcat:startDate`, `dcat:endDate`. Verified: `"not a date"` passes on Dataset, fails on Catalog (which uses `sh:node`) |
| Q-7 | 3.0.x `deprecateduris.ttl` | Deprecation property shapes have `sh:path`, `sh:severity`, `sh:message` and no constraint | No result is ever produced. Verified with a dataset using `dct:hasVersion` and `owl:versionInfo`: 0 results |
| Q-8 | 3.0.x `shapes.ttl` line 343, `range.ttl` line 230 | Shapes for the deprecated `dct:hasVersion`; none for `dcat:hasVersion`; also none for `dct:temporal` on Catalog and `foaf:page` on DataService; extra `dct:isPartOf` on Catalog (`range.ttl` line 100) | Legacy set covers 128 of the 131 table rows, plus 2 legacy properties and one inverse-path shape |
| Q-9 | 3.0.x legacy vs new | `locn:geometry` on `dct:Location`: legacy `sh:nodeKind sh:Literal`; new style `sh:class locn:Geometry` + `sh:BlankNodeOrIRI` (table: range Geometry) | The two flavours are contradictory here |
| Q-10 | 3.0.x legacy vs new | `foaf:primaryTopic` and `dct:relation` (Relationship): legacy `sh:node :DcatResource_Shape` (four concrete classes); new style `sh:class dcat:Resource` / node kind only | A new subclass of `dcat:Resource` is accepted by one flavour and rejected by the other unless double typed |
| Q-11 | 3.0.x legacy vs new | `dcatap:applicableLegislation` and `dcat:theme`: legacy `sh:nodeKind sh:IRI`; new style `sh:BlankNodeOrIRI` | legacy stricter |
| Q-12 | 3.0.0 `shacl/dcat-ap-SHACL.ttl` | Target classes include `rdfs:Literal`, `rdfs:Resource`, `xsd:dateTime`, `xsd:decimal`, …; `sh:class rdfs:Resource` on 7 (class, property) pairs (`dcat:accessURL`, `dcat:downloadURL`, `dcat:endpointURL`, …) | A minimal valid catalogue fails unless RDFS inference types everything as `rdfs:Resource`. Removed in 3.0.1 main file; 2 remain in `ranges.ttl` |
| Q-13 | 3.0.x new style | Temporal Literal ranges are only `sh:nodeKind sh:Literal` | No datatype check for 12 date properties |
| Q-14 | 3.0.x `shapes_recommended.ttl`, `mdr-vocabularies.shape.ttl` | Header still `owl:versionInfo "2.1.1"`, prefix `:` = `http://data.europa.eu/r5r#` (hash) | Metadata only; note the shape IRIs collide across files (`:Distribution_ShapeCV` is defined in both the CV file and `deprecateduris.ttl`) |
| Q-15 | all class-typed range checks | `sh:targetClass skos:Concept` requires `skos:prefLabel`, `skos:ConceptScheme` requires `dct:title` | Typing a code-list value as `skos:Concept` in the data makes it a focus node. The imports file notes the same problem for ODRL concepts (`imports.ttl`, comment lines 6-10) |
| Q-16 | 2.0.1 `shacl_shapes.ttl` line 272 | `sh:dateTime xsd:hexBinary` (typo for `sh:datatype`); line 266 `sh:hasValue spdx:checksumAlgorithm_sha1`; `owl:versionInfo "2.0.0"` | Checksum value unchecked; algorithm forced to SHA-1 |
| Q-17 | 1.1 `dcat-ap.shapes.ttl` | No explicit targets; relies on `owl:imports` to make the shape IRIs classes | Without import resolution nothing is validated (verified: 0 results) |
| Q-18 | 1.1 `dcat-ap-mandatory-classes.shapes.ttl` lines 99, 111, 123 | `sh:targetNode "foaf:Agent"` — a string literal, not an IRI | Three violations on every data graph (verified) |
| Q-19 | 1.1 files | `owl:versionInfo "1.2"` inside the 1.1 archives | metadata |
| Q-20 | 3.0.1 `mdr-vocabularies.shape.ttl` lines 264-271 | `:LicenseDocument_ShapeCV` has no `sh:severity` (default Violation) although `dct:type` on Licence Document is a level-c (RECOMMENDED) vocabulary in the 3.0.1 table | stricter than the specification |
| Q-21 | 3.0.1 `mdr-vocabularies.shape.ttl` | The level-b vocabulary of `dcat:theme` ("at least one value") is encoded as `sh:node :DataThemeRestriction` on *every* value, with Warning | every additional theme from another scheme produces a warning; "at least one" is not what is tested |

### 4.5 A cross-check you can rerun

`B2-artefacts/crosscheck.py` compares the specification tables with each flavour. For 3.0.1:

* New style: all 131 pairs present, **0 cardinality mismatches**, 39 recommended rows without any recommended marker.
* Legacy (`shapes.ttl` + `range.ttl` + `shapes_recommended.ttl`): 3 pairs missing, 3 extra, and 8 facet mismatches —
  `Catalogue.rights`, `Distribution.rights`, `Dataset.spatialresolution`, `CatalogueRecord.applicationprofile` (SHACL max 1,
  table unbounded), `Identifier.notation` (no min), and three recommended rows without a Warning min count
  (`Catalogue.dataset`, `Catalogue.service` — expressed through `sh:or` — and `DatasetSeries.geographicalcoverage`).

For 3.0.0 the legacy set has the `applicationprofile` and `notation` mismatches plus the same three recommended rows; the new
style again has no cardinality mismatch.

### 4.6 Licence for redistribution

* Repository licence file: `/home/user/refs/SEMICeu__DCAT-AP/LICENSE`, first line "Attribution 4.0 International" (Creative
  Commons Attribution 4.0 International Public License).
* Repository statement: `/home/user/refs/SEMICeu__DCAT-AP/README.md` line 28: "Copyright © 2026 European Union. All material in
  this repository is published under the licence CC-BY 4.0, unless explicitly otherwise mentioned."
* Specification statement: `releases/3.0.1/index.html` line 426 ("Copyright © 2025 European Union. All material in this
  repository is published under the license CC-BY 4.0, unless explicitly otherwise mentioned."), `releases/3.0.0/index.html` line 425.
* In-file statements: `dct:license <https://creativecommons.org/licenses/by/4.0>` in the 2.0.1 and 2.1.1 shape files and in
  3.0.x `shapes_recommended.ttl` and `mdr-vocabularies.shape.ttl` (line 62 / 61). 3.0.x `shapes.ttl`, `range.ttl`,
  `deprecateduris.ttl`, `imports.ttl`, `mdr_imports.ttl` and the new-style files carry no licence triple and fall under the
  repository statement.
* **Exception:** the 1.1 archives (and the 1.2 / 1.2.1 base shapes) declare
  `dct:license <https://joinup.ec.europa.eu/category/licence/isa-open-metadata-licence-v11>` with
  `dct:rightsHolder <http://publications.europa.eu/resource/authority/corporate-body/EURUN>` (e.g. `dcat-ap.shapes.ttl` lines 63
  and 67). That is "explicitly otherwise mentioned". verify: the terms of the ISA Open Metadata Licence v1.1 before bundling
  the 1.1 shapes (the licence text was not reachable from here).
* What CC BY 4.0 asks when the files are shipped inside another tool (`LICENSE` lines 215-244, Section 3(a)(1)): retain
  "identification of the creator(s)", "a copyright notice", "a notice that refers to this Public License", "a URI or hyperlink
  to the Licensed Material"; "indicate if You modified the Licensed Material"; and indicate the licence. The host repository
  (`/home/user/visual-profile-editor/LICENSE`) is Apache-2.0, so the shapes should sit in a clearly separated third-party
  folder with a notice file; a cleaned copy (dangling links removed) must be marked as modified **(inferred from the licence text)**.
* The extension repositories used as fixtures are CC BY 4.0 as well (GEO `LICENCE.md`, MOB `LICENCE.md`, DE `LICENSE`).

---

## 5. Question 4 — an implementable rule set for "E conforms to B"

### 5.0 The model the rules operate on

**Key.** `k = (target class IRI, property path IRI)`. Complex paths are out of the comparable fragment and are reported.

**Facet record per key** (one for B, one for E):

```yaml
key: [dcat:Distribution, dct:license]
min: 0                    # hard minimum (severity Violation)
max: 1                    # integer or "*"
obligation: recommended   # mandatory | recommended | optional  (label of the specification table)
value_kind: resource      # literal | resource
datatypes: []             # disjunction; empty = any literal
classes: [dct:LicenseDocument]   # conjunction
node_kinds: [IRI, BlankNode]     # subset of {IRI, BlankNode, Literal}
in: null                  # list of constants or null
has_value: []             # required constants
patterns: []              # conjunction
cv: {level: null, schemes: []}   # level: a | b | c | d | null  (section 3.4)
reuse_code: E             # A | E | P relative to the parent
deprecated: false
```

**Base B.** A pinned release. The authoritative facet table is the specification text
(`B2-artefacts/dcat-ap-3.0.1-base-table.tsv`, 131 rows: class, property, obligation, card, min, max, range, reuse code, CV
level, and what each SHACL flavour encodes). The SHACL files are test oracles, not the definition (finding 4).

**Publication mode of E** (must be explicit; the two modes have different failure modes):

* `delta` — E's shapes are *added* to B's (`owl:imports` or union). Effective facets are the meet:
  `min = max(B.min, Δ.min)`, `max = min(B.max, Δ.max)`, sets intersect or accumulate. mobilityDCAT-AP 3.0.0 states the
  consequence: "Because imported and local constraints apply together, the shapes can make a rule stricter but cannot
  loosen an inherited one." (MOB `src/index.html` line 1096).
* `standalone` — E restates everything and is validated alone. Anything E omits is loosened by omission.

**Three failure modes** (derived, our interpretation; each is checked separately):

1. *Documented loosening*: the profile model (LinkML / DSV / HTML table) states a weaker facet than B. Static check 5.1.
2. *Contradiction*: `B ⊓ Δ` admits no instance of a class (for example Δ `minCount 2` where B `maxCount 1`). Static check P-03 plus witness generation.
3. *Semantic drift*: a reused term is given a different meaning. Not machine-decidable; route to human review with the base definition shown next to the proposed usage (RG-51, RG-52).

**Finding levels.** `ERROR` blocks the change set. `WARN` needs an explicit human decision recorded with the change. `INFO` is logged.

### 5.1 Profile level — facet rules

For each key present in both B and E. "Legal" covers equal and tighter.

| ID | Facet | Legal when | Illegal when (level) | Source |
|---|---|---|---|---|
| P-01 | Minimum count | `E.min >= B.min` | `E.min < B.min` (ERROR) | RG-22 "Then it must be mandatory in the profile as well."; RG-26; RG-21 |
| P-02 | Maximum count | `E.max <= B.max`, unbounded counted as infinity | `E.max > B.max`, including "unbounded where B is bounded" (ERROR) | RG-23 "the property also must have at most one value"; RG-24 |
| P-03 | Satisfiability | `E.min <= E.max`; number of `has_value` constants `<= E.max`; `in` has at least `E.min` members; at most one datatype after intersection; not both a datatype and a class | otherwise the profile is empty for that class (ERROR, reported as UNSATISFIABLE, not as loosening) | derived (our interpretation) |
| P-04 | Obligation label | mandatory stays mandatory; optional may become recommended or mandatory; recommended may become mandatory | mandatory to recommended or optional (ERROR); recommended to optional (WARN, see note 1) | RG-22; DE `06_conformity.md` (section 6.5); GEO practice (section 6.2) |
| P-05 | Value kind | same kind | literal to resource or resource to literal (ERROR; use another property) | RG-27, RG-28 "Reuse not possible. Another property needs to be used." |
| P-06 | Datatype | B has no datatype (range Literal): any datatype. B has a union (Temporal Literal): `E.datatypes ⊆ B.datatypes`. B has one datatype: the same datatype (see note 2) | a datatype outside B's set (ERROR); an XSD-derived subtype of B's single datatype (WARN: legal per RG-29, rejected by the base shapes) | RG-29, RG-30; SHACL "A shape has at most one value for sh:datatype"; verified, note 2 |
| P-07 | Class | `E.class = B.class`; or `E.class rdfs:subClassOf* B.class` is asserted in the vocabulary index or in E's own vocabulary; or B's class is kept and the values are restricted to a list | a superclass of B's class (ERROR); an unrelated class (WARN: needs a recorded "semantically compatible" decision and double typing) | RG-31, RG-32; RG lines 1164-1166 "then this is not compliant with DCAT-AP" |
| P-08 | Node kind | `E.node_kinds ⊆ B.node_kinds` (for example IRI only where B allows IRI or blank node) | a kind B does not allow (ERROR) | RG-33 "Narrowing down the value space will not create any issues but extending it will."; set reading is derived |
| P-09 | Enumeration `sh:in` | B has a list: `E.in ⊆ B.in`. B has none: any list whose members satisfy B's other facets | members outside B's list, or dropping B's list (ERROR) | RG-33; derived |
| P-10 | Required constant `sh:hasValue` | adding a constant admissible under B; it implies `min >= 1` | removing a constant B requires (ERROR); a constant B's facets reject (ERROR, P-03) | derived; pattern used by HVD (`hvd-SHACL-usagenotes.ttl`, `…/DatasetShape/HVDELI`) |
| P-11 | Pattern, length, numeric bounds, `sh:languageIn`, `sh:uniqueLang` | E keeps every base constraint and adds its own as *additional* constraints | replacing or removing a base constraint (ERROR). Regex inclusion is not decidable in general, so "replace" is never accepted | derived |
| P-12 | CV level a (closed) | same vocabulary, or a subset of it | another vocabulary on the same property (ERROR; mint a sub-property) | RG-35, RG-54; AP301:10305 "All profiles in the ecosystem MUST avoid conflicts by creating subproperties." |
| P-13 | CV level b (at least one) | E keeps "at least one value from the base vocabulary"; other vocabularies only in addition | dropping the base value (ERROR); closing the property to another vocabulary (ERROR) | RG-36, RG-40; AP301:10311-10312 |
| P-14 | CV levels c and d | any vocabulary; the level may be raised | — | RG-37; AP301:10315-10326 |
| P-15 | Severity of the same constraint | `E.severity >= B.severity` with Info < Warning < Violation | Violation lowered (ERROR); Warning lowered to Info (WARN) | derived from 4.2 and SHACL "sh:Violation is the default if sh:severity is unspecified" |
| P-16 | Label, definition, usage note | unchanged, or more specific without contradiction; a context label is documentation only | contradicting or broadening the base text (ERROR after human review); changing the definition of an as-is reuse (ERROR) | RG-41, RG-42, RG-52; STYLE `clarification-on-reuse.adoc` "Definition: NO change allowed" (as-is and terminological reuse) |
| P-17 | Deprecated base terms | E does not require or recommend them | E makes a deprecated IRI mandatory or recommended (WARN) | derived from AP301:10949 "a sender SHOULD NOT provide" |
| P-18 | Inverse properties | E does not replace a base property by its inverse | replacement (WARN) | AP301:10907 "the inverse property cannot be used to replace completely the property"; level is derived |
| P-19 | Not using a base property | omission, or prohibition (`max = 0`), when `B.min = 0` | prohibiting a property with `B.min >= 1` (ERROR, P-03) | MOB line 117 "Non-usage of optional properties"; DE "können in der Erweiterung entfernt werden"; derived |

Note 1 — recommended to optional. RG says only tightening is possible (RG-20). DCAT-AP.de 2.0 allows it explicitly:
"Empfohlene Eigenschaften aus DCAT-AP 2.0 können in der Erweiterung als optional, empfohlen oder obligatorisch deklariert
werden." GeoDCAT-AP 3.1.0 does it once (`Distribution.availability`, line 14430: Optional; DCAT-AP 3.0.1 line 6715:
Recommended). It does not change which data is valid (the base raises a Warning either way). We classify it WARN so the
reviewer decides; this is a derived choice.

Note 2 — datatypes. `sh:datatype` compares the datatype IRI of the literal. Probe
(`B2-artefacts/data/probe_subtype_subclass.ttl`): `dcat:spatialResolutionInMeters "25"^^xsd:integer` against the cleaned 3.0.1
shapes gives `sh:DatatypeConstraintComponent` (base: `xsd:decimal`). Narrowing inside the Temporal Literal union is safe in
the legacy flavour (it lists the four datatypes) and invisible in the new style (node kind only).

Keys that exist only in E:

| ID | Case | Rule | Source |
|---|---|---|---|
| P-20 | Property added to a base class | Allowed. No base shape is closed (4.3), and "Properties that are not explicitly listed in this specification have no conformance expectation." | AP301:522; RG-10, RG-12 |
| P-21 | Added property is a DCAT property not listed by DCAT-AP for that class | It is already an optional field of the base for that class; E may constrain it freely but should follow DCAT's definition | AP301:521 "is considered an optional field for DCAT-AP for that class" |
| P-22 | Added property is a sub-property of a base property (declared in a vocabulary) | The base facets of the super-property do not apply to it in SHACL (no inference), but the *semantic* constraints do: its values are values of the super-property for a reasoning consumer. Check the union against the super-property's `max` and CV level (WARN when exceeded) | derived; evidence: RDFS inference makes `dcat:mediaType` values count as `dct:format` values and break `sh:maxCount 1` (5.6, CAV-5) |

### 5.2 Profile level — class rules

| ID | Rule | Level | Source |
|---|---|---|---|
| C-01 | The classes the Conformance Statement requires descriptions for keep their mandatory properties: Catalogue, Dataset, Distribution ("if any"), Data Service ("if any"), Agent; Catalogue Record when present | ERROR | AP301:436-447 |
| C-02 | A new class is allowed when no admissible existing class fits; it needs an IRI in E's namespace (or a reused IRI), a label and a definition | ERROR if missing | RG-12, RG-13 |
| C-03 | A class that specialises a base class is declared `rdfs:subClassOf` that class in E's vocabulary. All base facets of the superclass apply to it; E may tighten them for the subclass (same P-rules, B = superclass facets) | ERROR | RG-15, RG-43; STYLE "Must create a subclass that captures the adaptations" |
| C-04 | A new class must not duplicate a base class under another IRI | WARN | DE "sollten solche Klassen keine Ähnlichkeit zu ursprünglichen DCAT-AP-Klassen aufweisen"; RG reuse order |
| C-05 | A reused base class keeps its definition; a context label is documentation; usage notes may be sharpened | ERROR on changed definition | RG-44, RG-45; STYLE "Definition: NO change allowed" |
| C-06 | New mandatory properties on a supportive class shared across profiles (Agent, Kind, Licence Document, Standard, Concept, Location …) are flagged | WARN | RG lines 1632-1640 "the profile imposes that all licences must have a title" and "to minimise the cross-profile interference" |
| C-07 | A base class may be left unused only if the base does not require it; prohibiting instances of a required class makes E empty | ERROR | AP301:436-447; MOB `#classes-and-properties-not-used-from-DCAT-AP` |
| C-08 | A subclass of `dcat:Resource` used as value of `foaf:primaryTopic`, `dct:relation` (Relationship) or other base ranges must be double typed with one of `dcat:Catalog`, `dcat:Dataset`, `dcat:DataService`, `dcat:DatasetSeries` to pass the legacy shapes | WARN (documented in the profile's usage note) | Q-10; RG-32 "double type the resources" |

### 5.3 Profile level — namespace rules

| ID | Rule | Level | Source |
|---|---|---|---|
| N-01 | Minted classes and properties use only a namespace the profile owner controls. Never mint under `http://www.w3.org/ns/dcat#`, `http://purl.org/dc/terms/`, `http://data.europa.eu/r5r/` (DCAT-AP), `http://data.europa.eu/930/` (GeoDCAT-AP), `https://w3id.org/mobilitydcat-ap#`, or any other namespace found in the vocabulary index | ERROR | RG-13; AP301:10475 "URIs in a well-managed namespace" |
| N-02 | Minted IRIs are persistent and dereferenceable with content negotiation (HTML and RDF) | WARN at design time, ERROR at publication | RG-61, RG-62, RG-63 |
| N-03 | Minted terms are defined in a supporting vocabulary that is separate from the profile, with generic domain and range; the context-specific constraints live in the profile's shapes | WARN | RG-64 to RG-68 |
| N-04 | Shape IRIs live in the profile's own versioned namespace. No triple of E has a base shape IRI as subject. E never sets `sh:deactivated true` on a base shape | ERROR | SHACL "sh:deactivated can be set to true in the local shapes graph for imported shapes"; SHACL "A property shape has at most one value for sh:minCount"; MOB `src/shacl/README.md` "Each shape file declares its own versioned namespace, so shapes from different files do not collide" |
| N-05 | No version segment in term IRIs; the version goes in the profile IRI and the shapes-graph IRI | WARN | STYLE PC-R4 |
| N-06 | Code lists used in constraints are published as linked data and meet the base's requirements for controlled vocabularies | WARN | RG-14, RG-39; AP301:10283-10292 |

### 5.4 Profile level — term-reuse rules

| ID | Rule | Level | Source |
|---|---|---|---|
| T-01 | Search order before minting: DCAT-AP, then W3C DCAT, then other DCAT-AP profiles and admissible vocabularies | ERROR when a mint duplicates an indexed term with the same meaning | RG section 2.6; RG heading at line 408 |
| T-02 | A reused IRI exists in the vocabulary snapshot the tool indexes (exact IRI match, not a guess) | ERROR | derived (planned Verify step "term exists") |
| T-03 | Domain fit: the target class is the property's declared domain or a subclass of it, or the property has no domain | ERROR on a disjoint domain, WARN when unknown | RG-10 "given that it does not cause a semantic issue"; RG lines 428-430 |
| T-04 | An as-is reuse carries the base label, definition, usage note, cardinality and mandatory code lists unchanged | ERROR | RG lines 291-292 |
| T-05 | A different value kind or an incompatible range means a different property, not a redefinition | ERROR | RG-27, RG-28, RG-53 |
| T-06 | A semantic adaptation is expressed as a sub-property or subclass in E's vocabulary, with a more specific label and definition | ERROR | RG-43; STYLE "Must create a sub-property that captures the adaptations." |
| T-07 | A minted property must not resemble an existing base property (near-duplicate by label or definition) | WARN | DE "keine Ähnlichkeit zu ursprünglichen DCAT-AP-Eigenschaften"; RG reuse order |
| T-08 | Terms already minted by another DCAT-AP profile for the same need are preferred over a new mint | WARN | RG heading "covered by W3C DCAT or another vocabulary or DCAT-AP profile"; MOB line 113 "including reusage of classes from [[GeoDCAT-AP-v3.0.0]]" |

### 5.5 Profile level — documentation, declaration, versioning

| ID | Rule | Level | Source |
|---|---|---|---|
| D-01 | Every ProfileChange that mints, tightens or affects interoperability carries the requirement atoms it covers and a reason | ERROR | RG-07 |
| D-02 | Every element carries a reuse code relative to B: `A` as-is, `E` restricted or annotated, `P` profile-specific | INFO | AP301:615-617; HVD lines 504-506; GEO 3.1.0 lines 1354-1357 |
| D-03 | The profile states its usage context and how it differs from B | ERROR at publication | RG-72; RG line 1441 |
| D-04 | The profile declares its base and the exact base release, machine-readably | ERROR | PROF "Data that conforms to a profile, in PROF, must conform to anything the profile is a profile of."; HVD line 433 |
| D-05 | Published artefacts: HTML specification, SHACL shapes, and, when terms were minted, vocabulary HTML and RDF | ERROR at publication | RG-70 to RG-75 |
| D-06 | Instance data names the profile on the catalogue record with `dct:conformsTo` | INFO | AP301 row `CatalogueRecord.applicationprofile` (line 2044): "An Application Profile that the Catalogued Resource's metadata conforms to." (text from `shacl/dcat-ap-SHACL.ttl`) |
| V-01 | B is pinned to one release; store the release id and a hash of every oracle file used | ERROR | finding 2; 3.0.1 `CHANGELOG.md` issues 370, 380 |
| V-02 | E is versioned as a whole with semantic versioning; a loosening of E is a major change | WARN | STYLE PC-R3, PC-R4 |
| V-03 | When B gets a new release, verification is rerun. A base relaxation does not apply to earlier base releases; a base tightening can invalidate E | ERROR on rerun failure | derived from finding 2 |
| V-04 | A requirement that needs a loosening is answered with a new property or recorded as "needs a base change" and raised upstream | WARN | RG-24, RG-25 |

Declaration block that satisfies D-04 (parses; used in `B2-artefacts/examples/ex-legal.delta.shacl.ttl`):

```turtle
@prefix prof: <http://www.w3.org/ns/dx/prof/> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

<https://example.org/ex-dcat-ap/releases/0.1.0> a prof:Profile, owl:Ontology ;
    dct:title "EX-DCAT-AP 0.1.0 (example extension)"@en ;
    owl:versionInfo "0.1.0" ;
    prof:isProfileOf <https://semiceu.github.io/DCAT-AP/releases/3.0.1/> ;
    dct:conformsTo  <https://semiceu.github.io/DCAT-AP/releases/3.0.1/> .
```

verify: the IRI to use for the base. The specification's ReSpec configuration gives
`edDraftURI: "https://semiceu.github.io/DCAT-AP/releases/3.0.1"` (AP301 line 156) and the new-style shapes use
`<https://semiceu.github.io/DCAT-AP/releases/3.0.1>` (no trailing slash) as the subject of their `rdfs:member` list.

How facets compile into delta shapes (derived; mirrors 4.2 and MOB `src/shacl/README.md` "Severity levels"):

| Profile facet | Delta shape |
|---|---|
| mandatory | own property shape, `sh:minCount n`, `sh:severity sh:Violation` |
| recommended | own property shape, `sh:minCount 1`, `sh:severity sh:Warning` |
| optional, with range | own property shape with the range constraint; no `sh:minCount` |
| max | own property shape, `sh:maxCount n` |
| datatype subset | own property shape, `sh:datatype` (one) or `sh:or` of datatypes |
| class | own property shape, `sh:class`, plus the `rdfs:subClassOf` axiom in the vocabulary when it is a subclass |
| required constant | own property shape, `sh:hasValue` |
| closed code list (level a) | `sh:node` to a restriction shape `[ sh:path skos:inScheme ; sh:hasValue <scheme> ; sh:minCount 1 ]`, Violation |
| at least one from a code list (level b) | `sh:qualifiedValueShape` with that restriction and `sh:qualifiedMinCount 1`, Warning (the legacy encoding tests every value instead, Q-21) |

### 5.6 Instance level — every graph valid under E is valid under B

The statement is DCAT 3's definition of a profile, "A data catalog that conforms to the profile also conforms to DCAT."
(DCAT3 `TR/index.html` line 231), applied one level down; DCAT-AP.de says it for DCAT-AP directly (section 6.5).

**In delta mode the statement holds by construction** for the shapes: validation against `B ∪ Δ` reports every result
validation against `B` reports, as long as N-04 holds. What remains to test is satisfiability and the standalone
artefacts (LinkML, DSV, a merged SHACL file) that the compiler emits. **In standalone mode it must be tested.**

#### Procedure

1. **Assemble.** `E_eff` = the shapes a validator of E would load: `B ∪ Δ` (delta) or E's file (standalone).
2. **Lint.** Validate `E_eff` and Δ against the SHACL-SHACL shapes graph; reject unknown terms in the `sh:` namespace
   (`B2-artefacts/shacl_inventory.py`, `unknown_sh_terms`); reject `sh:property` objects without `sh:path`; check N-04.
3. **Static satisfiability** (P-03) on the merged facets. Stop with UNSATISFIABLE on a contradiction.
4. **Generate witnesses from the profile model** (not from weak shapes, CAV-11). At least:
   * `W_min`: one instance per target class with exactly `min` values per property.
   * `W_max`: one instance per target class with `max` values per property, 2 where unbounded.
   * one variant per alternative when a facet is a disjunction (each datatype of a union, each allowed node kind).
   Object values are fresh nodes typed with the class the profile declares (not with the base superclass), carrying the
   mandatory properties of that class, recursively; required constants are added and typed as well.
5. **Self-check.** Every witness must be valid under `E_eff`. If not, the generator does not cover a construct in E:
   report INCONCLUSIVE with the offending results, never PASS.
6. **Differential validation.** Validate every witness against each base oracle set (below). Count top-level results of
   severity `sh:Violation` only.
7. **Triage.** A base violation on a witness E accepts is a counterexample. Map it back through `sh:resultPath` and the focus
   node's class to the key, then to the ProfileChange and its atoms. Classify it as (a) loosening confirmed by a P-rule,
   (b) known disagreement between base flavours (4.4), or (c) under-specified witness.

Reference implementation of steps 3 to 6: `B2-artefacts/witness_diff.py` (supported fragment: `sh:targetClass`, IRI paths,
min, max, datatype, class, node kind, `sh:in`, `sh:hasValue`, and `sh:or` unions reached directly or through `sh:node`).

#### Engine call (pySHACL 0.40.2)

```python
from pyshacl import validate
conforms, report, _ = validate(
    witness_graph,
    shacl_graph=base_shapes,          # one oracle set, already cleaned (CAV-2)
    ont_graph=background,             # rdfs:subClassOf axioms only (CAV-6); None for the "zero" runs
    inference=None,                   # never 'rdfs' or 'owlrl' with the DCAT vocabulary (CAV-5)
    advanced=False, meta_shacl=False, abort_on_first=False,
)
SH = "http://www.w3.org/ns/shacl#"
hard = [r for r in report.objects(None, URIRef(SH + "result"))            # top-level only (CAV-3)
        if report.value(r, URIRef(SH + "resultSeverity")) == URIRef(SH + "Violation")]
valid_under_B = not hard              # do not use `conforms` (CAV-4)
```

#### Which base files to combine (3.0.1; same names for 3.0.0)

| Oracle set | Files under `releases/3.0.1/` | Verdict use |
|---|---|---|
| O1 "individual constraints" | `shacl/dcat-ap-SHACL.ttl` after removing the 2 dangling links | hard. Agrees with all 131 cardinalities of the tables |
| O2 "base zero" + "ranges zero" | `html/shacl/shapes.ttl` + `html/shacl/range.ttl` | hard, with the known stale facets Q-3 to Q-6, Q-8 to Q-11 reported separately. This is what MOB imports and ITB runs |
| O3 recommendations | + `html/shacl/shapes_recommended.ttl` | informative (Warnings); shows which recommended properties E's witnesses lack |
| O4 controlled vocabularies | `html/shacl/mdr-vocabularies.shape.ttl` + code lists (`mdr_imports.ttl` lists them) as background | hard for level a rows, informative otherwise; needs CAV-8 |
| O5 deprecations | `html/shacl/deprecateduris.ttl` | none (Q-7); implement the check yourself with `sh:maxCount 0`, Warning |

Do not merge O1 and O2 into one shapes graph: they contradict each other on `locn:geometry` (Q-9).

#### Caveats (each verified unless marked)

| ID | Caveat | Evidence |
|---|---|---|
| CAV-1 | The base flavours disagree. Report per oracle set and keep the 4.4 list as expected differences | `witness_diff.py` with E = O1 and B = O2: 14 keys rejected (4 stale maxima, 7 temporal datatype unions, 2 resource-class unions, `locn:geometry` node kind); reverse direction: 9 keys (among them `skos:notation` min, `spdx:algorithm` class, and IRIs accepted where `sh:shape` is ignored) |
| CAV-2 | Clean the published files before loading (dangling `sh:property` links). Keep the original next to the cleaned copy and mark the copy as modified (licence) | Q-1, Q-2; `clean_shapes.py` removes 2 and 206 links |
| CAV-3 | Count only results linked by `sh:result`. Nested results under `sh:detail` carry the nested shape's default severity | CV run on the rich witness: 6 top-level Warnings, 12 nested results that look like Violations |
| CAV-4 | `sh:conforms` is false on any result, including Warnings. pySHACL's `allow_warnings=True` changes that; counting Violations is clearer | 4.2; minimal catalogue + `shapes_recommended.ttl`: 25 Warnings, `conforms=False` |
| CAV-5 | No RDFS / OWL-RL inference together with the DCAT vocabulary. `dcat:dataset`, `dcat:service`, `dcat:catalog` are sub-properties of `dcat:resource`, itself a sub-property of `dct:hasPart`; `dcat:mediaType`, `dcat:compressFormat`, `dcat:packageFormat` are sub-properties of `dct:format`; `dcat:hasVersion` of `dct:hasVersion`; `dcat:landingPage` of `foaf:page` | Rich witness, `inference='rdfs'`, `ont_graph=dcat3.ttl`: 4 false violations (`dct:hasPart` class Catalog twice; `dct:format` max 1 and class) |
| CAV-6 | "Background knowledge" should be `rdfs:subClassOf` axioms only. Even those change targets: DCAT 3 declares `dcat:Catalog rdfs:subClassOf dcat:Dataset`, `dcat:DatasetSeries rdfs:subClassOf dcat:Dataset`, `dcat:Role rdfs:subClassOf skos:Concept`, so Dataset shapes then apply to catalogues and series, and roles need `skos:prefLabel`. Run with and without | `dl/dcatrdf/dcat3.ttl` (6 named subclass axioms); legacy self-test with background: `dcat:Role` fails `skos:prefLabel` min 1. SHACL: "The data graph is expected to include all the ontology axioms related to the data and especially all the rdfs:subClassOf triples" |
| CAV-7 | `sh:class` needs typed value nodes, and a typed node becomes a focus node of its own class's shapes. Typing a country IRI as `dct:Location` triggers the recommended `dcat:bbox` / `dcat:centroid` warnings; typing a code as `skos:Concept` requires `skos:prefLabel` | Rich witness against O3: 2 Warnings on the country node; Q-15 |
| CAV-8 | Controlled-vocabulary shapes test `skos:inScheme` on the value node **in the data graph**, and three of them require the scheme to be typed `skos:ConceptScheme`. Load the code lists or generate stubs. IANA media types and GeoNames are tested by IRI pattern only (`^http.*://www.iana.org/assignments/media-types/`, `^https://sws.geonames.org`) | Rich witness with stub `skos:inScheme` triples passes language, frequency, file type, availability, theme, access right, media type |
| CAV-9 | `sh:datatype` is an exact match; an XSD subtype fails | 5.1 note 2 |
| CAV-10 | A value typed only with an extension subclass fails the base `sh:class` unless the subclass axiom is in the data graph or the node is double typed | Probe: `exap:PublicBody` publisher fails `sh:class foaf:Agent`; passes with the axiom as background; the double-typed creator passes without it |
| CAV-11 | Generate witnesses from the profile model. The new-style shapes accept any literal for the 12 temporal properties; a witness built from them (`"witness 1"@en` for `dct:issued`) is rejected by the legacy union shape and looks like a counterexample | E = O1, B = O2: `dct:issued` / `dct:modified` node-constraint results on 4 classes |
| CAV-12 | Decide the mode first. A delta or annex tested standalone produces omission "counterexamples" | HVD 3.0.0 `shacl/hvd-SHACL.ttl` alone against DCAT-AP 3.0.0: title, description, publisher min-count results on 5 classes; `DCAT-AP 3.0.0 ∪ HVD` against DCAT-AP 3.0.0: PASS |
| CAV-13 | Shapes apply to every instance of the target class. A profile meant for a subset of datasets cannot be validated on a mixed catalogue | HVD line 3978: "At this moment the SHACL templates assume that all resources are subject to DCAT-AP HVD." |
| CAV-14 | Two witnesses per class are a bounded test, not a proof. Within the supported fragment every facet-level loosening of 5.1 produces a counterexample in `W_min` (minimum, missing range typing) or `W_max` (maximum, datatype, class, node kind); constructs outside the fragment are listed as unsupported and make the verdict INCONCLUSIVE | derived; self-tests PASS for O1 and O2 against themselves |
| CAV-15 | SHACL-SHACL accepts files with non-SHACL terms. All legacy files pass it although `shapes.ttl` contains `sh:shape`; 2.0.1 passes with `sh:dateTime`. Only the raw 3.0.1 new-style file fails (2 results, the dangling links) | run against `pyshacl/assets/shacl-shacl.ttl` on 16 files |
| CAV-16 | Release 1.1 shapes need import resolution to have targets, and its mandatory-classes file always fails; 2.x shapes mix base and range in one file | Q-17, Q-18 |
| CAV-17 | Speed is not an issue: each validation of a witness (58 to 878 triples) against a full shape set takes well under a second | timing of the self-check run: 0.6 s for four validations |

#### Known-answer results (regression fixtures)

| E | B (oracle) | Mode | Result |
|---|---|---|---|
| DCAT-AP 3.0.1 O1 | itself | standalone | PASS |
| DCAT-AP 3.0.1 O2 | itself | standalone | PASS |
| GeoDCAT-AP 3.1.0 `shacl/geodcat-ap-SHACL.ttl` | DCAT-AP 3.0.1 O1 | standalone | FAIL, exactly 3 counterexamples, all `sh:MaxCountConstraintComponent`: `dcat:Dataset` `dcat:temporalResolution`, `dcat:Dataset` `dcat:version`, `dcat:Distribution` `dcat:temporalResolution` |
| GeoDCAT-AP 3.1.0 | DCAT-AP 3.0.1 O2 | standalone | the same 3, plus the stale legacy facets (`dct:rights` ×2, `dcat:spatialResolutionInMeters`, `dct:conformsTo` on CatalogRecord, `locn:geometry` node kind) and CAV-11 / Q-10 artefacts |
| GeoDCAT-AP 3.0.0 | DCAT-AP 3.0.0 new style | static (`shacl_delta.py`) | 6 loosened maxima: `dct:rights` (Catalog, Distribution), `dcat:spatialResolutionInMeters`, `dcat:temporalResolution`, `dcat:version` (Dataset), `dcat:temporalResolution` (Distribution) |
| DCAT-AP HVD 3.0.0 `shacl/hvd-SHACL.ttl` | DCAT-AP 3.0.0 new style | standalone | FAIL by omission (CAV-12) plus one real loosening: `dcat:Distribution` `dct:rights` max count |
| DCAT-AP 3.0.0 ∪ HVD 3.0.0 | DCAT-AP 3.0.0 new style | delta | PASS |
| `examples/ex-legal.delta.shacl.ttl` ∪ O1 | O1 | delta | PASS (also with O2) |
| `examples/ex-illegal.standalone.shacl.ttl` | O1 | standalone | FAIL: `dct:description` min (Catalog), `dct:publisher` max (Catalog), `dcat:contactPoint` class + node kind (Dataset), `dcat:temporalResolution` datatype + max (Dataset), `dct:license` max + class (Distribution), `foaf:name` min (Agent, by omission) |
| `examples/ex-contradictory.delta.shacl.ttl` ∪ O1 | O1 | delta | UNSATISFIABLE: `dcat:Distribution` `dct:license` minCount 2 > maxCount 1 |

### 5.7 Worked example

Legal delta (complete file: `B2-artefacts/examples/ex-legal.delta.shacl.ttl`, 45 triples, passes SHACL-SHACL):

```turtle
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix exsh: <https://example.org/ex-dcat-ap/releases/0.1.0/shacl#> .

exsh:DistributionShape a sh:NodeShape ;
    sh:targetClass dcat:Distribution ;
    sh:property exsh:Distribution-licence-min .

# base facet: dct:license on Distribution, 0..1, Recommended. Change: min 0 -> 1 (P-01 legal; P-04 recommended -> mandatory)
exsh:Distribution-licence-min a sh:PropertyShape ;
    sh:path dct:license ;
    sh:minCount 1 ;
    sh:severity sh:Violation ;
    rdfs:comment "ProfileChange PC-001; atoms: A-07; base facet: min 0 -> 1 (tightening)" .
```

The same requirement expressed the illegal way ("several licences per distribution") is the RG example itself: "meaning
cardinality 1..*, this would not be compliant with DCAT-AP Distribution licence and another property would have to be used
for this" (RG-24). In a delta it is not expressible; in a standalone restatement it yields this counterexample from `W_max`:

```turtle
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix ex:   <https://example.org/witness/> .

ex:Distribution-5 a dcat:Distribution ;
    dct:license ex:res-6, ex:res-7 ;
    dcat:accessURL ex:res-8, ex:res-9 .
```

Valid under `ex-illegal.standalone.shacl.ttl`; the base answers `sh:MaxCountConstraintComponent` on `dct:license` (and
`sh:ClassConstraintComponent`, because the restatement also dropped the range).

### 5.8 What the existing `scripts/shacl_delta.py` needs to become the static checker

Read at `/home/user/vpe-rq2-branch/scripts/shacl_delta.py` (287 lines) with its demo write-up. It already normalises
`sh:targetClass` property shapes per key and classifies added / tightened / unchanged / loosened. Gaps against 5.1:

| Gap | Where | Needed change |
|---|---|---|
| One severity per key, strongest wins (`Facets.merge`, lines 77-78) | A Warning `minCount 1` (recommended) merged with a Violation `maxCount 1` reads as mandatory | keep facets per severity, or one record per (key, severity); obligation from the min count at Warning vs Violation |
| Class and datatype changes are always "tightened … verify" (lines 173-180) | a superclass or an unrelated datatype is reported as tightening | apply P-06 and P-07 with a subclass table and the exact-datatype rule |
| Classes merged by union and compared by set equality (lines 67, 173) | SHACL semantics is conjunction | superset = tighter, subset = looser, otherwise P-07 |
| "Base elements missing from the profile are treated as inherited" (docstring line 22) | right for delta mode, wrong for standalone | make the mode a parameter; in standalone mode a missing key with any base facet is a loosening by omission |
| No `sh:hasValue`, `sh:pattern`, `sh:node`, `sh:or`, `sh:deactivated` | reported as unhandled or ignored | P-09 to P-13; follow `sh:node` to scheme restrictions; treat `sh:deactivated` on a base IRI as ERROR (N-04) |
| Dangling `sh:property` objects appear as "non-IRI sh:path" (lines 119-122) | misleading message for Q-1 / Q-2 | detect "no `sh:path`" separately |
| Base taken from SHACL only | inherits Q-3 to Q-6 and has no recommended level in the new style | take B from the specification table (TSV) and use SHACL as oracle |
| No satisfiability check | min > max after merging is not reported | P-03 |

The demo's observation that GeoDCAT-AP 3.0.0 "loosened" six maxima is confirmed against the specification tables: they are
real differences in GeoDCAT-AP's own tables (section 6.2), and three of them were later legalised by DCAT-AP 3.0.1.

---

## 6. Question 5 — how published extensions state their conformance

### 6.1 DCAT-AP HVD 3.0.0 (annex in the same repository)

* "In order for applications to conform to DCAT-AP HVD, it MUST conform to DCAT-AP." followed by "In addition, the
  application must conform to the mentioned constraints and usage guidelines following similar conformance statements as
  specified in DCAT-AP." (`releases/3.0.0-hvd/index.html` lines 359-360)
* "It means that these guidelines are on top of the existing guidelines expressed by DCAT-AP." (line 281)
* "Despite DCAT-AP HVD being called an Annex to DCAT-AP it has all the properties of an application profile of DCAT-AP." (line 393)
* Partial listing: "only the classes and properties that are featured explicitly in the HVD IR are listed in this document" (line 397).
* Base version: "As the publication URL indicates this version of DCAT-AP HVD is based on DCAT-AP 3.0.0." (line 433)
* Reuse codes relative to DCAT-AP (lines 504-506): "A: reused as-is defined and expressed in DCAT-AP", "E: reused with additional
  restrictions, additional usage notes or more specific usage expectations compared to DCAT-AP", "P: profile specific extension
  where DCAT-AP had no requirements earlier on specified". Counts in its tables: E 15, A 8, P 6.
* Controlled vocabularies: "The usage of controlled vocabularies in DCAT-AP HVD conforms and extends the usage defined by DCAT-AP." (line 3485)
* Table differences against DCAT-AP 3.0.0: `applicableLegislation` 0..* to 1..* on Dataset, Dataset Series, Distribution, Data
  Service; `DataService.contactpoint` Recommended 0..* to Mandatory 1..*; `DataService.documentation` Optional to Mandatory;
  `Distribution.accessservice` Optional to Recommended; and one widening, `Distribution.rights` 0..1 to 0..* (line 2612), which
  DCAT-AP 3.0.1 later adopted in the base.

### 6.2 GeoDCAT-AP 3.0.0 / 3.1.0

* "GeoDCAT-AP is an extension of the DCAT application profile for data portals in Europe" (3.1.0 `index.html` line 1014);
  "This specification extends DCAT-AP with additional requirements for describing geospatial data." (line 1041)
* "This application profile extends [[DCAT-AP-3]] by including" "additional classes and properties", "additional
  recommendations on the use of classes and properties", "additional controlled vocabularies" (lines 1238-1241); "These
  extensions are meant to provide a DCAT-AP-conformant representation of geospatial metadata" (line 1243).
* Its Conformance Statement repeats DCAT-AP's provider and receiver text for its own tables (lines 1160-1185) and has no
  sentence "MUST conform to DCAT-AP".
* Compliance claim: "Compliance with [[DCAT-AP-3]] is ensured: The geospatial metadata elements covered by the defined
  mappings include all those that in [[DCAT-AP-3]] are mandatory, plus a subset of those that are recommended and optional." (line 23672)
* Validation: "One perspective is to consider GeoDCAT-AP as an extension to DCAT-AP and thus implement a two staged process:
  first validation against DCAT-AP and then additionally validate the GeoDCAT-AP specific constraints." (lines 23496-23497);
  the alternative is "a standalone specification"; a single standalone SHACL file is provided (lines 23498-23503).
* Base alignment is recorded in the changelog: "Updated links from DCAT-AP 3.0.0 to DCAT-AP 3.0.1" and a section "Alignment
  with DCAT-AP 3.0.1" (`releases/3.1.0/CHANGELOG.md`).
* Table differences against the base (parsed with `spec_tables.py`; 307 rows in 3.1.0, 178 not in DCAT-AP 3.0.1; reuse codes
  A 138, P 137, E 32):

| Row | DCAT-AP 3.0.1 | GeoDCAT-AP 3.1.0 | P-rule |
|---|---|---|---|
| `Dataset.temporalresolution` (line 10702) | 0..1 | 0..*, code A | P-02 ERROR |
| `Dataset.version` (line 10967) | 0..1 | 0..*, code A | P-02 ERROR |
| `Distribution.temporalresolution` (line 15702) | 0..1 | 0..*, code A | P-02 ERROR |
| `Distribution.availability` (line 14430) | Recommended | Optional | P-04 WARN |
| `DatasetSeries.temporalcoverage` (line 13607) | Optional | Recommended | legal |
| `DatasetSeries.description` (line 11854) | Mandatory 1..* | listed as Optional with card 1..* | label inconsistency |

  Against DCAT-AP 3.0.0, GeoDCAT-AP 3.0.0 additionally had `Catalogue.rights`, `Distribution.rights`, `Dataset.spatialresolution`
  0..1 to 0..*. RG names the route that was taken: "rights cardinality needs to be relaxed from 0..1 to 0..*, which was
  escalated as a DCAT-AP issue" (RG lines 1308-1312), and 3.0.1 relaxed the base (issues 370 and 380).

### 6.3 mobilityDCAT-AP 3.0.0

* "mobilityDCAT-AP is designed as an extension of [[DCAT-AP-v3.0.1]] in conformance with the
  [[DCAT-AP-Implementation-Guidelines]], the [[SEMIC-Style-Guide-for-Semantic-Engineers]] and the [[DCAT-AP-Reuse-Guidelines]]."
  (`src/index.html` lines 100-102) — the only extension here that cites the reuse guidelines.
* Lists its edits against the base (lines 110-120), among them "Change to obligation levels for some existing properties",
  "Non-usage of optional classes" and "Non-usage of optional properties", and concludes "they are meant to provide a
  DCAT-AP-conformant representation of metadata specific to mobility data" (line 126).
* Obligation classification is derived from cardinality: "Properties are "mandatory", if their cardinalities are defined as
  "1..1" or "1..*", otherwise they are "optional"." (line 944)
* Shapes are a delta: "The shapes extend the DCAT-AP 3.0.1 SHACL shapes: DCAT-AP's constraints are reused through owl:imports,
  and mobilityDCAT-AP adds only the constraints that differ from DCAT-AP." (line 1090)
* "A constraint appears in the mobilityDCAT-AP shapes only where mobilityDCAT-AP is stricter than, or adds to, DCAT-AP" (line 1094)
* "In the few cases where the DCAT-AP shapes are stricter than the mobilityDCAT-AP text intends, the inherited rule prevails;
  these are noted in the specification and raised with the DCAT-AP maintainers rather than worked around." (line 1096)
* Imports the legacy flavour: `owl:imports <https://semiceu.github.io/DCAT-AP/releases/3.0.1/html/shacl/shapes.ttl>`
  (`src/shacl/shapes.ttl` line 62) and `.../range.ttl` (`src/shacl/ranges.ttl` line 56); controlled-vocabulary shapes are
  self-contained by design (line 1098).
* Severity convention (`src/shacl/README.md`): "`sh:Violation` - Mandatory properties", "`sh:Warning` - Recommended and deprecated
  properties", "`sh:Info` - Optional properties".
* Deprecation policy: "Elements that are deprecated will continue to be accepted until an upcoming major release" (line 961).

### 6.4 HealthDCAT-AP

* Archived draft (`OldContent/index.html`; the GitHub page was decommissioned on 2025-09-22 per `CHANGELOG.md`): "For
  applications to comply with HealthDCAT-AP, they MUST first conform to DCAT-AP." (line 299); "HealthDCAT-AP is an application
  profile to DCAT-AP. The healthDCAT-AP specific requirements are compatible with the release of DCAT-AP 2 and release of
  DCAT-AP 3.0.0." (line 416); "HealthDCAT-AP extends DCAT-AP by including: additional classes and properties; additional
  recommendations on the use of classes and properties; additional controlled vocabularies." (lines 420-425)
* verify: the current release (the repository README points to `healthdataeu.pages.code.europa.eu/healthdcat-ap/releases/release-5/`;
  a web search reports the same "MUST first conform to DCAT-AP" sentence on release 6). The host is not reachable from this session.

### 6.5 DCAT-AP.de 2.0 — the most explicit rule list

`Releases/DCAT-AP.de V2.0/spec/06_conformity.md`, section "Konformität zu DCAT-AP 2.0" (German; translations are ours):

* Main rule: "Jede Erweiterung von DCAT-AP muss die minimalen Konformitätskriterien erfüllen, welche in Kapitel 6 der
  Spezifikation DCAT-AP 2.0 definiert sind." (every extension must meet the minimal conformance criteria of chapter 6).
* Instance-level statement: "Erweiterungen dürfen die DCAT-AP 2.0 Nutzungsbestimmungen nicht erweitern, sondern nur
  einschränken, sodass alle Informationen, die in Bezug auf die Erweiterung valide sind, auch weiterhin in Bezug auf DCAT-AP
  2.0 Validität besitzen." (extensions may only restrict, so that everything valid for the extension stays valid for DCAT-AP).
* "Obligatorische Eigenschaften aus DCAT-AP 2.0 müssen auch in der Erweiterung obligatorisch sein."
* "Empfohlene Eigenschaften aus DCAT-AP 2.0 können in der Erweiterung als optional, empfohlen oder obligatorisch deklariert werden."
* "Optionale Eigenschaften aus DCAT-AP 2.0 können in der Erweiterung als optional, empfohlen oder obligatorisch deklariert werden."
* "Empfohlene und optionale Eigenschaften aus DCAT-AP 2.0 können in der Erweiterung entfernt werden."
* New classes and properties are allowed but "sollten … keine Ähnlichkeit zu ursprünglichen DCAT-AP-Klassen aufweisen"
  (should not resemble original classes; same sentence for properties).
* "Erweiterungen müssen alle obligatorischen kontrollierten Vokabulare enthalten" and "können zusätzliche obligatorische
  kontrollierte Vokabulare beinhalten."
* Its validator profile is base plus additions: the SEMIC file `dcat-ap_2.1.1_shacl_shapes.ttl` together with
  `dcat-ap-spec-german-additions.ttl` and others (`Releases/DCAT-AP.de V2.0/shacl/README.md`).

verify: these rules match what a web search reports for the older SEMIC note "How to extend DCAT-AP"
(interoperable-europe.ec.europa.eu, not reachable from here); DCAT-AP.de appears to be its translation **(inferred)**.

### 6.6 W3C layer

* DCAT 3: "A DCAT profile is a specification for a data catalog that adds additional constraints to DCAT. A data catalog that
  conforms to the profile also conforms to DCAT." (DCAT3 line 231). The allowed kinds of additional constraints are listed
  there: cardinality constraints, subclasses and sub-properties, additional classes and properties, controlled vocabularies,
  access mechanisms (lines 234-238). It names profiles of profiles: "GeoDCAT-AP_IT [[?GeoDCAT-AP-IT]]: Italian profile of [[?GeoDCAT-AP]]" (line 5956).
* PROF: "A Profile may define constraints on the usage of one or more standards. All constraints of these standards are
  inherited, in the sense that an object conforming to a profile conforms to all the constraints" (PROF line 770), with the
  property chain `dct:conformsTo owl:propertyChainAxiom ( dct:conformsTo prof:isProfileOf )` (lines 88-89).
* SEMIC Style Guide DSC-R2: "in an Application Profile, the data shape constraints shall be as rigid as necessary, i.e.
  restrictive" and "any Application Profile reusing the Core Vocabulary shall not only import the ontology, but the data shapes
  as well" (`gc-data-shape-conventions.adoc`, lines 37-44).

### 6.7 Pattern summary

| Extension | Base pinned | Conformance wording | Shapes | Deviations found |
|---|---|---|---|---|
| DCAT-AP HVD 3.0.0 | DCAT-AP 3.0.0 | "MUST conform to DCAT-AP" + own additions | partial, standalone files; validator runs them separately | 1 widened maximum (later adopted by base) |
| GeoDCAT-AP 3.1.0 | DCAT-AP 3.0.1 | own provider / receiver statement; "DCAT-AP-conformant representation" | one standalone file; two-stage validation suggested | 3 widened maxima, 1 obligation downgrade |
| mobilityDCAT-AP 3.0.0 | DCAT-AP 3.0.1 | own statement; "extension … in conformance with" the reuse guidelines | delta with `owl:imports` of the legacy base shapes | none by construction; notes where the base shapes are stricter than its text |
| HealthDCAT-AP (draft) | DCAT-AP 2 and 3.0.0 | "MUST first conform to DCAT-AP" | separate shape files per data category | not analysed |
| DCAT-AP.de 2.0 | DCAT-AP 2.0 / 2.1.1 shapes | explicit rule list | base file plus German additions | not analysed |

---

## 7. Open points

1. **Recommended to optional** (P-04): RG says tighten only; DCAT-AP.de allows the downgrade; GeoDCAT-AP does it. We chose
   WARN. A decision by the user is needed.
2. **Which oracle is authoritative for the hard verdict** when O1 and O2 disagree (for example `dct:rights` max 1 in O2).
   We propose: specification table decides, both oracle results are shown, known stale facets are labelled.
3. **Base IRI for `prof:isProfileOf`** (with or without trailing slash) is not fixed by any source read here.
4. **XSD subtype narrowing** (P-06): legal by RG-29, rejected by the base shapes. We propose WARN plus keeping the base
   datatype in the lexical form (add facets such as `sh:minInclusive` or `sh:pattern` instead).
5. **Sub-property additions** (P-22) are invisible to SHACL without inference; how strict the tool should be is a design choice.
6. **Controlled-vocabulary oracle** needs the EU Vocabularies code lists (`publications.europa.eu`), which were not fetched
   here; stubs with `skos:inScheme` and `skos:prefLabel` were used. verify: with the real lists.
7. **ISA Open Metadata Licence v1.1** terms for the 1.1 shapes were not read. Do not bundle the 1.1 archives before checking.
8. **3.0.1 status label**: the specification file says "SEMIC Draft Specification", the README says "SEMIC Recommendation v3.0.1".
9. **W3C wording** (DCAT 3, PROF, SHACL) was read from the GitHub sources of the specifications, not from w3.org.
10. **Older SEMIC extension note and current HealthDCAT-AP release** could not be read (hosts not allowed in this session:
    `interoperable-europe.ec.europa.eu`, `healthdataeu.pages.code.europa.eu`).
11. **Witness generation for patterns, qualified shapes, SPARQL constraints and complex paths** is outside the prototype; an
    extension using them gets INCONCLUSIVE until the generator covers them.
12. **ITB "Full" profile**: the README describes it as the union of base, ranges, recommendations and controlled
    vocabularies; `config.properties` lists `deprecateduris.ttl` instead of the vocabulary file for `v3.0.1.Full`.

---

## 8. How to reproduce

```bash
W=/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research
A=$W/B2-artefacts ; R=/home/user/refs/SEMICeu__DCAT-AP/releases
python3 -m venv $W/venv && $W/venv/bin/pip install rdflib pyshacl pyyaml       # rdflib 7.6.0, pySHACL 0.40.2 were used
PY="$W/venv/bin/python -I"

# specification tables -> JSON -> base table
$PY $A/spec_tables.py $R/3.0.1/index.html > spec_3.0.1.json
$PY $A/build_base_table.py spec_3.0.1.json $R/3.0.1/index.html $R/3.0.1/shacl/dcat-ap-SHACL.ttl \
    $R/3.0.1/html/shacl/shapes.ttl,$R/3.0.1/html/shacl/range.ttl,$R/3.0.1/html/shacl/shapes_recommended.ttl base.tsv

# inventory and cross-check of the official shapes
$PY $A/shacl_inventory.py $R/3.0.1/html/shacl/shapes.ttl $R/3.0.1/shacl/dcat-ap-SHACL.ttl
$PY $A/crosscheck.py spec_3.0.1.json "NEW=$R/3.0.1/shacl/dcat-ap-SHACL.ttl"

# make the new-style file loadable, then run the witness test
$PY $A/clean_shapes.py $R/3.0.1/shacl/dcat-ap-SHACL.ttl dcat-ap-3.0.1.cleaned.ttl
$PY $A/witness_diff.py --ext dcat-ap-3.0.1.cleaned.ttl,$A/examples/ex-legal.delta.shacl.ttl \
    --base dcat-ap-3.0.1.cleaned.ttl --out out --label ex-legal            # PASS
$PY $A/witness_diff.py --ext $A/examples/ex-illegal.standalone.shacl.ttl \
    --base dcat-ap-3.0.1.cleaned.ttl --out out --label ex-illegal          # FAIL with counterexamples
$PY $A/witness_diff.py --ext dcat-ap-3.0.1.cleaned.ttl,$A/examples/ex-contradictory.delta.shacl.ttl \
    --base dcat-ap-3.0.1.cleaned.ttl --out out --label ex-contradictory    # UNSATISFIABLE

# single validation with a readable summary (top-level results only)
$PY $A/run_pyshacl.py $A/data/witness_rich_typed.ttl "O2=$R/3.0.1/html/shacl/shapes.ttl,$R/3.0.1/html/shacl/range.ttl"
```

## 9. Artefacts

All under `/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/research/B2-artefacts/`.

| File | What it is |
|---|---|
| `dcat-ap-3.0.1-base-table.tsv`, `dcat-ap-3.0.0-base-table.tsv` | 131 rows each: class, property, anchor, obligation, card, min, max, range, reuse code, CV level and vocabulary, new-style SHACL facets, legacy SHACL facets. Derived from CC BY 4.0 material of the European Union (SEMIC) |
| `spec_tables.py`, `build_base_table.py` | parsers that produced the tables |
| `shacl_inventory.py`, `crosscheck.py` | inventory of constructs and quirks; specification-versus-SHACL comparison |
| `clean_shapes.py` | removes dangling `sh:property` links |
| `run_pyshacl.py` | pySHACL wrapper that counts top-level results by severity |
| `witness_diff.py` | reference prototype of the instance-level test |
| `examples/ex-legal.delta.shacl.ttl` | legal delta extension with a PROF declaration |
| `examples/ex-illegal.standalone.shacl.ttl` | standalone restatement with five loosenings |
| `examples/ex-contradictory.delta.shacl.ttl` | delta that contradicts the base |
| `witnesses/*.ttl` | generated witness graphs (legal min and max, illegal max, GeoDCAT-AP 3.1.0 max) |
| `data/witness_min_untyped.ttl`, `data/witness_rich_typed.ttl` | hand-written catalogues used for the caveat experiments |
| `data/background_subclass_only.ttl` | the six named `rdfs:subClassOf` axioms of DCAT 3 |
| `data/probe_quirks.ttl`, `data/probe_subtype_subclass.ttl`, `data/probe_subclass_axiom.ttl` | probes for Q-6, Q-7, CAV-9, CAV-10 |
