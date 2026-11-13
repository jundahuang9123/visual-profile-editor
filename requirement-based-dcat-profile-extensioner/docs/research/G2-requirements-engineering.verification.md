# Verification report: G2-requirements-engineering (sceptic pass)

Date: 2026-11-13. Scope: the 25 reusable steps and 14 per-paper summaries in
`G2-requirements-engineering.md`.

## How I checked

- **Primary, read by me in the local clones** (untrusted reference data, read only, nothing executed):
  - `/home/user/refs/KE-UniLiv__IDEA2` at 7dc5b7a: README.md, idea2/prompts.py, schema2cq.py, notion_utils.py,
    reformulate_cq.py, runner.py, cq_measures.py, cq_linkage.py, cq_json_ld.py, exports.py, to_notion.py,
    iteration_evaluation.py, interfaces.py, output_constraints.py, utils.py, and the figure assets/img/idea2_workflow.png (viewed).
  - `/home/user/refs/KE-UniLiv__askcq` at fe1fb60: README.md, askcq/prompts.py, config.py, complexity.py, agreement.py,
    stored outputs of overview.ipynb, cq_embeddings.ipynb, cq_complexity.ipynb, cq_relevance.ipynb.
  - `/home/user/refs/KE-UniLiv__animl-ontology` at f6ce552: README.md, requirements/cqs.txt, testing/.
  - `/home/user/refs/oeg-upm__LOT-resources` at fa0ef6b: the three xlsx requirement templates (shared strings),
    templates for ORSD/orsd-template.tex, website/index.html (text extracted), figures/LOT-figures.drawio (labels extracted).
  - `/home/user/refs/aminzadenoori__LLMs-and-Prompt-Engineering-in-RE---Systematic-Literature-Review` at 4e3846f:
    README.md and the workbook (category sheet, three Stat sheets recounted, the Lubos2024-pw row).
  - raw.githubusercontent.com/microsoft/hve-core ... iso-29148-quality-attrs.md (secondary, fetched and read).
- **Secondary, web search summaries only** (no paper full text was reachable): arXiv 2604.01344 / CEUR Vol-4246 (IDEA2 workshop
  paper), arXiv 2404.16045 (Elicitron), arXiv 2509.11446 (Zadenoori), MDPI Automation 7(5) 169 (Bandi and Demir), the RE 2006
  abstract (Davis et al.), Lancaster/Aston records (Sutcliffe and Sawyer; Gervasi et al.), UZH and Pace copies of Glinz RE 2007,
  NeOn chapters, the 29148:2018 table of contents, arXiv 1611.08847 (requirements smells), the ER 2023 abstract (Monfardini).
- **Blocked**: WebFetch failed with ENOTFOUND for files.ifi.uzh.ch, core.ac.uk, www.mdpi.com and arxiv.org (one attempt each, not
  retried). These hosts, plus link.springer.com, ceur-ws.org, oa.upm.es and ieeexplore.ieee.org, must be allowed in the session's
  network settings before any "medium" item can be raised to "high".

Result: 14 confirmed, 11 partially confirmed, 0 unverified, 0 wrong. No fabricated citation was found. The repository-based
claims hold up well; the weak points are details taken from search summaries and several places where our own design is
phrased as if it followed from the paper.

## Verdicts per step

| Step | Verdict | What I checked and found |
|---|---|---|
| G2-S01 | partially confirmed | LOT columns confirmed verbatim in `Template for domain requirements.xlsx` and `Template for UC requirements.xlsx` (second column is "Domain" in one and "Sprint" in the other). The survey clause is weaker than stated: the ER 2023 abstract (search summary) says the survey asked about "faced difficulties" and that guidance is limited; the wording "writing, using and managing" was not seen. |
| G2-S02 | partially confirmed | Nine characteristic names confirmed in the hve-core file, which names section 5.2.5; the 2018 table of contents (search) lists 5.2.5, 5.2.6, 5.2.7 "requirement language criteria", 5.2.8 "requirements attributes". The language-criteria list was only confirmed for the **2011** edition (requirements smells paper: "loopholes, ambiguous adverbs or comparative and negative statements"); superlatives and incomplete references were not seen. Lubos2024-pw row confirmed in the workbook. |
| G2-S03 | partially confirmed | 5.2.6 exists and a practitioner summary says the set has five characteristics; the five names were not seen in a source independent of my own query. ORSD Task 6 "Validating the set of requirements" confirmed (Open University NeOn chapter, search); conflicts, missing requirements and contradictions confirmed; "carried out by users and domain experts" not confirmed. |
| G2-S04 | partially confirmed | Taxonomy (functional, performance, specific quality, constraints), the definition "an attribute of or a constraint on a system", and the definition/classification/representation problems all confirmed by search summaries of the RE 2007 PDF. The sentence that classification "must not depend on how the requirement is written" was not seen. |
| G2-S05 | partially confirmed | Slots 1 to 7 confirmed in `orsd-template.tex`. But the "(optional)" marks and "Competency Questions and sentences" are the LOT group's later template; nothing I saw shows the 2009 paper marks slots optional or allows sentences. ORSD as the output of LOT requirements specification confirmed in the figure labels. |
| G2-S06 | confirmed | Website text: terms plus synonyms, "These terms will be used during the ontology search ...". Pre-glossary rows confirmed in the template; NeOn Task 8 "Extracting terminology and its frequency" confirmed by search. |
| G2-S07 | partially confirmed | Nine scenarios confirmed (NeOn chapter via search; scenario 3 "Reusing ontological resources", 8 "Restructuring ontological resources", 9 localizing). The sub-activities of restructuring (modularise, prune, extend, specialise) and the reuse activities (search, assessment, comparison, selection, integration) were NOT found in any result. |
| G2-S08 | partially confirmed | PROMPT_COMP, class CQAnalysis and the flat-weighted score confirmed. Correlations -0.27 / -0.29 are in overview.ipynb, but cq_complexity.ipynb in the same repository stores -0.18 (c1_complexity) and -0.20 (filters). The two notebooks disagree. |
| G2-S09 | confirmed | PromptBuilder docstring and constructor (role, definition, examples, instruction, limit, raw data); `llm_setup_to_notion` stores ID, Model, Temperature, Usage, Role, Prompt; Gemini call uses response_mime_type application/json with response_schema list[str]. |
| G2-S10 | confirmed | Acceptance shares 0.909, 0.981, 0.500, 0.846, 0.667 and bidirectional coverage 0.0 to 15.3 confirmed in stored outputs; temperature 0 and seed 46 in config.py and README. The abstract sentence was not seen; the README says LLM sets are more complex and less readable "without further refinement". |
| G2-S11 | confirmed | `remove_similar_generated(..., threshold=0.95)`, all-mpnet-base-v2, `--nosimilarity`, README line on iteration 1; AskCQ README threshold 0.75 and coverage/novelty outputs. |
| G2-S12 | confirmed | "Upvoted By"/"Downvoted By" person fields, Score, Votes, Recap, Reformulates relation, comment retrieval, README "Priority labelling (Low, medium, high)", filter `less_than_or_equal_to: 0`. Note: one prompt constant says "score of less than 0" while the filter and README use <= 0. |
| G2-S13 | confirmed | CQ_INSTRUCTION_REFORMULATE, CQ_ACCEPTED, default comment text, the "(ID 42)" instruction, and positional pairing in runner.py lines 518 to 520. |
| G2-S14 | confirmed | Figure viewed: "x% of CQs accepted", "Max iteration reached", "No. of edits reached", "Expert time quota". Caveat: grep finds no implementation of these criteria in the code; the README procedure is "Repeat step 4 until no further CQs are needing reformulation". They are a design statement, not a tested mechanism. |
| G2-S15 | confirmed | Reformulates relation, sha256 in utils.py, exports.py context with prov, schema.org, Croissant, OWLUnit. Caveat: the context declares the prefix as the literal key "@prefix owlunit" with an angle-bracketed value, which is not a JSON-LD prefix definition, so "owlunit:CompetencyQuestion" would not expand. Do not copy the context as is. |
| G2-S16 | confirmed | Four-level rubric read in PROMPT_RELEVANCE_A/B/C; cq_relevance.ipynb outputs show the same question rated 1 in one run and 4 in another. Survey clause confirmed by the abstract (search). |
| G2-S17 | confirmed | 102 `.rq` files in testing/verified_positives, each headed "# CQ-n: ..."; testing/validated_negatives/1 holds a SHACL node shape plus acceptable_data.ttl and unacceptable_data.ttl; LOT figure has "Functional Ont Requirements formalization (optional)" and "Test suite". I did not trace the drawio connector itself. |
| G2-S18 | confirmed | All four results and the replication caveat match the RE 2006 abstract as returned by an independent search. |
| G2-S19 | partially confirmed | Four knowledge categories, roadmap and maturity conclusion confirmed (Lancaster record and authors' slides, search). Gervasi review-plus-framework confirmed. Not confirmed: "scenarios and prototypes ground conversations" and the definition "not accessible to anyone but the actor". |
| G2-S20 | confirmed | Serial and parallel generation, Action/Observation/Challenge, interviews, criteria plus chain-of-thought, more latent needs than human empathic lead user interviews: all in search summaries of arXiv 2404.16045. "Diversity sampling" is parallel generation followed by K-means filtering; serial generation gave the most diverse agents. |
| G2-S21 | confirmed | agreement.py and "Overall Fleiss' Kappa: 0.3539"; 162 of 204 accepted (79.4%); cohen_kappa_score and krippendorff on items rated by all raters. Gwet AC1 0.884 and PABAK 0.797 (AnIML, N=4) confirmed by a search summary of the arXiv table. |
| G2-S22 | partially confirmed | Menu strings confirmed. Workshop paper per search: 103 CQs, first-iteration acceptance 95.1%, cumulative acceptance 92.7% over 110 total **validation tasks**. "102 accepted", "review events" and "3 iterations" were not seen. |
| G2-S23 | partially confirmed | Eight categories and counts 28/20/16/15/13/11/4/3 confirmed in the authors' COUNTIF cells; 56/10/5/3 and 32/30/12 recounted. "About half share artefacts" conflicts with a search summary of the paper (61% share source code and prompts; shared datasets scarce); the guideline share was not found. Paper percentages (44% zero-shot, 29% few-shot, 6% RAG, 5% interactive) do not equal the workbook counts divided by 74. |
| G2-S24 | confirmed | 50 primary studies 2020 to 2026, 24 agent-based, SWEBOK V4.0a Software Requirements knowledge area, "early stages" confirmed by an extended search of the MDPI page. A table row "Total 19 / 5 / 24" was seen without column labels. |
| G2-S25 | confirmed | Figure labels (early stage, verified, ORSD formalization, new requirements, issues and bugs) and website text on sprints, prioritisation and expert validation. |

## Overreach flags (how_we_reuse must be labelled as our own adaptation)

- **G2-S02**: the standard names characteristics; the deterministic checks, the 0 to 3 rubric and the blocking rule are ours.
- **G2-S07**: NeOn has scenarios, not a decision ladder; the reuse_path vocabulary and the "mint_new is illegal unless" rule are ours.
- **G2-S08**: the paper measured complexity and correlated it with expert scores; using the count as an atomicity signal and a
  Verify checklist is ours and untested.
- **G2-S10**: the paper compared elicitation methods; it did not propose running several proposers and taking the union.
- **G2-S11**: 0.95 is a deduplication threshold for questions, 0.75 an analysis threshold for set coverage; neither was
  validated for class or property labels, and the two-band scheme is ours.
- **G2-S16**: the rubric rates relevance of a question to a user story; coverage of an atom by a profile change, and the
  eligibility thresholds (>= 3, 2, 1), are ours. The source itself shows the rating is unstable.
- **G2-S17**: one test per requirement is theirs; conforming/violating instance pairs per change and the "tighten, never
  loosen" check are ours.
- **G2-S18**: evidence about elicitation interviews does not support a review checklist; this is analogy only.
- **G2-S23**: the review classifies studies; tagging our calls and the ablation plan are ours.
- **G2-S24**: the review does not recommend a fixed low-autonomy pipeline over agent conversation; the step name suggests it does.

## Paper-level corrections

1. **alharbi2027idea2**: no search result shows the ISWC 2026 paper under this title; everything rests on the repository and
   the workshop paper, whose author list differs (Watkiss-Leek, Alharbi, Rostron, Ng, Johnson, Mitchell, Payne, Tamma,
   de Berardinis). The bibliography comment says the author's own notes (claude/rq1-related-work-idea2.md, read from LNCS 17128)
   exist; that file is not in this container and is the better source.
2. **alharbi2027idea2 (workshop figures)**: replace "110 review events" with "110 total validation tasks"; add first-iteration
   acceptance 95.1%; two scenarios (AnIML N=4, cultural heritage N=3). Confirmed: AC1 0.884, PABAK 0.797, a 23-item
   reformulation row with 69.6%. Not confirmed: 102 accepted, three iterations, 85.7%. A search snippet of another PDF version
   shows different agreement figures (Krippendorff alpha 0.177, Fleiss kappa 0.176), so versions may differ.
3. **alharbi2027idea2 (code)**: the stopping criteria exist only in the figure; one prompt says "less than 0" while the filter
   uses <= 0; the JSON-LD context has a malformed OWLUnit prefix.
4. **alharbi2026cq**: overview.ipynb and cq_complexity.ipynb give different correlations (-0.27 against -0.18).
5. **zadenoori2025slr**: "about half share code or data" should read, per search summary, 61% share source code and prompts
   while datasets are scarce; "about 15% cite prompting guidelines" was not found. The paper calls itself preliminary with no
   systematic cross-checking (search summary).
6. **ataei2025elicitron**: three experiments; serial generation was the most diverse; GPT-4-Turbo not confirmed. The arXiv v1
   title begins "Elicitron: An LLM Agent-Based Simulation Framework ...", which differs from the journal title in the bib.
7. **suarez2009orsd**: the "(optional)" slot marks and "or sentences" come from the LOT template, not from a 2009 source I saw.
   Tasks 6, 7 and 8 confirmed; top-down/bottom-up/middle-out and card sorting not confirmed.
8. **suarez2012neon**: the four-part description and nine scenarios are confirmed for the NeOn framework; restructuring
   sub-activities and the five reuse activities are not.
9. **glinz2007nfr**: search results attribute the faceted classification (kind; representation; satisfaction hard/soft; role
   prescriptive/assumptive) to Glinz's separate paper "Rethinking the Notion of Non-Functional Requirements"; do not attribute
   it to the RE 2007 paper without reading it.
10. **sutcliffe2013unknown**: the abstract also names Common Ground discourse theory, and the roadmap contrasts green-field and
    brown-field domains; the scenarios-and-prototypes sentence is unsupported.
11. **gervasi2013tacit**: the quoted working definition was not found.
12. **iso29148**: language criteria confirmed only for the 2011 edition. One search snippet says a document "supersedes
    BS ISO/IEC/IEEE 29148:2018, which is withdrawn"; verify whether a newer edition exists before citing 2018 as current.
13. **davis2006elicitation**: DBLP lists pages 176 to 185, the bib has 179 to 188 (search summary); check.
14. **monfardini2023**: DBLP lists the first author as Quirino (same person per search summary); check the name form.
