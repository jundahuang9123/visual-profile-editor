# G3 — Application-profile practice: what the cited works implemented, and what we can reuse

Group: `G3-application-profile-practice` · 21 bib keys · written 2026-11-13
Scope: application-profile methodology, and how real DCAT-AP extensions were derived from requirements.
Companion report: `B2-dcat-ap-conformance.md` (same folder) holds the full facet-by-facet conformance rule set. This report does not repeat it; it covers the bibliography, the process from requirement to change, the artefacts and templates, and the reusable steps.

---

## 0. How to read this report

**Two voices, kept apart.**
- *What they did* reports only what I saw in a source during this task.
- *How we reuse* is our design. It is not a claim of the cited work.

**Confidence.**
- **high**: I read the primary text (specification, official repository, official PDF).
- **medium**: I saw only an abstract or a search-engine summary of the primary page. The text itself was not opened.
- **low**: not confirmed. Such statements start with "verify:".

**Access in this session.** Only public GitHub clones and `raw.githubusercontent.com` were reachable. `dublincore.org`, `w3.org`, `ceur-ws.org`, `napcore.eu`, `zenodo.org`, `arxiv.org`, `interoperable-europe.ec.europa.eu`, `link.springer.com` and `healthdataeu.pages.code.europa.eu` were blocked (one attempt per host). Consequence: specifications were read in full from their repositories; the papers and reports listed in section 10 were seen only through search summaries, and one deliverable was not seen at all.

**Quotes** are kept to 25 words or fewer. Spelling in quotes is the source's.

---

## 1. Summary

1. The SEMIC reuse guidelines give a **four-rung decision ladder** per use case (reuse as-is, reuse and tighten, reuse from DCAT or another vocabulary, define new) and **eight "specific situations"** with explicit do/don't rules for cardinality, range, controlled vocabularies, semantics, new properties and usage contexts. This is the closest thing to an executable specification of our Propose and Verify stages. (high)
2. Every published extension I read states the same conformance principle: **conform to the base first, then add**. HVD and HealthDCAT-AP say it in one sentence; mobilityDCAT-AP 3.0.0 implements it in SHACL as **import of the base shapes plus deltas only**, and writes down the consequence: a delta can make a rule stricter, never looser; where the base is stricter than the extension wants, the base wins and the case is raised upstream. (high)
3. Real extensions **reuse far more than they mint**. GeoDCAT-AP 1.0 defined no new term. DCAT-AP-JRC 1.0 defines none. StatDCAT-AP 1.0.0 logs six new properties, four in its own namespace. mobilityDCAT-AP 1.1.0 states 48 added properties; its vocabulary file declares 12 properties and 2 classes in its own namespace. These numbers are usable as reference values for a mint-rate metric. (high; the two mobilityDCAT-AP counts are the specification's statement and my count of the Turtle file)
4. **Traceability in practice is issue-based**: each change line in a changelog cites an issue number; StatDCAT-AP adds a "new properties log" and a "resolution log" (issue, proposed resolution, final resolution); HVD writes the legal article into the usage note of many tightened properties; the W3C UCR note keeps requirement-to-use-case back-links with stable ids. None of them traces at the level of a single constraint to a single requirement sentence. Our atom-level trace goes further than the practice it builds on. (high for the observations; the comparison is my reading)
5. **A/E/P "reuse qualification"** (as-is, extended, profile-specific) is used by DCAT-AP 3, HVD, GeoDCAT-AP 3, HealthDCAT-AP and mobilityDCAT-AP 3. It can be derived mechanically from our delta status. (high)
6. The **process** is the same everywhere: collect requirements with stakeholders, build a technology-neutral model, map to the base, add what is missing, document, publish, maintain through issues. mobilityDCAT-AP names five steps; GeoDCAT-AP 1.0 three tasks; StatDCAT-AP a decision framework of five principles; the Singapore Framework five documentary components. (high for the specifications; medium for the papers behind them)
7. The FAIR and dataset-search works yield no step of comparable weight. I list one optional use (tags and a coverage view) and do not count it among the key steps.

---

## 2. Sources actually read (primary)

| Work | Where I read it | Version / date in the source |
|---|---|---|
| SEMIC, *How to create your DCAT-AP profile* | `/home/user/refs/SEMICeu__DCAT-AP-reuse-guidelines/index.html` and `README.md` (commit `e958ded`, 2026-06-10) | ReSpec config `publishDate: "2026-06-17"`; README names "v1.0.0" |
| DCAT-AP 3.0.0 | `/home/user/refs/SEMICeu__DCAT-AP/releases/3.0.0/` (`index.html`, `CHANGELOG.md`, `html/shacl/*.ttl`, `shacl/dcat-ap-SHACL.ttl`), commit `4470b8e` | "SEMIC Recommendation published at 2024-06-14" |
| DCAT-AP HVD annex 3.0.0 | same repository, `releases/3.0.0-hvd/` | "SEMIC Recommendation published at 2024-10-25" |
| DCAT-AP 3.0.1, 2.0.1 | same repository, `releases/3.0.1/`, `releases/2.0.1/DCAT_AP_2.0.1.pdf` | 3.0.1 page status reads "SEMIC Draft Specification published at 2025-07-10"; 2.0.1 dated 08/06/2020 |
| DCAT-AP issue submission guidelines | same repository, `DCAT-AP_Issue_submission_guidelines_v0.01.pdf`; also `SEMICeu/DCAT-AP.wiki` `Submission-guidelines.md` | v0.01 |
| SEMIC governance | `/home/user/refs/SEMICeu__Governance/` (commit `311d01a`) | files dated 2024-02-01 |
| GeoDCAT-AP 1.0 | `/home/user/refs/SEMICeu__GeoDCAT-AP/releases/1.0.0/geodcat-ap_1.0.pdf` (commit `7e7d6a8`) | 2015-12-23, 87 pages |
| GeoDCAT-AP 3.0.0 | same repository, `releases/3.0.0/`, `930/releases/3.0.0/voc/930.ttl` | "Candidate Recommendation published at 2024-10-04" |
| StatDCAT-AP 1.0.0 | `raw.githubusercontent.com/SEMICeu/StatDCAT-AP/12a2424…/Release 1.0/statdcat-ap_version_1.0.0_0.pdf` | 2016-12-15, 94 pages |
| mobilityDCAT-AP 1.1.0 | `mobilityDCAT-AP/mobilityDCAT-AP`, branch `gh-pages` (`f035bf9`), `releases/1.1.0/` | "NAPCORE Recommendation 17 January 2025" |
| mobilityDCAT-AP 3.0.0 | same branch `releases/3.0.0/`; branch `main` (`3f228c7`) `src/shacl/`, `src/migrationGuide/` | 19/10/2026. **Not the cited version.** Used because it states the delta principle explicitly |
| mobilityDCAT-AP wiki | `/home/user/refs/mobilityDCAT-AP__mobilityDCAT-AP.wiki/` (`8edb7af`) | chapter 6 is a copy of a NAPCORE report dated 12 April 2024 |
| mobilityDCAT-AP validation toolkit | `/home/user/refs/mobilityDCAT-AP__validation/` (`433f01e`) | 2026-04-03 |
| HealthDCAT-AP (pilot specification) | `/home/user/refs/healthdcat-ap__healthdcat-ap.github.io/OldContent/index.html` (`a155911`) | "published by the Work Package 6 of the EHDS2 pilot project as a Recommendation on December 22th, 2023". The GitHub page was decommissioned on 22-09-2025 |
| W3C Dataset Exchange UCR | `w3c/dxwg`, `ucr/static/index.html` (`02181f2`) | **Editor's Draft 10 January 2019**, one week before the cited Note of 17 January 2019 |
| DCAT 3 | `w3c/dxwg`, branch `rec-snapshot-2024` (`2bc58b9`), `dcat/publication-snapshots/REC/Overview.html` | "W3C Recommendation 22 August 2024" |
| Singapore Framework | `dcmi/repository` (`268219f`), `wikis_pre2016/architecture/architecturewiki/The_Singapore_Framework_for_Dublin_Core_Application_Profiles.md` | archive copy of the document "Date Issued: 2008-01-14" |
| DCMI Description Set Profile (draft) | same repository, `…/architecturewiki/DescriptionSetProfile.md` | wiki draft by M. Nilsson, the document the Singapore Framework cites as [DSP] |
| RDF Data Cube (development repository) | `UKGovLD/publishing-statistical-data` (`d382ad5`), `src/main/resources/integrity-*.sparql`, `src/test/…/TestWF.java` | the editors' working repository; the W3C Recommendation text itself was not reachable |
| DCAT-AP-JRC 1.0 | `/home/user/refs/ec-jrc__dcat-ap-jrc/docs/1.0/index.html` (`c2101b0`) | living document; cites the SDSVoc paper as [SDSVoc16-27] |

Working copies of the extracted text are in `…/research/G3-work/`; the two small converters I wrote are in `…/research/G3-tools/`. Nothing from the cloned repositories was executed.

---

## 3. What each work implemented or prescribes

### 3.1 `semicreuse2026` — SEMIC, *How to create your DCAT-AP profile* (deep, high)

**Premise.** DCAT-AP is a "master profile": every DCAT-AP profile must comply with its mandatory properties and mandatory controlled vocabularies. Creation "starts from a minimal DCAT-AP profile, gradually extending it to cover the requirements". "Profile" and "extension" are used interchangeably. New profiles should be announced as a DCAT-AP GitHub issue.

**Four steps.**
1. *Familiarise with DCAT-AP.* The guide lists the minimum conformant catalogue: Catalogue (title, description, publisher and its name, links to datasets and services), Dataset (title, description, links to distributions), Distribution (access URL), Data Service (title, endpoint URL, datasets served).
2. *Consider your use cases and propose their resolution.* Use cases are written as user stories ("As a data publisher, I want to represent dataset distribution file format"). They need not cover every element: "Use cases are intended to justify and explain relevant design decisions, in particular those that introduce new elements, tighten existing constraints". Each use case is resolved by one of four **standard situations**:
   - covered by DCAT-AP → reuse as-is (labels, cardinalities, definitions, usage notes, mandatory code lists, link to the reused element);
   - covered by DCAT-AP with context-specific adjustments → allowed "if they tighten existing constraints";
   - not covered by DCAT-AP but by W3C DCAT, another vocabulary or another DCAT-AP profile → reuse that, "given that it does not cause a semantic issue";
   - not covered by any known or admissible vocabulary → "an original approach", typically a new vocabulary with new classes and properties in the profile's own namespace.
   Each worked example uses the same four fields: *Use case / Existing DCAT-AP solution / (Problem) / Resolution*. I count six such examples in the text.
3. *Involve stakeholders to build consensus.* The process must be "transparent, accessible and traceable", in a public repository. Each use case becomes an issue whose description contains "a problem statement or requirement, and a proposed resolution, or its variants". The community agrees, disagrees or proposes an alternative. Without consensus: webinars with a prepared issue list and a vote; "The reached resolutions then need to be recorded with the issues".
4. *Publish.* A human-readable HTML specification (usage context, how the profile differs from DCAT-AP, contact), SHACL shapes, and, if new terms were created, a separate vocabulary document plus RDFS or OWL definitions that "relate the new classes and properties to existing ones". Stable, persistent URLs (w3id.org is named).

**Eight specific situations** (each with *Problem sketch / What to do / Explanation*):
1. Linked Data expectations: persistent, dereferenceable URIs with content negotiation; the resource URI must not be confused with identifier properties.
2. Property or class does not semantically fit: three outcomes (relabel in the documentation only; create a subclass or subproperty; do not reuse, define new).
3. Controlled vocabulary does not fit: extend it at the source first; otherwise the rule depends on how strongly the base binds the vocabulary (MUST / at least one / RECOMMENDED / MAY); a *different* vocabulary needs a *different* property.
4. Range does not fit: five cases (section 5, rule R3).
5. Where to attach a new property: define it in a supporting vocabulary with a domain and range "as open as possible", then describe its context-specific usage in the profile.
6. Cardinality differs: mandatory stays mandatory; at most one stays at most one; stricter is fine; for a justified relaxation "raise an issue" on DCAT-AP.
7. Usage scope or definitions of a reused class need to change: state the usage context in the introduction; refine usage notes; for several contexts of one class create a subclass per context; when a context spans several classes prefer a separate sub-profile (this is why HVD is an annex).
8. Describing a related resource with an external vocabulary: set the range to the most generic appropriate class; add formal constraints only when needed, and "in the most generic way possible", because profiles overlap.

**Why it matters for us.** It is a ready decision procedure for Propose (ladder), Verify (situations 2 to 6), Compile (step 4) and human review (step 3).

### 3.2 `semicdcatap` — DCAT-AP 3.0.0 (deep, high)

- **Conformance statement** with provider requirements (seven bullets: mandatory properties of Catalogue, Catalogue Record if provided, Dataset, Distribution if any, Data Service if any, Agent; publication requirements for controlled vocabularies) and receiver requirements (process all classes, properties and controlled vocabularies). "Processing" means accepting and passing on the data.
- **Obligation semantics** are defined for sender and receiver: mandatory (sender MUST), recommended (sender SHOULD if available), optional (sender MAY), deprecated; the receiver MUST be able to process all three.
- **A/E/P against DCAT**: every property row carries "A: reused as-is", "E: reused with additional usage notes or additional restrictions" or "P: … profile specific extension". The assessment "may vary over time" with the base version.
- **DCAT-AP as a filter**: DCAT properties not listed are implicitly optional and "have no conformance expectation".
- **Controlled vocabularies**: seven SHOULD-requirements for admissible vocabularies (open licence; maintained by an EU institution, a standards body or another trusted organisation; documented; multilingual labels; small number of general terms; URIs resolving to documentation; persistence and versioning policies). A table of 13 property/class rows whose vocabulary MUST be used, and one MAY row.
- **SHACL in two designs.** (a) Files grouped by purpose: `shapes.ttl` (existence, literal range, cardinalities), `range.ttl` (object ranges), `mdr-vocabularies.shape.ttl` (controlled vocabularies), `shapes_recommended.ttl`, `imports.ttl`, `mdr_imports.ttl`, `deprecateduris.ttl`. (b) A "new design where each constraint has got a unique identifier": in `shacl/dcat-ap-SHACL.ttl` I count 300 property shapes, each with its own IRI, `shacl:name`, `shacl:description` and an `rdfs:seeAlso` to the specification anchor (for example `…/3.0.0#Identifier.notation`). The specification says validation is contextual: "It is up to the implementers of the data exchange to define the validation they expect."
- **Changelog discipline**: every data-model change line starts with the issue number, for example "Issue 284: lift the max cardinality of application profile (dct:conformsTo) for Catalogue Record."
- **Inverse properties**: DCAT-AP lists only the canonical direction of an inverse pair.
- **HVD annex 3.0.0** (same repository) is the worked example of a tightening-only profile:
  - conformance: "In order for applications to conform to DCAT-AP HVD, it MUST conform to DCAT-AP."
  - a section "Mapping the HVD IR to DCAT-AP" where each topic is introduced from the regulation, assessed against DCAT-AP, and resolved;
  - property tables with *Card*, *Usage* and *Reuse* (A/E/P), where the usage note names the legal source ("Article 3.4 requires the designation of a point of contact for an API");
  - value pinning in SHACL (`shacl:hasValue <http://data.europa.eu/eli/reg_impl/2023/138/oj>`), and three shape files (base, ranges, usagenotes) plus a combined one;
  - a pattern for a **strong recommendation**: "The formal constraints have been relaxed, the usage qualification has been set to recommendation, and additional usage notes including this explanation have been added", plus an extra SHACL check.
- **DCAT-AP 2.0.1, Annex II** is a change table with the columns *URI / Type (obligation, class or property, owner class) / Action (New, Update, Deleted) / Description / Issue / Release*.
- **DCAT-AP 3.0.1** (later than the cited version) adds "Expected usage of controlled vocabularies" with four levels and two rules addressed to profiles: for a closed value space "All profiles in the ecosystem MUST avoid conflicts by creating subproperties"; and the two MUST levels "SHOULD only be used for requirements that can be verified by a machine". Its changelog shows that the reuse qualification is derived from the constraints: after relaxing a cardinality, "the reuse qualification changes from extended to as-is".
- **Issue template** (submission guidelines): submitter and affiliation; portal, service or product affected; "clear and concise description of the problem or requirement"; proposed solution. The operational team classifies each issue "as a bug fix, minor semantic issue or major semantic issue"; the editor answers within two weeks.
- **Issue states** (SEMIC governance repository): `feedback-requested`, `status:waitingForDecisionW3C`, `status:resolution-provided`, `status:fixed`, `status:wont-fix`, `future-work`, `release:x.y.z`, `next-webinar`.

### 3.3 The mobilityDCAT-AP family (deep)

#### `mobilitydcatspec` — mobilityDCAT-AP 1.1.0 (high)

- **Process named in the specification**: a roadmap of five key steps. The first two are quoted as "(1) gathering of requirements from experts and transport stakeholders, (2) definition of a conceptual model"; then (3) implementation of the model as a metadata scheme, (4) documentation and guidelines, (5) hosting and publication.
- **Declared kinds of edits against DCAT-AP 2.0.1** (seven): new classes; changed obligation of existing classes; new properties on existing classes, some newly created; changed obligation of existing properties; removal of some optional or recommended properties; refined usage notes; additional controlled vocabularies, some newly created.
- **Marking**: additions carry a "+" prefix, removals a "−". Each class section opens with notes listing the properties "not included in [DCAT-AP-v2.0.1]" and those "removed from" it. Annex A.2 lists all additions: "2 additional classes and 48 additional properties (some of which re-used across classes)".
- **Justification in the usage note** of each changed element, in a fixed phrase: "the obligation of this property is raised to “mandatory”, compared to [DCAT-AP-v2.0.1]", preceded by the reason (for Distribution: in mobility portals every dataset is expected to have a distribution).
- **Reuse from a sibling profile** is stated in the note: "This class addition is analogous to a class addition by [GEODCAT-AP-v2.0.0]."
- **Own vocabulary**: in `releases/1.1.0/mobilitydcat-ap.ttl` I count 2 classes and 12 properties declared in the `mobilitydcatap:` namespace. A minted property is declared with `rdfs:subPropertyOf` (for example `mobilitydcatap:mobilityTheme rdfs:subPropertyOf dcat:theme`), `dcam:domainIncludes` / `dcam:rangeIncludes` instead of hard domain and range, `skos:scopeNote` for the profile-specific obligation, and status annotations.
- **Mapping annex**: Annex B maps the elements of the earlier Coordinated Metadata Catalogue (32 elements, according to the specification) to classes and properties (columns: source section, source element, class, class URI, property, property URI). Some source elements map to two properties "due to semantic ambiguities".
- **Minimum profile and example populations**: a UML diagram of mandatory elements, and a real record converted with inline comments `OK`, `PROPOSAL`, `MODIFIED`, `ADDED`.
- **Change log lines** carry change, reason and issue: "Cardinality of property "schema" changed from 0..1 to 0..n. Reason: allow for naming multiple schemas. See issue #56".
- **Governance**: "This document is governed by the Change and Release Management Policy for DCAT-AP." The document history labels releases "Minor semantic release" and "Bug fix release".
- **SHACL 1.1.0**: three files (shapes, range, controlled vocabularies); the README states "All shapes extend and inherit from DCAT-AP 2.0.1 SHACL shapes."

**mobilityDCAT-AP 3.0.0 (19/10/2026, not the cited version; high).** Useful because it makes the mechanics explicit.
- `src/shacl/README.md`: the files "import the corresponding DCAT-AP 3.0.1 file via `owl:imports` and contain only the mobilityDCAT-AP-specific additions (deltas)". Severity levels: `sh:Violation` for mandatory, `sh:Warning` for recommended and deprecated, `sh:Info` for optional. Each file has its own versioned namespace.
- Annex G.1: "the shapes can make a rule stricter but cannot loosen an inherited one"; where the DCAT-AP shapes are stricter than intended, "the inherited rule prevails; these are noted in the specification and raised with the DCAT-AP maintainers rather than worked around".
- Property shapes are named resources with `sh:name`, `sh:description` (which states the change, for example "Raised to mandatory (1..1)."), `sh:message` and `sh:severity`.
- Reuse qualification extended to five values: A, E, GA, GE (as-is or extended from GeoDCAT-AP) and P.
- "Removed" was replaced: "The term "removed" caused some confusion, so it is replaced with "not used from DCAT-AP"." Annex A.3 lists each unused class or property with the reasoning.
- A **migration guide** (spreadsheet) with the columns *Category, Class, Property / Element, v1.1.0 situation, v3.0.0 situation, Triggering condition, Concrete action, RDF example, Spec section, GitHub issue(s), Status, Notes* and a change taxonomy: MUST change (namespace URI, property URI, property range, add property, restrict cardinality, apply new modeling concept), MUST stop using, MAY stop using, MAY relax (cardinality, range), MAY now add (property, class).
- The scope section names the DCAT-AP Reuse Guidelines (our key `semicreuse2026`) as one of three documents it conforms to; its reference list dates them 17 June 2026.

**Wiki (high).** Chapter 1 describes the mapping order used: "the first step was to check if and how existing elements from the general DCAT-AP vocabulary correspond to the elements of the conceptual model"; many could be reused, with rewritten usage notes and changed obligation levels; then other vocabularies (the Data Quality Vocabulary is the example); only where neither offered a term did the group add its own in a separate namespace. Chapter 6 (copy of a NAPCORE report) defines the three change types and the versioning scheme X.Y.Z, and the decision procedure (minor resolutions accepted after two weeks without opposition; major ones by a two-thirds vote). Chapter 4 separates syntax validation from schema validation.

**Validation toolkit (high).** `sample_data/` holds test graphs in the categories `baseline-dcat-ap`, `mobility`, `ranges`, `vocabularies`, `multilingual`, `partial_graphs`, `regression`, each split into `positives/` and `negatives/` with ids such as `B-N-04-dataset-without-distribution.ttl`. `scripts/validator.py` runs pySHACL with `inference='rdfs'`; a test passes when a positive conforms and a negative does not.

#### `scrocca2025mobilitydcat` — ESWC 2025 resource paper (medium: search summaries of arXiv 2503.11535 and of the Springer page; text not opened)

- Requirements were collected from a literature review and from project partners, portal developers, metadata providers, portal users and Semantic Web experts; stakeholders filled a template.
- Forty requirements in four categories: General (8), Existing Vocabularies (5), Content (22), Implementation (5).
- The conceptual model has two parts: entities with properties, and controlled vocabularies. Its first draft relied strongly on the DCAT-AP specification.
- The team checked whether each model element is covered by existing RDF vocabularies, in two groups, the first being vocabularies already used in DCAT-AP and its extensions.
- The cardinality proposed in the conceptual model was compared with the one in DCAT-AP; the extension rules allow a cardinality to be raised, not lowered.
- All five points above are the wording of search summaries, not quotations from the paper.
- verify: the paper is reported to describe validation tooling, a metadata generator and lessons from early adopters; I could not confirm the content of these sections.

#### `scrocca2022napdcat` — SEMANTiCS 2022 poster/workshop paper (medium, search summaries only)

Presents the roadmap and an overview of the elicited requirements; Table 1 lists the Content requirements, which the summaries say are the majority. The summaries report the consolidation into forty requirements and the categories for this paper as well. The specification was then called napDCAT-AP.

#### `bures2022napcore` — NAPCORE report 4.4.2.1 (medium, search summaries only)

The outcome of the first roadmap step. Its aim, as summarised, is to identify and prioritise the requirements for napDCAT-AP. Requirement statements reported by the summaries: reuse DCAT-AP classes and properties; reuse other DCAT-AP extensions such as GeoDCAT-AP; provide usage rules; base new controlled vocabularies preferably on SKOS; take the earlier NAP metadata catalogue as baseline. One summary calls the list a "specification sheet". The companion report 4.4.2.2 (*Approach towards napDCAT-AP specification*, not a bib key) is summarised as saying that mandatory DCAT-AP properties stay mandatory while recommended and optional ones may be removed.
verify: the fields of the requirement template and the prioritisation scheme.

### 3.4 HealthDCAT-AP (deep)

#### Pilot specification in the official repository (high)

- **Extension principles**, stated as a list: the extension "meets the minimal conformance criteria of DCAT-AP"; new classes and properties "must not replicate the functionality of existing DCAT-AP components"; mandatory DCAT-AP vocabularies are kept and others may be added; for cardinalities, "Mandatory properties retain their required status", recommended ones may become optional or mandatory, optional ones may become mandatory; "Recommended and optional properties may be removed".
- **Best practices**: review related extensions (StatDCAT-AP, GeoDCAT-AP); prioritise "vocabularies used in DCAT-AP for metadata property selection" (DCMI Terms, ADMS, PROV-O, ODRL are named; DPV, Schema.org and DQV are to be considered); use EU controlled vocabularies.
- **Conformance**: "For applications to comply with HealthDCAT-AP, they MUST first conform to DCAT-AP."
- **A/E/P per property**, and per class two generated sentences listing the E properties and the P properties.
- **Conditional obligations by access level**: three variants (public, restricted, non-public) with separate UML diagrams, a per-class table "Cardinalities Based on Dataset Access Rights", and separate SHACL files for open, protected and sensitive data. The specification notes: "The SHACL templates assume that all resources are subject to healthDCAT-AP."
- **Requirement source in the usage note**: properties cite the EHDS article (health category: Art. 51), and scope is pinned by value ("the value must include the ELI of the EHDS Regulation"; theme must include the EU data-theme "HEAL").
- **Reuse choices visible in the tables**: `dpv:hasLegalBasis`, `dpv:hasPersonalData`, `dpv:hasPurpose`, `dqv:hasQualityAnnotation`, `adms:sample` are reused; `healthdcatap:` terms are minted for health category, health data access body, coding system, population coverage, age range, record counts, retention period.

#### `derycke2025healthdcat` — NXDG 2025 paper (medium: abstract and search summaries of the CEUR and OpenReview pages)

Describes a structured, stakeholder-driven approach (summary wording): use-case analysis (persona-based), requirements definition, stakeholder engagement. The stated design principle is minimal extension: reuse all DCAT-AP core classes and properties and add only what health needs (sensitivity levels, access procedures, terminologies, quality). Validation: a multi-country pilot, a refinement phase and a pan-European public consultation. It presents itself as a blueprint for other domain profiles.
verify: the exact list of method steps and of lessons.

#### `healthdataeu2024d62` — Deliverable 6.2 (not read)

I could not open the Zenodo record. The pilot specification identifies itself as a WP6 deliverable and names "Deliverable 6.2 30 September 2024 (Recommendations on further development and deployment for possible EU-wide uptake)". A search summary adds that the model had been piloted by few partners, so wider feedback was sought.
verify: every statement about the content of D6.2 itself.

### 3.5 `w3cdcatucr` — Dataset Exchange Use Cases and Requirements (deep, high; Editor's Draft of 10 January 2019)

- **Use-case template**: authors had "to provide a problem statement, list of stakeholders experiencing the problem, and requirements suggested given the problem"; recommended additions were existing approaches, links, related use cases and comments.
- **Decision on each use case**: a proposal "to accept the use case as-is, accept the use case with changes, or reject the use case" was put to a vote, seeking consensus.
- **Derivation of requirements**: "The requirements were derived from the accepted use cases." The editors removed duplicates, edited the rest, added missing ones and "ensured links from requirements to use cases were maintained".
- **Identifiers and links**: use cases `[ID1]` to `[ID51]` (51 in the draft); requirements with a mnemonic id such as `[RPFINHER]` (68 in 14 groups). Each requirement shows its statement, related requirements, the use cases it comes from, the GitHub issue, and notes; each use case lists the requirements derived from it.
- **Tags** in four facets: deliverable; resource type (catalog, dataset, distribution); modelling aspect (coverage, documentation, packaging, provenance, publication, quality, referencing, representation, resolution, roles, semantics, service, space, status, time, usage_control, version); meta (aggregate, meta, out_of_scope). The document can be re-ordered "requirements first".
- **Requirements on profiles** that bear on our tool: 6.10.4 "Profiles may add to or specialise clauses from one or more base specifications. Such profiles inherit all the constraints from base specifications."; 6.11.1 human-readable definitions; 6.11.3 validation by schemas; 6.11.6 value lists; 6.11.7 cardinality rules "including "recommended""; 6.11.8 dependency rules; 6.11.9 user-interface support; 6.12.1 profile documentation.
- Use case ID41 (Karen Coyle) states what a consumer needs to know from a profile: which terms are mandatory, the cardinality rules, the valid values, the dependencies.

### 3.6 `statdcatap` and `geodcatap10` (deep, high)

**StatDCAT-AP 1.0.0.**
- *Decision framework* (five principles): align with DCAT and DCAT-AP; focus on elements that contribute to discovery; "use metadata terms from existing, well-known and well-maintained vocabularies"; encourage common controlled vocabularies; balance simplicity and complexity for a non-specialist audience.
- *Process*: the ISA Core Vocabulary process (working group, public review, issue tracker, mailing list) with a dated time plan from invitation to final version.
- *Extensions are introduced by the requirement they answer*: "A requirement has been expressed to expose information about" attributes and dimensions; then the properties created.
- *Annex II, "new properties log"*: columns *URI / Type (obligation, owner class) / Description (range, cardinality, note) / Issue links*. Six properties: four in the `stat:` namespace, plus `dqv:hasQualityAnnotation` and `dct:type` on Distribution.
- *Annex III, "resolution log"*: twenty issues from five bodies in the public review (30 August to 31 October 2016), in four categories (changes proposed, accept or reject; clarifications for implementers; further work, out of scope; editorial). Columns *Issue / Description / Proposed resolution / Final resolution*, with entries such as "Rejected proposed resolution." followed by the clarification added instead.
- *Conformance statement* in the DCAT-AP form (provider and receiver requirements).

**GeoDCAT-AP 1.0.**
- *Three tasks*: define alignment criteria and requirements; identify the metadata elements to cover; define the alignments.
- *Criteria*: "GeoDCAT-AP must include, at least, all the mandatory DCAT-AP elements."; other vocabularies only for elements DCAT-AP does not support; build on existing practice; new terms only as a last resort, to be "carefully assessed, and discarded" when they could conflict with standards in preparation.
- *Result*: "no new terms have been defined in the current version of GeoDCAT-AP."
- *Two profiles*: Core (elements for which DCAT-AP has a binding; harvestable by DCAT-AP applications) and Extended (the rest).
- *Mapping status*: complete, **partial** (only mandatory components mapped) and **provisional** (the alignments "must then be considered as unstable, and are meant to be replaced by appropriate terms defined in standard vocabularies").
- *Binding tables*: source element with its obligation (M/O/C/R) | DCAT-AP property with its obligation | domain | range | pointer to detailed usage notes. Obligations of both sides are shown side by side.
- *External validation of two modelling choices*: feedback was requested from the W3C Provenance Working Group.

### 3.7 `nilsson2008singapore` and `coyle2009dcap`

**Singapore Framework (high).** An application profile is a "packet of documentation" with five components: functional requirements (mandatory), domain model (mandatory), Description Set Profile (mandatory), usage guidelines (optional), encoding syntax guidelines (optional). "The functional requirements form the basis of evaluating the application profile for internal consistency". The framework is "a basis for reviewing Application Profiles for documentary completeness". Semantics live in the term definitions, "independent of any application profile"; the profile adds structural constraints. The DSP draft it cites defines two template levels (description templates per resource kind, statement templates per property) and a constraint list (minimum and maximum occurrence, class membership, property list or subproperty, literal language and datatype, value URI lists, vocabulary encoding schemes). It also says what a DSP does *not* cover: human-readable documentation, vocabulary definition, version control.

**Guidelines for Dublin Core Application Profiles (medium: search summaries of the DCMI page; text not opened).** A primer that follows the upper tier of the Singapore Framework as a roadmap. Reported sections: defining functional requirements; selecting or developing a domain model; selecting and defining metadata terms; designing the metadata record with a Description Set Profile; usage guidelines; syntax guidelines; a running example ("MyBookCase") with a DSP in an appendix. Reported statements: functional requirements start from the activity the metadata must support; usage guidelines give the "how" and "why" where the DSP gives the "what".
verify: the exact wording, and the guidance on choosing existing terms versus defining new ones.

### 3.8 Briefer entries

**`perego2016jrc` (medium for the paper; high for the DCAT-AP-JRC specification that builds on it).** The paper sets out cross-domain requirements for scientific data found while building the JRC data catalogue, and how DCAT-AP was extended; a DataCite-to-DCAT-AP mapping was the instrument. The specification shows the pattern in full: each requirement as "Ability to …", then a gap statement ("Points (2) … and (5) … are already supported by DCAT-AP via, respectively, dct:provenance and dct:source"), then the solution, preferring what GeoDCAT-AP already does. Criteria for additional vocabularies: "clear persistence and versioning policies" and cross-domain use. "DCAT-AP-JRC does not define classes or properties of its own". Property tables add two columns we do not have: *Scope* (data documentation, data citation, metadata management, metadata sharing) and *Spec.* (the specification where the use of the term is first defined). Obligation has a fourth value, conditional.

**`dragan2019maintenance` (medium, search summaries of the Joinup pages; PDF not opened).** One of a series of status reports under the Change and Release Management Policy for DCAT-AP: an overview of the GitHub issues, their status and proposed resolution, grouped as bug fixes, minor semantic changes, major semantic changes and closed issues. The policy's three change types and the two-week editor response are confirmed by primary sources I did read (the submission guidelines; the mobilityDCAT-AP governance chapter, which says it follows that policy).
verify: cut-off periods before a release (reported as one, three and eight months) and the release calendar.

**`w3cdcat3` (high).** Section 4 defines the object we generate: a DCAT profile is a specification that adds constraints to DCAT, and "A data catalog that conforms to the profile also conforms to DCAT." Allowed additions: cardinality constraints; subclasses and subproperties; classes and properties for fields DCAT lacks; controlled vocabularies or IRI sets; access mechanisms. Section 7: inverse properties "MUST NOT be used to replace" the canonical ones. Each property is specified with the fields *RDF Property, Definition, Range, Usage note*, and change notes such as "Property added in DCAT 2."

**`w3cdatacube` (high for the development repository; the Recommendation text was not reachable).** Well-formedness is defined by numbered integrity checks, each a one-line statement plus a SPARQL ASK query that returns true when there is a problem ("Every observation has a unique associated data set (true if there is a problem)"). The repository tests each check with a passing base graph and a failing delta graph named after the fault (`missing-dsd.ttl`, `duplicate-observation.ttl`). It also holds update scripts for a normalisation step (`closure.ru`, `flatten.ru`); I did not read how the tests apply them. StatDCAT-AP reuses the vocabulary as the range of its dimension and attribute properties.

### 3.9 Context works (brief; medium)

- **`wilkinson2016fair`**: fifteen principles and sub-principles (F1–F4; A1, A1.1, A1.2, A2; I1–I3; R1, R1.1–R1.3; wording seen only in reproductions). DCAT-AP itself cites FAIR in its legal-information section. Possible minor use: tag atoms and added elements with the sub-principle they serve and show coverage per letter. Not counted as a key step.
- **`koesten2020reuse`**: reuse features from the literature, then a study of more than 1.4 million data files from over 65,000 GitHub repositories with engagement metrics as a proxy for reuse. Recommendations reported by a secondary summary: a short informative textual summary; a structured README with links; processable file sizes; files that open with a standard library. No step for a metadata profile beyond what the base already mandates (title, description).
- **`chapman2020search`**: a survey that argues dataset search is a field of its own, separates "basic" search for existing datasets from search over assembled observations, and lists open problems (abstract and search summary). No implementable step found.
- **`gregory2020search`**: bibliometric study plus interviews; argues that data search is socio-technical and context-dependent. No implementable step found; it supports keeping the *subject* (who needs it) on each atom.

---

## 4. From requirement to change: the practices side by side

| | Requirements unit | Intermediate model | Reuse order | How an addition is justified | Conformance statement |
|---|---|---|---|---|---|
| SEMIC guidelines | use case as user story, one issue each | minimal DCAT-AP profile | DCAT-AP → DCAT / other vocabulary / other profile → new | issue with problem statement and proposed resolution | profiles "must comply with the requirements and restrictions imposed by DCAT-AP" |
| mobilityDCAT-AP | 40 requirements in 4 categories (medium) | conceptual model, technology-independent | DCAT-AP → other RDF vocabularies → own namespace | usage note phrase + "+" marks + annex of additions + changelog with issue | provider and receiver requirements; shapes import the base |
| HealthDCAT-AP | persona-based use cases (medium); legal articles | UML per access level | DCAT-AP → sibling extensions → vocabularies used by DCAT-AP → own | A/E/P column; article in usage note | "MUST first conform to DCAT-AP" |
| HVD annex | articles of the regulation | "Mapping the HVD IR to DCAT-AP" | DCAT-AP, mostly tightened (E); a few profile-specific (P) rows, among them the newly created `hvdCategory` | A/E/P; article in usage note | "MUST conform to DCAT-AP" |
| GeoDCAT-AP 1.0 | source-standard elements with obligation | list of elements to cover | DCAT-AP → existing vocabularies → (new, not used) | binding table with obligations of both sides; mapping status | "Compliance with DCAT-AP is ensured" |
| StatDCAT-AP 1.0.0 | requirements raised in the working group | — | DCAT-AP → existing vocabularies → `stat:` | new properties log; resolution log | provider and receiver requirements |
| DCAT-AP-JRC | "Ability to …" statements | core profile + domain extensions | DCAT-AP → Geo/StatDCAT-AP → other vocabularies; none minted | gap statement per requirement; *Spec.* column | — |
| W3C UCR | use case template; derived requirements | — | — | requirement ↔ use case links, GitHub issue | (requirement) profiles "inherit all the constraints" |

What none of them does: link one constraint value to one requirement sentence with a quoted span, or check the link mechanically. That is the part our tool adds.

---

## 5. Compact rulebook, with the source behind each rule

The full rule set is in report B2. Here are the rules my steps rely on, each with the sentence that backs it. Column "Our check" refers to the ids in `engine/verify.py` and `conformance/check.py`.

| # | Rule | Backing (source, short quote) | Our check |
|---|---|---|---|
| R1 | An extension may tighten, never loosen | Reuse guidelines: "It is not possible to loosen them under any conditions, as the result would no longer be compliant with DCAT-AP." | V3, C1. The source string of C1 calls this a derived rule; it is stated explicitly |
| R2 | Mandatory stays mandatory; at most one stays at most one | Reuse guidelines, cardinality: "Then it must be mandatory in the profile as well." HealthDCAT-AP: "Mandatory properties retain their required status." | V3, C1 |
| R3 | Range: class→literal no; literal→class no; literal→literal only a subtype; class→controlled vocabulary yes; class→other class only if semantically compatible | Reuse guidelines: "Narrowing down the value space will not create any issues but extending it will." | V2/V3; the fifth case needs a judgment (status `incomparable` → review) |
| R4 | A different controlled vocabulary needs a different property; a closed value space is kept; extend the vocabulary at its source first | Reuse guidelines: "If another controlled vocabulary is to be used, then it must be used with a different property." DCAT-AP 3.0.1: "All profiles in the ecosystem MUST avoid conflicts by creating subproperties." | **gap**: the strength of a vocabulary binding (MUST / at least one / RECOMMENDED / MAY) is not a facet yet |
| R5 | Reuse only if the base definition still holds | Reuse guidelines: "users outside of the profile context will interpret the data using the DCAT-AP interpretation, which must not be confusing". | **gap**: no semantic-fit check |
| R6 | New terms live in the profile's own managed namespace, with a generic definition and open domain and range, and are related to existing terms | Reuse guidelines: "Ensure the domain is as open as possible"; step 4: definitions "should relate the new classes and properties to existing ones". | C3, C4; **gap**: openness and genericity lints |
| R7 | Data valid under the extension is valid under the base | DCAT 3: "A data catalog that conforms to the profile also conforms to DCAT." HVD: "it MUST conform to DCAT-AP." | C7 |
| R8 | Where the base is stricter than the requirement, the base wins and the case is raised upstream | mobilityDCAT-AP 3.0.0, G.1: "the inherited rule prevails … raised with the DCAT-AP maintainers rather than worked around". Reuse guidelines: "raise an issue." | **gap**: no escalation outcome |
| R9 | Design decisions that add or tighten need a stated use case | Reuse guidelines: "Use cases are intended to justify and explain relevant design decisions, in particular those that introduce new elements, tighten existing constraints". | T1, C5 |
| R10 | Inverse properties never replace the canonical direction | DCAT 3, section 7: "they MUST NOT be used to replace them". | **gap** |
| R11 | Do not "remove" base elements; at most declare them not used, with a reason | mobilityDCAT-AP 3.0.0: "The term "removed" caused some confusion, so it is replaced with "not used from DCAT-AP"." | not modelled (see section 8, tension T1) |
| R12 | Use MUST only for what a machine can verify | DCAT-AP 3.0.1: the first two levels "SHOULD only be used for requirements that can be verified by a machine". | **gap** |

### 5.1 The current code against these sources

Read-only look at `requirement-based-dcat-profile-extensioner/backend/` at commit `63e732f` (working tree of 2026-11-13). The code is changing; treat these as pointers.

1. `compile/shacl.py` already emits deltas only, adds `prov:wasDerivedFrom` to the atoms and an `owl:imports`. The import target is `kb.base.info.homepage`, which is the HTML specification page. mobilityDCAT-AP imports the **shapes document** (`owl:imports <https://semiceu.github.io/DCAT-AP/releases/3.0.1/html/shacl/shapes.ttl>`). A validator that follows imports needs the shape file IRI. I could not test which DCAT-AP shape URLs resolve.
2. The source text of check C1 calls "may restrict, not relax" a derived rule. The guideline states it outright (rule R1), so C1 can cite it directly. C7's source ("derived") can cite DCAT 3 section 4 and the HVD conformance sentence (rule R7).
3. C7 generates one positive witness. I found no negative cases in `conformance/` or `tests/` (step G3-S11).
4. `Facets.controlled_vocabulary` is a list without a binding strength (step G3-S04).
5. Property shapes get one IRI per class and path. DCAT-AP's newer shape file has one IRI per constraint, which is what lets implementers "cherry pick" constraints and lets a report point at a single constraint.
6. I found no semantic-fit check, no inverse-pair guard, no escalation outcome, no impact class and no A/E/P field (steps S05, S23, S02/S10, S16, S07).

---

## 6. Reusable key steps

Each step: what they did (source-bound), how we reuse it (our design), stage, evidence, confidence.

### G3-S01 — Four-rung resolution ladder per requirement
- **From**: `semicreuse2026`; corroborated by `mobilitydcatspec`, `statdcatap`, `geodcatap10`, `perego2016jrc`.
- **What they did**: every use case is resolved by one of four standard situations in a fixed order: covered by DCAT-AP (reuse as-is); covered with adjustments (tighten); covered by DCAT, another vocabulary or another DCAT-AP profile (reuse that); not covered (new term in own namespace). Each worked example has the fields *Use case / Existing DCAT-AP solution / Resolution*.
- **How we reuse**: Propose first emits `resolution_case ∈ {covered_as_is, tighten_base, reuse_other, mint}` and only then the facets. The mapping to our contract is direct: `covered_as_is` → `AtomDisposition.covered_by_base`; `tighten_base` → `refine_property`; `reuse_other` → `reuse_property` / `reuse_class`; `mint` → `mint_property` / `mint_class`. The prompt presents the rungs as an ordered checklist and requires, for every rung skipped, one sentence naming the candidate examined and why it fails. The six worked examples of the guideline (CC BY 4.0) are few-shot exemplars in the same field layout. Verify rejects a later rung when an earlier rung had a candidate that was not discussed (extends V4 from "mint" to every rung).
- **Stage**: propose.
- **Evidence**: `/home/user/refs/SEMICeu__DCAT-AP-reuse-guidelines/index.html`, Step 2: "For each use case, its data representation can be designed according to the following standard situations".
- **Confidence**: high.

### G3-S02 — Tighten-only cardinality rule with upstream escalation
- **From**: `semicreuse2026`, `mobilitydcatspec`, `derycke2025healthdcat` (pilot specification).
- **What they did**: mandatory stays mandatory; a maximum of one stays one; stricter is allowed; a needed relaxation is raised as an issue on the base (GeoDCAT-AP did so for *rights*). mobilityDCAT-AP 3.0.0 notes one such case in the header of its shapes file as "to be reported to the DCAT-AP maintainers".
- **How we reuse**: V3 keeps the lattice test (`new.min ≥ base.min`, `new.max ≤ base.max`). New: a violation is **not** sent to Repair with the instruction "loosen"; Repair may only (a) drop the facet and inherit, (b) move the need to another property (S04/S06), or (c) mark the atom `needs_review` with outcome `escalate_upstream` and a drafted issue in the DCAT-AP template (S15).
- **Stage**: verify.
- **Evidence**: reuse guidelines: "It is not possible to loosen them under any conditions". mobilityDCAT-AP 3.0.0, Annex G.1: "the shapes can make a rule stricter but cannot loosen an inherited one".
- **Confidence**: high.

### G3-S03 — Range compatibility decision table (five cases)
- **From**: `semicreuse2026`.
- **What they did**: five combinations of base range and required range with a verdict each (rule R3), with examples: contact point as text is impossible; *release date* restricted to `xsd:date` is fine, adding `xsd:gDay` is not; `eli:LegalResource` → `skos:Concept` is acceptable only if the instances fit the base definition, and then double typing is advised.
- **How we reuse**: V2/V3 use a decision table keyed by (base kind, new kind). Needed data: an XSD derivation table plus the DCAT-AP union datatypes; the subclass closure from the vocabulary index. Case five without subclass evidence yields `incomparable` → human review with the base class definition shown; on acceptance the engine adds a usage note recommending double typing.
- **Stage**: verify.
- **Evidence**: reuse guidelines, range section: "Narrowing down the value space will not create any issues but extending it will."
- **Confidence**: high.

### G3-S04 — Controlled-vocabulary strength rules
- **From**: `semicreuse2026`, `semicdcatap`, `mobilitydcatspec`.
- **What they did**: four binding strengths. MUST: keep the vocabulary; for other values create a separate property and map. At least one: keep one value from the original, add others. RECOMMENDED or MAY: another vocabulary may be used with the same property. Before all that, try to extend the vocabulary at its source. A different vocabulary for classification goes on a different property (GeoDCAT-AP service category; HVD category; mobilityDCAT-AP `mobilityTheme` as subproperty of `dcat:theme`). Vocabularies must meet seven publication requirements.
- **How we reuse**: add `cv_strength` to `BaseElement.facets` (filled from the DCAT-AP tables) and to `Facets`. Verify table: MUST + different list → error with repair hint "mint a subproperty of the base property and bind the new list there; add a mapping note". Admissibility of a proposed vocabulary is a warning checklist (licence, maintainer, documentation, languages, URIs, persistence policy) shown to the reviewer. A fifth repair hint: "propose the missing values to the vocabulary owner" as an escalation outcome.
- **Stage**: verify.
- **Evidence**: reuse guidelines: "If another controlled vocabulary is to be used, then it must be used with a different property." DCAT-AP 3.0.1, section 10: "All profiles in the ecosystem MUST avoid conflicts by creating subproperties."
- **Confidence**: high.

### G3-S05 — Semantic-fit test before reusing a base term
- **From**: `semicreuse2026`.
- **What they did**: three outcomes when a term "seems appropriate at first glance" but its definition or usage note does not match: terminological difference only (relabel in the documentation); compatible but distinct (subclass or subproperty); significant difference (do not reuse). The example is *applicable legislation*: legislation that mandates a dataset versus legislation that mentions it.
- **How we reuse**: a separate judge call per reuse or refine change. Input: the atom, the base label, definition and usage note verbatim, and the proposed usage. Output: one of `same_meaning`, `narrower_compatible`, `different_meaning`, with the base sentence that decides it. Effects: keep; convert to a mint with `sub_property_of`; convert to a mint without it. A split vote goes to the human queue. The base definition quoted by the judge is stored in the trace.
- **Stage**: judge_vote.
- **Evidence**: reuse guidelines, situation 2: "users outside of the profile context will interpret the data using the DCAT-AP interpretation, which must not be confusing".
- **Confidence**: high.

### G3-S06 — Mint protocol: generic vocabulary term plus contextual profile usage
- **From**: `semicreuse2026`, `mobilitydcatspec`, `statdcatap`.
- **What they did**: a new property is defined once in a supporting vocabulary in a managed namespace, with open domain and range and a generic definition ("status of the catalogued resource", not "status of the Dataset"), and then *used* in the profile with class-specific notes and cardinality. The two are "distinct specifications, each with their own lifecycle". mobilityDCAT-AP declares minted properties with `rdfs:subPropertyOf`, `dcam:domainIncludes`, `dcam:rangeIncludes` and a scope note; GeoDCAT-AP's vocabulary uses `rdfs:subPropertyOf` and `rdfs:isDefinedBy`.
- **How we reuse**: a mint change yields two outputs: (a) a vocabulary entry (label, generic definition, `sub_property_of` or `super_class` when a nearest existing term exists, soft domain and range, `rdfs:isDefinedBy`); (b) the profile element with the facets. Lints: the definition must not name the target class; the IRI must be in the project namespace; label and definition are mandatory. Compile writes a separate vocabulary file next to the shapes.
- **Stage**: propose.
- **Evidence**: reuse guidelines, situation 5: "Ensure the domain is as open as possible: use dcat:Resource for catalogable resources, or rdfs:Resource for generic resources". `releases/1.1.0/mobilitydcat-ap.ttl`: `mobilitydcatap:mobilityTheme … rdfs:subPropertyOf dcat:theme`.
- **Confidence**: high.

### G3-S07 — Derived reuse qualification A/E/P per element
- **From**: `semicdcatap` (3.0.0, HVD annex, 3.0.1 changelog), `derycke2025healthdcat` (pilot specification), `mobilitydcatspec` (3.0.0).
- **What they did**: every property row is tagged A (as-is), E (extra restrictions or usage notes) or P (profile-specific). The tag depends on the base version and changes when constraints change.
- **How we reuse**: compute it, do not ask the LLM for it: `unchanged` → A; `tightened` or added usage note → E; not constrained by the base on that class → P. Optionally record the source of a P element (sibling profile, other vocabulary, minted), as mobilityDCAT-AP 3.0.0 does with GA/GE. Show it as a column on the workbench and in the generated documentation; recompute when the base profile version changes.
- **Stage**: traceability.
- **Evidence**: `releases/3.0.0-hvd/index.html`: "This reuse qualification assessement is w.r.t. a specific version of DCAT-AP." `releases/3.0.1/CHANGELOG.md`: "As consequence the reuse qualification changes from extended to as-is."
- **Confidence**: high.

### G3-S08 — Usage notes that state the change against the base and its reason
- **From**: `mobilitydcatspec`, `semicdcatap` (HVD annex).
- **What they did**: the usage note of a changed element says what changed relative to the named base version and why; additions are marked "+"; per class, notes list what is new; an annex lists all additions. HVD names the legal article in the note.
- **How we reuse**: `verbalise` builds the note from `FacetJustification`: reason sentence, then "Thus, *facet* is *tightened* from *base value* to *new value* compared to *base id*", then the atom ids. Documentation shows per class the blocks "added by this extension" and "tightened", and one annex table of all additions. The same sentence goes into `sh:description` of the property shape (as mobilityDCAT-AP 3.0.0 does: "Raised to mandatory (1..1).").
- **Stage**: traceability.
- **Evidence**: mobilityDCAT-AP 1.1.0, section 4.10.1: "the obligation of this property is raised to “mandatory”, compared to [DCAT-AP-v2.0.1]". HVD annex: "Article 3.4 requires the designation of a point of contact for an API."
- **Confidence**: high.

### G3-S09 — Delta-only SHACL that imports the base shapes
- **From**: `mobilitydcatspec` (1.1.0 README; 3.0.0 sources), `semicdcatap`.
- **What they did**: extension shapes `owl:imports` the base shapes and restate nothing ("inherit, do not re-encode"). Files are split by kind of check (cardinality and value kind; ranges; controlled vocabularies; deprecations; imports). Each property shape is a named resource with name, description, message and severity. DCAT-AP publishes a variant with one IRI per constraint and a link to the specification anchor.
- **How we reuse**: our compiler already writes deltas with `prov:wasDerivedFrom` to the atoms (section 5.1). Remaining from these sources: import the IRI of the base **shape files**, not the specification page; optionally split the output into `shapes.ttl`, `ranges.ttl`, `vocabularies.ttl` and `imports.ttl` with a versioned namespace each; give every constraint its own shape IRI derived from (class, path, facet); add `sh:message`, and `rdfs:seeAlso` to the documentation anchor; decide whether optional elements get `sh:Info`. A self-contained file (base plus deltas) should stay available for validators that do not follow imports.
- **Stage**: compile.
- **Evidence**: `mobilityDCAT-AP/mobilityDCAT-AP`, `src/shacl/README.md`: "the constraint files import the corresponding DCAT-AP 3.0.1 file via `owl:imports` and contain only the mobilityDCAT-AP-specific additions (deltas)". DCAT-AP 3.0.0: "a new design where each constraint has got a unique identifier".
- **Confidence**: high.

### G3-S10 — Conformance by inheritance; the base wins, the case is escalated
- **From**: `mobilitydcatspec`, `semicreuse2026`, `semicdcatap` (HVD), `derycke2025healthdcat` (pilot specification), `w3cdcat3`.
- **What they did**: conformance to the extension presupposes conformance to the base. With imported shapes this holds by construction. Where base shapes are stricter than the extension's text, the stricter rule stays and is reported upstream.
- **How we reuse**: the Conformance stage reports three things: static (no facet `loosened` or `conflict`); empirical (witnesses, S11); and a list of **escalations** (atoms that cannot be met without loosening), each with the base constraint, the atom and a drafted upstream issue. The generated specification opens its conformance section with the sentence used by HVD and HealthDCAT-AP, naming the base id and version.
- **Stage**: conformance.
- **Evidence**: mobilityDCAT-AP 3.0.0, Annex G.1: "the inherited rule prevails; these are noted in the specification and raised with the DCAT-AP maintainers rather than worked around". HVD: "it MUST conform to DCAT-AP."
- **Confidence**: high.

### G3-S11 — Positive and negative witness suites, including base regression cases
- **From**: `mobilitydcatspec` (its Annex G points to the project's validation toolkit), `w3cdatacube`.
- **What they did**: test graphs per category in `positives/` and `negatives/`, with an id and the fault in the file name; a category `baseline-dcat-ap` checks plain base cases; a run passes when positives conform and negatives do not. Data Cube tests each integrity check with a valid base graph and a small failing delta.
- **How we reuse**: C7 today generates one positive witness. Add: for every included change one **negative delta** (the positive minus the newly required value, or with a value outside the range or list) that must fail under the extension; and a fixed set of base positives and negatives that must keep their verdict under base ∪ extension. Report per change: positive passes, negative fails, base verdicts unchanged. File names carry the change id.
- **Stage**: conformance.
- **Evidence**: `/home/user/refs/mobilityDCAT-AP__validation/sample_data/baseline-dcat-ap/{positives,negatives}/` and `scripts/validator.py` (a negative test passes when the graph does not conform; paraphrase).
- **Confidence**: high.

### G3-S12 — Requirement records with stable ids, tags and maintained back-links
- **From**: `w3cdcatucr`.
- **What they did**: use cases by template (problem statement, stakeholders, suggested requirements; optional existing approaches, links, related cases); stable ids; four tag facets; requirements derived from accepted use cases, deduplicated; links in both directions and to the tracking issue; a view "requirements first".
- **How we reuse**: atoms keep `source_reference`; intake adds optional `use_case_id`, `stakeholders` and tags from two facets (resource type → class mapping; modelling aspect → retrieval hint and clustering for Consolidate). Deduplication at intake keeps the merged ids. The trace matrix is navigable both ways on the workbench: atom → changes → shapes, and element → atoms, with two orderings (atoms first, elements first).
- **Stage**: traceability.
- **Evidence**: `w3c/dxwg`, `ucr/static/index.html`, section 3: "The editors also ensured links from requirements to use cases were maintained."
- **Confidence**: high.

### G3-S13 — Requirement categories that route differently
- **From**: `scrocca2022napdcat`, `bures2022napcore`, `scrocca2025mobilitydcat`.
- **What they did**: forty requirements in four categories: General (8), Existing Vocabularies (5), Content (22), Implementation (5). By the summaries, General requirements are high-level specifications and Existing Vocabularies name initiatives to be considered.
- **How we reuse**: our reading is that only Content requirements describe information the metadata must carry. Intake classifies each atom. *Content* atoms go to Propose. *Existing vocabularies* atoms configure Retrieve (preferred vocabularies and sibling profiles). *General* and *Implementation* atoms become run-level settings or get the disposition `out_of_scope` with the category as reason, so they are visible and not silently dropped.
- **Stage**: atom_intake.
- **Evidence**: search summaries of `arxiv.org/abs/2503.11535` and `ceur-ws.org/Vol-3235/paper22.pdf` (texts not opened): forty requirements, "General (8), Existing Vocabularies (5), Content (22), Implementation (5)".
- **Confidence**: medium.

### G3-S14 — Information need first, mapping second, obligations side by side
- **From**: `mobilitydcatspec` (specification and wiki), `scrocca2025mobilitydcat`, `geodcatap10`, `nilsson2008singapore`.
- **What they did**: requirements are first turned into a technology-independent conceptual model; then each element is checked against DCAT-AP, then other vocabularies; requested and existing obligations are compared. GeoDCAT-AP prints both obligations in one table row. The Singapore Framework makes the domain model a mandatory component.
- **How we reuse**: keep Propose in two passes. Pass 1 writes `information_needed` and a neutral description (entity, attribute, value kind, requested obligation) with no IRIs. Pass 2 maps it to candidates and shows a two-column comparison "requested | base" for obligation, cardinality and range. The second pass never sees pass-1 text that contains a term name.
- **Stage**: propose.
- **Evidence**: mobilityDCAT-AP wiki, chapter 1: "the first step was to check if and how existing elements from the general DCAT-AP vocabulary correspond to the elements of the conceptual model".
- **Confidence**: high.

### G3-S15 — Issue-shaped proposals and a resolution log for human review
- **From**: `semicreuse2026`, `statdcatap`, `w3cdcatucr`, `dragan2019maintenance`, `semicdcatap` (submission guidelines, governance labels).
- **What they did**: one issue per use case with problem statement and proposed resolution "or its variants"; community response agree, disagree or alternative; the W3C group voted on each use case (accept as-is, accept with changes, reject); StatDCAT-AP publishes a table *Issue / Description / Proposed resolution / Final resolution*; SEMIC labels track the state of each issue.
- **How we reuse**: a review item shows: the atom (problem statement), the proposed change (resolution), `alternatives` (variants), failed checks. Reviewer actions are exactly: accept as-is, accept with changes (edit), reject, defer (future work), escalate upstream. Each action stores a reason. The queue states map to our `DecisionStatus`. Export: a resolution-log annex in the StatDCAT-AP column layout, and for escalations an issue text in the DCAT-AP template (submitter, product affected, problem or requirement, proposed solution).
- **Stage**: hitl_review.
- **Evidence**: reuse guidelines, Step 3: "Its description should contain a problem statement or requirement, and a proposed resolution, or its variants". StatDCAT-AP 1.0.0, Annex III (column headings).
- **Confidence**: high.

### G3-S16 — Change impact classes and version bump
- **From**: `dragan2019maintenance`, `mobilitydcatspec` (governance chapter, document history, migration guide), `semicdcatap` (submission guidelines).
- **What they did**: three classes: bug fix; minor semantic change (affects interoperability in a non-disruptive way, for example adding optional properties); major semantic change (for example adding mandatory properties or a mandatory vocabulary). Versions follow X.Y.Z accordingly. The migration guide of mobilityDCAT-AP 3.0.0 sorts changes by what a data provider must do.
- **How we reuse**: classify each included change by rule: editorial (labels, notes) → patch; new optional or recommended element → minor; new mandatory element, raised minimum, narrowed range, closed value list → major. The change set gets the highest class and a suggested version. Compile emits a provider checklist with the categories MUST add, MUST restrict, MAY add.
- **Stage**: traceability.
- **Evidence**: mobilityDCAT-AP wiki, chapter 6 (copy of the NAPCORE governance report): "Major semantic changes are changes that have (more) serious consequences for interoperability, for example, the addition of mandatory properties". DCAT-AP submission guidelines: "classify the issue as a bug fix, minor semantic issue or major semantic issue".
- **Confidence**: high.

### G3-S17 — Change table and change-log sentences generated from typed records
- **From**: `semicdcatap` (2.0.1 Annex II; 3.0.0 changelog), `statdcatap` (Annex II), `mobilitydcatspec`.
- **What they did**: a change table with URI, type, action, description, issue and release; a "new properties log"; changelog sentences in a fixed grammar with reason and issue number.
- **How we reuse**: `compile/docs.py` renders two artefacts from the `ProfileChange` list, with atoms in place of issues: (a) the table *URI | type (obligation, class or property, owner class) | action | description (range, cardinality) | atoms | version*; (b) sentences of the form "*Element* of class *C*: *facet* changed from *x* to *y*, to *reason*. Covers *atom ids*." No free text is written by the LLM at this point.
- **Stage**: compile.
- **Evidence**: `releases/2.0.1/DCAT_AP_2.0.1.pdf`, Annex II (columns URI, Type, Action, Description, Issue, Release). mobilityDCAT-AP 1.1.0, H.1: "Cardinality of property "schema" changed from 0..1 to 0..n. Reason: allow for naming multiple schemas. See issue #56".
- **Confidence**: high.

### G3-S18 — Documentary completeness check of the compiled package
- **From**: `nilsson2008singapore`, `coyle2009dcap`, `semicreuse2026` (Step 4).
- **What they did**: an application profile is a documentation package: functional requirements, domain model and constraint definition are mandatory; usage and syntax guidelines optional. SEMIC's publication step lists the HTML specification (context, difference from DCAT-AP, contact), SHACL shapes, and for new terms a vocabulary document and an RDF file.
- **How we reuse**: a final checklist in Compile, shown on the workbench: requirements (the atom set, with scope and out-of-scope atoms); domain model (class diagram of the extension against the base); constraints (SHACL, LinkML, DSV); usage notes for every added or tightened element; syntax (JSON-LD context); vocabulary file when anything was minted; statement of how the profile differs from the base. Missing mandatory parts block export. The first component doubles as the evaluation basis: every element must trace to it (C5) and every in-scope atom must have a coverage state.
- **Stage**: compile.
- **Evidence**: `dcmi/repository`, Singapore Framework copy, section 3.2: "The functional requirements form the basis of evaluating the application profile for internal consistency".
- **Confidence**: high for the Singapore Framework and the SEMIC step; medium for `coyle2009dcap`.

### G3-S19 — Coverage status per mapping and a core/extended split
- **From**: `geodcatap10`.
- **What they did**: mappings are complete, partial (only mandatory components representable) or provisional (unstable, to be replaced when a standard term exists). Two profiles are published: Core, consumable by plain DCAT-AP applications, and Extended.
- **How we reuse**: `CoverageLink.coverage` gains the value `provisional` (a term chosen for want of a better one, flagged for revisit, shown as unstable in the documentation). Compile can emit two views: *core* (reuse and tightening of base elements only) and *full* (with additions), so a reader sees what a plain DCAT-AP consumer will understand.
- **Stage**: traceability.
- **Evidence**: `releases/1.0.0/geodcat-ap_1.0.pdf`, section 4.3: "must then be considered as unstable, and are meant to be replaced by appropriate terms defined in standard vocabularies".
- **Confidence**: high.

### G3-S20 — Several usage contexts: subclass or sub-profile instead of conditional notes
- **From**: `semicreuse2026`, `derycke2025healthdcat` (pilot specification), `semicdcatap` (HVD annex).
- **What they did**: when one class is used in several contexts with different obligations, create a subclass per context; when a context spans several classes, make a separate sub-profile. HealthDCAT-AP publishes three variants by access level; HVD is an annex because its context covers datasets, services and distributions. Both note that their shapes assume every resource is in scope.
- **How we reuse**: intake extracts a `condition` from atoms ("if the dataset contains personal data"). Consolidate groups atoms by condition. One conditioned class → propose `mint_class` as subclass with its own shape; a condition touching two or more classes → propose a named variant (separate shape file with its own target). Conditions are never encoded only in usage notes.
- **Stage**: propose.
- **Evidence**: reuse guidelines, situation 7: "create a subclass of the corresponding DCAT-AP class for each of the contexts". HealthDCAT-AP: "Cardinalities Based on Dataset Access Rights: Open, Protected, and Sensitive Health Data".
- **Confidence**: high.

### G3-S21 — Strong-recommendation pattern and the machine-verifiability rule
- **From**: `semicdcatap` (HVD annex 3.0.0; DCAT-AP 3.0.1).
- **What they did**: for a requirement that is strongly recommended but not obligatory, HVD kept the formal minimum relaxed, set the usage qualification to recommended, explained it in the usage note, and added a SHACL check. DCAT-AP 3.0.1 says the MUST levels should be used only for machine-verifiable requirements.
- **How we reuse**: the modality-to-constraint mapping gets a middle path. `should` → obligation recommended, no minimum, a Warning-severity shape and a usage note quoting the atom. A `must` atom whose condition no shape can test (for example "must be of sufficient quality") is downgraded to recommended plus usage note, with a T1 note saying why; it is not turned into an unverifiable mandatory constraint.
- **Stage**: propose.
- **Evidence**: `releases/3.0.0-hvd/index.html`: "The formal constraints have been relaxed, the usage qualification has been set to recommendation, and additional usage notes including this explanation have been added."
- **Confidence**: high.

### G3-S22 — Numbered integrity constraints as ASK queries, one failing fixture each
- **From**: `w3cdatacube`.
- **What they did**: well-formedness as a numbered list of checks, each with a one-line statement and an ASK query that is true on violation; tests pair a valid graph with a small delta that triggers exactly one check.
- **How we reuse**: express the profile-level invariants of the change set (V5, C2 to C5) over an RDF rendering of the `ProfileChangeSet` as numbered queries with a statement each, for example "every minted property has a label, a definition and a range" or "no two included changes set different maxima on the same class and path". Each query ships with one failing fixture. This makes the checks inspectable on the workbench and citable in the paper by number.
- **Stage**: verify.
- **Evidence**: `UKGovLD/publishing-statistical-data`, `src/main/resources/integrity-1.sparql`: "Every observation has a unique associated data set (true if there is a problem)"; `src/test/java/com/epimorpics/qbwf/TestWF.java`.
- **Confidence**: high for the development repository; the Recommendation's wording was not checked.

### G3-S23 — Base-level guards: inverse pairs, unlisted DCAT properties, no removal
- **From**: `w3cdcat3`, `semicdcatap`, `mobilitydcatspec`.
- **What they did**: DCAT allows inverse properties only in addition to the canonical ones. DCAT-AP treats DCAT properties it does not list as optional without conformance expectation. mobilityDCAT-AP replaced "removed" by "not used from DCAT-AP" and documents the reason for each unused element.
- **How we reuse**: three small rules. (a) A table of the eleven inverse pairs from DCAT 3 section 7; a change that uses the inverse where the canonical property exists is rewritten or rejected. (b) Retrieve labels a DCAT property that the base profile does not list as "in DCAT, not constrained by the base" so that it lands on rung three of the ladder. (c) No change kind removes a base element; an atom that asks for it yields a `usage_note` change "not used", with a warning that receivers must still process it.
- **Stage**: verify.
- **Evidence**: DCAT 3 REC, section 7: "they MAY be used only in addition to those described in 6. Vocabulary specification, and that they MUST NOT be used to replace them".
- **Confidence**: high.

### G3-S24 — Retrieval tiers and admissibility criteria for vocabularies
- **From**: `derycke2025healthdcat` (pilot specification), `statdcatap`, `perego2016jrc` (DCAT-AP-JRC specification), `geodcatap10`, `scrocca2025mobilitydcat`.
- **What they did**: the sources agree in outline on an order of preference: DCAT-AP itself first; related extensions and the vocabularies DCAT-AP already uses next; other well-maintained vocabularies after that; own terms last. Admissibility criteria are named: persistence and versioning policy, cross-domain use, maintenance. No single source ranks sibling extensions against other vocabularies; the tiers below are ours.
- **How we reuse**: the vocabulary index stores a tier per term: T0 base profile on the same class; T1 base profile on another class; T2 DCAT 3 outside the base; T3 sibling DCAT-AP profiles; T4 vocabularies the base already uses; T5 other admitted vocabularies. Retrieval boosts by tier and writes the tier into `Candidate.why`. A vocabulary enters the index only with the admissibility fields filled (maintainer, licence, versioning policy); missing fields produce a warning on any change that uses it.
- **Stage**: retrieve.
- **Evidence**: HealthDCAT-AP pilot specification: "Prioritising vocabularies used in DCAT-AP for metadata property selection". StatDCAT-AP 6.2: "use metadata terms from existing, well-known and well-maintained vocabularies". DCAT-AP-JRC: "They have clear persistence and versioning policies."
- **Confidence**: high.

### G3-S25 — Profile-level reuse metrics with reference values from published extensions
- **From**: `mobilitydcatspec`, `statdcatap`, `geodcatap10`, `perego2016jrc`.
- **What they did**: published extensions report, or let one count, how much was added and how much of it was newly defined (section 1, point 3).
- **How we reuse**: three run-level measures on every change set: **mint rate** (minted terms / added elements), **tier distribution** of reused terms (S24), and the **A/E/P distribution** (S07). The published profiles give orientation values, not targets: GeoDCAT-AP 1.0 zero minted; DCAT-AP-JRC 1.0 zero; StatDCAT-AP 1.0.0 four of six new properties in its own namespace; mobilityDCAT-AP 1.1.0 twelve properties declared in its own namespace against 48 added properties stated in the specification. A mint rate far above these values is a signal for review, shown on the workbench.
- **Stage**: evaluation.
- **Evidence**: mobilityDCAT-AP 1.1.0, A.2: "2 additional classes and 48 additional properties (some of which re-used across classes)"; my count of `mobilitydcatap:` declarations in `releases/1.1.0/mobilitydcat-ap.ttl` (2 classes, 12 properties). GeoDCAT-AP 1.0: "no new terms have been defined".
- **Confidence**: high for the quoted statements; the count is mine.

---

## 7. Templates worth copying

**Issue / escalation text** (DCAT-AP submission guidelines): short title naming the class or property; submitter and affiliation; portal, service or product affected; description of the problem or requirement; proposed solution.

**Use case record** (W3C UCR): id; title; author; tags; stakeholders; problem statement; existing approaches; links; related use cases; requirements derived.

**Requirement record** (W3C UCR): group; title; mnemonic id; one-sentence statement; related requirements; source use cases; tracking issue; notes.

**Worked example for prompts** (SEMIC): *Use case* → *Existing DCAT-AP solution* → *Problem* (optional) → *Resolution*.

**Property row** (HVD, GeoDCAT-AP 3, HealthDCAT-AP): Property | Range | Card | Definition | Usage | Reuse (A/E/P). DCAT-AP-JRC adds *Scope* and *Spec.* (where the use was first defined).

**Change-log sentence** (mobilityDCAT-AP): *element* of class *C*: *facet* changed from *x* to *y*. Reason: *r*. See issue *#n*.

**Change table** (DCAT-AP 2.0.1 Annex II): URI | Type | Action | Description | Issue | Release.

**Resolution log** (StatDCAT-AP Annex III): Issue | Description | Proposed resolution | Final resolution.

**Delta shape** (mobilityDCAT-AP 3.0.0):

```turtle
:Dataset_Shape_accrualPeriodicity a sh:PropertyShape ;
  sh:path dct:accrualPeriodicity ; sh:minCount 1 ; sh:maxCount 1 ;
  sh:name "frequency"@en ;
  sh:description "How often the delivered content is updated. Raised to mandatory (1..1)."@en ;
  sh:message "Frequency is mandatory. Exactly one value must be provided"@en ;
  sh:severity sh:Violation .
```

**Test-suite layout** (mobilityDCAT-AP validation): `<category>/{positives,negatives}/<ID>-<fault>.ttl`.

---

## 8. Tensions between the sources, and open points

- **T1 — Dropping optional base elements.** HealthDCAT-AP and (by a search summary) the NAPCORE approach report allow removing recommended and optional properties. mobilityDCAT-AP 1.1.0 did so and marked them "−". DCAT-AP's receiver requirement asks receivers to process *all* classes and properties. The 2026 SEMIC guideline does not discuss removal. mobilityDCAT-AP 3.0.0 retreats to "not used", with reasons. Our safest reading: providers stay conformant; a receiver built only from the extension may not be a conformant DCAT-AP receiver. Hence rule (c) of S23.
- **T2 — Hard domain versus open domain.** SEMIC advises the most open domain; GeoDCAT-AP's vocabulary sets `rdfs:domain dcat:DataService` on service properties; mobilityDCAT-AP uses `dcam:domainIncludes`. S06 follows the SEMIC advice and the mobilityDCAT-AP form.
- **T3 — Severity of a strong recommendation.** HVD gives its extra check severity Violation although the property is only recommended. Our default in S21 is Warning; this is our choice.
- **T4 — "Recommended" as an obligation level** is being phased out: mobilityDCAT-AP 3.0.0 keeps only mandatory and optional and says DCAT-AP 3.0.1 uses "recommended" only in parts. Our `Obligation` still has three levels; keep them, and make the mapping to severity configurable.
- **T5 — Shapes assume every resource is in scope.** Both HVD and HealthDCAT-AP say so and call conditional validation future work. Variant shapes (S20) inherit this limit unless we target by a marker value.
- **Open**: I could not read the papers behind mobilityDCAT-AP and HealthDCAT-AP. Their method sections may contain a decision rule or an evaluation I have not captured (section 10).

---

## 9. Observations on the bibliography (for the author to check; I changed nothing)

1. `semicreuse2026`: the bib comment says the page shows no version or date. The repository source carries `publishDate: "2026-06-17"` in the ReSpec configuration, the README names "v1.0.0", and lists a webinar on 21/04/2026. Independently, the reference list of mobilityDCAT-AP 3.0.0 cites it as "DCAT-AP Reuse Guidelines. SEMIC. 17 June 2026." I could not see how the page itself renders.
2. `w3cdcatucr`: the counts given here (51 use cases, 68 requirements) are from the Editor's Draft of 10 January 2019 in the repository, not from the Note of 17 January 2019.
3. `mobilitydcatspec`: 1.1.0 is confirmed as "NAPCORE Recommendation 17 January 2025" extending DCAT-AP 2.0.1. A version 3.0.0 dated 19/10/2026 now exists, extends DCAT-AP 3.0.1 and cites the SEMIC reuse guidelines.
4. `derycke2025healthdcat` / `healthdataeu2024d62`: the GitHub page of HealthDCAT-AP was decommissioned on 22-09-2025; the repository README points to a "Release 5" on `healthdataeu.pages.code.europa.eu`. A 2026 secondary source mentions a "Release 7"; verify.
5. `semicdcatap`, `geodcatap10`, `statdcatap`: titles and dates in the bib match the documents I read (2024-06-14; 2015-12-23; 2016-12-15).
6. `scrocca2025mobilitydcat`: an arXiv version exists (2503.11535) and, by a search summary, a Zenodo copy; relevant only if an open-access pointer is wanted.

---

## 10. Not found, or seen only second-hand

| Key | State | What I tried |
|---|---|---|
| `healthdataeu2024d62` | **not read** | `zenodo.org` and `doi.org` blocked; search returned context only. The pilot HTML specification names the deliverable |
| `coyle2009dcap` | second-hand (medium) | `dublincore.org` blocked (curl and WebFetch); not in `dcmi/repository`; about twenty guessed DCMI repository names were not accessible; several searches |
| `scrocca2025mobilitydcat` | second-hand (medium) | arXiv, Springer, Zenodo blocked; several searches. Specification, wiki and repositories read in full |
| `scrocca2022napdcat` | second-hand (medium) | `ceur-ws.org` blocked; several searches |
| `bures2022napcore` | second-hand (medium) | `napcore.eu` blocked; several searches |
| `derycke2025healthdcat` | second-hand (medium) | `ceur-ws.org` and OpenReview not reachable; several searches. Pilot specification read in full |
| `dragan2019maintenance` | second-hand (medium) | Joinup PDF blocked; two searches; cross-checked against primary texts that describe the same policy |
| `perego2016jrc` | second-hand for the paper (medium) | `w3.org` blocked; one search; the DCAT-AP-JRC specification that cites it read in full |
| `w3cdatacube` | development repository read; Recommendation text not read | `w3.org` blocked; one search |
| `wilkinson2016fair`, `gregory2020search`, `koesten2020reuse`, `chapman2020search` | abstracts and secondary summaries only | publisher sites blocked; one or two searches each; the Koesten repository holds only a README and model code |

---

## 11. Sources

**Read in full (repository paths as in section 2).**
- https://github.com/SEMICeu/DCAT-AP-reuse-guidelines
- https://github.com/SEMICeu/DCAT-AP (releases 2.0.1, 3.0.0, 3.0.0-hvd, 3.0.1; submission guidelines) and its wiki
- https://github.com/SEMICeu/Governance
- https://github.com/SEMICeu/GeoDCAT-AP (releases 1.0.0, 3.0.0; vocabulary 930)
- https://raw.githubusercontent.com/SEMICeu/StatDCAT-AP/12a2424312f615e31ee3f7db881f5f564851551f/Release%201.0/statdcat-ap_version_1.0.0_0.pdf
- https://github.com/mobilityDCAT-AP/mobilityDCAT-AP (branches `main`, `gh-pages`), its wiki, and https://github.com/mobilityDCAT-AP/validation
- https://github.com/healthdcat-ap/healthdcat-ap.github.io (`OldContent/index.html`)
- https://github.com/w3c/dxwg (`ucr/static/index.html`; branch `rec-snapshot-2024`, `dcat/publication-snapshots/REC/Overview.html`)
- https://github.com/dcmi/repository (Singapore Framework copy; Description Set Profile draft)
- https://github.com/UKGovLD/publishing-statistical-data
- https://github.com/ec-jrc/dcat-ap-jrc (`docs/1.0/index.html`)
- https://github.com/laurakoesten/Dataset-Reuse-Indicators (README only)

**Seen only through search summaries (not opened).**
- https://arxiv.org/abs/2503.11535 · https://link.springer.com/chapter/10.1007/978-3-031-94578-6_13
- https://ceur-ws.org/Vol-3235/paper22.pdf
- https://napcore.eu/wp-content/uploads/2022/08/NAPCORE-4.4.2.1-Requirement-analysis_v1.0.pdf · https://napcore.eu/wp-content/uploads/2022/08/NAPCORE-4.4.2.2-Approach-towards-napDCAT-AP-specification_v1.0-Report.pdf
- https://ceur-ws.org/Vol-4064/NXDG25-paper5.pdf · https://openreview.net/forum?id=ZYvyYQlHQB
- https://www.dublincore.org/specifications/dublin-core/profile-guidelines/
- https://interoperable-europe.ec.europa.eu/collection/semic-support-centre/solution/dcat-application-profile-data-portals-europe/document/report-maintenance-dcat-ap-july-2019
- https://www.w3.org/2016/11/sdsvoc/SDSVoc16_paper_27
- https://www.go-fair.org/fair-principles/ · https://www.cell.com/patterns/fulltext/S2666-3899(20)30184-7 · https://arxiv.org/abs/1801.04971 · https://arxiv.org/abs/1901.00735
