# G4-llm-reliability: sceptic's verification report

Date: 13 November 2026. Scope: the 24 reusable steps and 19 per-paper summaries of `G4-llm-reliability.md`.

## How I checked

- Code claims: re-read independently in the cloned repositories under `/home/user/refs/` (grep and file reads, nothing executed):
  U0iS112__654321 (commit 074ddfc), lm-sys__FastChat, i-Eval__FairEval, nlpyang__geval, ypw0102__BatchEval,
  composable-models__llm_multiagent_debate, composable-models__llm_debate (project page), instadeepai__DebateLLM,
  deeplearning-wisc__debate-or-vote, breckbaldwin__llm-stability (v2 PDF via pdftotext, evaluate.py, notebooks),
  princeton-nlp__ALCE (preprint PDF via pdftotext, eval.py, prompts), google-research-datasets__AIS, hitz-zentroa__lm-contamination,
  usnistgov__trec_eval, ShuyinOuyang__LLM-is-a-box-of-chocolate, and the Stureborg poster PDF.
- Abstract-level claims: my own web searches (Nii, Hearsay-II, Choi et al., FairEval, AIS, Voorhees, Zobel, Smit et al., Chmielewski, Atil et al., G-Eval).
- Limits: WebFetch failed for ar5iv.labs.arxiv.org and en.wikipedia.org (hosts not allowed); no further hosts tried.
  The shared web-search budget ran out before I could re-check four abstract-level items: the Ouyang et al. abstract numbers,
  the Stureborg et al. arXiv abstract, the Zheng et al. abstract (bias catalogue), and the Buckley and Voorhees abstract.
  Those remain exactly as unverified as the researcher marked them. No paper full text was read by me beyond the ALCE preprint,
  the Atil v2 PDF, the Ouyang appendix and the Stureborg poster.

## Verdicts per step

| Step | Verdict | What I found |
|---|---|---|
| S01 | partially_confirmed | Search supports: knowledge sources communicate only through the blackboard, hypotheses on levels, KS triggered by blackboard events, a scheduler choosing one action, a "focus-of-control mechanism to identify potential actions" (Hearsay-II). Not found: the terms "blackboard monitor" and "condition-action", "limited resources ... most promising first" (only a 2026 blog says this), and Nii's own three-component wording. |
| S02 | confirmed | attribute_mapper.py: state has candidates / validated_candidates / matrix / final_mapping; four signal methods each return accepted + reason "in the same array position"; selection prompt "You MUST accept exactly ONE candidate", output accepted + reason per candidate. |
| S03 | confirmed | blackboard_semantic_mapping.py l.225 `results = {"attributes","evaluation","discussions"}`, before/after evaluation, reasoning_effect; FastChat common.py result dict holds judge (model, prompt name), user_prompt, judgment, tstamp. |
| S04 | confirmed | "DO NOT output the TTL triple itself." (l.105, l.159); accepted = rdf_syntax_ok and subject_in_ontology and predicate_in_ontology and predicate_is_datatype_property and range_ok. Note: the "property type" check is specifically "is a datatype property". |
| S05 | partially_confirmed | Atil v2 PDF: "We set the temperature to 0, top-p to 1, and fix the seed"; raw agreement far below answer agreement; output length vs stability sentence present. Notebooks confirm schema and strict-mode statements. Two details too strong: the fixed-seed setting is Atil et al. only (not shown for Ouyang et al.), and the single-job result is one task and one model, 10 runs of 100 questions ("deterministic so far"). |
| S06 | partially_confirmed | Choi abstract (search): voting alone accounts for most gains across seven benchmarks; martingale; "debate alone does not improve expected correctness". Code: 5 agents, 5 rounds default, majority with random tie-break. Smit abstract (search): debate does not consistently beat self-consistency/ensembling, but the same abstract says tuned debate (agreement modulation) can outperform the non-debate protocols tested; the step omits this. Du et al.: most_frequent is used in eval_gsm.py, eval_mmlu.py and gen_math.py, not for biographies. |
| S07 | partially_confirmed | All quoted prompt rules found in discussion_engine.py and reasoning_agent.py; conclusion labels found. Detail: the 3-turn limit is the default argument `amount_turns = 3` that the reasoning agent writes into the discussion JSON; the engine itself falls back to 4 (`discussion.get("max_turns", 4)`) and does not enforce 3. Choi part: abstract says interventions "biasing the belief update toward correction" help. |
| S08 | confirmed | compute_reasoning_effect lists before/after per changed attribute; final_evalutions_signals.py counts amount_change/better/worse/same for weak and strong; DebateLLM systems.py defines changed_answer, relied_on_other, bullied_by_other as described. |
| S09 | confirmed | google_ma_debate.yaml suffix_seperator_0..10 (eleven levels, wording as quoted); README l.114: about 15% (Multi-Persona) and about 5% (SoM) on USMLE. |
| S10 | confirmed | judge_prompts.jsonl: "Begin your evaluation by providing a short explanation ... After providing your explanation, you must rate ... strictly following this format"; common.py temperature=0, rating = -1, winner = "error"; FairEval "Evaluation evidence:"; eval_conversation.py: yes/no/uncertain, uncertain returns None and is not appended. |
| S11 | confirmed | show_result.py l.64: tie if g1 is tie or g1 != g2; common.py l.569 "inconsistent"; FairEval.py l.91 gen_prompt(ques, ans2, ans1), scores mapped back and pooled. |
| S12 | partially_confirmed | FairEval: temperature=1, n=args.k (default 3), mean over all samples including the swapped-order ones. G-Eval gpt4_eval.py: n=20, temperature=2, max_tokens=5; meta_eval averages. "As a stand-in for a probability-weighted score" is the researcher's interpretation; I saw no source for it in this task. |
| S13 | partially_confirmed | Search of the abstract: "balanced position diversity entropy to measure the difficulty of each example and seeks human assistance when needed". That the entropy is computed over samples times both orders is not confirmed; README and script contain nothing on it. |
| S14 | confirmed | con_detailed.txt: one metric, criterion definition, numbered steps, form; poster text: earlier-dimension scores bias later ones, sparse use of 1-100 (peaks at 90, 95; 1-60 almost unused), "deterministic, non-CoT prompting with a 1-10 score granularity and using GPT-4 performed the best". Source is the short poster version with a different title, not the cited arXiv paper. |
| S15 | confirmed | Get_usr_batch.py: batchsize default 10, iteration_round default 5, sort by model score then stride so each batch spans strata, shuffle within batch; prompt text as quoted; calulate_usr.py takes the mean across rounds; README: 10.5% Pearson, 64% API cost. |
| S16 | partially_confirmed | G-Eval abstract (search): potential bias towards LLM-generated texts. Poster: GPT-4 biased toward low-perplexity summaries; the "generated by itself" sentence is offered as an implication, not a measured result. FastChat prompt forbids position, length and name bias. MT-Bench "self-enhancement bias" not independently confirmed (search returned nothing, budget then exhausted). |
| S17 | partially_confirmed | AIS README and CSVs: majority of 5, AIS only when INT = 1, Flagged, Q1/Q2 wordings exactly as stated, agreement counts. Search: definition uses a "standalone proposition" and an "according to" test. "Explicature" not confirmed. Flagged means the task is malformed so that no judgment is possible. |
| S18 | confirmed | ALCE PDF section on citation precision ("does not require citing a minimal set ..."; "irrelevant" iff alone not entailing and the rest still entailing; partial support limitation); eval.py: no citation or out-of-range citation gives joint_entail = 0 without an NLI call; leave-one-out only when recall is 1 and more than one citation. Extra detail: eval.py truncates to the first 3 citations by default (at_most_citations=3). |
| S19 | partially_confirmed | PDF: n = 4, best by automatic citation recall, "at a cost of n times more compute"; RERANK was included in the human evaluation and the paper notes human and ALCE scores are close "except for RERANK (which uses the automated citation recall for reranking)". "Correctness did not rise" not checked by me in the tables; the "because" in the last clause is the researcher's reading. |
| S20 | confirmed | compute_agreement.py (with and without tie, GPT-4 vs human and human vs human); FastChat README "over 80% agreement"; ALCE PDF: kappa 0.698 / 0.525, accuracy 85.1% / 77.6%, detection recall/precision 82.3/84.2 and 75.6/66.1; AIS agreement counts. ALCE figures are from the May 2023 preprint. |
| S21 | confirmed | Atil v2 PDF defines TARr@N and TARa@N and reports min/median/max; evaluate.py has best_possible_accuracy and worst_possible_accuracy; Ouyang repo: logs for topn_1 (five separate logs) and topn_5 at temperature 0, 0.5, 1; README names test pass rate and OER; appendix example 3/7, 4/7, 5/7 at temperature 0. |
| S22 | confirmed | CONTRIBUTING.md prompt and the contaminated / suspicious / clean definitions, number of executions plus screenshot as evidence; data.json has 375 rows; abstract in README: levels of contamination, flagging papers. The protocol is from the companion index, not from the paper text (the researcher says so). |
| S23 | confirmed | m_bpref.c comment "dependent on only judged docs; no assumption of non-relevance if not judged" and citation of the SIGIR 2004 paper; m_unjudged.c "red flag" wording; Zobel abstract (search): relative performance reliable, recall overestimated, new pooling strategy. |
| S24 | confirmed | Search (NIST slides, secondary summaries, IP&M abstract): three judgment sets for TREC-4 and two for TREC-6, union and intersection qrels, Kendall's tau, rankings highly correlated despite substantial disagreement. Secondary level only; Waterloo and numeric values not confirmed. |

## Overreach flags (how_we_reuse reads as if the work prescribed our design)

S04 ("Confirms 'typed ProfileChange, never free SHACL'": one prototype doing the same is not a confirmation),
S06 (none of the three works prescribes "no free debate"; Smit et al. also report tuned debate winning),
S07 (the "verifier results as fixed facts" and the allowed-action set are ours; Choi et al. only say biased updates help),
S13 (auto-accept only at entropy 0 is our rule),
S15 (BatchEval scores text quality; using batches to detect unequal treatment of requirements is a new use),
S16 (separate judge family, hiding the rationale and term masking are not proposed by the cited works),
S20 (the sample size of about 100 links and "licenses automatic acceptance" are ours),
S22 (asking a model what a profile adds to its base is a different probe from regenerating a dataset split),
S23 (treating a gold profile as an incomplete judgment set is an analogy from document retrieval to profile elements).

## Paper-level corrections and notes

See the structured output; the main ones concern the 3-turn limit in SAST-Blackboard, the omitted second half of the Smit et al. abstract,
the unconfirmed "explicature" and "blackboard monitor" wordings, and the small size of the single-job determinism experiment.

## Hosts that would have to be allowed to raise the medium items

ar5iv.labs.arxiv.org, en.wikipedia.org (both failed to resolve), plus the hosts already listed by the researcher.
