# G1 — Ontology generation, evaluation and schema/metadata extraction with LLMs

Research notes for the requirement-based-dcat-profile-extensioner (RBDPE).
Group: G1-ontology-generation. Date of research: 2026-11-13.
Bib keys covered: `lippolis2025ontology`, `fathallah2026rigor`, `zhang2024ontochat`, `lippolis2025oeassist`,
`lippolis2025bench4ke`, `mai2024adapt`, `sadruddin2025schema`, `busch2025dcat`.

## 0. How to read this report

Three kinds of statement are kept apart everywhere:

- **PAPER / REPO** — what the work did, taken from a source I opened in this task (official repository files, the
  authors' own slide decks stored in those repositories, or a search-engine summary of the abstract).
- **OBSERVATION (ours)** — something I measured or noticed myself in a released repository (a count, a tally, a code
  path). It is not a claim made by the authors.
- **ADAPTATION (ours)** — how RBDPE could reuse the idea. This is our design, not the paper's claim.

Confidence labels: **high** = seen in a primary source (official repository file, authors' slides, spec);
**medium** = from an abstract or a secondary summary returned by web search; **low** = not confirmed, text starts with "verify:".

### Access limits that shape the evidence

- `arxiv.org`, `ar5iv.labs.arxiv.org`, `export.arxiv.org`, `www.alphaxiv.org` and `huggingface.co` could not be fetched
  from this session (host not resolvable through the network policy; one attempt per host). Publisher pages were not tried
  beyond that. **I did not read the full text of any of the eight papers.**
- What I did read: ten public GitHub repositories (cloned, read only, never executed), two slide decks by the authors
  that are stored in those repositories, and web-search summaries.
- Consequence: numeric results printed in the papers' tables are **not** reproduced here unless I saw them in a
  repository file or in the authors' slides. Every number below names its source.

### Repositories read (all under `/home/user/refs/`)

| Bib key | Repository | Commit (date) | Licence seen |
|---|---|---|---|
| lippolis2025ontology | `dersuchendee/Onto-Generation` | 13d2e17 (2025-08-15) | README says MIT, no LICENSE file |
| lippolis2025ontology (Ontogenia prompt source) | `dersuchendee/Ontogenia` | 1038183 (2024-05-29) | README says MIT, no LICENSE file |
| lippolis2025ontology (CQbyCQ baseline prompt) | `LiUSemWeb/LLMs4OntologyDev-ESWC2024` | 3609cde | none seen |
| fathallah2026rigor | `NadeenAhmad/RIGOR` | 88c5820 (2026-11-06) | MIT |
| zhang2024ontochat | `King-s-Knowledge-Graph-Lab/OntoChat` | 737b7cc (2026-04-22) | MIT |
| lippolis2025oeassist | `dersuchendee/OE-Assist` | e0d2c16 (2025-11-06) | none seen |
| lippolis2025bench4ke | `fossr-project/ontogenia-cini` | e187fa4 (2026-08-25) | Apache-2.0 |
| mai2024adapt | `boschresearch/llm-vs-gibberish-ontologies` | da3e97a (2024-11-07) | AGPL-3.0 |
| sadruddin2025schema | `sciknoworg/schema-miner` | 13c47dc (2026-08-14) | MIT |
| busch2025dcat | `l94779589/Exploring-LLM-Capabilities-in-Extracting-DCAT-Compatible-Metadata-for-Data-Cataloging` | 3c6ceb7 (2025-01-16) | none seen |

Licence note for implementers: we reuse **ideas and steps**, not code. If prompt text or code is ever copied, the
AGPL-3.0 repository (mai2024adapt) and the three repositories without a licence need care.

---

## 1. Short answer: what this group gives RBDPE

1. A **concrete generate-validate-repair loop with provenance** that is already implemented and public
   (RIGOR, `app.py`): deterministic backbone first, three-source top-k retrieval, a generator that only emits deltas,
   an LLM judge with a severity-graded verdict, deterministic graph validation on "core + delta", at most three
   attempts with error-specific correction hints, element-level `prov:wasDerivedFrom`, fall-back to the backbone.
   This is the closest published analogue of our Retrieve → Propose → Verify → Repair engine.
2. **Two requirement-by-requirement prompting techniques** with full prompt text (Memoryless CQbyCQ, Ontogenia):
   one requirement per call, an "is it already answerable?" pre-check, a fixed decomposition procedure
   (subject / predicate / object / value), a list of common mistakes in the prompt footer, temperature and penalties at zero.
3. **A definition of "the requirement is covered" that can be executed**: a competency question is modelled if a SPARQL
   query extracting the answer can be written (OE-Assist), plus the empirical warning that wrong LLM suggestions
   reduce reviewer accuracy and two mitigations that we can build into the workbench.
4. **Human-in-the-loop protocols**: structured expert feedback in four rubric headings and/or a directly edited
   schema, re-injected into the next LLM round, with saved intermediate versions (schema-miner).
5. **Evaluation instruments**: four-view quality evaluation including the share of superfluous elements;
   threshold hit rate against a gold standard; verifier scored as a classifier on a set with explicit negatives;
   ablations that keep the deterministic backbone constant; counterbalanced assisted/unassisted user study;
   blind side-by-side expert rating.
6. **Leakage controls**: replacing terms by gibberish to test whether the model reasons or remembers
   (mai2024adapt), and shipping benchmarks in a password-protected archive (lippolis2025ontology).

---

## 2. Per-paper findings

### 2.1 fathallah2026rigor — Retrieval-Augmented Generation of Ontologies from Relational Databases (RIGOR)

Bib: arXiv:2506.01232v2, "Accepted at ISWC 2026". Official code: `https://github.com/NadeenAhmad/RIGOR`
(the repository's own BibTeX lists the same seven authors in the same order as the bib entry and the booktitle
"Proceedings of the International Semantic Web Conference (ISWC 2026)"). Depth: **deep** (pipeline code read).

**PAPER / REPO — the pipeline as implemented in `app.py` (high confidence)**

The module docstring states the design in seven points; the first two are
"FK-guided traversal with parent/reference tables processed before children" and
"Deterministic Direct Mapping is always merged first, guaranteeing schema coverage."
`run_semantic_enrichment()` then does:

1. Load and clean the schema (ETL columns with prefix `s_` dropped; date/time types corrected from column names).
2. Initialise a local embedding model (`all-MiniLM-L6-v2`, normalised embeddings, FAISS `IndexFlatIP`).
3. Index domain documents: character chunks of at most 1200 with 150 overlap, each prefixed with `[filename]`.
4. Index external ontologies: **one chunk per class and per property**, built as
   `[{filename}] Class: {name} IRI: {cls} — label: … — comment: …` (comment cut at 200 characters).
5. Load an optional seed core ontology.
6. Compute the traversal order (topological over foreign keys; cycles appended in sorted order).
7. For each table:
   - **A. Deterministic direct mapping** for the table is built with rdflib and merged into the core *before* any LLM call
     (table → class; non-FK column → datatype property; FK column → object property; universal restriction for every
     mapped property; existential restriction for primary-key, unique or not-null columns; `owl:hasKey`).
     Each generated element gets `rdfs:label`, `rdfs:comment` and `prov:wasDerivedFrom <…/provenance/{table}/{column}>`.
   - **B. Retrieval**: top-3 chunks from each of three indexes — the *current growing core ontology* (re-chunked every
     iteration, one chunk per class/property with label, comment, range), the documents, and the external ontologies.
     The query is the table name, its class name, its column names and its FK target tables concatenated.
   - **C. Generation / judging / validation loop**, at most `MAX_JUDGE_RETRIES + 1 = 3` attempts:
     - Gen-LLM (temperature 0.2) receives a prompt with bracketed sections `[DIRECT MAPPING FOR THIS TABLE]`,
       `[CLEANED DATABASE SCHEMA …]`, `[FOREIGN KEY CONSTRAINTS …]`, `[RETRIEVED DOCUMENTATION]`,
       `[RETRIEVED CURRENT CORE ONTOLOGY CONTEXT]`, `[RETRIEVED EXTERNAL ONTOLOGY HINTS]`,
       `[CORRECTION INSTRUCTIONS FROM PREVIOUS JUDGE PASS]`, `[MANDATORY TASKS]` (9 items), `[STRICT CONSTRAINTS]` (7 items), `[OUTPUT]`.
       The framing sentence is "Your role is semantic enrichment, not schema reconstruction."
       Output format: OWL 2 Manchester Syntax only.
     - Judge-LLM (temperature 0.1) receives direct mapping, delta, schema, FK constraints and core context, and 14
       criteria in three tiers (Critical 1–7, Important 8–12, Minor 13–14). It must answer in a fixed structure:
       `Decision: APPROVED | REJECTED | APPROVED_WITH_CORRECTIONS`, three issue lists by severity, and a
       `Corrected fragment` (full Manchester text) when the decision is not APPROVED.
     - `REJECTED` → the critical issues become the correction hint of the next generation attempt.
     - Otherwise the accepted text (the judge's corrected fragment if present, else the generator's delta) is parsed
       into an rdflib graph and **deterministically validated on a candidate graph = core + delta**, restricted to the
       tables processed so far. Errors (first 20) become the next correction hint
       ("Fix ALL of these structural errors").
     - If no attempt passes: "No valid semantic delta after retries; deterministic mapping retained".
   - Post-table validation of the core; an error raises.
8. Final deterministic validation over the whole schema (raises on error, prints warnings), then serialisation as
   OWL/XML with `prov:generatedAtTime` on the ontology.

Deterministic validation rules (`validate_graph_against_rigor`): no IRI typed both object and datatype property;
exactly one domain and one range per property; datatype-property ranges must be XSD; self-referential object
properties need an explicit "recursive"/"self" justification in a comment; every table has its class, every FK its
object property, every other column its datatype property (schema coverage); **warnings** for missing label, comment
or `prov:wasDerivedFrom`.

Judge criteria worth keeping verbatim in mind (both are "Critical"):
"The delta must not remove or contradict deterministic direct mapping coverage." and
"Required primary-key/not-null/unique existential restrictions must be preserved or strengthened."
Generator task 8: "Add external alignment using owl:equivalentClass, rdfs:subClassOf, or skos:exactMatch only when
supported by retrieved external ontology hints."

**PAPER / REPO — evaluation tooling (high confidence, from README and scripts)**

- Baselines: W3C-style direct mapping (`mapping.py`, no LLM); schema-only LLM baseline (`baseline.py`, no RAG, no judge);
  non-iterative single pass with RAG but without judge or growing core (`non-iterative.py`).
- Generators: Claude Opus 4.6, Mistral Small 24B, DeepSeek Chat via OpenRouter. Evaluation judge: GPT-5.4,
  "intentionally from a different model family than all three generators to eliminate self-evaluation bias" (README).
- Schemas: Chinook (music), a liver cancer registry, eICU-CRD.
- `eval.py`: seven LLM-judge dimensions scored 0–5 per ontology chunk (accuracy, completeness, conciseness,
  adaptability, clarity, consistency, domain enrichment); structural counts; semantic coverage of the schema
  (embedding match of table/column names against class/property names, threshold 0.55); rdflib parse validation.
- `ontology_checker.py`: HermiT consistency and the OOPS! pitfall scanner (REST API), results merged into the evaluation JSON.
- `run_ablation.py`: seven variants (`no_rag`, `only_schema_context`, `only_external_ontologies`,
  `only_relevant_documents`, and three `without_*`). Its docstring: "Ablations hide selected context sources from the
  Gen-LLM prompt, but do not remove the direct-mapping backbone."
- `expert_survey/survey.html` with `METHOD_KEY.json`: blind expert rating — four anonymised fragments (A–D =
  direct mapping, baseline, non-iterative, RIGOR) per table, 0–5 on seven dimensions, a ranking and optional comments, exported as JSON.
- `cqs.py`: five competency questions per table are generated by an LLM from the table schema (temperature 0.5), each with a short answer.

**From web search only (medium confidence)** — the arXiv abstract describes a Gen-LLM that produces
"provenance-annotated ontology fragments (delta ontologies)" validated and corrected "by an independent Judge-LLM";
a search summary of the HTML version says a delta is refined "by either a human expert or a Judge-LLM, followed by
deterministic graph validation". A search snippet attributes F1 of 0.73 (classes), 0.67 (relations) and 0.52
(attributes) on a "BURR-ISWC" benchmark to one version of the paper; I could not confirm these numbers in a primary source.

**OBSERVATIONS (ours, from the repository at 88c5820)**

- In `app.py` the in-loop generator and judge wrap the **same** OpenRouter client and model
  (`llm_client` is passed to both `OntologyLLM` and `JudgeLLM`); they differ in prompt and temperature. Independence
  by model family is implemented for the *evaluation* judge only. The paper text may describe this differently — verify before citing.
- The deterministic validator has **no check on alignment targets**: the rule "only when supported by retrieved
  hints" lives in the generator prompt and in a "Minor" judge criterion. (In the stored Chinook/Claude output the two
  `skos:exactMatch` targets I checked do occur in `external_ontologies/music.owl`, so I found no ungrounded alignment there.)
- The Manchester parser (`parse_restriction`) understands only `some` and `only`. Any other class expression after
  `SubClassOf:` falls through to `parse_prefixed_or_uri`, which turns the whole expression into a named IRI.
  In `output/generated_ontologies/rigor_chinook_claude_ontology.owl` I counted 62 distinct IRIs of this kind
  (pattern `_exactly_1_`, `_max_1_`, `_min_1_`), e.g. `#Genre_GenreId_exactly_1_xsd_integer` used as a superclass;
  the Chinook outputs of the two other generators contain 5 and 16 matching lines, the two other Claude outputs I
  checked (`rigor_eicu_crd_claude_ontology.owl`, `rigor_real_world_claude_ontology.owl`) none. The IRI form is exactly what the fall-through path of the current parser
  produces for an expression such as `Genre_GenreId exactly 1 xsd:integer`, so cardinality restrictions written by
  the LLM appear to have been silently mis-read. This is direct evidence for our decision to have the LLM fill a
  typed record and never write, or have parsed, concrete syntax.
- The evaluation CQs are LLM-generated from the schema itself, and the evaluation judge prompt contains the database
  schema. For our own evaluation we should use human-authored requirements and a human-made gold extension.
- `eval.py` ships with `ENABLE_CQ_JUDGE = False`.
- The README expands the acronym as "Retrieval-Augmented Iterative Generation of Ontologies with Refinement"; a
  search summary of the arXiv abstract gives "Retrieval-augmented Iterative Generation of RDB Ontologies". Use the paper's own wording.

### 2.2 lippolis2025ontology — Ontology Generation Using Large Language Models (ESWC 2025)

Official material: `https://github.com/dersuchendee/Onto-Generation` (prompts, dataset, generated ontologies, OOPS!
reports, expert assessments, ESWC slides). Ontogenia's procedure text: `https://github.com/dersuchendee/Ontogenia`.
Depth: **deep** (prompts and evaluation files read; paper text not read).

**PAPER / REPO (high confidence)**

- Input per task: a competency question (CQ) and an ontology story; output: OWL in Turtle.
  Two settings (slides): *independent* generation (one CQ + story → one OWL file) and *incremental* generation
  (all CQs of a story, looping until modelling is finished).
- **Memoryless CQbyCQ** (`PromptingTechniques/README.md`): derived from the earlier CQbyCQ technique, but
  "the {rdf} section, which refers to the previous interactions, is always empty" and the story carries no other
  CQs; "This causes a considerable reduction in the LLM's context." Per-CQ outputs are combined by a simple merge (slides).
  Prompt anatomy: task statement; definitions of classes, hierarchies, reification, properties and restrictions;
  the fixed prefixes; an instruction to state first whether the CQ is already answerable
  ("is this competency question answerable by the previous version of the RDF (given down) or not?"), with the hint
  that this is most likely not the case; the story; then enumerated lists of "possible mistakes that you might make"
  (general, class extraction, hierarchy, object properties, data properties); finally the previous RDF slot.
- **Ontogenia**: metacognitive prompting. Inputs: user story, one or more CQs, a nine-step procedure, a description
  of the expected ontology elements, and ontology design patterns passed as JSON `{name: pattern_owl}`.
  Procedure (`Ontogenia/data/procedure.txt`): (1) understand the CQ; (2) identify the context;
  (3) "Divide the competency question in subject, predicate, object and predicate nominative" and map subject/object
  to classes, predicate to an object property, predicate nominative to a datatype property;
  (4) subclass test ("is A an element of B?"); (5) restrictions (allValuesFrom / hasValue / someValuesFrom / minCardinality 0 or 1);
  (6) equivalence and disjointness; (7) add them; (8) "Confirm the final answer and explain the reasoning";
  (9) confidence evaluation and a test on instances. The grouped variant prepends the previous output ("memory").
  The older Ontogenia script also groups CQs thematically before generation and runs four trials
  (CQs only; + patterns; + procedure; all).
- Models (file names and README): GPT-4 (API version 1106), o1-preview, Llama 3.1 405B instruct.
  GPT-4 was run with "hyperparameters (frequency_penalty, presence_penalty, and temperature) set to zero", so that an
  already defined prefix, class or property can be reused without being penalised.
- Dataset (slides): 100 CQs, 29 user stories, gold-standard ontologies; 65 complex and 35 simple CQs; 7 domains.
  A search summary of the abstract speaks of "ten ontologies with 100 distinct CQs and 29 different user stories".
  The dataset is distributed zipped with a published password: "To prevent LLMs from including this dataset in their
  training data, it is zipped and locked with a publicly available password."
- Evaluation, four views (slides): OOPS! pitfall scan; CQ verification (share of modelled CQs, done manually by two
  ontology engineers); superfluous components (manual, two engineers); expert evaluation (two experts, Cohen's kappa 0.61).
  Slide takeaways: o1-preview yields the fewest pitfalls; the Llama model many pitfalls and almost 40% superfluous
  components; "Generally, ~30% of generated classes and properties were superfluous."; LLMs outperform novice
  ontology engineers and previous methods; weaknesses are OOPS! pitfalls and superfluous elements.
- Expert-found problem classes (slides) and which instrument detects them: missing labels/comments, taxonomy loops,
  multiple domains/ranges (OOPS!); unnecessary and duplicate classes/properties (superfluous-component analysis);
  CQs not properly modelled, poor axioms, bad taxonomy (CQ verification).
- Expert assessment sheets (`Experiment Results/Expert evaluation/*.xlsx`): per file, free comments of two experts, and
  per CQ a status (`ok`/`yes`, `maybe`, `no`) with the element that addresses the CQ.

**OBSERVATIONS (ours)**

- The Memoryless prompt tells the model to create properties as `owl:Property` and to prefix classes with `Cl_`.
  Both surface in the expert sheets as defects ("owl:Property -redefining OWL language?",
  "Why the strange naming of classes with a Cl_-prefix?"). Lessons for us: a non-existent vocabulary term in a prompt
  propagates into the artefact (hence a deterministic "term exists" check), and identifier conventions must be owned by the engine.
- The sheets also show duplicates and missing documentation for memoryless outputs ("Duplicate classes, such as
  Cl_FestivalOccurrence", "No labels or comments"): the price of a memoryless context is duplication, which RIGOR
  addresses by retrieving from the growing core.
- Precise per-model proportions of modelled CQs are in figures I could not extract; do not quote numbers from this report for them.

### 2.3 lippolis2025oeassist — Large Language Models Assisting Ontology Evaluation (ISWC 2025)

Official material: `https://github.com/dersuchendee/OE-Assist` (prompt, OntoEval dataset, LLM outputs, study tool,
participant responses, ISWC slides). Depth: **deep**.

**PAPER / REPO (high confidence)**

- Task: CQ verification — decide whether an ontology models a CQ, given an ontology story.
  Definition used in the prompt: "a competency question is modelled by an ontology if you could write a SPARQL query
  to extract the answer", under a closed-world assumption.
- Prompt (`prompts/eval-prompt.MD`): instructions; a worked example (one small ontology, one story, four CQs with
  answers, including a negative one); output contract: `**Yes**` plus a SPARQL query, or `**No**` plus a SPARQL query
  that extracts a *partial* answer. The same prompt served the automatic and the user experiment.
- Dataset OntoEval (slides): 1,393 CQs with ontology and story; 1,204 modelled; 33 domains. OntoEval-small: 20 complex
  CQs, 10 modelled, 6 domains.
- Automatic evaluation (slides): o1-preview, o3-mini, GPT-4o-0513; "Metric: macro-F1 on the full set and accuracy on
  the balanced set". The repository stores three runs for GPT-4o and o3-mini and one for o1-preview.
- User study (slides and `OE-Assist Tool/app.py`): 19 participants; 20 verification tasks, 10 with an LLM suggestion
  (label + SPARQL) and 10 without; order A-first/B-first selectable; answers Yes / No / I don't know plus a 1–5
  difficulty rating; a questionnaire after every 10 tasks.
- Findings (slides): perceived difficulty decreased with assistance; about a fifth of participants reported
  distraction; overall performance did not change significantly; no significant difference between o1-preview and
  the ontology engineers; "When using suggestions, if the LLM was incorrect the accuracy drops significantly (-28%)";
  "If the LLM suggestion was correct, there is a significant improvement (+13%)".
- Mitigations named on the slides: "pre-check suggested SPARQL against the actual ontology before showing the label"
  and "show a calibrated confidence or provenance for suggestions". Also: wording quality of the CQ and ontology
  documentation strongly affect outcomes.

**OBSERVATIONS (ours)**

- `OntoEval Dataset/OntoEval.csv` has 1,393 rows with `Annotations` = yes 1,203 / no 190 (the slides say 1,204 modelled).
  The set is strongly imbalanced, which explains the macro-F1 / balanced-accuracy choice.
- My tally of `Evaluation/OE-Assist OntologyEngineers responses.csv` (264 responses, 19 persons): correct decisions
  97/128 = 0.76 with suggestion and 99/136 = 0.73 without. This is my own count, consistent with "did not change significantly".
- A web summary mentions a Protégé plugin; the repository contains a Flask study application, not a plugin. Unverified.

### 2.4 zhang2024ontochat — OntoChat (ESWC 2024 Satellite Events)

Official code: `https://github.com/King-s-Knowledge-Graph-Lab/OntoChat`. Depth: **deep** for code; paper text not read.

**PAPER / REPO**

- Abstract via search (medium): a framework for requirement elicitation (user story creation, CQ extraction),
  analysis (CQ verification, reduction, clustering) and testing of preliminary ontology versions; evaluated by
  replicating the engineering of the Music Meta Ontology and with questionnaires (N = 6 music experts for the story
  part; N = 8 ontology engineers for clustering, per search summary).
- Code (high):
  - *CQ extraction prompt* (`ontochat/functions.py`, function `cq_generator`, commented out at HEAD): three parts —
    example pairs of data and CQ; "how to make them less complex" (check whether a CQ "can be divided into multiple
    questions" and split it); "how to remove real entities to abstract them" (replace named entities and literal years by general concepts).
  - *CQ analysis* (`ontochat/analysis.py`): sentence embeddings (`all-MiniLM-L6-v2`, unit-normalised) with
    agglomerative clustering and a dendrogram, or LLM clustering; optional step
    "Perform paraphrase detection for the following competency questions" returning the duplicates before clustering;
    clustering instruction "Keep the granularity of the topic in each cluster at a similar level", JSON output `{topic: [CQs]}`.
  - *Ontology verbaliser* (`ontochat/verbaliser.py`): turns the ontology into plain text — each class with its
    parents and comment, named individuals, each object property with sub-property, comment, possible domains and ranges.
  - *Ontology testing* (`ontochat/ontolib.py`): for each CQ, verbalisation + "You are asked to infer if the ontology
    described before can address the following competency question"; variant b: "Only reply: 'Yes', 'No' and provide
    an explanation after a comma."; the answer is parsed with a regular expression into (label, explanation).
  - *Test data* (`data/`): 28 positive CQs and 28 negative CQs for the Music Meta ontology (my count of non-empty
    lines in the two files); the tutorial notebook builds a confusion matrix of the yes/no checker over both sets.
  - *Settings* (`ontochat/config.py`): temperature 0, seed 1234.
  - *User story elicitation* (the only tab active at HEAD): the agent asks one elicitation question at a time, gives
    an example answer and names a prompt template, does not move on until the user confirms, and refuses off-task
    requests; story template = persona, goal (description, actions, keywords), scenario (before, challenges, during, after).
    These parts belong to later OntoChat work (participatory prompting), cited in the README next to the ESWC 2024 paper.

**OBSERVATION (ours)** — at HEAD the CQ extraction, clustering and testing interfaces are commented out in `app.py`;
the library functions remain. The yes/no checker judges a *verbalisation*, without any executable witness — weaker than OE-Assist's definition.

### 2.5 sadruddin2025schema — LLMs4SchemaDiscovery / schema-miner (ESWC 2025)

Official code: `https://github.com/sciknoworg/schema-miner` (now version 3.2.7, which also contains the follow-up
SCHEMA-MINERpro ontology grounding). Depth: **deep** for prompts, CLI and archived experiment data; paper text not read.

**PAPER / REPO (high confidence unless marked)**

- Three stages. Stage 1: an initial JSON schema from a single process specification document ("often a list of 5 to
  15 properties written by a domain expert", README). Stage 2: refinement over a small curated set of papers with
  expert feedback. Stage 3: refinement over a larger, non-curated corpus with expert review.
- Prompts (`schema_miner/prompts/schema_extraction/`): role "data schema designer"; stage 2/3 prompts describe an
  *iterative process* in which each iteration receives one paper, the current schema and optional domain-expert
  feedback, and list five objectives (validate existing properties, add new ones, apply expert recommendations,
  document and organise, avoid redundancy). Notable constraints: always return the full schema, never a partial one;
  "The schema should remain stable across iterations and must not include unnecessary new properties if they overlap
  with existing ones"; no example values from the papers.
- Human feedback, three methods (archived data `data/archived/stage-2/.../domain-expert-reviews/method-{1,2,3}`):
  method 1 = descriptive feedback under four headings — "Property Merging", "Property Grouping", "Missing Properties",
  "Adequacy of Descriptions"; method 2 = "Domain expert edited schema of the initial generated version";
  method 3 = both. A search summary of the paper confirms that descriptive feedback, schema editing and their combination were compared (medium).
- Loop mechanics (`schema_miner/cli.py`): papers processed one at a time or in batches; the schema is updated after
  each paper and saved as `intermediate-schema/<model>/schema_iter_N.json`; after each batch the tool asks
  "Enter expert feedback for the next batch (or press Enter to continue without feedback)"; feedback given at the start of a batch is reused for every paper of that batch.
- Output parsing (`utils/json_utils.py`, `inference_runner.py`): try plain JSON, then fenced blocks, then the text
  after a `</think>` tag; otherwise the step returns no schema.
- Evaluation utilities: pairwise ROUGE, BLEU and BERTScore between the schemas of different models
  (`utils/evaluation_utils.py`; `results/.../quantitative_evaluation.csv`), and expert-made "Ideal Schema" files in `results/`.
- Follow-up work in the same repository (SCHEMA-MINERpro, Semantic Web journal 2026 per README — not the ESWC paper):
  grounding of schema properties in QUDT, either by one prompt per field or by a tool-calling agent that retrieves
  the top-3 chunks (300 tokens, overlap 30, FAISS) from the QuantityKind and Unit vocabularies and must answer with
  JSON `{valid, quantityKind[], unit[]}`; the retrieval prompt says "if you have any doubts, return that the property cannot be grounded".

**OBSERVATIONS (ours)** — at HEAD, `extract_schema_stage3` uses `prompt_template2` (the stage-3 template file exists
but is not referenced there). The archived atomic-layer-deposition "experimental use case" folders hold 14 directory
entries for stage 2 and 118 for stage 3 (not verified as paper counts).

### 2.6 lippolis2025bench4ke — Bench4KE (ESWC 2026)

Official code: `https://github.com/fossr-project/ontogenia-cini` (the repository's BibTeX: Ciancarini, Lippolis,
Nuzzolese, Presutti, Ragagni; LNCS 16550, pp. 212–231 — matches the bib entry). Depth: **deep** for code.

**PAPER / REPO**

- Abstract via search (medium): an extensible API-based benchmarking system for knowledge-engineering automation;
  first release targets CQ generation; gold standard from 17 real-world ontology projects; a suite of similarity
  metrics; comparative analysis of 6 LLM-based CQ generation systems; designed to extend to SPARQL generation,
  ontology testing and drafting.
- Code (high):
  - The system under test is called through an HTTP endpoint that receives a CSV and returns generated CQs.
  - Metrics (`restapi/app/services/cq_validator.py`, `catalogue/metric/*.ttl`): SBERT cosine (`all-MiniLM-L6-v2`),
    Jaccard, BERTScore (`microsoft/deberta-xlarge-mnli`), BLEU, ROUGE-L, best-match cosine per generated and per gold
    item, precision at threshold 0.6, and an LLM judge rating each generated CQ 1–5 on relevance, clarity and depth.
  - **Hit rate** (`catalogue/metric/HitRate.ttl`): "fraction of benchmark CQs matched by at least one generated CQ
    above threshold" (SBERT cosine ≥ 0.6). **Augmented hit rate**: an independent evaluator LLM is asked to generate
    CQs for the uncovered areas; a generated CQ counts only if it matches a gold CQ above the threshold, and the
    metric adds the gold items recovered this way.
  - Independence guard (`hit_rate_evaluator.py`): a `ValueError` if the declared tool model equals the evaluator
    model — "Using the same LLM for generation and evaluation introduces bias."
  - The metric catalogue is itself published as RDF (`dqv:Metric`, DCAT metadata).
  - The bundled example generator (`restapi/cq_generator_app.py`) uses a stack of system messages: concept extraction
    before writing, abstraction control, terminology consistency, de-duplication ("Do not output paraphrased
    duplicates."), source priority, coverage without padding, CQ patterns, and a strict JSON output with clusters,
    `pattern` and `expected_answer_type`.
  - `maintenance.md` states "17 ontology-driven projects, 843 CQs"; the task catalogue entry also gives 843 CQs
    (and names four projects).

**OBSERVATIONS (ours)**

- `restapi/app/benchmarkdataset.csv` at HEAD has 754 rows / 722 distinct CQ strings / 17 projects;
  `benchmarkdataset_full.csv` has 852 rows / 18 projects. The documented 843 does not match either file exactly.
- In `hit_rate_evaluator.py` the docstring of the gap-filling function says it uses the scenario "not the missed CQs
  themselves, so the evaluation is not circular", but the prompt built in the same function lists the missed
  benchmark CQs. The augmented hit rate should therefore be read with care; for our own metrics we would not show gold items to a generator.
- `experimental-results/` stores results for five named tools (NeOn-GPT, OntoChat, Pan, RETROFIT-CQs, Rebboud); the
  abstract speaks of six. In the per-scenario summary files the mean hit rate lies between about 0.01 and 0.42, while
  the LLM-judge overall mean lies between about 3.7 and 4.7 on the 1–5 scale. A rubric judge therefore barely
  separates outputs that differ strongly in coverage of the gold standard. This is my reading of the stored CSVs, not a statement from the paper.

### 2.7 mai2024adapt — Do LLMs Really Adapt to Domains? An Ontology Learning Perspective (ISWC 2024)

Official code: `https://github.com/boschresearch/llm-vs-gibberish-ontologies` (AGPL-3.0). Depth: medium (READMEs and
prompt code read; paper text not read).

- PAPER (abstract via search, medium): the authors ask whether LLMs really adapt to domains or only learn lexical
  senses. They use WordNet to synthesise parallel corpora with English and gibberish terms. Finding: off-the-shelf
  LLMs "do not consistently reason over semantic relationships between concepts, and instead leverage senses and
  their frame"; fine-tuning improves performance on lexical semantic tasks even when the terms are arbitrary and unseen in pre-training.
- REPO (high): `wordnet-gibberish` creates "synthetic datasets from WordNet ontologies, by replacing the lexical
  forms with gibberish" (two translators: the `gibberify` package or a GPT-2 based word generator; the gibberish
  forms and definitions are stored next to the real ones); three domain subsets (WN-sweets, WN-football, WN-music).
  `finetune-llm-ontology` runs relation extraction and taxonomy discovery (positive and negative hypernym pairs;
  JSON answer with optional chain-of-thought field) on GPT-3.5, GPT-4, Llama-2-13B-chat and Zephyr-7B-beta, with
  one-shot or few-shot prompts, LoRA fine-tuning and a cross-domain transfer test; evaluation uses a triple store and Prolog.
- Relevance: it is the methodological basis for a **term-masking leakage test** of our proposer, and an argument for
  term-free atoms plus "retrieved candidates only".

### 2.8 busch2025dcat — Exploring LLM Capabilities in Extracting DCAT-Compatible Metadata for Data Cataloging

Official material: the GitHub repository named in the table above (prompts, n8n workflows, evaluation scripts, result
spreadsheets). Depth: medium (prompts and evaluation scripts read; paper text not read).

- Scope: **instance-level** metadata — generating *values* of DCAT properties from text documents. It does not
  generate or extend a profile. Its use for us is limited to prompt/output discipline and facet-specific evaluation.
- PAPER (abstract and listings via search, medium): eight properties (title, description, creator, language, spatial,
  issued, keyword, theme); zero-shot and few-shot prompting and a fine-tuned model for classification; larger models
  perform better, fine-tuning improves classification, few-shot is better in most cases; output often comparable to
  human-curated metadata. A peer-reviewed version is listed at DATA 2025 (SciTePress, pp. 299–309, DOI 10.5220/0013458500003967).
- REPO (high):
  - One prompt pair (zero-shot, few-shot) **per property**, each with an exact output format: a Python list for
    creators and keywords (at most 20), `YYYY-MM` for the issue date, one country name for spatial, a JSON array of identifiers for theme.
  - Theme assignment is **selection from a closed list**: "Assign the best matching EuroVoc IDs from this list",
    output only the identifiers. The few-shot theme workflow contains embedding and vector-store nodes, consistent
    with retrieving similar annotated documents as examples.
  - Models in the result files: GPT-4o, GPT-4o mini, Gemini 1.5 Pro and Flash, Llama 3.1 8B and 70B, Llama 3.2 3B;
    fine-tuned Gemini 1.5 Flash for theme.
  - Evaluation scripts by value type: ROUGE and cosine similarity for free text; F1@5/10/15 with stemming for
    keywords; fuzzy matching at 100/90/70 for names; micro-F1 for theme identifiers.
  - Datasets listed per property (`Datasets_Utilized.txt`), e.g. EURLEX57K and GIZ sector data for theme, SemEval-2010 and SemEval-2017 for keywords.

---

## 3. Reusable key steps for RBDPE

Stages follow the planned engine: atom intake → retrieve → propose → verify → repair → (judge/vote) → human review →
compile → conformance, plus traceability, evaluation and architecture.
Names in `code font` such as `AtomAssessment.disposition` refer to the snapshot of
`requirement-based-dcat-profile-extensioner/backend/profile_extensioner/contracts.py` that I read on 2026-11-13
(read only; that package is still being written, so names may change).

Each entry: **What they did** (PAPER/REPO) → **How we reuse** (ADAPTATION, ours) → **Evidence** → **Confidence** (of the "what they did" part).

### Atom intake

**G1-S01 — Atom intake lint: split compound, abstract entities, detect paraphrases, cluster**
(`zhang2024ontochat`, `lippolis2025bench4ke`)
- What they did: OntoChat's CQ extraction prompt makes the model split compound questions and replace named entities
  by general concepts; its analysis step runs LLM paraphrase detection and then topic clustering (LLM, or agglomerative
  clustering over sentence embeddings). Bench4KE's example generator adds abstraction control, terminology
  consistency and de-duplication instructions and returns clustered, typed JSON.
- How we reuse: four lint passes at intake, each writing `LintIssue` records: (1) `compound` — more than one
  requirement in an atom; propose a split, the human confirms, the original stays as parent; (2) vocabulary terms or
  named instances in a "term-free" atom; (3) `duplicate_of` — paraphrase detection (embedding pre-filter plus one LLM
  confirmation per candidate pair) so one change can cover both atoms; (4) a topic cluster per atom, used to batch
  Propose and to group the workbench list. Input: `AtomSet`. Output: lint issues and cluster ids on the blackboard.
- Evidence: `OntoChat/ontochat/analysis.py`: "Perform paraphrase detection for the following competency questions";
  `ontochat/functions.py`: "check if any of them can be divided into multiple questions";
  `ontogenia-cini/restapi/cq_generator_app.py`: "Do not output paraphrased duplicates."
- Confidence: high.

### Retrieve

**G1-S02 — One index record per term, and three labelled retrieval sources including the growing artefact**
(`fathallah2026rigor`)
- What they did: external ontologies are indexed as one text chunk per class/property (file, kind, local name, IRI,
  label, shortened comment). Per table, the top-3 chunks are retrieved from each of three indexes — the growing core
  ontology (re-indexed every iteration), the documentation, the external ontologies — with a query made of table,
  class, column and FK-target names.
- How we reuse: the vocabulary index holds one record per term (`Term`: IRI, kind, label, definition, domain, range,
  vocabulary, source); embedding text is built from those fields; an exact IRI lookup backs the "term exists" check.
  Retrieve returns three *separately labelled* lists per atom: (A) base-profile elements of the atom's target class
  plus accepted and pending changes (prevents duplicates across atoms); (B) the source excerpt around
  `Atom.source_reference`; (C) vocabulary candidates. k per source is configurable (RIGOR uses 3; `PipelineConfig.top_k` is 8).
- Evidence: `RIGOR/app.py` — `retrieve_top_k(retrieval_query, core_index, core_chunks, k=3)`;
  `load_external_ontologies`: `text = f"[{filename}] Class: {name} IRI: {cls}"`.
- Confidence: high.

### Propose

**G1-S03 — One requirement per call with a memoryless context; merging is engine work**
(`lippolis2025ontology`)
- What they did: Memoryless CQbyCQ handles one CQ per call; the slot for previously generated RDF is always empty and
  the story contains no other CQs; per-CQ outputs are merged afterwards.
- How we reuse: one Propose call per atom (or per small duplicate cluster) with only that atom, its source excerpt,
  the retrieved candidates and the base-profile slice of the target class. The accumulated change set is never pasted
  in as free text. Merging and conflict detection are deterministic (consolidate stage). Because the paper's expert
  sheets show duplicates in memoryless outputs, we pair this with retrieval over pending changes (G1-S02, list A).
- Evidence: `Onto-Generation/PromptingTechniques/README.md`: "the {rdf} section, which refers to the previous
  interactions, is always empty"; "This causes a considerable reduction in the LLM's context."
- Confidence: high.

**G1-S04 — Fixed decomposition procedure: subject / predicate / object / value, then explain and rate confidence**
(`lippolis2025ontology`)
- What they did: Ontogenia gives the model a nine-step metacognitive procedure: understand the CQ, identify the
  context, split it into subject, predicate, object and predicate nominative and map these to class, object property
  and datatype property, test subclass relations, add restrictions, add equivalence/disjointness, confirm and explain, rate confidence and test on instances.
- How we reuse: the Propose system prompt carries a fixed numbered procedure: (1) restate the atom; (2) context =
  target class in the base profile; (3) split into subject / predicate / object / value type and map them to
  `target_class`, `path`, `range_class`, `range_datatype`; (4) decide reuse / refine / mint; (5) derive facets from the
  modality; (6) check against the base; (7) justify every facet (`FacetJustification.reason`) and give `confidence`.
  The decomposition is stored with the proposal so the reviewer can see how the atom was read.
- Evidence: `Ontogenia/data/procedure.txt`: "Divide the competency question in subject, predicate, object and
  predicate nominative."; "Confirm the final answer and explain the reasoning."
- Confidence: high.

**G1-S05 — Answerability pre-check before proposing ("already covered by the base")**
(`lippolis2025ontology`)
- What they did: before writing any OWL the model must state whether the CQ is already answerable by the current
  ontology; if yes, it returns the ontology unchanged.
- How we reuse: the first field the proposer fills is `AtomAssessment.disposition`, with `covered_by` element
  references when the base already satisfies the atom; then no change is emitted. Verify re-checks deterministically
  that each cited element exists in the base and that its facets satisfy the atom's modality, so a hallucinated
  "already covered" fails. Our deviation: the prompt must not suggest a prior (the original says roughly 90% are not answerable).
- Evidence: `Onto-Generation/PromptingTechniques/README.md`: "is this competency question answerable by the previous
  version of the RDF (given down) or not?"
- Confidence: high.

**G1-S06 — Prompt anatomy with named sections, mandatory tasks, strict constraints and a common-mistakes footer; deterministic call settings**
(`fathallah2026rigor`, `lippolis2025ontology`, `zhang2024ontochat`)
- What they did: RIGOR's generator prompt is a sequence of bracketed, named sections ending in numbered mandatory
  tasks and strict constraints, with a dedicated section for correction instructions. Memoryless CQbyCQ ends with
  enumerated lists of typical mistakes per element type. GPT-4 was run with temperature and both penalties at zero;
  OntoChat fixes temperature 0 and a seed.
- How we reuse: a prompt builder with fixed sections filled from typed inputs — `[ATOM]`, `[SOURCE EXCERPT]`,
  `[BASE PROFILE SLICE]`, `[PENDING CHANGES]`, `[CANDIDATE TERMS]`, `[CORRECTION INSTRUCTIONS]`, `[MANDATORY TASKS]`,
  `[STRICT CONSTRAINTS]`, `[COMMON MISTAKES]`, `[OUTPUT SCHEMA]`; empty sections print "None". The mistakes list is a
  versioned file per change kind, extended from verifier failures and human rejections. Temperature 0, no
  frequency/presence penalty where the provider exposes them (identifiers must be reusable), fixed seed where
  supported. The rendered prompt and parameters are stored in `LLMCallRecord`, so each section is inspectable on the workbench.
- Evidence: `RIGOR/app.py`: sections "[MANDATORY TASKS]", "[STRICT CONSTRAINTS]", "[CORRECTION INSTRUCTIONS FROM
  PREVIOUS JUDGE PASS]"; `Onto-Generation` prompt: "here are some possible mistakes that you might make"; its README:
  "hyperparameters (frequency_penalty, presence_penalty, and temperature) set to zero"; `OntoChat/ontochat/config.py`.
- Confidence: high.

**G1-S07 — Select reused terms from a closed candidate list, with an explicit way to abstain**
(`busch2025dcat`, `sadruddin2025schema`)
- What they did: for `dcat:theme` the model must pick identifiers from an explicit list and output only identifiers
  in a fixed format; each property has its own strict output format. In schema-miner's grounding agent the model sees
  retrieved vocabulary chunks, answers in a fixed JSON shape, and is told to decline when in doubt.
- How we reuse: the proposer may name a reused term only by choosing a candidate id from the list shown in the prompt
  (enum-constrained field in the output schema for `path` and `range_class`); an IRI not in the list is rejected by
  Verify. An explicit abstain value with a reason per rejected candidate (`MintJustification.rejected_candidates`)
  opens the mint path. Facet outputs have fixed types (integers, CURIEs, lists of concept IRIs).
- Evidence: Busch repository `Prompts/DCAT_Theme_EUROLEX57K.txt`: "Assign the best matching EuroVoc IDs from this
  list"; `schema-miner/schema_miner/prompts/ontology_grounding/agent_qudt_prompt1.py`: "if you have any doubts,
  return that the property cannot be grounded".
- Confidence: high.

**G1-S08 — Reuse before mint, grounded only in retrieved evidence; a small pattern library**
(`fathallah2026rigor`, `lippolis2025ontology`)
- What they did: RIGOR allows external alignments only when supported by retrieved external-ontology hints, and the
  judge asks that core concepts be "reused, subclassed, or aligned rather than duplicated". Ontogenia passes ontology
  design patterns to the model as named OWL snippets.
- How we reuse: decision order enforced in the prompt and in Verify — reuse a base element → reuse a retrieved
  vocabulary term → refine/specialise → mint — with `MintJustification.reason_no_reuse` mandatory for a mint. A
  sub-property or sub-class link to an external term is accepted only if the target is among the retrieved candidates
  and exists in the index; we check this deterministically (in RIGOR's code the rule lives in the prompt and in a
  minor judge criterion only). A handful of named DCAT-AP extension patterns (add a property to an existing class;
  tighten cardinality; restrict a range to a controlled vocabulary; add a subclass with extra constraints) is offered as templates.
- Evidence: `RIGOR/app.py`: "Add external alignment using owl:equivalentClass, rdfs:subClassOf, or skos:exactMatch
  only when supported by retrieved external ontology hints."; Onto-Generation prompt: "You can use the following ontology design patterns in OWL format".
- Confidence: high.

### Architecture

**G1-S09 — Deterministic backbone first; the LLM only emits deltas; fall back to the backbone**
(`fathallah2026rigor`)
- What they did: the direct mapping of each table is generated without an LLM and merged first, which guarantees
  coverage; the LLM is told its role is enrichment; if no delta survives the retries, the backbone is kept and the run continues.
- How we reuse: the base DCAT-AP profile is loaded deterministically and is immutable. Model output is only ever a
  set of `ProfileChange` deltas. If an atom has no verified change after the repair rounds, the base stays untouched,
  the atom is marked unaddressed / pending review and queued for the human; the pipeline still compiles.
- Evidence: `RIGOR/app.py`: "Deterministic Direct Mapping is always merged first, guaranteeing schema coverage.";
  "No valid semantic delta after retries; deterministic mapping retained".
- Confidence: high.

**G1-S10 — A typed change record instead of model-written syntax; identifiers owned by the engine**
(`fathallah2026rigor`, `lippolis2025ontology`)
- What they did: RIGOR has the model write Manchester syntax and reads it with a tolerant custom parser that handles
  only `some`/`only` restrictions. Memoryless CQbyCQ prescribes a `Cl_` class prefix inside the prompt.
- OBSERVATION (ours): unparsed class expressions become named IRIs — 62 distinct artefact IRIs in one stored RIGOR
  output; the `Cl_` prefix was criticised by the experts ("Why the strange naming of classes with a Cl_-prefix?").
- How we reuse: the model fills the typed `ProfileChange` (JSON schema). LinkML, SHACL and DSV come only from the
  deterministic compiler. IRIs, prefixes and local names of minted terms are produced by the engine. No parser for
  model-written Turtle or SHACL exists, so no construct can be silently mis-read.
- Evidence: `RIGOR/app.py` `parse_restriction` regex `(some|only)` with fallback to `parse_prefixed_or_uri`;
  `RIGOR/output/generated_ontologies/rigor_chinook_claude_ontology.owl` (62 matches of `_exactly_1_|_max_1_|_min_1_`);
  `Onto-Generation/Experiment Results/Expert evaluation/assessment_theater_combined.xlsx`.
- Confidence: high.

### Verify

**G1-S11 — Validate on a scratch copy (base + accepted + candidate) before committing; re-validate per unit and at the end**
(`fathallah2026rigor`)
- What they did: an approved delta is parsed, added to a copy of the core, and the copy is validated
  deterministically — restricted to the tables processed so far — before the delta is merged; the core is validated
  again after each table and once at the end, where an error aborts.
- How we reuse: Verify applies each proposed change to a scratch copy of (base ∪ included changes), runs the
  deterministic checks there and commits only on pass; checks are scoped to what has been processed (a change is not
  failed because other atoms are still open). The same checks run again after consolidation and once over the whole
  change set before compile; a final failure blocks release. Our deviation from RIGOR's order: deterministic checks
  run *before* any judge call, because they are cheap and objective.
- Evidence: `RIGOR/app.py`: `candidate += core`, `candidate += delta_graph`,
  `validate_graph_against_rigor(candidate, processed_schema)`; comment "validate only tables processed so far, not future tables".
- Confidence: high.

**G1-S12 — Coverage needs an executable witness**
(`lippolis2025oeassist`)
- What they did: a CQ counts as modelled if a SPARQL query extracting the answer can be written; the model returns
  Yes with the query, or No with a query for the partial answer; closed-world reading.
- How we reuse: every `CoverageLink` gets a witness — a query over the compiled shapes graph (the property shape on
  `target_class` with the path and the facet values the atom requires) that must return a row. The witness is derived
  by rule from the typed change, not written by the model; a judge explanation may be attached. For partial coverage
  the link records what is missing. A claim whose witness fails is downgraded to `needs_review`.
- Evidence: `OE-Assist/prompts/eval-prompt.MD`: "a competency question is modelled by an ontology if you could write
  a SPARQL query to extract the answer".
- Confidence: high.

### Repair

**G1-S13 — Bounded repair loop with error-specific correction hints**
(`fathallah2026rigor`)
- What they did: at most three generation attempts per table (`MAX_JUDGE_RETRIES = 2`). After a judge rejection the
  critical issues are fed back; after a deterministic failure up to 20 error messages are fed back; an empty response
  gets its own hint. The hint is a dedicated section of the next prompt.
- How we reuse: a repair call is the Propose prompt plus `[CORRECTION INSTRUCTIONS]` listing the failed `CheckResult`
  codes and messages (capped) and, if a judge rejected, its critical issues; unparsable output gets its own hint.
  Rounds are bounded by `PipelineConfig.repair_rounds`; afterwards `Decision.status = needs_review`;
  `Provenance.repair_round` records the round.
- Evidence: `RIGOR/app.py`: `MAX_JUDGE_RETRIES = 2`; "Fix ALL of these structural errors".
- Confidence: high.

### Judge / vote

**G1-S14 — Judge contract: decision, severity-graded issues, corrected fragment; judge independent of the proposer**
(`fathallah2026rigor`, `lippolis2025bench4ke`)
- What they did: RIGOR's judge returns one of three decisions, issue lists in three severity tiers and a corrected
  fragment. Bench4KE's hit-rate evaluator raises an error when the declared tool model equals the evaluator model;
  RIGOR's evaluation judge is from another model family than the generators.
- How we reuse: a typed verdict — decision ∈ {approve, reject, approve_with_corrections}, issues with severity
  (critical / important / minor), check id and message, optional corrected `ProfileChange`. Critical blocks and feeds
  Repair; important sets `needs_review`; minor is logged. A corrected change is a new proposal and must pass Verify.
  Configuration check: the judge model (`LLMSettings.step_models`) must differ from the proposer model; otherwise the
  workbench warns and the verdict is marked self-judged. Both model ids are stored.
- Evidence: `RIGOR/app.py`: "Decision: APPROVED | REJECTED | APPROVED_WITH_CORRECTIONS";
  `ontogenia-cini/restapi/app/services/hit_rate_evaluator.py`: "Using the same LLM for generation and evaluation introduces bias."
- Confidence: high.

**G1-S15 — Give the judge (and the reviewer) a verbalised slice of the profile**
(`zhang2024ontochat`)
- What they did: a verbaliser lists classes with parents and comments, individuals, and relations with possible
  domains and ranges in plain text; each CQ is then tested with a Yes/No question, optionally "Yes/No, explanation".
- How we reuse: the judge prompt is built from a deterministic verbalisation of the relevant slice only
  ("Property P on class X: range R, at least 1, obligation mandatory, values from vocabulary V"), not from raw SHACL.
  The same text is shown on the workbench, so judge and human read the identical statement. The answer starts with the label, then the explanation.
- Evidence: `OntoChat/ontochat/verbaliser.py` ("The main classes of the ontology are listed below:");
  `ontochat/ontolib.py`: "Only reply: 'Yes', 'No' and provide an explanation after a comma."
- Confidence: high.

### Human review

**G1-S16 — Guardrails against over-trust in machine suggestions**
(`lippolis2025oeassist`)
- What they did: in the user study, correct suggestions raised and incorrect suggestions lowered reviewer accuracy
  (+13% / −28% on the slides); the authors name two mitigations: check the suggested query against the ontology before
  showing the label, and show calibrated confidence or provenance.
- How we reuse: (1) a machine verdict is shown as verified only when the deterministic checks and the coverage
  witness passed; otherwise it is labelled an unverified suggestion; (2) every card shows its evidence next to the
  label — witness, candidates considered, check results, votes agreeing/total; (3) the reviewer can answer
  "cannot decide"; (4) decision, time and whether a suggestion was shown are logged, so over-trust can be measured.
- Evidence: `OE-Assist/slidesiswc2025.pdf`: "pre-check suggested SPARQL against the actual ontology before showing
  the label"; "if the LLM was incorrect the accuracy drops significantly (-28%)".
- Confidence: high.

**G1-S17 — Structured expert feedback (rubric and/or direct edit) re-injected into the next round; saved intermediates**
(`sadruddin2025schema`)
- What they did: three feedback methods — descriptive feedback under four headings (merging, grouping, missing
  properties, adequacy of descriptions), an expert-edited schema, or both — passed as "Domain Expert Feedback" into
  the refinement prompt; feedback is collected between batches; the schema is saved after every iteration; the prompt
  demands stability across iterations.
- How we reuse: human decisions carry structured feedback codes besides free text — merge-with, retarget
  (class/path), missing requirement, wording — plus direct edit of the typed change. On re-run the feedback for the
  affected atoms is injected as `[HUMAN FEEDBACK]`, together with a stability rule (accepted changes are not altered;
  no overlapping additions). Each stage run stores a snapshot of the change set on the append-only blackboard.
- Evidence: `schema-miner/data/archived/stage-2/Atomic-Layer-Deposition/domain-expert-reviews/experimental-usecase/method-1/gpt-4-turbo.txt`
  (headings "Property Merging", "Property Grouping", "Missing Properties", "Adequacy of Descriptions");
  `schema_miner/cli.py`: "Enter expert feedback for the next batch (or press Enter to continue without feedback)".
- Confidence: high.

### Traceability

**G1-S18 — Element-level provenance; a missing trace is a defect**
(`fathallah2026rigor`, `lippolis2025ontology`)
- What they did: RIGOR attaches `prov:wasDerivedFrom` to every generated or modified class and property and reports
  missing provenance as a validator warning. The ESWC 2025 study measured superfluous components — elements no
  requirement needs — at roughly 30% of generated classes and properties.
- How we reuse: `ProfileChange.covers` (atom id, reason, evidence quote) and one `FacetJustification` per constraint;
  the compiler writes `prov:wasDerivedFrom` from each generated shape to the atom and emits the trace matrix. A change
  without a coverage link, or a facet without justification, fails Verify as an **error** (RIGOR only warns).
  We report the superfluous-change rate — zero by construction in the full pipeline, measured in ablations.
- Evidence: `RIGOR/app.py`: "Add prov:wasDerivedFrom annotations for every newly introduced or modified
  class/property."; Onto-Generation slides: "Generally, ~30% of generated classes and properties were superfluous."
- Confidence: high.

### Conformance

**G1-S19 — "Preserved or strengthened": the delta may never remove or contradict the backbone; severity-graded rule catalogue**
(`fathallah2026rigor`)
- What they did: two critical judge criteria forbid removing or contradicting the deterministic mapping and require
  key/not-null/unique restrictions to be preserved or strengthened; the deterministic validator enforces coverage of
  the backbone, type consistency, one domain and one range, XSD datatype ranges, and warns about missing documentation.
- How we reuse: conformance compares every (target class, path) facet of the extension with the base and classifies
  it added / tightened / unchanged / loosened (`DeltaStatus`); "loosened" or a missing base constraint is an error —
  our "may tighten, never loosen". Every rule has an id, a severity (error / warning / info) and a message; errors
  block, warnings go to review. Rules taken over: a path is not both object- and datatype-valued; datatype ranges are
  valid XSD; every element has label and definition.
- Evidence: `RIGOR/app.py`: "The delta must not remove or contradict deterministic direct mapping coverage.";
  "Required primary-key/not-null/unique existential restrictions must be preserved or strengthened."
- Confidence: high.

### Evaluation

**G1-S20 — Score the verifier/judge as a classifier on a gold set with explicit negatives**
(`zhang2024ontochat`, `lippolis2025oeassist`)
- What they did: OntoChat tests its yes/no checker on 28 positive and 28 negative CQs with a confusion matrix.
  OE-Assist uses 1,393 annotated CQ–ontology pairs and reports macro-F1 on the full, imbalanced set and accuracy on
  a balanced subset; the release holds three runs for two of its three models.
- How we reuse: a labelled set of (atom, change set) pairs with deliberate negatives — atoms the extension does not
  cover, wrong range or cardinality, changes that loosen the base (`Atom.counterfactual_of` supports paired negatives).
  Report macro-F1 on the full set, accuracy on a class-balanced subset and a confusion matrix; repeat LLM runs.
- Evidence: `OntoChat/ontochat/tutorial.ipynb` ("Loaded … positive and … negative CQs"); OE-Assist slides: "Metric:
  macro-F1 on the full set and accuracy on the balanced set"; our count of `OntoEval.csv`: yes 1,203 / no 190.
- Confidence: high.

**G1-S21 — Four-view quality evaluation including the superfluous-element rate**
(`lippolis2025ontology`)
- What they did: pitfall scan (OOPS!), share of modelled CQs (manual CQ verification by two engineers), share of
  superfluous components (manual, two engineers), and expert evaluation by two experts with reported agreement (Cohen's kappa 0.61).
- How we reuse: for every generated extension report (1) structural validity — SHACL-SHACL, profile lint,
  conformance report; (2) requirement coverage — share of atoms with a passing witness; (3) superfluous rate — share
  of added elements or facets no atom needs, judged by two annotators; (4) expert review with a fixed rubric
  (usability, completeness, accuracy; per atom yes / maybe / no plus the addressing element) and inter-annotator agreement.
- Evidence: `Onto-Generation/ontology_generation_ESWC_presentation_slides.pdf` (evaluation slides; "Two expert
  ontology engineers with the inter-annotator agreement (Cohen's kappa) of 0.61").
- Confidence: high.

**G1-S22 — Threshold hit rate against a gold standard, facet-appropriate measures, and no reliance on rubric scores alone**
(`lippolis2025bench4ke`, `busch2025dcat`)
- What they did: Bench4KE's hit rate is the fraction of gold CQs matched by at least one generated CQ with embedding
  cosine ≥ 0.6, next to precision at the same threshold and lexical/semantic similarity metrics; an LLM judge rates
  items 1–5. The DCAT extraction study uses a different measure per value type (ROUGE/cosine for text, F1@k for
  keywords, fuzzy match for names, micro-F1 for controlled identifiers).
- OBSERVATION (ours): in Bench4KE's stored summaries the hit rate ranges from about 0.01 to 0.42 while the judge's overall mean stays between about 3.7 and 4.7.
- How we reuse: compare a generated `ProfileDelta` with a gold delta by element-level hit rate — exact
  (target class, path) match for reused terms; for minted terms label+definition similarity above a calibrated
  threshold — plus precision at that threshold. Per facet: exact match for identifiers and counts, set-based
  micro-F1 for controlled vocabularies, text similarity only for definitions. Never use a 1–5 LLM rubric as the only quality signal.
- Evidence: `ontogenia-cini/catalogue/metric/HitRate.ttl`: "fraction of benchmark CQs matched by at least one
  generated CQ above threshold"; `ontogenia-cini/experimental-results/*_US_validation_results.csv`; Busch repository `Evaluation_Code/`.
- Confidence: high.

**G1-S23 — Leakage controls: term masking and a protected benchmark**
(`mai2024adapt`, `lippolis2025ontology`)
- What they did: mai2024adapt builds parallel datasets in which the lexical forms of WordNet concepts are replaced by
  gibberish and compares LLM performance on relation extraction and taxonomy discovery (the abstract, via search,
  reports that off-the-shelf models lean on lexical senses rather than reasoning over relations). lippolis2025ontology
  distributes its dataset in a password-protected archive to keep it out of training data.
- How we reuse: (1) a masked-term experiment condition — rebuild the vocabulary index with labels and IRI local names
  replaced by pseudo-words, definitions/domains/ranges unchanged; run the same atoms and compare reuse accuracy with
  the unmasked run. A large drop means the proposer relies on memorised DCAT knowledge instead of the retrieved
  definitions. `PipelineConfig.exclude_namespaces` already hides whole vocabularies; masking is the finer variant.
  (2) publish gold atoms and gold extension in a protected archive. Design consequence: only retrieved candidates may be used (G1-S07).
- Evidence: `llm-vs-gibberish-ontologies/README.md`: "creating synthetic datasets from WordNet ontologies, by
  replacing the lexical forms with gibberish"; `Onto-Generation/README.md`: "To prevent LLMs from including this
  dataset in their training data, it is zipped and locked with a publicly available password."
- Confidence: high (method, from the repositories); the finding about lexical senses is medium (abstract via search).

**G1-S24 — Ablations and baselines that keep the backbone constant**
(`fathallah2026rigor`, `lippolis2025ontology`)
- What they did: RIGOR compares direct mapping, a schema-only LLM baseline and a non-iterative RAG variant, and
  ablates each retrieval source while always keeping the direct mapping. The Ontogenia script runs four trials
  (requirements only; + patterns; + procedure; all).
- How we reuse: experiment conditions through `PipelineConfig` switches with the base profile fixed: no retrieval;
  vocabulary only; base context only; no source excerpt; no judge; no repair; one call for all atoms versus one call
  per atom. Two baselines: base profile unchanged, and a single-prompt extension without verification. Score with G1-S20 to G1-S22.
- Evidence: `RIGOR/run_ablation.py`: "Ablations hide selected context sources from the Gen-LLM prompt, but do not
  remove the direct-mapping backbone."; `Ontogenia/code-thematic-cqs.py` (Trial 1 to Trial 4).
- Confidence: high.

**G1-S25 — User-study protocols: counterbalanced assisted versus unassisted review, and blind side-by-side expert rating**
(`lippolis2025oeassist`, `fathallah2026rigor`)
- What they did: OE-Assist — each participant solves 20 verification tasks, half with an LLM suggestion, with a
  selectable order of the two conditions; answers Yes / No / I don't know plus a 1–5 difficulty rating; analysis split
  by correctness of the suggestion. RIGOR — experts see four anonymised fragments per table, score each 0–5 on seven dimensions, rank them, and export JSON.
- How we reuse: workbench study with a fixed set of coverage decisions, half with and half without the machine
  suggestion, order counterbalanced; record accept / reject / cannot decide, difficulty and time; analyse accuracy
  separately for correct and incorrect suggestions. For output quality: anonymised extensions from different
  conditions rated side by side on fixed dimensions and ranked.
- Evidence: `OE-Assist/OE-Assist Tool/app.py` (settings A/B, `A_first`/`B_first`, "I don't know", difficulty); OE-Assist
  slides: "20 CQ verification tasks, 10 with LLM suggestions, 10 with not"; `RIGOR/expert_survey/survey.html`:
  "Fragments are labelled A, B, C, D — method names are hidden."
- Confidence: high.

---

## 4. Mapping onto the current contract snapshot

What the snapshot of `contracts.py` already expresses, and what this literature adds on top (ADAPTATION, ours).

| Topic | Already in the snapshot | What the literature adds |
|---|---|---|
| Already-covered atoms | `AtomDisposition = covered_by_base`, `AtomAssessment.covered_by` | Ask for it *first* in the prompt (G1-S05) and re-check the cited elements deterministically. |
| Candidates | `Candidate` with score, rank, `in_base_on_class`, `base_facets`, `why` | Three labelled sources including pending changes (G1-S02); closed-list selection and abstain value (G1-S07). |
| Reuse before mint | `ChangeKind` order, `MintJustification.rejected_candidates` | Deterministic check that alignment targets are retrieved and exist (G1-S08). |
| Trace | `ProfileChange.covers`, `FacetJustification`, `CoverageLink.evidence_quote` | Executable witness per coverage link (G1-S12); missing trace as an error; superfluous-change rate (G1-S18). |
| Verification | `CheckResult` (V/T/C codes), `verification` list | Scratch-copy staging and processed-scope validation (G1-S11); severity tiers aligned with the judge verdict (G1-S19). |
| Repair | `PipelineConfig.repair_rounds = 3`, `Provenance.repair_round` | Correction-hint section built from check codes and judge issues, capped (G1-S13). |
| Judge / votes | `attribution_check`, `votes`, `votes_agreeing` | A typed verdict with three decisions and three severities; judge-model independence check (G1-S14); verbalised input (G1-S15). |
| Conformance | `DeltaStatus` incl. `loosened`, `ConformanceReport.delta_counts`, `witness_turtle` | The "preserved or strengthened" formulation as the rule text (G1-S19). |
| Human review | `Decision`, `DecisionStatus`, `SignOff`, append-only `BlackboardEntry` | Structured feedback codes re-injected into prompts (G1-S17); over-trust guardrails in the UI (G1-S16). |
| Audit | `LLMCallRecord` with prompts and `prompt_version` | Named prompt sections and stored call parameters (G1-S06). |
| Leakage | `PipelineConfig.exclude_namespaces`, `use_hints` | Term-masking condition and a protected benchmark (G1-S23). |
| Experiments | pipeline switches for conditions | Concrete ablation list and baselines (G1-S24); metrics (G1-S20 to G1-S22); study protocols (G1-S25). |
| Intake | `LintIssue` codes such as `contains_term`, `compound` | Paraphrase detection and clustering (G1-S01). |

---

## 5. Leads from the task description: confirmed or corrected

| Lead | Result |
|---|---|
| Prompting techniques and decomposition for ontology generation from CQs and user stories | **Confirmed.** Memoryless CQbyCQ and Ontogenia; full prompt and procedure text read. |
| Iterative retrieval-augmented generation of fragments with a judge model and provenance | **Confirmed with corrections.** In the released code a deterministic direct mapping comes first and the LLM only enriches; a deterministic graph validation follows the judge; the in-loop judge uses the same model as the generator; fragments are Manchester syntax read by a limited custom parser. |
| Conversational pipeline: user story, CQ extraction, clustering/filtering, ontology testing | **Confirmed.** At repository HEAD only story elicitation is active in the UI; the other functions remain in the library modules. |
| LLM-assisted ontology evaluation | **Confirmed**, with the over-trust finding and two mitigations. |
| Human-in-the-loop schema mining | **Confirmed.** Three stages, three feedback methods, batch-wise feedback, saved intermediates. |
| Benchmarks for CQ generation | **Confirmed.** Hit rate with threshold 0.6, evaluator independence guard, metric catalogue in RDF. |
| Do LLMs adapt to a domain or rely on lexical memory | **Confirmed** at the level of abstract and method (gibberish parallel corpora); numbers not read. |
| busch2025dcat | **Scope clarified.** Value extraction for DCAT properties from documents, not profile generation. Reusable: per-property output formats, closed-list selection, value-type-specific metrics. |

Design tensions worth a sentence in the paper (ours): memoryless calls versus duplication (G1-S03 with G1-S02);
judge-first (RIGOR) versus deterministic-first (ours, G1-S11); rubric judges saturate (G1-S22); requirements
generated by an LLM from the artefact under test make an evaluation circular (observation in 2.1).

---

## 6. Bibliography notes for the author

- `busch2025dcat` cites the arXiv preprint. Web search lists a published version: DATA 2025 (SciTePress), pp. 299–309,
  DOI 10.5220/0013458500003967 (medium confidence; from the SciTePress listing and dblp as returned by search).
- `lippolis2025oeassist`: the bib entry has no volume; a search summary of the Springer page gives LNCS vol. 16140 (medium).
- `lippolis2025bench4ke`: the key suggests Lippolis 2025, the entry (correctly, matching the repository's BibTeX) is
  Ciancarini et al., ESWC 2026. Cosmetic only.
- `fathallah2026rigor`: author order and venue match the repository's BibTeX. Check the acronym expansion and the
  phrase "independent Judge-LLM" against the paper text before quoting (see 2.1).
- `zhang2024ontochat`, `lippolis2025ontology`, `mai2024adapt`, `sadruddin2025schema`: DOI and pages agree with the citations printed in the official repositories or with the DOI in search listings.

## 7. Not found or uncertain

- Full paper texts: not read for any of the eight works (hosts blocked). To verify numbers, `arxiv.org` must be allowed in the session's network settings.
- lippolis2025ontology: per-model proportions of modelled CQs and OOPS! counts are in figures; not extracted.
- lippolis2025oeassist: macro-F1 and balanced-accuracy values not seen; 1,204 (slides) versus 1,203 (CSV) modelled CQs; the Protégé plugin mentioned by a web summary was not found in the repository.
- fathallah2026rigor: paper v2 text (Algorithm 1, judge description) not compared with the code; F1 0.73 / 0.67 / 0.52 on "BURR-ISWC" and "mean scores above 4.5/5" come from search snippets only.
- zhang2024ontochat: quantitative results of the ESWC 2024 paper not seen; survey figures in web summaries are unverified.
- lippolis2025bench4ke: the sixth evaluated system is not identifiable from the repository; documented gold-standard size (843 CQs) differs from the CSV files at HEAD.
- mai2024adapt: numeric results not seen; one secondary summary lists Falcon-40B among the models, the repository README does not.
- sadruddin2025schema: evaluation findings of the ESWC paper not read; the repository is a later, refactored version.
- busch2025dcat: per-property scores not extracted from the result spreadsheets; findings are from secondary summaries.

## 8. Sources

Repositories (read at the commits in section 0):
- https://github.com/NadeenAhmad/RIGOR — `app.py`, `eval.py`, `cqs.py`, `ontology_checker.py`, `run_ablation.py`, `non-iterative.py`, `baseline.py`, `mapping.py`, `expert_survey/`, `README.md`, `output/generated_ontologies/`
- https://github.com/dersuchendee/Onto-Generation — `README.md`, `PromptingTechniques/README.md`, `Dataset_OntoGen/`, `Experiment Results/Expert evaluation/`, `ontology_generation_ESWC_presentation_slides.pdf`
- https://github.com/dersuchendee/Ontogenia — `data/procedure.txt`, `data/patterns.csv`, `code-thematic-cqs.py`, `README.md`
- https://github.com/LiUSemWeb/LLMs4OntologyDev-ESWC2024 — `Prompts/CQbyCQ.md`, `README.MD` (baseline technique only)
- https://github.com/dersuchendee/OE-Assist — `prompts/eval-prompt.MD`, `OntoEval Dataset/`, `Evaluation/`, `OE-Assist Tool/app.py`, `slidesiswc2025.pdf`
- https://github.com/King-s-Knowledge-Graph-Lab/OntoChat — `ontochat/functions.py`, `analysis.py`, `verbaliser.py`, `ontolib.py`, `config.py`, `tutorial.ipynb`, `app.py`, `data/`, `assets/user_study/`
- https://github.com/fossr-project/ontogenia-cini — `README.md`, `restapi/app/services/cq_validator.py`, `hit_rate_evaluator.py`, `restapi/cq_generator_app.py`, `catalogue/`, `keac/README.md`, `maintenance.md`, `experimental-results/`
- https://github.com/sciknoworg/schema-miner — `README.md`, `schema_miner/prompts/`, `schema_miner/schema_extractor/extract_schema.py`, `schema_miner/cli.py`, `schema_miner/ontology_grounding/agentic_qudt_grounding.py`, `schema_miner/utils/`, `data/archived/`, `results/`
- https://github.com/boschresearch/llm-vs-gibberish-ontologies — `README.md`, `wordnet-gibberish/README.md`, `finetune-llm-ontology/README.md`, `taxonomy_discovery_gpt.py`, `wordnet_gibberish/translator/pure_gibberish.py`
- https://github.com/l94779589/Exploring-LLM-Capabilities-in-Extracting-DCAT-Compatible-Metadata-for-Data-Cataloging — `README.md`, `Prompts/`, `Evaluation_Code/`, `Datasets_Utilized.txt`, `N8N_Workflows/`, `Results/` (file names only)

Paper pages referenced through web search (not fetched directly):
- https://arxiv.org/abs/2503.05388 (lippolis2025ontology)
- https://arxiv.org/abs/2506.01232 (fathallah2026rigor)
- https://arxiv.org/abs/2403.05921 (zhang2024ontochat)
- https://arxiv.org/abs/2507.14552 (lippolis2025oeassist)
- https://arxiv.org/abs/2505.24554 (lippolis2025bench4ke)
- https://arxiv.org/abs/2407.19998 (mai2024adapt)
- https://arxiv.org/abs/2504.00752 (sadruddin2025schema)
- https://arxiv.org/abs/2507.05282 and https://scitepress.org/PublishedPapers/2025/134585 (busch2025dcat)
