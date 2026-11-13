# G1-ontology-generation: sceptic verification report

Date: 2026-11-13. Role: independent re-check of the researcher's 25 reusable steps and 8 paper summaries.

## Method and limits

- I re-read the primary material myself instead of trusting the evidence strings: the cloned official repositories under `/home/user/refs/` (RIGOR 88c5820, Onto-Generation 13d2e17, Ontogenia 1038183, OE-Assist e0d2c16, OntoChat 737b7cc, ontogenia-cini e187fa4, schema-miner 13c47dc, Busch repository 3c6ceb7, llm-vs-gibberish-ontologies da3e97a, LiU CQbyCQ 3609cde). I extracted the two author slide decks with `pdftotext` and recomputed counts with my own scripts. Nothing from the repositories was executed.
- Ten web searches (standard mode) for abstract-level cross-checks. No paper full text was read by me either (publisher/arXiv fetch is blocked), so "confirmed" means: confirmed against official code, prompt files, data files or author slides, NOT against the printed paper.
- Consequence for citing: every step is evidence about the released artefact. Where the bib key is cited for it, the wording should be "the released implementation/prompt/slides of X", unless the paper text is checked.

## Verdict summary

| Step | Verdict | Main point |
|---|---|---|
| G1-S01 | partially_confirmed | OntoChat split/abstract prompt exists only in a commented-out function at HEAD; paraphrase + clustering confirmed; Bench4KE generator instructions confirmed |
| G1-S02 | confirmed | app.py lines 763, 815-880, 894-898, 1481-1485 |
| G1-S03 | partially_confirmed | "always empty" and "considerable reduction" verbatim; the "outputs are merged afterwards" detail not found for Memoryless CQbyCQ |
| G1-S04 | confirmed | procedure.txt read in full, nine steps as described |
| G1-S05 | partially_confirmed | Pre-check confirmed (with "most likely (~90%)"); the same line is already in the LiU ESWC 2024 CQbyCQ prompt, so it is inherited, not new in lippolis2025ontology |
| G1-S06 | confirmed | 9 tasks / 7 constraints counted; mistakes list; zero hyperparameters; OntoChat temperature 0, seed 1234 |
| G1-S07 | partially_confirmed | Both quotes verbatim; the schema-miner grounding agent is follow-up work, not the ESWC 2025 paper cited by the key |
| G1-S08 | confirmed | Mandatory task 8, judge criteria 11 and 13, patterns_json |
| G1-S09 | confirmed | docstring, prompt line 982, log line 1591 |
| G1-S10 | confirmed | regex `(some|only)` at line 1200; fallback to base IRI; 62 artefact IRIs reproduced; Cl_ prefix prescribed and criticised |
| G1-S11 | confirmed | lines 1556-1569, 1592-1594, 1608-1613 |
| G1-S12 | confirmed | eval-prompt.MD read |
| G1-S13 | confirmed | MAX_JUDGE_RETRIES = 2, range(1, 4), errors[:20], empty-response hint |
| G1-S14 | confirmed | judge output contract, 14 criteria, same client for Gen and Judge, ValueError in hit_rate_evaluator.py, eval judge of another family |
| G1-S15 | confirmed | verbaliser.py 182-198, ontolib.py prompts and regex |
| G1-S16 | confirmed (slides only) | all figures are on the authors' slides; none checked against the paper |
| G1-S17 | confirmed | four headings, method-1/2/3 folders, cli.py prompt, template rules |
| G1-S18 | confirmed | prov task 9, validator warning line 1375, slide line "~30%" |
| G1-S19 | confirmed | judge criteria 6 and 7; validator read in full |
| G1-S20 | confirmed | 28 + 28 lines; 1,393 rows, 1,203 yes / 190 no; run folders |
| G1-S21 | confirmed (slides only) | four views, two engineers for CQ verification and for superfluous components, kappa 0.61 |
| G1-S22 | confirmed | HitRate.ttl; thresholds 0.6; ranges recomputed: hit rate 0.014-0.423, judge overall 3.71-4.71 |
| G1-S23 | confirmed | README quotes; abstract finding via web search (medium) |
| G1-S24 | confirmed | seven variants in run_ablation.py; Trials 1-4 |
| G1-S25 | confirmed | app.py A_first/B_first; survey.html lines 340-349 |

## Details per step

### G1-S01 (partially_confirmed)
- `ontochat/analysis.py` 150-203: `llm_cq_clustering` with optional paraphrase detection ("Perform paraphrase detection for the following competency questions") followed by topic clustering; `agglomerative_clustering` over `all-MiniLM-L6-v2` embeddings is a separate function. Confirmed.
- `ontochat/functions.py` 184-216: the prompt that splits compound questions and abstracts real-world entities is inside `# def cq_generator`, which is commented out at HEAD (61 of 250 lines are comments). The researcher's long report says so (line 290); the JSON step text does not.
- `restapi/cq_generator_app.py` 84-203: `_CLUSTERING`, `_ABSTRACTION_CONTROL`, `_TERMINOLOGY_CONSISTENCY`, "Do not output paraphrased duplicates.", JSON with `clusters` and `expected_answer_type`. Confirmed. Whether this generator is described in the Bench4KE paper was not checked.

### G1-S03 (partially_confirmed)
- `PromptingTechniques/README.md` line 3 confirms both quotes verbatim. I found the word "merging" only in the Ontogenia description (line 73: "generating and merging the resulting ontology at each step"). I did not find a statement that Memoryless CQbyCQ outputs are merged afterwards. Web summary (secondary) only says it handles one CQ at a time without earlier outputs.
- how_we_reuse says "the paper's expert sheets show duplicated classes in memoryless outputs". The theater sheet does contain "Duplicate classes, such as Cl_FestivalOccurrence", but I did not verify that this row refers to a Memoryless CQbyCQ output. Treat as unverified attribution.

### G1-S05 (partially_confirmed)
- Line 21 of the Memoryless prompt: "is this competency question answerable by the previous version of the RDF (given down) or not? (most likely (~90%) is it not answerable)". Confirmed.
- The same "most likely" sentence occurs in `LiUSemWeb/LLMs4OntologyDev-ESWC2024/Prompts/CQbyCQ.md` (1 match). The pre-check is therefore inherited from the ESWC 2024 CQbyCQ technique that Memoryless CQbyCQ modifies. Note also that in the memoryless variant the "previous RDF" slot is always empty, so the pre-check has nothing to check there; its usefulness in that paper is not demonstrated.

### G1-S07 (partially_confirmed)
- Busch prompt `DCAT_Theme_EUROLEX57K.txt` lines 10-21: "Assign the best matching EuroVoc IDs from this list", "output only the selected IDs as numbers formatted as a JSON array". Other prompts: YYYY-MM, Python list, country name only. Confirmed.
- `schema_miner/prompts/ontology_grounding/agent_qudt_prompt1.py` line 28: "if you have any doubts, return that the property cannot be grounded". Confirmed, but this module belongs to the follow-up grounding work in the refactored repository (v3.2.7), not to the ESWC 2025 paper behind `sadruddin2025schema`. Cite the repository, not the paper, for this part.

### G1-S10 (confirmed)
- `parse_restriction` regex `([A-Za-z0-9_\-]+)\s+(some|only)\s+(.+)`; `parse_prefixed_or_uri` falls through to `default_base[safe_local_name(t)]`. My own grep over `rigor_chinook_claude_ontology.owl` gives 62 distinct `rdf:about`/`rdf:resource` values with `_exactly_/_min_/_max_/...` in the local name (for example `#Album_AlbumId_exactly_1_xsd_integer`). The causal link "parser turned cardinality expressions into named IRIs" is the researcher's (plausible) inference; neither of us ran the parser.
- "Important: Class names have Cl_ as the prefix for example Cl_Professors" is in the Memoryless prompt (and in the LiU prompt it derives from). Expert comments "Why the strange naming of classes with a Cl_-prefix?" (theater) and "Again the annoying naming of the classes, with Cl_" (music) confirmed.

### G1-S11 (confirmed, one nuance)
- Per-table re-validation is scoped to that one table (`{table_name: schema[table_name]}`), the in-loop validation to the tables processed so far, the final validation to the whole schema; failures raise `RuntimeError`.

### G1-S14 (confirmed)
- `JudgeLLM(llm_client)` and `OntologyLLM(llm_client)` share one `OpenRouterLLM` client (lines 1451-1453); judge temperature is 0.1. `eval.py` line 100-103: `JUDGE_MODEL = "openai/gpt-5.4"`, "from a different model family than all three generators". Bench4KE: `raise ValueError("evaluator_llm must differ from tool_llm ...")` only when `tool_llm` is declared.
- The arXiv v1 abstract (web search) says fragments are validated by "human reviewers or an auxiliary Judge-LLM"; the human option is not in `app.py`.

### G1-S16, G1-S21 (confirmed against slides only)
- OE-Assist slides: 19 users; 20 tasks, 10 with suggestions; Yes / No / I don't know plus 1-5 difficulty; "The order of the tasks was randomized every time"; "Overall performance did not change significantly"; "No significant difference between o1-preview and Ontology Engineers"; -28% / +13%; both mitigations verbatim.
- Onto-Generation slides: "Performed manually by two ontology engineers" appears under CQ verification and under superfluous components; "Generally, ~30% of generated classes and properties were superfluous"; "Llama ... almost 40%"; kappa 0.61; expert evaluation "(i) Comments on usability, completeness and accuracy. (ii) Assessment concerning intended modelling." "maybe" occurs in the theater and music sheets; I did not inspect the sheet layout cell by cell.
- These numbers must be cited as "authors' slides" until the paper text is read.

### G1-S20 (confirmed)
- `grep -c .` gives 28 non-empty lines in each OntoChat CQ file (`wc -l` shows 27 because the last line has no newline). OntoEval.csv: 1,393 rows, Annotations yes 1,203 / no 190; slides table says 1,204 modelled. OntoEval small: 20 rows, settings a/b 10 each. Run folders: GPT-4o Run1-3, O3-mini Run1-3, O1-preview single.

### G1-S22 (confirmed)
- My recomputation over the five `*_US_validation_results.csv` files: hit rate 0.014 (Pan) to 0.423 (NeOn-GPT); judge overall mean 3.71 (OntoChat) to 4.71 (Pan). The contrast is our reading of stored files, as the researcher already states. Each file has only 2-5 scenario rows.

### G1-S25 (confirmed, one nuance)
- The study tool offers `A_first` / `B_first`; the slides say task order was randomised. Neither source says "counterbalanced"; that word is our design, and the step name should not suggest the paper did it.

## Overreach flags (how_we_reuse goes beyond the source; label as our own adaptation)

- G1-S03: the claim about duplicated classes "in memoryless outputs" is not tied to a verified sheet row; pairing with retrieval over pending changes is ours.
- G1-S07: the source is instance-level value extraction (closed list of EuroVoc ids) and a follow-up grounding agent; an enum-constrained choice of property/class IRIs in a profile is our transfer.
- G1-S12: the paper has an LLM write SPARQL over an OWL ontology for a competency question; a rule-derived witness query over a compiled SHACL shapes graph for a requirement atom is a different mechanism and ours.
- G1-S18: "superfluous rate zero by construction" is an untested claim about our pipeline (a change can carry a coverage link and still be unnecessary); RIGOR's provenance points to schema elements, not requirements.
- G1-S19: RIGOR's "preserved or strengthened" concerns PK/not-null/unique restrictions of a direct mapping, enforced by an LLM judge criterion; "may tighten, never loosen" facet comparison against DCAT-AP is our rule (and should rather be grounded in the DCAT-AP / SEMIC reuse guidelines).
- G1-S23: "only retrieved candidates may be used" does not follow from mai2024adapt, which reports that fine-tuning helps; the masked-vocabulary condition is our experiment design inspired by it.

## Paper-level corrections

1. fathallah2026rigor: the only paper version I could find by search is arXiv v1 (June 2025), which describes validation by "human reviewers or an auxiliary Judge-LLM" and an evaluation on TWO medical databases (liver cancer registry, PhysioNet ICU) with six CQ-scoring dimensions. The repository (three schemas incl. Chinook, deterministic direct-mapping backbone, seven dimensions, three generator LLMs) reflects a later revision. I could not confirm that a v2 exists on arXiv, nor the ISWC 2026 acceptance, except through the repository's own BibTeX (README line 276-277). `eval.py` line 4-5 says "as required by the ESWC 2026 reviewer feedback". The summary should say "per the repository at HEAD 88c5820", not "the paper".
2. fathallah2026rigor: `eval.py` header says "6 dimensions" while the code list (line 851) and README (line 172) have 7 (domain_enrichment added). "Seven" is right for the code; the inconsistency is in the repository.
3. lippolis2025ontology: the arXiv listing (via search) describes the benchmark as "ten ontologies with 100 distinct CQs and 29 different user stories"; "7 domains" is from the slides only. The "Cl_" prefix and the answerability pre-check are inherited from the ESWC 2024 CQbyCQ prompt (LiU repository), not introduced by this paper.
4. zhang2024ontochat: the split/abstract CQ-extraction prompt is in commented-out code at HEAD; the JSON summary presents it in the present tense. Search confirms presentation in the ESWC 2024 Special Track on LLMs for Knowledge Engineering and evaluation by replicating the Music Meta ontology; participant numbers not confirmed. One AI-generated review site mentions 87.5% accuracy for the CQ checker: unverified, do not cite.
5. lippolis2025bench4ke: versions disagree. Search snippets: v1 abstract "four real-world ontology projects" and four systems; a later version "17 real-world projects"; a secondary listing "6 systems". The repository says 17 projects / 843 CQs (maintenance.md line 74) and stores results for five tools. Take all counts from the ESWC 2026 proceedings version before citing.
6. sadruddin2025schema: search confirms three stages and that combining descriptive feedback with direct schema editing is reported as best (secondary summary, medium). A search summary speaks of "eight co-authors" while the bib entry lists ten authors: check the author list against the proceedings. Stage 3 at HEAD uses `prompt_template2` (extract_schema.py line 167) although a `prompt_template3.py` exists: confirmed.
7. busch2025dcat: search confirms publication in DATA 2025 (SciTePress), pp. 299-309, DOI 10.5220/0013458500003967; the bib entry is still @misc/arXiv only and should be updated after a check of the SciTePress page.
8. mai2024adapt: abstract-level finding confirmed by search. A secondary summary lists Falcon-40B among the tested models; the repository README lists GPT-3.5, GPT-4, Llama-2-13B-chat and Zephyr-7B-beta. Do not state the model list as complete without the paper.
9. lippolis2025oeassist: search confirmed arXiv 2507.14552, the title and the 1,393-CQ dataset, but not the ISWC 2025 venue or authors (those come from the bib entry). Slides say 1,204 modelled CQs, the released CSV has 1,203.
10. General: all 25 steps carry confidence "high". For G1-S16 and G1-S21 (slides only), the Bench4KE result contrast in G1-S22 (our reading) and the schema-miner part of G1-S07 (follow-up code), "high" holds for the artefact, not for the cited paper.
