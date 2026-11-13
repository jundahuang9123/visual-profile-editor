# G2 — Requirements engineering (classical, LLM/agent-based, ontology requirements)

Research note for the **requirement-based-dcat-profile-extensioner**. Written 13 November 2026.
Bibliography keys covered (14): `alharbi2027idea2`, `alharbi2026cq`, `ataei2025elicitron`, `zadenoori2025slr`, `bandi2026agents`, `suarez2009orsd`, `suarez2012neon`, `poveda2022lot`, `monfardini2023`, `iso29148`, `glinz2007nfr`, `sutcliffe2013unknown`, `gervasi2013tacit`, `davis2006elicitation`.

## 0. How to read this note

**Two voices, kept apart.** Every entry separates *(A) what the work did or prescribes* from *(B) how we could adapt it*. (B) is our design proposal. It is never a claim made by the cited work.

**Confidence labels.**

| Label | Meaning |
|---|---|
| high | Seen in a primary source during this task: an official code repository, an official template, or an author-published replication package |
| medium | From an abstract or a secondary summary (search-engine summaries of publisher, arXiv and author pages) |
| low / `verify:` | Not confirmed in this task. Listed in section 6 |

**Access limits that shape the confidence levels.** From this container only public GitHub clones and `raw.githubusercontent.com` work. arXiv, Springer, CEUR, MDPI, UPM's archive, Zenodo, figshare, ISO and IEEE were all refused by the network proxy, so I read **no paper full text**. What I did read in full:

| Local clone (untrusted reference data, read only) | Commit | Serves key |
|---|---|---|
| `/home/user/refs/KE-UniLiv__IDEA2` | `7dc5b7a` (2026-08-30) | `alharbi2027idea2` |
| `/home/user/refs/KE-UniLiv__askcq` | `fe1fb60` (2026-07-13) | `alharbi2026cq` |
| `/home/user/refs/oeg-upm__LOT-resources` | `fa0ef6b` (2025-06-20) | `poveda2022lot`, `suarez2009orsd` |
| `/home/user/refs/aminzadenoori__LLMs-and-Prompt-Engineering-in-RE---Systematic-Literature-Review` | `4e3846f` (2025-09-06) | `zadenoori2025slr` |
| `/home/user/refs/KE-UniLiv__animl-ontology` | `f6ce552` (2026-04-24) | supporting evidence for IDEA2's downstream use (not a bibliography entry) |
| `/home/user/refs/_single_files/microsoft-hve-core/*.md` | fetched 2026-11-13 | secondary source for `iso29148` (not a bibliography entry) |

Everything else comes from server-side web search, whose output is a summary, not the page. I therefore paraphrase those sources and never quote them.

**To raise the medium items to high**, these hosts need to be allowed in the session's network settings: `arxiv.org`, `link.springer.com`, `ceur-ws.org`, `www.mdpi.com`, `oa.upm.es`, `zenodo.org`, `figshare.com`, `ieeexplore.ieee.org`, `www.iso.org`.

## 1. Overview

| Key | Work | Found | What I actually saw | Depth |
|---|---|---|---|---|
| `alharbi2027idea2` | Collaborative human-AI workflow for ontology requirement engineering in use (ISWC 2026, In-Use) | yes, but **paper text not seen** | Full IDEA2 code repository; workflow figure; downstream AnIML repository; search summaries of the earlier workshop paper | deep (tool) |
| `alharbi2026cq` | Comparative study of CQ elicitation methods (ESWC 2026) | yes | Full AskCQ repository: dataset, prompts, analysis code, notebook outputs | deep |
| `poveda2022lot` | LOT framework (EAAI 2022) | yes | Official LOT-resources repository: website text, figure source, requirement templates | deep |
| `suarez2009orsd` | How to write and use the ORSD (OTM 2009) | yes | ORSD template as distributed by the same group; search summaries of the paper | deep (template), medium (guidelines) |
| `iso29148` | ISO/IEC/IEEE 29148:2018 | yes, paywalled | Secondary sources only | medium |
| `zadenoori2025slr` | LLMs for RE, systematic review (arXiv 2509.11446) | yes | Authors' replication workbook (all 74 studies, category definitions, counts) | deep (data) |
| `ataei2025elicitron` | Elicitron (JCISE 2025) | yes | Abstract-level summaries; no public code found | medium |
| `bandi2026agents` | AI agents for RE automation, systematic review (Automation 2026) | yes | Abstract-level summaries | brief |
| `suarez2012neon` | NeOn methodology chapter (2012) | yes | Summaries of the chapter and of companion NeOn papers | brief |
| `monfardini2023` | Use of CQs in ontology engineering, survey (ER 2023) | yes | Abstract-level summaries | brief |
| `glinz2007nfr` | On non-functional requirements (RE 2007) | yes | Abstract-level and secondary summaries | brief |
| `sutcliffe2013unknown` | Elicitation: towards the unknown unknowns (RE 2013) | yes | Abstract-level and secondary summaries | brief |
| `gervasi2013tacit` | Unpacking tacit knowledge for RE (2013) | yes | Abstract-level summaries | brief |
| `davis2006elicitation` | Effectiveness of elicitation techniques (RE 2006) | yes | Abstract-level summary | brief |

**Corrections to the leads I was given.**
- The IDEA2 repository cites the **workshop paper** (Watkiss-Leek et al., LLMs4KGOE at ESWC 2026, CEUR Vol-4246, arXiv 2604.01344), not the ISWC paper in the bibliography. The ISWC title appears on a co-author's GitHub profile as accepted at ISWC 2026. I assume, and could not confirm, that the ISWC paper reports the same workflow in use.
- The replication package of `zadenoori2025slr` titles the study a "Systematic Mapping Study"; the arXiv title in the bibliography says "Systematic Literature Review". Same authors, same 74 studies.
- `bandi2026agents` is narrower than "generative AI for RE": 24 of its 50 primary studies describe an agent architecture.
- No public Elicitron code was found. The pipeline description rests on the abstract and the publisher's summary.

## 2. Deep dives

### 2.1 `alharbi2027idea2` — IDEA2: expert-in-the-loop requirement elicitation

**Sources.** Repository `KE-UniLiv/IDEA2` (README, 20 Python modules, assets, workflow figure) — high. Workshop paper results — medium, from search summaries. ISWC paper text — not seen.

**(A) What the tool implements (read from the code).**

*Sequence of model output, expert feedback and refinement.*

1. **Inputs.** Requirement specifications: user stories and personas (Markdown), schema definitions (XSD/XML), or an existing CQ draft (CSV). Source: workflow figure, README.
2. **Extraction and filtration (iteration 1).** The prompt is assembled from named components: role, CQ definition, few-shot examples taken from other domains, instruction, a size limit ("Generate around 100 competency questions."), then the raw source. Output is requested as JSON (a list of strings). An optional filter embeds the questions with `all-mpnet-base-v2` and removes any whose cosine similarity to another exceeds 0.95.
3. **Publishing.** Each question becomes one row in a collaborative dashboard (a Notion database) with ID, text, Source, Iteration and a relation to a second table that stores the generation configuration (generation id, model, temperature, usage, role, prompt).
4. **Expert validation.** Domain experts upvote or downvote, comment, and set a priority. Score and vote count are computed fields. The rule is a simple majority.
5. **Pull.** Rejected questions (score ≤ 0, current iteration only) are pulled with their voters and comment threads. If no comment exists, a default instruction is inserted. Accepted ones are pulled too.
6. **Reformulation.** The prompt explains the evaluation (N experts, majority score), states that unlisted items were accepted and count as good examples, instructs the model to reformulate only the rejected ones and add nothing new, and passes the rejected items as JSON (text, id, hash, voters, score, votes, comments, iteration). The whole earlier chat history is prepended.
7. **Re-publishing.** Reformulations are new rows with iteration + 1, linked to their originals through a "Reformulates" relation. A "Recap" field tells the reviewer what the original was, what feedback it received, its score and its vote count.
8. **Loop** until a stopping criterion holds. The figure names four: x% of CQs accepted; max iteration reached; number of edits reached; expert time quota.
9. **Export.** JSON-LD with OWLUnit `CompetencyQuestion`, PROV-O (`wasGeneratedBy`, `wasAttributedTo` a SoftwareAgent, `generatedAtTime`), schema.org and Croissant; per item: text, SHA-256 hash, iteration, model, temperature.
10. **Metrics.** Accepted share per iteration, share of items each annotator answered, number of comments, negative-score statistics, pairwise Cohen's kappa and Krippendorff's alpha (nominal, items rated by all raters).

*Who decides what.*

| Actor | Decides |
|---|---|
| Ontology engineer | Triggers runs; chooses model, temperature and prompt components; supplies the project template |
| LLM | Drafts and reformulates. It never judges its own output in this tool |
| Domain experts | Accept or reject, comment, prioritise. They are the only acceptance authority |

*Observations from reading the code (mine, not the authors').*
- In the standard reformulation path, outputs are paired with rejected inputs **by position**. The stand-alone reformulation path instead makes the model echo `(ID n):` before each output. The second is the robust one.
- The README's "fine-tunes the LLM's generations" means accumulating chat history in context, not weight updates.
- The similarity filter deletes near-duplicates outright; nothing records what was dropped.

*Reported results (workshop paper, via search summaries — medium).* AnIML case: four domain experts from the industry partner; 103 initially generated CQs; three iterations; 102 accepted from 110 review events, a cumulative acceptance of 92.7%. Cultural-heritage case: a reformulation test on 23 CQs previously rejected in the AskCQ study, with 69.6% accepted at first review and 85.7% of the remaining seven in the next round. Agreement reported as Gwet's AC1 0.884 and PABAK 0.797. Two repository facts agree with this: `animl-ontology/requirements/cqs.txt` has 102 lines, and the IDEA2 assets hold 23 reformulation records.

*Downstream use (AnIML ontology repository — high, not a bibliography entry).* The 102 validated questions each have one SPARQL query (`testing/verified_positives/<n>.rq`, header `# CQ-<n>: …`). Negative requirements are SHACL shapes with paired `acceptable_data.ttl` and `unacceptable_data.ttl`.

**(B) Reuse.** Steps G2-S09, S11–S15, S17, S21, S22.

### 2.2 `alharbi2026cq` — comparative study of CQ elicitation methods (AskCQ)

**Sources.** Repository `KE-UniLiv/askcq` (dataset, prompts, modules, executed notebooks) — high. Abstract — medium.

**(A) What they did.**
- **Design.** One user story with two personas (cultural heritage: a donor loans items to a music museum). Five CQ sets from the same source: two ontology engineers working manually (44 and 54 CQs), manual instantiation of CQ patterns from Ren et al. 2014 (38), GPT-4.1 (26), Gemini 2.5 Pro (42). Total 204. Sets were anonymised for evaluation by three ontology-engineering experts.
- **Generation prompt.** Deliberately minimal: a one-sentence system role and one instruction, then the persona descriptions and the user story. No CQ definition, no target count, no desired properties, to avoid biasing the output. Temperature 0, top-p 1, penalties 0, seed 46.
- **Features measured.**

| Feature | How |
|---|---|
| Suitability | Three experts accept or reject; aggregated score −3…+3 |
| Ambiguity | Binary label derived from the experts' comments |
| Relevance | LLM rating on a 4-point scale against the user story, with rationale; three prompt variants tried on a subset first |
| Readability | Flesch-Kincaid grade, Dale-Chall and other indices |
| Complexity | Length; "requirement complexity" = count of ontological primitives an LLM extracts (concepts, properties, relationships, filters, cardinality hint, aggregation hint); linguistic and syntactic complexity via spaCy |
| Semantic overlap | Sentence-BERT embeddings; coverage and novelty between sets at threshold 0.75 |

- **Results stored in the repository's executed notebooks** (these may differ in rounding or definition from the paper's tables).

| Set | n | Accepted (score > 0) | Fleiss' kappa |
|---|---|---|---|
| Human annotator 1 | 44 | 90.9% | 0.23 |
| Human annotator 2 | 54 | 98.1% | 0.32 |
| Pattern | 38 | 50.0% | 0.23 |
| GPT-4.1 | 26 | 84.6% | 0.09 |
| Gemini 2.5 Pro | 42 | 66.7% | 0.27 |
| All | 204 | 79.4% (162 of 204; my count from the dataset) | 0.35 |

- **Overlap between methods is small.** Bidirectional coverage between any two sets ranges from 0% to 15.3%. Even the two human engineers cover only 11–21% of each other's questions.
- **Correlates of the expert score** (notebook output): filters −0.29, requirement complexity −0.27, Dale-Chall −0.25, ambiguity −0.23. A random-forest regression on all features explains little (R² 0.11).
- **The LLM relevance rating is unstable.** Stored outputs for the same eight questions change with model version and prompt variant (one question moves from 1 to 4).
- **Abstract-level conclusion (medium).** LLMs can produce a first set of CQs, the output depends on the model, and it generally needs a refinement step.

**(B) Reuse.** Steps G2-S08, S10, S11, S16, S21. Two design consequences: a single LLM run is not a complete elicitation, and compound, filter-laden requirements are accepted less often, which supports working on atoms.

### 2.3 `poveda2022lot` — LOT

**Sources.** `oeg-upm/LOT-resources`: website text, draw.io source of the methodology figures, templates — high.

**(A) What LOT prescribes.** Four activities: requirements specification, implementation, publication, maintenance.

*Requirements specification, recovered from the figure's connectors.*

| Step | Output artefact | Next |
|---|---|---|
| Use case specification | Use cases | Purpose and scope identification |
| Data exchange identification | Data documentation and examples | Purpose and scope identification |
| Purpose and scope identification | Ontology purpose and scope | Requirements proposal |
| Functional requirements proposal | Requirements (early stage) | Requirements completion |
| Functional requirements completion | Requirements (verified) | ORSD formalization |
| ORSD formalization | ORSD | Implementation (the figure also links this step to ontology reuse) |
| Requirements formalization (optional) | Test suite | — |

Domain experts and users validate, with the development team, that requirements are correct and complete. Actors in the figure: ontology developers, users, experts.

*Requirement list template* (spreadsheet header row): Identifier (domain+id); Domain (or Sprint, in the use-case variant); Competency question or natural-language sentence (fact); Answer; Status (Proposed, Accepted, Rejected, Pending, Deprecated); Superseded by; Comments; Extracted from (provenance); Priority (High, Medium, Low).

*Implementation* runs in sprints over prioritised requirements: conceptualization, ontology reuse, encoding, evaluation. For reuse, terms and their synonyms are extracted from the requirements or the data and used to search for existing ontologies. *Publication*: documentation, then online publication. *Maintenance*: bugs and new requirements feed back into the proposal step.

The site links supporting tools: Chowlk, OOPS!, Themis, Widoco, OnToology, AR2DTool, and the CORAL corpus of requirements annotated with lexico-syntactic patterns.

**(B) Reuse.** Steps G2-S01, S06, S17, S25.

### 2.4 `suarez2009orsd` — the Ontology Requirements Specification Document

**Sources.** ORSD template (LaTeX and Word) in LOT-resources, from the same research group — high for the fields. Paper guidelines — medium.

**(A) Template fields.**

| # | Slot | Note |
|---|---|---|
| 1 | Purpose | |
| 2 | Scope | |
| 3 | Implementation language | optional |
| 4 | Intended end-users | optional |
| 5 | Intended uses | |
| 6a | Non-functional requirements | |
| 6b | Functional requirements | groups of competency questions or sentences |
| 7 | Pre-glossary of terms | optional: terms from CQs with frequency; terms from answers with frequency; objects |

*Guidelines (medium).* A task sequence: identify purpose, scope and implementation language; intended end-users; intended uses; requirements; group requirements; validate the set; prioritise; extract terminology. CQs can be found top-down (decompose complex questions), bottom-up (compose simple ones) or middle-out. Grouping can use card sorting. Validation looks for conflicts, missing CQs and contradictions, is done by users and domain experts, and uses criteria that include correctness, completeness and verifiability.

**(B) Reuse.** Steps G2-S03, S05, S06.

### 2.5 `iso29148` — ISO/IEC/IEEE 29148:2018

**Sources.** Secondary only (a Microsoft requirements-authoring reference that names the characteristics by clause, Wikipedia, practitioner explainers, papers that apply the standard) — medium. The standard itself is paywalled and was not seen.

**(A) What it prescribes.**
- **Nine characteristics of an individual requirement** (clause 5.2.5): necessary, appropriate, unambiguous, complete, singular, feasible, verifiable, correct, conforming.
- **Characteristics of a set of requirements**: complete, consistent, feasible, comprehensible, and able to be validated. The first four are listed in several secondary sources; the fifth rests on one explainer.
- **Requirement language criteria**: avoid superlatives, subjective language, vague pronouns, ambiguous adverbs and adjectives, open-ended non-verifiable terms, comparative phrases, loopholes, incomplete references, negative statements.
- **Requirement construct**: condition, subject, action, object, constraint; "shall" marks a binding requirement.
- **Attributes**: unique identification, rationale, priority, difficulty, traceability (partially confirmed).

**(B) Reuse.** Steps G2-S02, S03. The nine names are the right vocabulary for the workbench's atom-quality panel because reviewers can look them up.

### 2.6 `zadenoori2025slr` — LLMs for requirements engineering

**Sources.** Replication workbook, 23 sheets — high. Paper-level statements — medium.

**(A) What the review establishes.** 74 primary studies; in the workbook 22 are from 2023 and 52 from 2024.

*Prompting strategies (authors' own count cells, multi-label, n = 74).*

| Strategy | Studies |
|---|---|
| Zero-shot | 28 |
| Few-shot | 20 |
| Reasoning and task decomposition | 16 |
| Context-rich | 15 |
| Template-based | 13 |
| Iterative | 11 |
| RAG-driven | 4 |
| Interactive | 3 |

*RE tasks (my tally of the workbook's 74 rows, multi-label).* Validation 16; elicitation 15; other software-engineering tasks 12; modelling 9; classification 8; tracing 5; defect detection 4; documentation 4; legal analysis 3; terminology extraction 1; retrieval 1.

*Evaluation.* Laboratory experiments 56; judgment studies 10; field studies 5; experimental simulations 3. Output analysis: quantitative 32; mixed 30; qualitative 12.

*Models (authors' count cells).* "Giant" models 53 mentions, against 41 for all smaller classes together.

*Paper-level statements (medium).* The field has shifted toward elicitation and validation and away from defect detection and classification. About 15% of studies cite prompting guidelines and about half share code or data.

*Caveat.* A few rows of the public workbook look misaligned between columns (a prompt description that does not match its title). I rely on the category definitions and counts, not on per-study details.

*Pointer found in the workbook.* One recorded study prompts an LLM to classify requirements against ISO 29148 quality characteristics, with explanations and improvement suggestions (Lubos et al., RE@Next! 2024).

**(B) Reuse.** Step G2-S23. The planned engine combines the four least-used strategies in this literature: retrieval, typed templates, an iterative repair loop and human interaction.

### 2.7 `ataei2025elicitron` — agent-based simulation for elicitation

**Sources.** Abstract and publisher summary via search — medium. No code repository found.

**(A) Pipeline.**
1. Generate LLM user agents within a design context, either serially in one context or in parallel, with diversity sampling.
2. Each agent simulates using the product and records steps as Action, Observation, Challenge.
3. Interview the agents to surface needs.
4. An LLM classifies needs as latent using supplied criteria and chain-of-thought, then a report is produced.

*Reported.* Context-aware generation increases the diversity of needs; more latent needs than a human empathic-lead-user interview baseline; criteria plus chain-of-thought gave the best latent-need classification. Model: GPT-4-Turbo.

**(B) Reuse.** Step G2-S20, as an optional gap probe whose output is never evidence.

## 3. Brief notes

**`bandi2026agents`.** Systematic review of 50 primary studies (2020–2026) on generative AI for RE, of which 24 describe an agent architecture, single or multi-agent with roles (6 from 2024, 11 from 2025, 7 from 2026). Studies are mapped to SWEBOK V4.0a requirements activities, with tracing treated as a practical consideration. Research questions cover architectures, challenges and research needs. Conclusion: the field is at an early stage. Detailed counts per activity were not retrievable. → G2-S24.

**`suarez2012neon`.** NeOn replaces a single workflow with nine scenarios: (1) specification to implementation; (2) reusing and re-engineering non-ontological resources; (3) reusing ontological resources; (4) reusing and re-engineering them; (5) reusing and merging; (6) reusing, merging and re-engineering; (7) reusing ontology design patterns; (8) restructuring (modularise, prune, extend, specialise); (9) localising. Companion papers describe the framework as a glossary of processes and activities, the scenarios, two life-cycle models and prescriptive guidelines. Reuse guidance names search, assessment, comparison, selection and integration. → G2-S07.

**`monfardini2023`.** Survey of 63 ontology engineers on how they use competency questions. CQs mainly help define scope and evaluate the conceptualization. Guidance is limited, so engineers have difficulty writing, using and managing CQs. Data are on figshare (not accessed). → supports G2-S01 and G2-S16: an atom should work as a scope boundary and as an evaluation unit, and needs management support.

**`glinz2007nfr`.** Identifies definition, classification and representation problems with the term "non-functional requirement". Proposes a concern-based taxonomy: functional requirements, performance requirements, specific quality requirements, constraints. Defines a non-functional requirement as an attribute of or a constraint on a system, and stresses that classification should not depend on how a requirement happens to be written. → G2-S04.

**`sutcliffe2013unknown`.** Surveys elicitation techniques through known knowns, known unknowns, unknown knowns and unknown unknowns; finds techniques relatively mature; proposes a roadmap for tacit-knowledge problems. Secondary sources: scenarios and prototypes ground conversations, observation helps articulate tacit knowledge. → G2-S19.

**`gervasi2013tacit`.** Reviews how several disciplines view tacit knowledge, proposes a conceptual framework for RE, and lists research challenges. Working definition: knowledge not accessible to anyone but the actor who holds it. → G2-S19.

**`davis2006elicitation`.** Systematic review of empirical studies. Abstract-level results: interviews, preferably structured, are among the most effective techniques; card sorting, ranking and thinking aloud tend to be less effective; analyst experience does not appear relevant; intermediate representations showed no significant positive effect. The authors caution that the underlying studies were not replicated. → G2-S18.

## 4. Reusable key steps

Twenty-five steps. "They did" is the source's content. "We" is our adaptation.

### Intake

**G2-S01 — Requirement atom register with LOT fields and a status lifecycle** · stage `atom_intake` · from `poveda2022lot`, `monfardini2023` · confidence **high**
- *They did.* LOT's requirement template has columns Identifier; Domain or Sprint; CQ or sentence; Answer; Status (Proposed, Accepted, Rejected, Pending, Deprecated); Superseded by; Comments; Extracted from (provenance); Priority. The CQ survey reports that engineers have difficulty writing, using and managing competency questions (medium).
- *We.* `RequirementAtom` = id, group, statement, subject, modality, optional example answer, status, `superseded_by`, comments, source reference (document, locator, quote), priority. Only `accepted` atoms may be cited as coverage. Splitting or rewriting never edits in place: the old atom is deprecated and points to its successor, so coverage links stay auditable.
- *Evidence.* `oeg-upm__LOT-resources/templates for requirements specification/Template for domain requirements.xlsx`, header cell "Status (Proposed, Accepted, Rejected, Pending, Deprecated)".

**G2-S02 — Atom well-formedness gate** · stage `atom_intake` · from `iso29148`, `zadenoori2025slr` · confidence **medium**
- *They did.* 29148 names nine characteristics of an individual requirement and language criteria against vague wording. The review's dataset records a study that has an LLM assess requirements against 29148 characteristics with explanations and suggested improvements.
- *We.* Two layers. Deterministic: singular (one subject, one modality, no coordinated obligations), conforming (template fields present, modality from a controlled list), complete (subject, modality, object, source reference), term-free (no CURIEs or IRIs — our own atom rule), vague-term lexicon. LLM rubric: 0–3 with a one-sentence rationale for necessary, unambiguous, verifiable, appropriate. Failing singular, unambiguous or verifiable blocks the atom from Propose until a human splits, rewrites or overrides with a reason. Suggested rewrites create a new atom version, never a silent edit.
- *Evidence.* `microsoft/hve-core` reference file: it "names the nine ISO/IEC/IEEE 29148:2018 section 5.2.5 individual-requirement characteristics". Workbook row `Lubos2024-pw`.

**G2-S04 — Requirement-kind routing** · stage `atom_intake` · from `glinz2007nfr` · confidence **medium**
- *They did.* Concern-based taxonomy: functional, performance, specific quality, constraint. Classification must not depend on representation.
- *We.* Atom `kind` with a profile-specific mapping (our design): *content* (what must be describable → class or property changes), *constraint* (obligation, cardinality, range, value set → constraint modifications), *quality of the profile* (labels, IRIs, documentation → profile-level checks, not term proposals), *out of scope*. Only content and constraint atoms go to Retrieve and Propose. Kind is assigned on the normalised intent, with the classifier's rationale stored.
- *Evidence.* Search summaries of the RE 2007 paper (author-hosted PDF at `files.ifi.uzh.ch/rerg/amadeus/publications/papers/RE07_Glinz.pdf`, not fetched).

**G2-S05 — Extension brief modelled on the ORSD** · stage `atom_intake` · from `suarez2009orsd`, `poveda2022lot`, `suarez2012neon` · confidence **high** (fields), medium (task list)
- *They did.* ORSD slots: purpose; scope; implementation language; intended end-users; intended uses; non-functional and functional requirements (grouped); pre-glossary of terms. In NeOn and in LOT the ORSD is the output of the requirements specification activity and the input to reuse and implementation.
- *We.* `ExtensionBrief`, created before any LLM call: purpose; scope (base profile and version, classes in and out of scope); target languages (LinkML, SHACL, DSV); intended users and uses; non-functional requirements for the extension (namespace policy, naming conventions, reuse policy); grouped atoms; pre-glossary. It is the first workbench page, is prepended to every prompt, and is exported with the change set as its human-readable specification.
- *Evidence.* `oeg-upm__LOT-resources/templates for ORSD/orsd-template.tex`, row "Functional  Requirements: : Lists or tables of requirements written as Competency Questions and sentences".

**G2-S20 — Simulated stakeholder walk-throughs to find missing atoms** · stage `atom_intake` · from `ataei2025elicitron` · confidence **medium**
- *They did.* Diverse simulated user agents log Action, Observation, Challenge while using a product; interviews and criteria-based classification surface latent needs.
- *We.* Optional gap probe, off by default. Generate a small diverse set of catalogue stakeholders (publisher, portal operator, data consumer, steward, domain specialist) in one serial call. Each walks through tasks against the draft extension (describe, find, assess, access, cite) and logs challenges. Challenges become *candidate* atoms with origin `synthetic` and no source reference. They cannot be cited as coverage until a human attaches a real source or accepts them explicitly.
- *Evidence.* arXiv 2404.16045 abstract and the Autodesk Research publication page, via search summary.

### Retrieve and propose

**G2-S06 — Pre-glossary terms with synonyms as retrieval queries** · stage `retrieve` · from `suarez2009orsd`, `poveda2022lot` · confidence **high**
- *They did.* The ORSD pre-glossary lists terms from CQs and answers with frequencies. LOT's reuse activity extracts terms and synonyms from requirements and searches for existing ontologies with them.
- *We.* Per atom, extract candidate terms (noun phrases → concept candidates; verbal and prepositional phrases → relation or attribute candidates), add synonyms, and use them as the top-k queries against the vocabulary index. Keep `term → atom ids` and frequency. A glossary panel lets the human fix a term-to-concept binding once for all atoms.
- *Evidence.* LOT website text: "These terms will be used during the ontology search with the aim of looking for existing ontologies that best fit them."

**G2-S07 — Reuse decision ladder from the NeOn scenarios** · stage `propose` · from `suarez2012neon` · confidence **medium**
- *They did.* Nine scenarios, including reuse as-is, reuse with re-engineering, pattern reuse and restructuring by specialising; reuse activities search, assess, compare, select, integrate.
- *We.* Each ProfileChange carries `reuse_path`: `covered_by_base`, `specialise_base`, `reuse_external_term`, `reuse_extension_pattern` or `mint_new`, plus a `reuse_assessment` list (candidate, source vocabulary, fit, decision, reason). Verify rejects `mint_new` unless at least one retrieved candidate was assessed and rejected with a reason.
- *Evidence.* Search summaries of the 2012 chapter and of the companion paper at `oa.upm.es/72421`.

**G2-S08 — Extract the needed modelling primitives per atom before proposing** · stage `propose` · from `alharbi2026cq` · confidence **high**
- *They did.* An LLM extracts, per question, the minimal concepts, properties, relationships, filters, cardinality hint and aggregation hint, with a rationale, into a typed schema; the count is the complexity score. Higher counts correlate with lower expert scores.
- *We.* A `NeedAnalysis` call per atom: concepts, attributes, relations, value constraints, cardinality hint, rationale. Three uses: retrieval queries; a completeness checklist for Verify (each primitive is accounted for by a change or by an existing base element); an atomicity signal (a high count flags "probably not atomic, split").
- *Evidence.* `KE-UniLiv__askcq/askcq/prompts.py`: "Focus on the *minimal* set of primitives essential to fulfill the requirement expressed in the question."

**G2-S09 — Modular, versioned prompt components with a stored generation configuration** · stage `propose` · from `alharbi2027idea2` · confidence **high**
- *They did.* Prompts are built from named components selectable at run time; output is schema-constrained JSON; each run's model, temperature, role and prompt are stored in a configuration table that every generated item links to.
- *We.* `PromptSpec` = ordered, content-hashed components (role, task definition, ProfileChange schema, examples, instruction, brief, retrieved candidates, atom payload). `GenerationConfig` = provider, model, temperature, seed, component hashes. Every ProfileChange and every repair stores its `generation_config_id`. The workbench shows the exact prompt behind each decision.
- *Evidence.* `KE-UniLiv__IDEA2/idea2/schema2cq.py` (`PromptBuilder`), `idea2/notion_utils.py` (`llm_setup_to_notion`); README: "Saving of LLM configurations (provenance information, such as temperature, model and role)".

**G2-S10 — More than one proposer; drafts always go through refinement** · stage `propose` · from `alharbi2026cq` · confidence **high**
- *They did.* Five sets from one source differ in acceptance (50% to 98%) and barely overlap (0–15% bidirectional coverage). Abstract: LLM output depends on the model and needs refinement. Runs used temperature 0 and a fixed seed.
- *We.* Propose accepts several proposer configurations (different providers or models, optionally a rule-based proposer for routine cases). Proposals are unioned, deduplicated and labelled with their proposer. None skips Verify and human review. Default temperature 0 and a fixed seed where the provider allows. The evaluation reports acceptance per proposer.
- *Evidence.* `KE-UniLiv__askcq/askcq/overview.ipynb` and `cq_embeddings.ipynb` stored outputs; README: "All LLMs were prompted with temperature=0, frequency_penalty=0, presence_penalty=0, and seed=46 to maximise reproducibility."

### Verify and repair

**G2-S03 — Requirement-set checks before proposing** · stage `verify` · from `iso29148`, `suarez2009orsd` · confidence **medium**
- *They did.* 29148 has set-level characteristics (complete, consistent, feasible, comprehensible, able to be validated). The ORSD guidelines include validating the set for conflicts, missing questions and contradictions with users and domain experts.
- *We.* One set-level report per atom set: near-duplicates (S11); contradictions (same subject and aspect with incompatible modality or cardinality — deterministic first, then an LLM pass); terminology consistency against the pre-glossary; a completeness question to the human, with the base profile's classes as a checklist. Each conflict is a blocking review item, since no ProfileChange can satisfy both atoms.
- *Evidence.* Search summaries of the standard and of the ORSD paper (`oa.upm.es/5474`).

**G2-S11 — Near-duplicate detection with two similarity bands** · stage `verify` · from `alharbi2027idea2`, `alharbi2026cq` · confidence **high**
- *They did.* IDEA2 drops generated questions above 0.95 cosine similarity. AskCQ treats 0.75 as the threshold for one question being covered by another set.
- *We.* One similarity service, three uses: atoms against atoms; proposed terms against each other; a proposed new term's label and definition against the base profile and the vocabulary index, to catch a minted duplicate of an existing term. Two bands: ≥ 0.95 → merge suggestion; 0.75–0.95 → "possibly covered", a reuse candidate the proposer must assess (S07). Flag and keep, never delete. Both thresholds are starting values to calibrate on our data.
- *Evidence.* `idea2/cq_measures.py`: `remove_similar_generated(similarity_matrix, cqs, threshold=0.95)`; AskCQ README: "Threshold $\tau=0.75$".

**G2-S13 — Repair prompt driven by structured feedback, scoped to rejected items, one-for-one by ID** · stage `repair` · from `alharbi2027idea2` · confidence **high**
- *They did.* The reformulation prompt explains the scoring, treats unlisted items as accepted examples, restricts the model to the rejected items, forbids new ones, and passes rejected items as JSON with votes and comments.
- *We.* `RepairRequest` = list of {change id, version, failed checks (rule id, message), reviewer feedback (reason code, comment), atom payloads, allowed edits}. Prompt rules: fix only the listed changes; exactly one output per change id; echo the id; create nothing new; accepted changes are in-context exemplars. The response is rejected if ids are missing, duplicated or new, which avoids positional pairing. At most three rounds, then the human queue with the full history.
- *Evidence.* `idea2/prompts.py`: "Only reformulate the rejected competency questions, do not extract new competency questions."

**G2-S14 — Explicit, configurable stopping criteria** · stage `repair` · from `alharbi2027idea2` · confidence **high**
- *They did.* Four named criteria end the loop: share accepted, maximum iterations, number of edits, expert time quota.
- *We.* `LoopPolicy` = max repair rounds (3), acceptance target, max edits per change, reviewer time budget. The engine records which criterion ended each loop. Unresolved items go to the review queue marked "unresolved after n rounds"; nothing is dropped.
- *Evidence.* `KE-UniLiv__IDEA2/assets/img/idea2_workflow.png`, box "Stopping Criteria".

### Human review

**G2-S12 — Review ledger: votes, score, comments and priority per item** · stage `hitl_review` · from `alharbi2027idea2` · confidence **high**
- *They did.* One dashboard row per item with voters for and against, computed score and vote count, priority, comment thread, link to the item it reformulates, and a recap of the original. Majority decides; score ≤ 0 means rework. Only domain experts accept.
- *We.* `ReviewLedger` per ProfileChange: reviewer, decision (accept, reject, needs change), reason code, comment, priority, timestamp, version reviewed. Decision rule is configurable: single reviewer, or panel majority with a tie counting as not accepted. Any LLM judge verdict is a separate advisory column and never a vote. A recap card shows what a revised change replaces and the earlier comments.
- *Evidence.* README: "Reformulation of a CQ takes place when any given CQ has a score of $<= 0$ on the Notion database."

**G2-S18 — Structured review checklist, not only a comment box** · stage `hitl_review` · from `davis2006elicitation` · confidence **medium**
- *They did.* Across empirical studies, structured interviews were among the most effective elicitation techniques.
- *We (by analogy).* A fixed question set per ProfileChange: Does it cover the cited atom? Is the reused term semantically right? Right class, domain and range? Is the cardinality justified by the atom's modality? Was a reuse alternative wrongly rejected? Answers are coded, with an optional comment, and reject reasons come from a codebook. Coded answers feed S13 directly and make reviewers comparable (S21).
- *Evidence.* Search summary of the RE 2006 abstract (DOI 10.1109/RE.2006.17).

**G2-S19 — Assumptions queue and example instances to surface tacit knowledge** · stage `hitl_review` · from `sutcliffe2013unknown`, `gervasi2013tacit` · confidence **medium**
- *They did.* Framed elicitation by what is known and unknown to each party; tacit knowledge is held but not articulated; prototypes and scenarios ground the conversation.
- *We (our design).* (1) Each ProfileChange lists `assumptions` — anything the LLM relied on that no atom states. Assumptions form their own review queue. (2) The workbench renders a small example record for each change so a domain reviewer reacts to something concrete. (3) Open issues are typed: question for stakeholders, unconfirmed assumption, out-of-scope discovery. (4) A list of base-profile areas no atom touches hints at what nobody asked about.
- *Evidence.* Search summaries of both works and of a 2023 experience report that builds its table on them (arXiv 2301.10211).

### Traceability and conformance

**G2-S15 — Version lineage and PROV-style export** · stage `traceability` · from `alharbi2027idea2` · confidence **high**
- *They did.* Reformulations link to originals; items are identified by content hash; export uses PROV-O with model, temperature and iteration per item.
- *We.* ProfileChange versions chain through `revises`. Each version has a content hash. The change set exports with PROV-O: each added or modified element `prov:wasDerivedFrom` its atoms, `prov:wasGeneratedBy` a propose or repair activity with its generation configuration, `prov:wasAttributedTo` the LLM agent and the approving human. The workbench shows a lineage timeline per element.
- *Evidence.* `idea2/cq_linkage.py` (`link_reformulations`); `idea2/exports.py` (context maps `CompetencyQuestion` to `owlunit:CompetencyQuestion` and declares the PROV namespace).

**G2-S16 — Four-level coverage rubric with a mandatory rationale on every atom–change link** · stage `traceability` · from `alharbi2026cq`, `monfardini2023` · confidence **high**
- *They did.* An LLM rates relevance to the source on four levels with a rationale: explicit; inferable; enabler only; extra and unnecessary. The CQ survey finds that practitioners use competency questions mainly to define scope and to evaluate the conceptualization (medium).
- *We.* Each `covers` link carries `coverage_level` and `why`: 4 = the atom explicitly demands this element; 3 = necessary to realise the atom though unstated; 2 = enabler only; 1 = not required. A change needs one link at level ≥ 3 to be eligible. Level-2-only changes need human confirmation. Level 1 is scope creep and is rejected. The proposer writes the rationale; an independent judge call re-rates; disagreements go to the human. The atoms × changes matrix is the final traceability artefact, and atoms without a level ≥ 3 link are reported as uncovered.
- *Caveat.* The same repository shows the rating shifting with model and prompt, so calibrate it and keep human spot checks.
- *Evidence.* `askcq/prompts.py`: "4 = The competency question addresses a requirement that is explicitly expressed in the user story."

**G2-S17 — One executable check per requirement, with paired acceptable and unacceptable data** · stage `conformance` · from `poveda2022lot`, `alharbi2027idea2` · confidence **high**
- *They did.* LOT has an optional step that formalises requirements into a test suite. The ontology built from IDEA2's requirements ships one query per question and, for constraints, a SHACL shape with an acceptable and an unacceptable data file.
- *We.* Compile emits, per accepted ProfileChange, a shape fragment, a minimal conforming instance and a minimal violating instance, each annotated with atom ids. Checks: the shape accepts the first and rejects the second, and the conforming instance also validates against the base DCAT-AP shapes. That makes "may tighten, never loosen" testable and each atom verifiable.
- *Evidence.* `KE-UniLiv__animl-ontology/README.md`: "A validation suite containing SPARQL queries mapped to the project's Competency Questions."; `testing/validated_negatives/1/` holds `1.ttl`, `acceptable_data.ttl`, `unacceptable_data.ttl`. The AnIML repository is not a bibliography entry.

### Evaluation and architecture

**G2-S21 — Agreement statistics when two or more reviewers judge the same items** · stage `evaluation` · from `alharbi2026cq`, `alharbi2027idea2` · confidence **high** (code), medium (AC1 and PABAK)
- *They did.* Fleiss' kappa for three annotators; pairwise Cohen's kappa and Krippendorff's alpha in the tool; the workshop paper reportedly adds Gwet's AC1 and PABAK.
- *We.* Compute Cohen or Fleiss kappa and Krippendorff's alpha over review decisions, plus AC1 and PABAK, because acceptance-heavy data depress kappa (AskCQ: 79% accepted, kappa 0.35). Report per run and per change type.
- *Evidence.* `askcq/agreement.py`; `overview.ipynb` output "Overall Fleiss' Kappa: 0.3539"; `idea2/notion_utils.py` (`calculate_kappa_from_csv`).

**G2-S22 — Process metrics per round** · stage `evaluation` · from `alharbi2027idea2` · confidence **high** (code), medium (numbers)
- *They did.* Accepted share per iteration, share of items each annotator answered, comment counts; the paper reportedly gives cumulative acceptance over review events.
- *We.* Log first-pass acceptance of ProfileChanges, acceptance after each repair round, review events per accepted change, comments per change, reviewer coverage, field-level human edits, time to decision.
- *Evidence.* `idea2/iteration_evaluation.py` (metric menu); search summary of arXiv 2604.01344.

**G2-S23 — Label each LLM call with the review's strategy categories, ablate, publish a replication package** · stage `evaluation` · from `zadenoori2025slr` · confidence **high** (counts and definitions)
- *They did.* Defined eight prompting-strategy categories and counted them over 74 studies; RAG-driven (4) and interactive (3) are the rarest; 56 of 74 evaluations are laboratory experiments.
- *We.* Tag every call: Retrieve = RAG-driven; Propose = template-based, context-rich, few-shot; Repair = iterative; workbench = interactive. Plan ablations that switch each off (no retrieval; free text instead of the typed record; no repair loop; no human feedback). Add a judgment study with two or three experts alongside the quantitative comparison. Ship prompts, configurations and data.
- *Evidence.* Replication workbook, sheet "Prompting strategies categoriza": "Using Retrieval-Augmented Generation techniques in prompts by incorporating retrieved external information or documents to provide the model with relevant context."

**G2-S24 — Role-scoped pipeline rather than free agent conversation** · stage `architecture` · from `bandi2026agents` · confidence **medium**
- *They did.* Classified agent-based RE systems as single-agent or role-based multi-agent, mapped them to RE activities, and judged the field early-stage.
- *We.* An architecture decision record: a fixed pipeline of narrow roles — retriever, proposer, deterministic verifier, repairer, optional judge — each mapped to one RE activity, with typed, stored messages between them. No role can accept its own output.
- *Evidence.* Search summary of `mdpi.com/2673-4052/7/5/169`.

**G2-S25 — LOT's activity flow as workbench phases, with a verified-atoms gate and a maintenance loop** · stage `architecture` · from `poveda2022lot` · confidence **high**
- *They did.* Requirements move from proposed to verified by domain experts before formalization; implementation proceeds in sprints over prioritised requirements; maintenance feeds bugs and new requirements back.
- *We.* Phases: Sources and scope → Atoms proposed → Atoms verified → Brief → Retrieve → Propose → Compile → Conformance and tests → Export. Propose consumes only verified atoms. Atoms are processed in priority-ordered batches so a reviewer never faces the whole set. A new atom or a reported defect opens a new change-set version; accepted elements are never mutated in place.
- *Evidence.* `oeg-upm__LOT-resources/figures/LOT-figures.drawio` connectors; website text: "The ontology development team builds the ontology iteratively, implementing only a certain number of requirements in each iteration."

## 5. Where the steps land in the planned engine

| Planned stage | Steps |
|---|---|
| Atoms (intake) | S01, S02, S04, S05, S20 |
| Retrieve | S06 |
| Propose | S07, S08, S09, S10 |
| Verify | S03, S11 |
| Repair | S13, S14 |
| Human review | S12, S18, S19 |
| Traceability | S15, S16 |
| Compile and conformance | S17 |
| Evaluation | S21, S22, S23 |
| Architecture | S24, S25 |

**What these works change in the plan.**
1. **Add a need-analysis call before Retrieve** (S08). The plan goes straight from atoms to retrieval.
2. **Give the "reuse before mint" rule a decision vocabulary and an assessment record** (S07).
3. **Make coverage a graded, justified link** (S16) rather than a bare list of atom ids.
4. **Emit a conforming and a violating instance per change** (S17), which turns the final conformance check into per-change tests.
5. **Type the repair request and enforce one-for-one ids** (S13). IDEA2's positional pairing is the failure mode to avoid.
6. **Treat LLM judgements as advisory.** In the best-documented tool the humans alone accept, and the AskCQ data show an LLM rating moving with model and prompt.

## 6. Not confirmed in this task

Each item is `verify:` before it is cited.

1. **`alharbi2027idea2`** — the ISWC 2026 paper's own content: case studies, numbers, lessons learned, and whether it describes exactly the repository's workflow.
2. **IDEA2 workshop figures** — 103 initial CQs, 102 accepted from 110 review events (92.7%), four experts, three iterations, 69.6% and 85.7% in the reformulation test, AC1 0.884, PABAK 0.797. All from search summaries.
3. **AskCQ** — whether the paper's tables match the repository notebook outputs used here.
4. **`iso29148`** — exact definitions and clause numbers; "able to be validated" as the fifth set characteristic; the full attribute list; the 2018 wording of the language criteria.
5. **`suarez2009orsd`** — exact wording and numbering of the tasks for intended uses and terminology extraction; the full list of validation criteria.
6. **`suarez2012neon`** — the exact title of scenario 3; whether the 2012 chapter itself uses the four-part description of the framework.
7. **`glinz2007nfr`** — the names of the classification facets (sources disagree) and the decision questions of the taxonomy.
8. **`sutcliffe2013unknown`** — the mapping of techniques to the four knowledge categories. **`gervasi2013tacit`** — the dimensions of the framework.
9. **`ataei2025elicitron`** — whether serial generation beats parallel; the latent-need criteria; precision and recall figures; the number of experiments (sources say two or three).
10. **`zadenoori2025slr`** — the percentages printed in the paper (a third-party summary gives 44% zero-shot and 29% few-shot; the workbook counts give 28 and 20 of 74).
11. **`bandi2026agents`** — distribution over RE activities; single- versus multi-agent counts; the listed challenges.
12. **`monfardini2023`** — detailed percentages (a slide deck gives 14.3% and 27%; not used here).
13. **`davis2006elicitation`** — a later review describes the interview finding as favouring unstructured interviews, which conflicts with the abstract's "preferably structured".
14. **CORAL corpus** (linked from the LOT site; not a bibliography entry) — reported as 834 annotated requirements and 29 lexico-syntactic patterns. It could support mapping requirement forms to modelling constructs, but I did not see it.

## 7. Sources

**Read in full (primary).**
- https://github.com/KE-UniLiv/IDEA2
- https://github.com/KE-UniLiv/askcq
- https://github.com/oeg-upm/LOT-resources
- https://github.com/aminzadenoori/LLMs-and-Prompt-Engineering-in-RE---Systematic-Literature-Review
- https://github.com/KE-UniLiv/animl-ontology
- https://raw.githubusercontent.com/elliottwl/elliottwl/main/README.md (lists the ISWC paper as accepted)

**Read in full (secondary).**
- https://github.com/microsoft/hve-core — `.github/skills/project-planning/requirements-author/references/_shared/iso-29148-quality-attrs.md` and `…/brd/iso-29148-quality-gate.md`

**Seen only through search summaries.**
- IDEA2 workshop paper: https://arxiv.org/abs/2604.01344 · https://ceur-ws.org/Vol-4246/llms4kgoe-8.pdf
- AskCQ paper: https://arxiv.org/abs/2507.02989 · https://link.springer.com/chapter/10.1007/978-3-032-25156-5_4
- Elicitron: https://arxiv.org/abs/2404.16045 · https://www.research.autodesk.com/publications/elicitron-llm-based-simulation-framework-design-requirements/ · https://doi.org/10.1115/1.4067388
- LLM4RE review: https://arxiv.org/abs/2509.11446 · https://zenodo.org/records/17068742
- Agents review: https://doi.org/10.3390/automation7050169 · https://www.mdpi.com/2673-4052/7/5/169
- ORSD: https://link.springer.com/chapter/10.1007/978-3-642-05151-7_16 · https://oa.upm.es/5474/1/INVE_MEM_2009_64393.pdf
- NeOn: https://link.springer.com/chapter/10.1007/978-3-642-24794-1_2 · https://oa.upm.es/72421/1/REV_JCR_37_C.pdf · https://oeg.fi.upm.es/index.php/en/methodologies/59-neon-methodology/index.html
- LOT paper: https://doi.org/10.1016/j.engappai.2022.104755 · https://oa.upm.es/78273/1/LatestMainPaper.pdf
- CQ survey: https://link.springer.com/chapter/10.1007/978-3-031-47262-6_3 · https://figshare.com/articles/dataset/Use_of_Competency_Questions_in_Ontology_Engineering_-_A_Survey/23280698
- ISO 29148: https://www.iso.org/standard/72089.html · https://standards.ieee.org/standard/29148-2018.html · https://en.wikipedia.org/wiki/Software_requirements_specification · https://www.modernrequirements.com/blogs/iso-29148-explained/ · https://arxiv.org/pdf/2408.10886 · https://arxiv.org/pdf/1611.08847
- Glinz: https://files.ifi.uzh.ch/rerg/amadeus/publications/papers/RE07_Glinz.pdf · https://www.researchgate.net/publication/4292007_On_Non-Functional_Requirements
- Sutcliffe and Sawyer: https://eprints.lancs.ac.uk/id/eprint/66712/ · https://www.semanticscholar.org/paper/622cc0cb9ca42605fec7b3cdc0bd71053bcec39b · https://arxiv.org/abs/2301.10211
- Gervasi et al.: https://link.springer.com/chapter/10.1007/978-3-642-34419-0_2
- Davis et al.: https://openalex.org/works/W2108410964 · https://ui.adsabs.harvard.edu/abs/2006icre.conf...28D/abstract
- CORAL: https://zenodo.org/records/4432491 · https://coralcorpus.linkeddata.es/

**Helper scripts written for this note** (read-only spreadsheet parsing): `/tmp/claude-0/-home-user-visual-profile-editor/b471f26b-782a-5ee3-bb4a-223b051d6027/scratchpad/rbdpe/work/g2/xlsx_dump.py`, `slr_tally.py`, `slr_rows.py`, `slr_cols.py` in the same directory.
