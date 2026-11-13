# G4 — Making LLM decisions reliable and auditable

Debate versus vote, LLM-as-judge, attribution and citation quality, benchmark contamination, non-determinism,
the blackboard model, and evaluation with incomplete or disagreeing judgments.

Research note for the **requirement-based-dcat-profile-extensioner** (RBDPE). Written 13 November 2026.
Bibliography keys covered (19): `du2024debate`, `smit2024mad`, `choi2025debate`, `zheng2023judge`, `liu2023geval`,
`wang2024fair`, `stureborg2024inconsistent`, `yuan2024batcheval`, `rashkin2023ais`, `gao2023alce`,
`sainz2023contamination`, `ouyang2025nondeterminism`, `atil2025nondeterminism`, `erman1980hearsay`,
`nii1986blackboard`, `chmielewski2026blackboard`, `zobel1998reliable`, `voorhees2000variations`, `buckley2004incomplete`.

---

## 0. How to read this note

**Two voices, kept apart.** Every entry separates *(A) what the work did or prescribes* from *(B) how we could adapt it*.
(B) is our design proposal. It is never a claim made by the cited work.

**Confidence labels.**

| Label | Meaning |
|---|---|
| high | Seen in a primary source during this task: an official code repository, a paper PDF shipped inside an official repository, or an official tool (NIST `trec_eval`) |
| medium | From an abstract or a secondary summary (server-side web search summaries of arXiv, ACL Anthology, publisher and author pages) |
| low / `verify:` | Not confirmed in this task. Listed in section 8 |

**Access limits that shape the confidence levels.** From this container only public GitHub clones and
`raw.githubusercontent.com` work. `arxiv.org`, `aclanthology.org`, `proceedings.mlr.press`, `proceedings.neurips.cc`,
`openreview.net`, `ceur-ws.org`, `dl.acm.org`, `api.crossref.org`, `api.semanticscholar.org`, `dblp.org` and
`huggingface.co` were refused by the network proxy (one probe each; WebFetch failed the same way on `arxiv.org`).
Web search runs server-side and returns summaries, not pages, so I **paraphrase** search-derived material and
**quote only from files I opened**.

**What I read in full or in the relevant parts** (untrusted reference data, read only, nothing executed):

| Local clone under `/home/user/refs/` | Commit (date) | Serves key | What it contains |
|---|---|---|---|
| `princeton-nlp__ALCE` | `246c476` (2024-10-09) | `gao2023alce` | `eval.py`, prompts, human-evaluation data, **the paper PDF** (`paper/ALCE.pdf`, preprint of 24 May 2023) |
| `google-research-datasets__AIS` | `d3c826d` (2023-01-14) | `rashkin2023ais` | README, four annotation CSV files with the annotators' answer wordings |
| `lm-sys__FastChat` (`fastchat/llm_judge/`) | `587d5cf` (2025-06-02) | `zheng2023judge` | judge prompts, judge runner, swap logic, agreement script |
| `i-Eval__FairEval` | `453c117` (2023-09-10) | `wang2024fair` | `FairEval.py` (MEC and BPC), human labels |
| `nlpyang__geval` | `6f84404` (2024-02-03) | `liu2023geval` | prompts, scoring script, meta-evaluation script |
| `ypw0102__BatchEval` | `afa3898` (2024-05-20) | `yuan2024batcheval` | batch prompts, iteration and re-batching script, README with the abstract |
| `_single_files/G4/southnlp2024-poster-42.pdf` | fetched 2026-11-13 | `stureborg2024inconsistent` | 3-page poster paper by the same authors (short version, different title) |
| `composable-models__llm_multiagent_debate` | `9846749` (2025-04-24) | `du2024debate` | debate scripts for arithmetic, GSM, MMLU, biographies |
| `composable-models__llm_debate` | `858ed7f` (2026-09-13) | `du2024debate` | the authors' project page (abstract, settings) |
| `instadeepai__DebateLLM` | `1386095` (2024-04-18) | `smit2024mad` | eight protocols, prompt configs, metrics, README with findings |
| `deeplearning-wisc__debate-or-vote` | `82c929e` (2025-10-15) | `choi2025debate` | debate and vote runner, evaluator |
| `U0iS112__654321` | `074ddfc` (2025-12-07) | `chmielewski2026blackboard` | **SAST-Blackboard**: the system's code (commit by co-author Jan Schindler) |
| `jundahuang9123__blackboard-workbench` | `aaf7057` (2026-10-07) | supporting, not a bibliography entry | the author's own review workbench around SAST-Blackboard; names the upstream repository |
| `breckbaldwin__llm-stability` | `c089c02` (2025-11-11) | `atil2025nondeterminism` | `evaluate.py`, the **v2 paper PDF**, follow-up experiment notebooks |
| `ShuyinOuyang__LLM-is-a-box-of-chocolate` | `23d9172` (2024-08-04) | `ouyang2025nondeterminism` | request and similarity scripts, logs, `Appendix.pdf` |
| `hitz-zentroa__lm-contamination` | `7f1fe69` (2024-04-11) | `sainz2023contamination` | protocol, blog post, index data, paper abstract |
| `usnistgov__trec_eval` | `35cf096` (2026-10-15) | `buckley2004incomplete` | Buckley's own `bpref` implementation, the `unj` measure, the `bpref_bug` notice |

No full text was read for: `choi2025debate`, `zheng2023judge`, `liu2023geval`, `wang2024fair`, `yuan2024batcheval`,
`rashkin2023ais`, `sainz2023contamination`, `ouyang2025nondeterminism` (code and abstracts only),
`stureborg2024inconsistent` (short version only), `atil2025nondeterminism` (v2 read, v5 is cited),
`chmielewski2026blackboard` (code only), and the five classics `erman1980hearsay`, `nii1986blackboard`,
`zobel1998reliable`, `voorhees2000variations`, `buckley2004incomplete` (search summaries; for the last one also the tool).

**To raise the medium items to high**, these hosts need to be allowed in the session's network settings:
`arxiv.org`, `aclanthology.org`, `proceedings.mlr.press`, `proceedings.neurips.cc`, `direct.mit.edu`, `dl.acm.org`,
`ojs.aaai.org`, `dbis.rwth-aachen.de` (SDS 2026 pre-prints), `ceur-ws.org`.

---

## 1. Short answer: what this group gives RBDPE

1. **Vote first, debate only where a verifier can inject truth.** The three debate studies, read together, say: debate
   beats a single agent (`du2024debate`), does not reliably beat self-consistency or ensembling and is sensitive to
   its hyperparameters (`smit2024mad`), and most of its gain is explained by majority voting alone
   (`choi2025debate`). RBDPE's current design (N independent proposals, majority over the decision signature, no
   majority means human review) is the well-supported default. Steps G4-S06 to G4-S09.
2. **The 2026 blackboard paper is findable as code.** `chmielewski2026blackboard` is SAST-Blackboard; its repository is
   named in the author's own `blackboard-workbench`. It implements the pattern RBDPE is built around: typed candidates,
   a deterministic validator, one agent per evidence signal writing accept/reject plus reason into a per-candidate
   matrix, a selection step, then a *selective, bounded* discussion with a closed command set, and a before/after
   evaluation of what the discussion changed. Steps G4-S02, G4-S03, G4-S04, G4-S07, G4-S08.
3. **Attribution has an operational definition and two metrics we can port one-to-one.** AIS asks whether a statement
   holds *according to* the identified source and judges it in two stages (understandable? then fully attributable?).
   ALCE turns this into citation recall (do all cited sources together support the statement) and citation precision
   (is each cited source needed, tested by leave-one-out). In RBDPE the statement is a facet of a profile change and
   the source is a requirement atom. Steps G4-S17 to G4-S19.
4. **LLM judges have documented, fixable failure modes.** Position bias: run both orders and treat disagreement as
   "inconsistent". Evidence before verdict, several sampled judgements, one criterion per call, a coarse scale, and a
   measured agreement with humans before the judge is trusted. Steps G4-S10 to G4-S16, G4-S20.
5. **Temperature 0 is not determinism; the stored answer is the record.** RBDPE's replay cache already follows from
   this. What is missing is the *measurement*: total agreement rate over raw answers and over parsed decisions,
   min/median/max instead of mean, best-possible and worst-possible scores over N runs. Steps G4-S05, G4-S21.
6. **Contamination must be measured per model and per benchmark profile**, with a recorded probe and a three-level
   label. Step G4-S22.
7. **A gold profile is an incomplete judgment set.** IR evaluation says: do not count unjudged items as wrong, report
   how much of the output was unjudged, pool the outputs of all conditions for adjudication, and claim only the
   comparisons that stay stable when the judge changes. Steps G4-S23, G4-S24.
8. **The classic blackboard model gives the vocabulary** for the architecture section: a shared, levelled solution
   record; independent knowledge sources that interact only through it; a separate control component that decides
   what runs next. Step G4-S01.

Three concrete observations on the current RBDPE snapshot follow from the literature (ours, section 5): the judge's
output schema puts `verdict` before `explanation` (evidence-first would reverse it); the replay-cache key does not
include `temperature`; and automatic acceptance uses the model's self-reported `confidence`, for which none of the
works read here offers support.

---

## 2. Overview

| Key | Work | Found | What I actually saw | Depth |
|---|---|---|---|---|
| `gao2023alce` | Enabling LLMs to generate text with citations (EMNLP 2023) | yes | paper PDF (preprint in repo), `eval.py`, prompts, human-eval data | deep |
| `rashkin2023ais` | Measuring attribution in NLG models (CL 2023) | yes | official annotation data and README; definition via search summaries | deep (data), medium (definition) |
| `zheng2023judge` | Judging LLM-as-a-judge with MT-Bench and Chatbot Arena (NeurIPS 2023) | yes | official judge code and prompts; abstract-level findings | deep (code) |
| `wang2024fair` | LLMs are not fair evaluators (ACL 2024) | yes | official `FairEval.py`; abstract-level findings | deep (code) |
| `liu2023geval` | G-Eval (EMNLP 2023) | yes | official prompts and scripts; abstract-level findings | deep (code) |
| `chmielewski2026blackboard` | Signal-aware semantic typing via blackboard-orchestrated LLMs (SDS 2026) | yes, **paper text not seen** | the system's code repository in full; workshop listing via search | deep (code) |
| `atil2025nondeterminism` | Non-determinism of "deterministic" LLM settings (arXiv v5) | yes | v2 paper PDF, `evaluate.py`, follow-up notebooks; v5 abstract via search | deep |
| `du2024debate` | Multiagent debate (ICML 2024) | yes | official scripts and project page | medium-deep |
| `smit2024mad` | Should we be going MAD? (ICML 2024) | yes | official library, prompt configs, README | medium-deep |
| `choi2025debate` | Debate or vote (NeurIPS 2025) | yes | official code; conclusions via search summaries | medium-deep |
| `yuan2024batcheval` | BatchEval (ACL 2024) | yes | official prompts, scripts, README abstract | brief-plus |
| `stureborg2024inconsistent` | LLMs are inconsistent and biased evaluators (arXiv 2405.01724) | yes | 3-page poster version by the same authors; arXiv abstract via search | brief-plus |
| `sainz2023contamination` | NLP evaluation in trouble (Findings of EMNLP 2023) | yes | official index repository: protocol, blog, abstract | brief-plus |
| `ouyang2025nondeterminism` | Non-determinism of ChatGPT in code generation (TOSEM 2025) | yes | official scripts, logs, appendix PDF; abstract via search | brief-plus |
| `buckley2004incomplete` | Retrieval evaluation with incomplete information (SIGIR 2004) | yes | Buckley's `bpref` source in `trec_eval`; abstract via search | brief-plus |
| `erman1980hearsay` | The Hearsay-II speech-understanding system (ACM CSUR 1980) | yes | search summaries only | brief |
| `nii1986blackboard` | The blackboard model of problem solving (AI Magazine 1986) | yes | search summaries only | brief |
| `zobel1998reliable` | How reliable are the results of large-scale IR experiments? (SIGIR 1998) | yes | abstract-level summaries | brief |
| `voorhees2000variations` | Variations in relevance judgments (IP&M 2000) | yes | abstract-level summaries | brief |

---

## 3. Findings per topic

### 3.1 Attribution and citation quality — `gao2023alce`, `rashkin2023ais`

#### (A) What `rashkin2023ais` did

- **Definition (medium, search summaries of the arXiv and journal versions).** "Attributable to Identified Sources"
  (AIS) holds that generated statements about the external world must be verifiable against a provided source. The
  test is whether a generic hearer would accept "According to P, s" for source P and statement s. The statement is
  judged in its contextual meaning (its *explicature*: a de-contextualised, standalone proposition), and the simple
  case of a standalone proposition is defined first.
- **Two-stage annotation (high, official data repository).** The released files hold two questions per item. Q1
  interpretability, with the recorded answers "Yes, I understand it." and "No, the response is unclear."; Q2
  attribution, with "Yes, fully attributable." and "No, not fully attributable.". The README states: "Attribution
  judgements were given only to outputs that were marked as `1` in the `INT` column." Each label is "by majority out
  of 5" annotators, the number of agreeing annotators is stored per item (`# agree (INT)`, `# agree (AIS)`), and a
  third field `Flagged` marks items "malformed such that it is impossible to make interpretability and attribution
  judgments".
- **Scope of validation.** Four source datasets: two conversational sets (QReCC, Wizard of Wikipedia), one
  summarisation set (CNN/DM), one table-to-text set (ToTTo). Counts in the files: 1,390, 997, 798 and 1,378 rows.
- Evidence: `/home/user/refs/google-research-datasets__AIS/README.md`, `ann_*.csv`.

#### (A) What `gao2023alce` did

Source: `/home/user/refs/princeton-nlp__ALCE/paper/ALCE.pdf` (the preprint of 24 May 2023 shipped in the official
repository; numbers may differ from the EMNLP camera-ready) and `eval.py`.

- **Benchmark.** ALCE evaluates LLM answers with citations on ASQA, QAMPARI and ELI5 along three dimensions:
  fluency, correctness, citation quality.
- **Entailment model.** An NLI model (TRUE, a T5-11B model; `AUTOAIS_MODEL="google/t5_xxl_true_nli_mixture"`)
  decides whether a premise entails a hypothesis. Input format in code: `"premise: {} hypothesis: {}"`, entailed when
  the output is `"1"`.
- **Citation recall** (§3.3): per statement, 0 or 1, averaged over statements. "its citation recall is 1 if and only
  if there is at least one citation (Ci ≠ ∅) and ϕ(concat(Ci), si) = 1". The paper ties this to AIS: entailment by
  the concatenated citations "implies that si is true based solely on concat(Ci)".
- **Citation precision**: per citation, 0 or 1, averaged over citations. A citation is "irrelevant" when two
  conditions hold: "(a) ϕ(ci,j, si) = 0, AND (b) ϕ(concat(Ci \ {ci,j}), si) = 1". A citation scores 1 if the statement
  has recall 1 and the citation is not irrelevant. The design choice is explicit: the measure "does not require
  citing a minimal set and it permits citing redundant passages entailing similar claims".
- **Code behaviour** (`compute_autoais`): a statement without any citation, or with a citation index out of range,
  gets recall 0 **without calling the model**; the leave-one-out precision test runs only for statements with more
  than one citation and recall 1; statistics on multi-citation sentences and over-citation are printed.
- **Stated limit.** The algorithm "overlooks the scenario when one citation partially supports the statement".
- **Prompt for generation with citations** (`prompts/asqa_default.json`): the instruction asks to use "only the
  provided search results (some of which might be irrelevant)", to "Always cite for any factual claim", and to
  "only cite a minimum sufficient subset of the documents". Two in-context demonstrations are prepended.
- **Post-editing by attribution (RERANK, §4.3).** "We randomly sample n (n = 4 in our experiments) responses for each
  question, and select the best response using the automatic citation recall score." Finding: it improves citation
  quality, "does not improve the correctness and costs n times more compute"; because the automatic score is then
  optimised directly, the authors check this condition with humans.
- **Validation of the automatic metric against humans (§6).** Annotators judged recall on (sentence, all cited
  passages) and precision on (sentence, one citation) with three levels: fully, partially, does not support. Reported:
  Cohen's kappa between human and automatic 0.698 for recall and 0.525 for precision; accuracy against human labels
  85.1% and 77.6%; detecting insufficient citations with recall 82.3% and precision 84.2%; detecting irrelevant
  citations with recall 75.6% and precision 66.1%, with the explanation that the NLI model cannot see partial
  support and therefore produces false positives.
- **Findings worth knowing.** On ELI5, 49% of the baseline's generations were not fully supported by their
  citations. A closed-book answer with citations added afterwards reaches good correctness and poor citation quality
  (ASQA citation recall 26.7% against 73.6% for the retrieve-then-cite baseline).

#### (B) Adaptation for RBDPE (ours)

- **Units.** Statement = one facet justification of a `ProfileChange` (or the claim "this element exists" for the
  change as a whole). Citations = the atoms in `FacetJustification.atom_ids` (or `covers`). Premise = the atom
  statement(s) only.
- **Trace recall**: share of facets whose cited atoms jointly support them. **Trace precision**: share of
  (facet, atom) links that are not irrelevant by the two-condition leave-one-out rule. Recall failure is an error
  (repair or review); a precision failure is a "superfluous link" warning.
- **Two questions for the judge and for the human reviewer**, in AIS order: is the verbalised change understandable
  on its own; is it fully attributable to the cited atoms alone. The existing judge prompt already forbids outside
  knowledge ("do not rely on what published profiles do"), which matches what ALCE, citing AIS, calls being true
  "based solely on" the cited source.
- **Closed-book warning.** The ALCE closed-book result is the argument for RBDPE's order of operations: retrieve and
  read the atom first, then propose with the link, never propose from model memory and attach atoms afterwards.
- **Do not reuse a metric you optimised.** If trace recall is used to pick among sampled proposals (G4-S19), it
  cannot also be reported as an independent quality result for that run.

---

### 3.2 LLM-as-judge — `zheng2023judge`, `wang2024fair`, `liu2023geval`, `yuan2024batcheval`, `stureborg2024inconsistent`

#### (A) `zheng2023judge` (code: `fastchat/llm_judge/`)

- **Three grading modes**: single-answer grading on a 1–10 scale (the README's recommended default for MT-Bench),
  pairwise against a baseline, pairwise over all pairs.
- **Prompt contract** (`data/judge_prompts.jsonl`): explanation first, verdict last, in a strict pattern. Single:
  "Begin your evaluation by providing a short explanation. … strictly following this format: "[[rating]]"". Pairwise
  adds explicit bias instructions: "Avoid any position biases and ensure that the order in which the responses were
  presented does not influence your decision." and "Do not allow the length of the responses to influence your
  evaluation. Do not favor certain names of the assistants."
- **Reference-guided judging** for the categories where the judge itself is weak (`NEED_REF_CATS = ["math",
  "reasoning", "coding", "arena-hard-200"]`): the prompt adds a reference answer and says "Begin your evaluation by
  comparing the assistant's answer with the reference answer. Identify and correct any mistakes."
- **Position swap.** `play_a_match_pair` calls the judge twice, once per order. Aggregation in `show_result.py`:
  `if row["g1_winner"] == "tie" or row["g1_winner"] != row["g2_winner"]:` both models get a tie. The loader names the
  disagreeing case explicitly: `winner = "inconsistent"`.
- **Run settings and record.** Judge calls use `temperature=0`. An unparseable answer becomes rating `-1` or winner
  `"error"` and is filtered out later. Every judgement line stores the full `user_prompt`, the `judgment` text, the
  judge as `(model_name, prompt name)` and a timestamp.
- **Validation against humans.** `compute_agreement.py` computes judge-human and human-human agreement, with and
  without ties. README: "humans and GPT-4 judge achieve over 80% agreement, the same level of agreement between
  humans."
- **Bias catalogue (medium, abstract and secondary summaries).** Position bias, verbosity bias, self-enhancement
  bias, limited ability to grade math and reasoning. A table in the paper reports, per judge, consistency under swap,
  the share biased toward the first position, and format errors; most judges favour the first position. Few-shot
  examples were tested as a way to raise consistency.

#### (A) `wang2024fair` (code: `FairEval.py`)

- **Finding (medium, abstract).** Rankings can be swung by the order of the two answers alone; the cited example is
  Vicuna-13B beating ChatGPT on 66 of 80 queries with ChatGPT as evaluator.
- **Multiple Evidence Calibration (MEC), in code.** The prompt demands the explanation before the scores: "Please
  first provide a comprehensive explanation of your evaluation … Then, output two lines indicating the scores", with
  the output template `Evaluation evidence: … / Score of the Assistant 1: … / Score of the Assistant 2: …`. The call
  samples `n=args.k` answers (default 3) at `temperature=1`; the scores are averaged.
- **Balanced Position Calibration (BPC), in code.** `if args.bpc == 1:` the same question is asked again with
  `gen_prompt(ques, ans2, ans1)`; the swapped scores are mapped back and pooled before averaging.
- **Human-in-the-loop calibration (medium, abstract; not in the released script).** A "balanced position diversity
  entropy" measures how much the judgements disagree across samples and orders; the most uncertain examples go to a
  human.

#### (A) `liu2023geval` (code: `gpt4_eval.py`, `prompts/summeval/*.txt`)

- **Prompt structure**: task introduction; one criterion with its definition ("Your task is to rate the summary on
  one metric."); numbered "Evaluation Steps"; the input; a form to fill ("Evaluation Form (scores ONLY): -
  Consistency:"). Per the paper (medium), the evaluation steps are generated by the model from the task and
  criterion (auto chain-of-thought), and the final score is the probability-weighted sum over score tokens.
- **Released scoring procedure (high).** For GPT-4 the script samples instead of reading probabilities:
  `temperature=2, max_tokens=5, … n=20`, and `meta_eval_summeval.py` takes `score = sum(all_scores) /
  len(all_scores)`. Note: the `temperature=2` in the script may differ from what the paper states (not checked).
- **Meta-evaluation**: Pearson, Spearman and Kendall correlation with human scores, computed per source document and
  averaged.
- **Caveat stated by the authors (medium, abstract)**: LLM-based evaluators may be biased toward LLM-generated text.

#### (A) `yuan2024batcheval` (code: `Run_data/`)

- **Idea** (README abstract): sample-wise judging is "(1) Sensitive to prompt design; (2) Poor resistance to noise;
  (3) Inferior ensemble performance with static reference"; BatchEval judges batch-wise and iteratively. The stated
  optimum is a "two stage procedure with heterogeneous batch composition strategy and decimal scoring format".
- **Prompt**: "You will be given a batch of {{number}} samples." … "You should carefully horizontally compare the
  given samples in order to assign a suitable float score to each sample." The form forces analysis first:
  "(Attention: Don't give your scores during this step)", then all scores in one list.
- **Procedure in code**: batch size 10, 5 iteration rounds, temperature 0.2. After each round `generate_new_data`
  sorts all samples by the model's score and builds the next batches by taking one sample from each score stratum
  (`datas[bottle*j+i]`), then shuffles inside the batch. The final score is the mean over rounds. Reported headline
  (README): 10.5% better Pearson correlation at 64% of the API cost on average.

#### (A) `stureborg2024inconsistent`

Primary text read: the authors' 3-page poster paper "Limitations of Large Language Models as Automatic Evaluators"
(SouthNLP 2024), a short version of the cited arXiv paper. Findings there (high for the short version):

- GPT-4 as evaluator is "disproportionately biased towards low perplexity summaries" compared with experts; the
  authors add that such evaluators "may show a biased preference for text which is generated by itself".
- With a 1–100 scale the model uses the range sparsely and prefers round numbers such as 90 and 95.
- Anchoring inside one generation: "scores assigned to previous dimensions of analysis biasing future scores in the
  same generation".
- Recipe: "deterministic, non-CoT prompting with a 1-10 score granularity and using GPT-4 performed the best".
- Scale of the study: more than 560,000 model outputs; SummEval as development set, RoSE as test set.

From the arXiv abstract and secondary summaries (medium): low "inter-sample" agreement of the evaluator with itself
(Krippendorff's alpha, treating repeated samples as annotators) and sensitivity to prompt differences that do not
matter to humans.

#### (B) Adaptation for RBDPE (ours)

- **Judge contract.** Explanation (the decisive words of the atom) before the verdict; strict, typed verdict;
  temperature 0 where the provider allows it; an explicit value for "cannot judge"; unparseable answers recorded as
  such and never counted as a verdict.
- **Order effects exist wherever the model sees a list**: retrieved candidates, alternative changes, several atoms.
  Run a second permutation; a different decision is "inconsistent" and goes to a human.
- **The deterministic checks are our "reference answer".** FastChat gives the judge a reference where it is weak;
  RBDPE can give the judge the verifier's facts (term exists, base facets, licensed obligation) so that it judges
  wording, not vocabulary knowledge.
- **A design tension to settle empirically, not by citation.** FairEval and FastChat put evidence before the verdict;
  the Stureborg poster found non-CoT prompting best for numeric summary scores. These concern different outputs
  (pairwise preference versus a 1–10 score). For a three-way attribution verdict we should test both variants on the
  judge validation set (G4-S20) and keep the better one.
- **Batch judging and multi-attribute anchoring are different things.** BatchEval puts several *samples* under *one*
  criterion; the anchoring finding concerns several *criteria* for one sample. RBDPE can use batches for a
  consistency pass and still keep one criterion per call.

---

### 3.3 Debate versus vote — `du2024debate`, `smit2024mad`, `choi2025debate`

#### (A) `du2024debate`

- **Protocol in code** (`gsm/gen_gsm.py`, `mmlu/gen_mmlu.py`, `biography/gen_conversation.py`): each agent answers
  independently and keeps its own context. From the second round on, each agent receives the other agents' latest
  answers wrapped in a fixed frame: "These are the solutions to the problem from other agents:" … "Using the
  solutions from other agents as additional information, can you provide your answer to the math problem?". With no
  other agent the script falls back to self-check ("Can you double check that your answer is correct.").
- **Settings**: 3 agents and 2 rounds for GSM, MMLU and biographies; 2 agents and 3 rounds for arithmetic. The
  project page explains the choice: "we use three language-model agents that debate for two rounds, largely for
  computational reasons", and says performance can improve with more agents or rounds.
- **Final answer**: the most frequent answer among the agents after the last round (`most_frequent`), i.e. a
  majority vote over post-debate answers.
- **Factuality check by a judge model** (`biography/eval_conversation.py`): one question per ground-truth fact, "Give
  a single word answer, yes, no, or uncertain."; "uncertain" and unparseable answers are excluded, not guessed.
- **Claim** (project page): debate improves reasoning and factual accuracy over single-agent generation on six
  benchmarks; different models can be mixed.

#### (A) `smit2024mad`

- **A benchmark library with a unified interface** (`debatellm/systems.py`): single agent, round-robin debate,
  Society of Minds (the Du et al. protocol), Ensemble Refinement, Multi-Persona (affirmative, negative and judge
  roles; the judge decides after each round whether to stop), debate with judge, ChatEval (one-by-one, simultaneous,
  with summariser), and Medprompt (several reasoning passes with answer-choice shuffling, then the most frequent
  answer).
- **Finding** (README): "no single debate or prompting strategy consistently outperforms others across all
  scenarios". From the abstract (medium): multi-agent debate does not reliably outperform self-consistency and
  ensembling, but is more sensitive to hyperparameters; tuned, some debate protocols do better.
- **Agreement modulation**, the paper's own contribution, as prompt text
  (`experiments/conf/system/debate_prompts/google_ma_debate.yaml`): eleven levels from "You discard these agents'
  opinions 100% of the time." to "You incorporate these agents' opinions 90% of the time and have almost no
  reservations." and "You fully incorporate these agents' opinions 100% of the time, without reservations." README:
  about 15% improvement for Multi-Persona and about 5% for Society of Minds on USMLE when this level is tuned; the
  90% setting gave Multi-Persona a new high score on MedQA.
- **Metrics per agent and per debate** (docstrings in `systems.py`): `changed_answer`, `relied_on_other` ("initially
  incorrect (in round 0), but gave the correct answer in the final round"), `bullied_by_other` ("initially correct
  (in round 0), but gave an incorrect answer in the final round"), `any_correct_answer`, `agents_in_agreement`,
  `unique_first_answers`, plus cost, time and tokens per question. Results are plotted as accuracy against cost.

#### (A) `choi2025debate`

- **Experiment design in code** (`src/main.py`, `src/evaluator.py`): N agents (default 5) answer independently;
  **round 0 is evaluated as a majority vote** over these answers; then up to 5 debate rounds follow, each evaluated
  again by majority. Ties are broken at random (`random.choice(most_common)`). Topologies: decentralised (each agent
  sees all peers), sparse (two neighbours), centralised (one agent sees all, the others see only that agent).
  Homogeneous agents or personas. Sampling at temperature 1.0 from local models (Qwen2.5-7B, Llama-3.1-8B,
  Qwen2.5-32B). Per-round accuracy is logged, which makes "vote only" and "vote after debate" directly comparable.
- **Conclusions (medium, abstract and secondary summaries).** Across seven benchmarks, majority voting alone accounts
  for most of the gain usually credited to multi-agent debate. Modelled as a stochastic process, debate induces a
  martingale over the agents' beliefs: in expectation it does not raise correctness. Debate helps only when the
  update is biased toward correct answers. Secondary summaries name three variants: an oracle that locks a correct
  belief once reached (an upper bound, not deployable), a "conformist" that keeps answers matching the previous
  majority, and a "follower" that adopts the previous majority with fixed probability. These variants are **not** in
  the released code (only unused `--solver` and `--alpha` options exist).

#### (B) Adaptation for RBDPE (ours)

- Keep independent votes with a majority over the normalised decision as the default; do not add free debate.
- If agents interact at all, give them something that is *known to be true*: the deterministic verifier's results.
  That is our reading of "bias toward correction"; the papers do not prescribe it for profile engineering.
- Whatever interaction is added (repair rounds, a council), log the state before and after, and count corrected,
  harmed and unchanged decisions. Keep the mechanism only if corrected exceeds harmed on a development split.
- Report cost next to quality for every condition, as the DebateLLM benchmark does.

---

### 3.4 The blackboard — `chmielewski2026blackboard`, `erman1980hearsay`, `nii1986blackboard`

#### (A) `chmielewski2026blackboard`: SAST-Blackboard as implemented

How it was found: the paper text is not reachable from here. Web search confirms the title, the five authors and a
20-minute slot on the SDS 2026 agenda (10 May 2026, with ESWC 2026 in Dubrovnik), and summarises the authors'
announcement: instead of one prompt mixing documentation, example values and schema information, specialised agents
each assess one signal and write explicit assessments and rationales to a shared blackboard, followed by a
structured selection and discussion. The code repository is named in the README of the author's own
`jundahuang9123/blackboard-workbench` ("A browser workbench for Sebastian Chmielewski's SAST-Blackboard",
`github.com/U0iS112/654321`). Everything below is from that code at commit `074ddfc` (high for the implementation;
I did not see the paper's own description or results).

Task: map each leaf attribute of a JSON sample (VC-SLAM corpus) to an ontology class and datatype property.

| Stage | What the code does | File |
|---|---|---|
| Record per attribute | An `AttributeMapper` holds `state` (`candidates`, `validated_candidates`, `matrix`, `final_mapping`) and `logs` (one entry per stage, including `raw_llm_response`). This is the blackboard record for one attribute. | `components/attribute_mapper.py` |
| Generate | The model returns exactly 3 candidates as JSON objects `{"object", "relation", "reason"}`. Rules in the prompt: "DO NOT output the TTL triple itself."; the triple string is assembled by code. | same |
| Validate (deterministic) | Per candidate: triple syntax, class exists in the ontology, property exists, property is a datatype property, the sample's values are reasonable for the property's range. All five must hold for `accepted_by_validator`. Each result becomes a matrix row: `"agents": {"validator": {"accepted": …, "reason": …}}`. | same |
| Assess signals (4 agents) | Documentation, historical mappings, example values, attribute-name proximity. Each agent receives the material of its signal and the validated candidates (the documentation agent also gets the ontology, the example-value agent also the documentation; the name agent gets nothing but the attribute name and the candidates) and returns, per candidate, `{"accepted": bool, "reason": text}` (name proximity adds a 0–3 score). Votes are written into the matrix under the agent's name. | same |
| Select | A selection agent reads the whole matrix: "You MUST accept exactly ONE candidate (and reject all others)." and "Try to use the reasoning's of the others agents". It is told the measured base rates ("hits@1 … is 70% , and your hits@3 is 81%") and asked to be "very biased towards the first candidate, but not to much". | same |
| Declare discussions | A reasoning agent sees all final mappings and matrices of the sample and declares discussions only where it sees a reason: participants with a role (`weak` may change, `strong` mostly gives feedback), a reason, `max_turns` (3). "Do not perform discussion, only declare them." The prompt lists what is **not** a reason (redundant data, same values in different fields). | `components/reasoning_agent.py` |
| Discuss (bounded) | Turn by turn, each participant answers with `{"attribute", "response", "commands", "command_parameters"}`. "In TURN 1 you MUST NOT execute any commands." From turn 2 the only commands are `Change:Candidate` with the index of one of the participant's own top-3 validated candidates, and `DiscussionState:End`. The engine applies commands, keeps `final_mapping_before_discussion`, and labels the outcome `Correction`, `Acceptance` or `No agreement`. | `components/discussion_engine.py` |
| Evaluate | Top-1 evaluation against the reference **before** and **after** discussion; `reasoning_effect` lists every attribute whose mapping changed. A global evaluation counts, per role, whether a change was `better`, `worse` or `same`, counts discussion outcomes, and computes for each signal the "pool" of candidates it accepted and whether the correct mapping is in it. | `core/blackboard_semantic_mapping.py`, `evaluation_methods/methods/final_evalutions_signals.py` |
| Baseline | "SimpleLLM": four models (configured: GPT-4o, GPT-4o-mini, GPT-5, GPT-5-mini, temperature 0) each propose up to 10 candidates per attribute; the final mapping is chosen by a vote of the models over the merged candidates, or by counting candidates in each model's top 3. The configured model weights are all within 10^-4 of 1 (a helper can recompute their order from earlier hit rates), so they act as tie-breakers. | `simplellm/codebase/core/paper_agents.py` |

Observations from reading the code (mine, relevant for anyone reusing it):

- Votes are aligned to candidates **by array position** (`zip(validated, votes)`), so a shorter model answer
  silently shifts or drops votes.
- `run_discussion(disc, mappers)` is called without the source data, documentation and history, so the discussion
  prompt renders those context blocks as `None` at this commit.
- The engine labels the unresolved case `"No agreement"`, while the global statistics read the key
  `"Disagreement"`; unresolved discussions are therefore not counted in the totals at this commit.
- The selection, reasoning and discussion prompts hard-code hit rates ("Historically the hits@1 … is 70%"). The
  code does not say where they were measured; if it was the evaluation corpus, an evaluation needs a separate split.
- The workbench README (the author's own test, not a result of the paper) reports one complete local run in which
  the built-in evaluation was 0 of 4 exact matches both before and after discussion, and says this verifies
  execution, not mapping quality.

A boundary for citation: the review layer in `blackboard-workbench` (machine result stored unchanged with a hash,
posts and decisions appended as events against an item version, stale decisions rejected, agent posts advisory
only; `docs/ARCHITECTURE.md`) is the author's own design. It is not part of SAST-Blackboard and should not be
attributed to `chmielewski2026blackboard`.

#### (A) `erman1980hearsay` and `nii1986blackboard` (medium; search summaries, no full text)

- **Hearsay-II** reconstructs an interpretation from hypotheses at several levels of abstraction held on a shared
  blackboard; independent knowledge sources are written as condition-action pairs and are triggered by changes on
  the blackboard; a monitor and a heuristic scheduler compute priorities and give limited processing resources to
  the most promising action first. It is generally named as the first blackboard system.
- **Nii** defines the model with three parts: knowledge sources (the domain knowledge, kept separate and
  independent), the blackboard data structure (the solution space, organised in one or more application-dependent
  hierarchies; knowledge sources interact *solely* through it), and control (knowledge sources respond
  opportunistically to changes rather than in a fixed order; in the framework a control element picks the next
  eligible knowledge source). Nii's text (seen through summaries of the Stanford report version, which combines both
  parts of the article) illustrates opportunistic problem solving with a jigsaw-puzzle and a koala example, and
  separates the abstract model from the more detailed "blackboard framework" that describes the components and
  their behaviour.

#### (B) Adaptation for RBDPE (ours)

- The **levels** of our blackboard: atom → assessment → candidates → profile change → profile element → artefact →
  conformance report. `BlackboardEntry` is already append-only; the rule to add is that stages read and write only
  through it.
- Each stage is a **knowledge source** with a declared trigger (entry kinds it reacts to) and action (entry kinds it
  writes). The human reviewer is a knowledge source with the highest authority, not a separate channel.
- **Control** is a separate, small component: it decides what is stale and what runs next (cheap deterministic
  checks before model calls; the most uncertain items first).
- From SAST-Blackboard we take the **matrix** (one row per candidate, one column per knowledge source, each cell an
  accept/reject with a reason), the **closed command set** for any discussion, and the **before/after accounting**.
  We key votes by candidate id, not by position.

---

### 3.5 Non-determinism — `atil2025nondeterminism`, `ouyang2025nondeterminism`

#### (A) `atil2025nondeterminism`

Versions: the bibliography cites arXiv v5 (2 April 2025, title "Non-Determinism of "Deterministic" LLM Settings").
The repository ships the **v2 PDF** (19 August 2024, title "LLM Stability: A detailed analysis with some surprises"),
which I read in full. v5 abstract via search (medium): five LLMs configured to be deterministic, eight tasks, 10
runs, zero-shot and few-shot; accuracy variation up to 15% across runs and a gap between best possible and worst
possible performance of up to 70%; no model gives repeatable accuracy on all tasks.

From the v2 PDF and `evaluate.py` (high):

- **Setting**: temperature 0, top-p 1, fixed seed; 8 multiple-choice tasks from BBH and MMLU; 5 runs (20 for a
  normality check).
- **Metrics**: "Total agreement rate@N (TAR@N), which is the percentage of test set questions across N runs where all
  answers are identical", in two forms: **TARr@N** over the raw response string and **TARa@N** over the parsed
  answer. Plus min, median and max accuracy and the min-max spread. In the current code also
  `best_possible_accuracy` (correct in any run) and `worst_possible_accuracy` (correct in all runs).
- **Why not mean and standard deviation**: "The reason for not reporting standard deviation and means is that the
  variations are not normal." (20 identical runs; Kolmogorov-Smirnov test rejects normality).
- **Results in v2**: accuracy spreads of 5–10% on some model-task pairs; raw agreement far below answer agreement
  (median TARr@5 for few-shot GPT-4o 3%, TARa@5 94%); a fine-tuned GPT-3.5 was almost perfectly stable.
- **Correlations**: "as an LLM's output length increases, the stability of the output decreases"; the authors
  suggest restricting the maximum generation length.
- **Engineering implications named by the authors**: unit tests need a framework that tolerates variation; format
  instability breaks downstream parsers; instability multiplies along a chain of model decisions (their example:
  four classifiers at 95% stability give 0.95^4 = 0.814).

Follow-up notebooks in the same repository (high as the authors' own analyses; they are **not** part of the cited
paper):

- JSON schema in the prompt: "Schemas do help with determinism generally at the raw output level and answer level
  but it may come with a performance penalty on accuracy."
- OpenAI strict structured output: "the system is producing consistent json but just not the same json."
- Hosting: a locally deployed model running one job at a time was deterministic over 10 runs of 100 questions, where
  the shared hosted endpoints were not ("single-job LLMs are deterministic so far").
- Token probabilities did not predict which answers were unstable.
- Newer hosted models (Gemini 2.5 Pro, DeepSeek R1) were less deterministic than older ones; a stable subset of
  items remains across repeated runs.
- Cause (medium, search summary of v5): the authors do not prove one; they point to shared compute with co-mingled
  inputs as the likely explanation.

#### (A) `ouyang2025nondeterminism`

- **Design (high, repository)**: 829 problems from CodeContests, APPS and HumanEval (count from the abstract); the
  same zero-shot prompt ("Generate Python3 code (Markdown):") requested repeatedly; logs exist for temperature 0,
  0.5 and 1 and for two request ways: five separate requests, or five candidates in one request (`topn 5`).
- **Three kinds of similarity** (`syntactic_similarity_OER.py`, `structural_similarity.py`): *semantic* by behaviour
  on tests (test pass rate; OER, in code the share of test cases on which all five candidates produce the same
  output, with equal outputs that are timeouts, exceptions or execution errors counted separately; the README also
  names a variant `OER_ow`), *syntactic* (longest common subsequence, Levenshtein edit distance), *structural* (two
  measures named `United_Diff` and `Tree_Diff`). The appendix tables report mean, mean variance, mean maximum
  difference, maximum difference and the "ratio of worst cases".
- **Research questions** (appendix): influence of temperature; requesting several candidates in one call versus
  separate calls; correlation with task features; GPT-4 versus GPT-3.5; prompt engineering (concise output,
  chain-of-thought).
- **Finding at temperature 0 (high for the example, medium for the general statement).** The appendix shows three
  solutions "generated by ChatGPT under temperature=0, which have different test pass rates, namely 42.9% (3/7),
  57.1% (4/7), and 71.4% (5/7)". Abstract-level: temperature 0 reduces non-determinism compared with the default but
  does not remove it; under default settings the share of tasks with zero equal test output across requests was
  75.76%, 51.00% and 47.56% on the three benchmarks.

#### (B) Adaptation for RBDPE (ours)

- The replay cache and the audit record (`LLMCallRecord`, `request_hash`, `variant`) are the right foundation. The
  sentence already in `llm/client.py`, "the stored answer IS the record of what a run decided", is the practical
  conclusion of both papers.
- Add the measurement: a **stability report** over N independent runs per atom with TARr (identical raw answer),
  TARa (identical decision signature), min/median/max of the element-level scores, and best-possible/worst-possible
  scores.
- Compare decisions by their **normal form** (the signature), never by text. Keep free-text fields short.
- Typed output helps agreement on the raw text but is not a guarantee, and it may cost accuracy; measure both.
- For results that must be reproducible bit for bit, a locally hosted single-job model is the only setting the
  follow-up experiments found deterministic. For hosted models, publish N and the spread.

---

### 3.6 Benchmark contamination — `sainz2023contamination`

#### (A) What the work did

- **The paper is a position paper** (abstract, reproduced in the official repository): the worst contamination is a
  model trained on the test split and then evaluated on it; the extent is unknown because it is hard to measure; it
  inflates the contaminated model's results; the paper "defines different levels of data contamination and argues
  for a community effort", including automatic and semi-automatic measures and "suggestions for flagging papers
  with conclusions that are compromised by data contamination". Search summaries indicate three contamination types
  with "guideline" as one of them; the other two labels were not visible to me.
- **The concrete protocol is in the companion LM Contamination Index** (`CONTRIBUTING.md`, blog post). Ask the model
  to reproduce the benchmark: "Please, generate the first instances of {DATASET_NAME} dataset {SPLIT} split in
  {FORMAT} format." (zero-shot, for instruction-tuned models) or give a few instances and let it continue. Then
  label per split: **contaminated** "if it is able to generate examples of the dataset (text or labels)";
  **suspicious** if it produces "characteristic attributes such as data format, ids, or other relevant information";
  **clean** otherwise; `n/a` for splits that are not public. Each contribution must state "the number of executions
  needed to obtain the result" and attach evidence.
- **Registry format** (`data.json`, 375 rows): model, dataset, status per split, optional percentages, guideline
  status, source.
- **A second detection pattern, cited in the blog** (an observation by Horace He on GPT-4 and coding problems):
  solving the problems published before the model's training cut-off and none of those published after it
  "strongly points to contamination".

#### (B) Adaptation for RBDPE (ours)

- DCAT-AP and its national and domain profiles are public documents; every strong model has probably read them. The
  benchmark's safeguards (term-free atoms, `use_hints = false`, `exclude_namespaces`) reduce what the *input* leaks,
  not what the *model* remembers.
- Add a **memorisation probe** per (model, gold profile) before a benchmark run: ask the model, without atoms, to
  list what the named profile adds to or tightens on its base; score the overlap with the gold delta; store the
  prompt, the number of attempts, the answer and a three-level label.
- Report results per label, and use counterfactual atoms (`Atom.counterfactual_of` exists in the contract) to show
  that the output follows the requirement and not the remembered profile.

---

### 3.7 Judging with incomplete or disagreeing judgments — `zobel1998reliable`, `voorhees2000variations`, `buckley2004incomplete`

#### (A) What the works did

- **`zobel1998reliable`** (medium, abstract and later papers citing it). TREC judges only a *pool*: the top
  documents of the participating systems. Zobel examined whether results based on pooled judgments are reliable.
  Conclusions: the measured *relative* performance of systems is reliable and the pooled judgments are a fair basis
  for measurement (pooling bias has no significant impact); *recall is overestimated* because many relevant
  documents were probably never found and judged; a different pooling strategy can find more relevant documents for
  the same effort. The paper also examines significance tests for comparing systems.
- **`voorhees2000variations`** (medium, abstract, NIST summary, later papers). Relevance judgments differ widely
  between assessors. The study had TREC-4 documents judged again by further assessors and used an independent set
  of TREC-6 judgments from the University of Waterloo, built alternative judgment sets (including union and
  intersection of assessors' relevant sets), and compared the system rankings they produce with Kendall's tau.
  Conclusion: the rankings are highly correlated; comparative evaluation is stable although the judgments themselves
  are not. Exact overlap and tau values were not visible to me.
- **`buckley2004incomplete`** (high for the measure via `trec_eval`; medium for the paper's experiments). Abstract:
  standard measures are not robust to substantially incomplete judgments; the paper introduces a measure that
  correlates highly with existing ones when judgments are complete and is more robust when they are not. The measure
  is `bpref`. In Buckley's implementation: "Calculate judgement based measures (dependent on only judged docs; no
  assumption of non-relevance if not judged)". Definition in the tool: with R judged relevant documents and the top
  R judged non-relevant documents, "bpref is the fraction of the preferences that the ranking preserves"; unjudged
  documents are skipped. The same tool has a companion measure `unj` (share of unjudged documents at a cut-off):
  "a "red flag" measure: high values at low cutoffs indicates that the run is poorly covered by the test
  collection". The `bpref_bug` notice of 2005 documents a correction of the original computation and says the
  SIGIR 2004 paper used the earlier variant.

#### (B) Adaptation for RBDPE (ours)

- A **gold profile is a pooled judgment set**. It contains what its authors decided, not every defensible element.
  A generated element that is absent from the gold delta is *unjudged*, not automatically wrong.
- Report three numbers, not one: strict precision (unjudged counted as wrong), judged-only precision after experts
  adjudicated the unjudged elements, and the unjudged share itself as a warning sign.
- **Pool for adjudication**: take the union of the elements produced by all pipeline conditions, remove
  duplicates, hide which condition produced what, and have experts judge that pool once. Every condition is then
  scored against the same enlarged judgment set, and later conditions can be scored fairly as long as their
  unjudged share stays low.
- **Rank stability instead of absolute truth**: with two experts, compute the ranking of the conditions under each
  expert's judgments, under their union (lenient) and intersection (strict), and report Kendall's tau between the
  rankings. Claim only the comparisons that hold under all of them.

---

## 4. Reusable key steps for RBDPE

Each step: what they did (specific) → how we reuse it (ours) → stage → evidence → confidence.
Paths are relative to `/home/user/refs/` unless stated.

### Architecture

**G4-S01 — Blackboard triad: levelled record, independent knowledge sources, separate control**
- From: `nii1986blackboard`, `erman1980hearsay`.
- What they did: knowledge is split into independent knowledge sources that interact only through a shared
  blackboard organised in hierarchies of the solution space; knowledge sources are condition-action units triggered
  by blackboard changes; a control component (in Hearsay-II a monitor plus a heuristic scheduler) chooses the next
  action opportunistically and spends limited resources on the most promising one first.
- How we reuse it: `BlackboardEntry` stays the only channel between stages. Declare per stage the entry kinds that
  trigger it and the entry kinds it writes. Add a small scheduler that (1) marks downstream entries stale when an
  input changes, (2) orders the agenda: deterministic checks before model calls, then items by uncertainty. Levels:
  atom, assessment, candidates, change, element, artefact, conformance. Human decisions are entries of the same kind.
- Stage: architecture. Evidence: search summaries of AI Magazine 7(2) (ojs.aaai.org/index.php/aimagazine/article/view/537),
  Stanford report CS-TR-86-1123, and ACM CSUR 12(2) (doi 10.1145/356810.356816); paraphrased. Confidence: medium.

**G4-S02 — Decision matrix: one row per candidate, one column per knowledge source, each cell a vote with a reason**
- From: `chmielewski2026blackboard`.
- What they did: every candidate mapping gets a matrix row; the validator and four signal agents each write
  `{"accepted": bool, "reason": …}` into it; the selection agent must read the matrix and accept exactly one
  candidate with a reason per candidate.
- How we reuse it: derive from `ProfileChange.verification`, `alternatives` and the retrieved `Candidate` list a
  matrix per atom: rows are the candidate terms or alternative changes, columns are V1..V6, T1, the attribution
  judge, the reuse check. Each cell stores passed, reason, author. The proposer's choice must cite cells; the
  workbench renders the matrix as the main inspection view. Key cells by candidate id.
- Stage: architecture. Evidence: `U0iS112__654321/blackboard/codebase/components/attribute_mapper.py`: `"agents":
  {"validator": {"accepted": accepted, "reason": cand_log}}`; "You MUST accept exactly ONE candidate (and reject all
  others)." Confidence: high.

**G4-S03 — One self-contained, replayable decision record per run**
- From: `chmielewski2026blackboard`, `zheng2023judge`.
- What they did: SAST-Blackboard writes one JSON per sample with, per attribute, the complete `state` and `logs`
  (including raw model answers), all discussions turn by turn, the list of changes caused by discussion, and the
  evaluation before and after. FastChat stores for every judgement the full prompt, the full answer, the judge model
  and prompt name, and a timestamp.
- How we reuse it: one export bundle per project: atoms, assessments, matrix, changes with trace, every
  `LLMCallRecord`, every blackboard entry, human decisions kept apart from machine output, and a hash of the bundle
  in `SignOff`. The bundle is what a reviewer of the paper would need to re-check a decision without rerunning.
- Stage: traceability. Evidence: `U0iS112__654321/blackboard/codebase/core/blackboard_semantic_mapping.py`:
  `results = {"attributes": {}, "evaluation": {}, "discussions": {}}`;
  `lm-sys__FastChat/fastchat/llm_judge/common.py`: result fields `"user_prompt"`, `"judgment"`, `"judge"`, `"tstamp"`.
  Confidence: high.

### Propose and verify

**G4-S04 — Typed candidate, assembly by code, deterministic gate before any model judgement**
- From: `chmielewski2026blackboard`.
- What they did: the model returns `{"object", "relation", "reason"}`; the prompt forbids writing the triple; code
  assembles it. A deterministic validator checks syntax, existence of class and property, property type, and whether
  the actual values fit the range. Only validated candidates reach the signal agents and the selection.
- How we reuse it: confirms "typed `ProfileChange`, never free SHACL" and "verify before judge". Two additions:
  keep the per-check booleans with the candidate (their `validator_meta`) so the matrix can show *why* a candidate
  was dropped, and add a value-plausibility check where sample metadata records exist.
- Stage: verify. Evidence: `attribute_mapper.py`: "DO NOT output the TTL triple itself."; `accepted =
  (cand_log["rdf_syntax_ok"] and cand_log["subject_in_ontology"] and …)`. Confidence: high.

**G4-S05 — Controls for non-determinism at call time**
- From: `atil2025nondeterminism`, `ouyang2025nondeterminism`.
- What they did: showed that temperature 0 with a fixed seed does not give identical outputs on hosted models, that
  raw strings vary far more than parsed answers, and that longer outputs are less stable; follow-up experiments
  found that a schema raises raw agreement but may cost accuracy, that strict structured output still varies in
  content, and that a single-job local model was deterministic.
- How we reuse it: (1) keep the replay cache and treat the stored answer as the decision; (2) include every setting
  that changes the answer in `request_hash` and in `LLMCallRecord` (temperature and output limit are currently
  missing from the hash); (3) store the model identifier returned by the provider; (4) compare decisions by
  signature; (5) cap the length of free-text fields; (6) offer a local single-job model as the "reproducible"
  profile of the tool.
- Stage: propose. Evidence: `breckbaldwin__llm-stability/LLM_Stability_paper_v2.0.pdf`: "as an LLM's output length
  increases, the stability of the output decreases"; `experiments/strict_json_schema/anaysis.ipynb`: "the system is
  producing consistent json but just not the same json"; `ShuyinOuyang__LLM-is-a-box-of-chocolate/Appendix.pdf`.
  Confidence: high.

### Vote, debate, repair

**G4-S06 — Independent proposals with a majority vote as the default; no free debate**
- From: `choi2025debate`, `smit2024mad`, `du2024debate`.
- What they did: Choi et al. evaluate the majority vote over independent first answers (round 0) and after each
  debate round, and conclude that the vote explains most of the gain and that debate alone does not raise expected
  correctness. Smit et al. find that debate protocols do not reliably beat self-consistency and ensembling and are
  harder to tune. Du et al., who report gains from debate, also take the most frequent final answer.
- How we reuse it: `PipelineConfig.votes` with an odd N; majority over the normalised decision signature (already
  implemented); no strict majority means `needs_review` (already implemented), never a random tie-break; store all N
  answers so that TARa (G4-S21) falls out for free; document in the paper that debate was deliberately left out as
  the default and why.
- Stage: judge_vote. Evidence: `deeplearning-wisc__debate-or-vote/src/evaluator.py`: `debate_answer =
  random.choice(most_common) # if there is a tie, will choose randomly`; `instadeepai__DebateLLM/README.md`: "no
  single debate or prompting strategy consistently outperforms others across all scenarios"; conclusions of Choi et
  al. from search summaries of arXiv 2508.17536. Confidence: medium (mechanics high, conclusions from abstracts).

**G4-S07 — If agents interact: selective, bounded, with a closed command set**
- From: `chmielewski2026blackboard`, `choi2025debate`.
- What they did: SAST-Blackboard lets a reasoning agent declare discussions only where needed, assigns weak and
  strong roles, limits turns to 3, forbids commands in turn 1, and afterwards allows only `Change:Candidate <index>`
  among already validated candidates or `DiscussionState:End`; the outcome is labelled Correction, Acceptance or No
  agreement. Choi et al. argue that debate needs a bias toward correct answers to help.
- How we reuse it: a "council" only for changes with split votes, an inconsistent judge, or an open `Conflict`.
  Allowed actions: choose another already verified alternative, withdraw, end. No new terms or facets inside the
  council. The verifier's results are shown as fixed facts. Maximum 3 turns; every turn is a blackboard entry; the
  outcome label is stored; "no agreement" goes to the human queue.
- Stage: repair. Evidence: `U0iS112__654321/blackboard/codebase/components/discussion_engine.py`: "In TURN 1 you MUST
  NOT execute any commands."; `reasoning_agent.py`: "Do not perform discussion, only declare them." Confidence: high.

**G4-S08 — Account for what interaction changed: corrected, harmed, unchanged**
- From: `chmielewski2026blackboard`, `smit2024mad`.
- What they did: SAST-Blackboard snapshots the selection before discussion, evaluates before and after, lists every
  change, and counts per role whether a change was better, worse or the same. DebateLLM records per agent whether it
  changed its answer, was helped by others, or was talked out of a correct answer, plus cost, time and tokens.
- How we reuse it: for every repair round and council store the change hash before and after. With a gold delta,
  report corrected (wrong to right), harmed (right to wrong), unchanged, and calls and tokens per corrected change.
  Use these counts to set `repair_rounds` and to decide whether a council exists at all.
- Stage: evaluation. Evidence: `blackboard_semantic_mapping.py`: `compute_reasoning_effect`,
  `results["evaluation"]["before_reasoning"]`; `instadeepai__DebateLLM/debatellm/systems.py`: "bullied_by_other …
  initially correct (in round 0), but gave an incorrect answer in the final round". Confidence: high.

**G4-S09 — One explicit "deference" setting in interaction prompts, tuned on a development split**
- From: `smit2024mad`.
- What they did: added a sentence that fixes how much an agent should adopt the others' opinions, in eleven levels,
  and treated the level as a hyperparameter; tuning it changed accuracy substantially for some protocols.
- How we reuse it: if a repair or council prompt shows another agent's or the judge's opinion, state how much weight
  it has, with a small fixed set of wordings (for example: verifier facts are binding; judge remarks are advice).
  Record the level in `prompt_version`. Tune only on a development split.
- Stage: repair. Evidence: `instadeepai__DebateLLM/experiments/conf/system/debate_prompts/google_ma_debate.yaml`:
  "You incorporate these agents' opinions 90% of the time and have almost no reservations." Confidence: high.

### Judge

**G4-S10 — Judge contract: evidence first, strict verdict, abstain and error as explicit values**
- From: `zheng2023judge`, `wang2024fair`, `du2024debate`.
- What they did: FastChat asks for a short explanation first and the verdict last in a fixed pattern, calls the judge
  at temperature 0, and records `-1` or `"error"` when the pattern is missing. FairEval's template starts with
  "Evaluation evidence:". Du et al.'s fact check allows "uncertain" and drops those answers.
- How we reuse it: order the fields of `AttributionOut` as explanation (starting with the atom's decisive words),
  `unsupported_facets`, `verdict`; add the verdict value `cannot_judge` that routes to review; record an invalid
  judge answer as a failed call, never as `unsupported`. Test the evidence-first variant against a verdict-only
  variant on the validation set (G4-S20), because the Stureborg poster found non-CoT prompting better for numeric
  scores.
- Stage: judge_vote. Evidence: `lm-sys__FastChat/fastchat/llm_judge/data/judge_prompts.jsonl`: "Begin your
  evaluation by providing a short explanation."; `common.py`: `temperature=0`;
  `composable-models__llm_multiagent_debate/biography/eval_conversation.py`: "Give a single word answer, yes, no, or
  uncertain." Confidence: high.

**G4-S11 — Order-swap consistency check**
- From: `zheng2023judge`, `wang2024fair`.
- What they did: FastChat judges each pair in both orders and counts a win only when both runs agree; otherwise the
  result is a tie, and the loader calls the case "inconsistent". FairEval asks again with the answers swapped and
  pools the scores.
- How we reuse it: for every model decision over an ordered list (candidate terms, alternative changes, several
  atoms) run a second call with the order reversed or shuffled by a seeded permutation. Equal decision: accept and
  record `order_consistent = true`. Different decision: `needs_review`, both answers shown. Report the consistency
  rate per model as a quality figure of the judge.
- Stage: judge_vote. Evidence: `lm-sys__FastChat/fastchat/llm_judge/show_result.py`: `if row["g1_winner"] == "tie" or
  row["g1_winner"] != row["g2_winner"]:`; `i-Eval__FairEval/FairEval.py`: `gen_prompt(ques, ans2, ans1)`.
  Confidence: high.

**G4-S12 — Several sampled judgements instead of one**
- From: `wang2024fair`, `liu2023geval`.
- What they did: FairEval samples k judgements (default 3) and averages the scores; the G-Eval script samples 20
  short answers and averages the parsed scores as a stand-in for a probability-weighted score.
- How we reuse it: judge each change k = 3 times with the `variant` mechanism of the client; verdict by majority;
  store agreeing and total votes on the T2 result. For graded criteria use the mean of the samples.
- Stage: judge_vote. Evidence: `FairEval.py`: `temperature=1, max_tokens=512, n=args.k`; `nlpyang__geval/gpt4_eval.py`:
  `n=20`; `meta_eval_summeval.py`: `score = sum(all_scores) / len(all_scores)`. Confidence: high.

**G4-S13 — Send the most disputed items to the human first**
- From: `wang2024fair`.
- What they did: defined an entropy over the judgements obtained across samples and both orders and used it to
  select the examples a human should decide.
- How we reuse it: per change compute the entropy of the verdict distribution over (k samples × 2 orders) together
  with the vote split of the proposals; sort the review queue by it; allow `auto_accept` only at entropy 0 with all
  checks passed. Show the split to the reviewer.
- Stage: hitl_review. Evidence: search summary of the ACL 2024 abstract (aclanthology.org/2024.acl-long.511);
  paraphrased; the released script does not contain this part. Confidence: medium.

**G4-S14 — One criterion per judge call, coarse scale**
- From: `liu2023geval`, `stureborg2024inconsistent`.
- What they did: G-Eval uses one prompt per criterion with the criterion's definition and numbered evaluation steps
  and a form to fill. Stureborg et al. found that scores for earlier criteria bias later ones in the same
  generation, that a 1–100 scale collapses to a few round numbers, and that a 1–10 scale worked best.
- How we reuse it: separate calls for separate questions (attribution of facets; adequacy of the no-reuse
  justification; quality of label and definition). Categorical verdicts or 1–10, never 1–100. Each judge prompt
  carries the criterion definition and the steps to follow.
- Stage: judge_vote. Evidence: `nlpyang__geval/prompts/summeval/con_detailed.txt`: "Your task is to rate the summary
  on one metric."; `_single_files/G4/southnlp2024-poster-42.pdf`: "scores assigned to previous dimensions of analysis
  biasing future scores in the same generation". Confidence: high (for the short version of the Stureborg paper).

**G4-S15 — Batch-wise comparative pass for consistency across changes**
- From: `yuan2024batcheval`.
- What they did: judged 10 samples per prompt with the instruction to compare them, analysis for all samples before
  any score, decimal scores, 5 rounds with re-batching so that each batch mixes quality levels, mean over rounds.
- How we reuse it: a consistency knowledge source in `consolidate`: batches of (atom, change) pairs that share a
  facet type are shown side by side; the model first analyses all, then flags unequal treatment (same modality,
  different obligation; same information need, different term). Re-batch once by the first verdict. Its output is a
  list of `Conflict` candidates for review, not an accept/reject decision.
- Stage: judge_vote. Evidence: `ypw0102__BatchEval/Run_data/prompts/topical_chat/coh_analyze_batch.txt`: "You should
  carefully horizontally compare the given samples in order to assign a suitable float score to each sample."
  Confidence: high.

**G4-S16 — Guard against a judge that likes what it (or its family) wrote**
- From: `liu2023geval`, `stureborg2024inconsistent`, `zheng2023judge`.
- What they did: reported a possible bias of LLM evaluators toward LLM-generated text, a preference of GPT-4 for
  low-perplexity text, and a self-enhancement bias; the MT-Bench pairwise prompt forbids favouring length or names.
- How we reuse it: configure the judge model separately from the proposer (`step_models`), prefer another family,
  and record a check when they are equal. The judge sees the verbalised change and the atoms, not the proposer's
  rationale, so that length and style of the rationale cannot sway it. In experiments add a term-masked condition to
  see whether familiar vocabulary names drive the verdict.
- Stage: judge_vote. Evidence: `southnlp2024-poster-42.pdf`: "LLM evaluators may show a biased preference for text
  which is generated by itself"; `judge_prompts.jsonl`: "Do not allow the length of the responses to influence your
  evaluation."; abstracts of G-Eval and MT-Bench via search. Confidence: medium.

### Traceability

**G4-S17 — The attribution test in two questions**
- From: `rashkin2023ais`.
- What they did: defined attribution by the test "According to P, s" on the statement's standalone meaning, and
  annotated in two stages: first whether the output is understandable, then, only if so, whether it is fully
  attributable to the source; five annotators, majority label, agreement count stored, a flag for items that cannot
  be judged.
- How we reuse it: the verbaliser must produce a standalone sentence per facet ("According to atom A-12, datasets
  must state …"). T2 asks Q1 then Q2 with the two-valued answers; Q1 failures go back to the verbaliser or mark the
  change unclear. The review form in the workbench uses the same two questions and stores how many reviewers agreed.
- Stage: traceability. Evidence: `google-research-datasets__AIS/README.md`: "Attribution judgements were given only
  to outputs that were marked as `1` in the `INT` column."; answer wordings in `ann_*.csv`; definition from search
  summaries of the journal and arXiv versions. Confidence: medium (two-stage procedure high, wording of the
  definition medium).

**G4-S18 — Trace recall and trace precision with a leave-one-out test**
- From: `gao2023alce`.
- What they did: recall 1 for a statement iff it has a citation and all its citations together entail it; a
  citation is irrelevant iff it alone does not entail the statement and the others still do; precision counts the
  non-irrelevant citations of fully supported statements; format errors (no citation, unknown id) give recall 0
  without a model call; redundant but supporting citations are not punished; partial support is a known blind spot.
- How we reuse it: T1 (atom exists, quote verbatim) gates T2. T2 per facet: joint support by the cited atoms gives
  recall. For facets with more than one atom and recall 1, one extra call per atom gives precision. Project metrics:
  trace recall, trace precision, share of multi-atom facets, share of superfluous links. Allow a third human label
  "partially supports" in the validation study because the automatic test cannot see it.
- Stage: traceability. Evidence: `princeton-nlp__ALCE/paper/ALCE.pdf` §3.3: "it does not require citing a minimal set
  and it permits citing redundant passages entailing similar claims"; `eval.py`, function `compute_autoais`.
  Confidence: high.

**G4-S19 — Break ties among sampled proposals by support, not by self-confidence**
- From: `gao2023alce`.
- What they did: sampled four answers and kept the one with the best automatic citation recall; citation quality
  rose, correctness did not, cost was fourfold; they verified the gain with humans because the selection criterion
  and the metric coincide.
- How we reuse it: optional policy when the votes show no majority: prefer the proposal with the highest trace
  recall, mark the decision as "selected by support", and still queue it for review. Never report trace recall as an
  independent result for runs that used it for selection.
- Stage: judge_vote. Evidence: `ALCE.pdf` §4.3: "We randomly sample n (n = 4 in our experiments) responses for each
  question, and select the best response using the automatic citation recall score." Confidence: high.

### Evaluation

**G4-S20 — Validate the judge against humans before trusting it**
- From: `zheng2023judge`, `gao2023alce`, `rashkin2023ais`.
- What they did: MT-Bench compares judge-human with human-human agreement, with and without ties. ALCE reports
  Cohen's kappa and accuracy of the automatic metric against human labels, and precision and recall for detecting
  the bad cases. AIS stores per item how many of five annotators agreed.
- How we reuse it: a study of about 100 (facet, atom) links sampled across verdicts. Two reviewers label them with
  the G4-S17 questions. Report human-human agreement, judge-human agreement, Cohen's kappa, and the judge's
  precision and recall for "unsupported". Repeat when the judge model or `JUDGE_VERSION` changes. This table is what
  licenses automatic acceptance.
- Stage: evaluation. Evidence: `lm-sys__FastChat/fastchat/llm_judge/compute_agreement.py`; `ALCE.pdf` §6: "substantial
  agreement for citation recall (0.698) and moderate agreement for citation precision (0.525)". Confidence: high.

**G4-S21 — Stability report: TARr, TARa, min/median/max, best-possible and worst-possible**
- From: `atil2025nondeterminism`, `ouyang2025nondeterminism`.
- What they did: defined total agreement over N runs on raw output and on parsed answers; reported min, median, max
  and spread instead of mean and deviation because the variation is not normal; added best-possible and
  worst-possible accuracy; Ouyang et al. measured agreement of behaviour (same test outputs), of text and of
  structure over five requests, under three temperatures and two request ways.
- How we reuse it: a command that reruns a project N times without the cache and reports per atom and overall:
  TARr (identical raw answer), TARa (identical decision signature), element-level F1 as min/median/max, and F1 when
  an element counts if produced in any run or only if produced in all runs. Publish N, the model identifier and the
  settings with every result table. For our case the analogue of Ouyang's behavioural agreement is: do the compiled
  shapes of two runs accept and reject the same test records.
- Stage: evaluation. Evidence: `LLM_Stability_paper_v2.0.pdf`: "The reason for not reporting standard deviation and
  means is that the variations are not normal."; `evaluate.py`: `'best_possible_accuracy':
  any_correct_count/num_questions`; `ShuyinOuyang__LLM-is-a-box-of-chocolate/README.md`: "test pass rate, OER,
  OER_ow, LCS, LED". Confidence: high.

**G4-S22 — Contamination probe and registry entry per model and gold profile**
- From: `sainz2023contamination`.
- What they did: asked the model to regenerate a benchmark split, labelled the outcome contaminated, suspicious or
  clean, required the number of attempts and evidence, and collected the results in a public table; argued that
  conclusions from contaminated settings should be flagged.
- How we reuse it: a pre-run step that asks the configured model, without atoms, what a named gold profile adds to
  or tightens on its base; overlap with the gold delta decides the label; prompt, attempts, answer and label become
  a project-level blackboard entry and a row in the paper's contamination table. Results are reported per label.
  Counterfactual atoms test whether the output follows the requirement where it contradicts the remembered profile.
- Stage: evaluation. Evidence: `hitz-zentroa__lm-contamination/CONTRIBUTING.md`: "Please, generate the first
  instances of {DATASET_NAME} dataset {SPLIT} split in {FORMAT} format." Confidence: high (protocol from the
  authors' index; the paper itself was seen only as abstract).

**G4-S23 — Score on judged items, report the unjudged share, pool outputs for adjudication**
- From: `buckley2004incomplete`, `zobel1998reliable`.
- What they did: Buckley and Voorhees introduced a measure that uses only judged documents and makes no assumption
  about unjudged ones; `trec_eval` also reports the unjudged share as a warning. Zobel showed that pooled judgments
  compare systems fairly while absolute recall is overestimated, because relevant items outside the pool exist.
- How we reuse it: three figures per condition: strict precision, judged-only precision after adjudication, unjudged
  share. Adjudication pool = union of generated elements of all conditions, de-duplicated and blinded. Recall
  against a gold delta is an upper estimate and is labelled as such. A condition with a high unjudged share is
  flagged, not ranked.
- Stage: evaluation. Evidence: `usnistgov__trec_eval/m_bpref.c`: "Calculate judgement based measures (dependent on
  only judged docs; no assumption of non-relevance if not judged)"; `m_unjudged.c`; Zobel via search summaries of
  the SIGIR 1998 abstract. Confidence: high for the measure, medium for Zobel's findings.

**G4-S24 — Show that conclusions survive a change of judge**
- From: `voorhees2000variations`.
- What they did: built alternative relevance judgment sets from different assessors, including union and
  intersection, and showed with Kendall's tau that system rankings stay highly correlated although the judgments
  differ substantially.
- How we reuse it: with two reviewers, score all conditions under reviewer A, reviewer B, union and intersection;
  report the four rankings and Kendall's tau between them, plus plain inter-reviewer agreement. State in the paper
  that the claims are comparative and name the comparisons that hold under all four sets.
- Stage: evaluation. Evidence: search summaries of the IP&M article (doi 10.1016/S0306-4573(00)00010-8) and the NIST
  publication page; paraphrased. Confidence: medium.

---

## 5. Mapping onto the current RBDPE snapshot

Snapshot read on 13 November 2026 (files under `backend/profile_extensioner/`; the code was still being written, so
line-level details may have moved). What already exists, and what this literature adds (ours).

| Topic | Already in the snapshot | What this group adds |
|---|---|---|
| Votes | `PipelineConfig.votes`; majority over `_signature` in `engine/propose.py`; no strict majority → `needs_review` in `engine/pipeline.py` | Keep as the default and say why (G4-S06). Store all N answers for TARa (G4-S21). Optional tie policy by support (G4-S19). |
| Judge | `AttributionOut(verdict, explanation, unsupported_facets)`; `JUDGE_SYSTEM` forbids outside knowledge and asks for the atom's decisive words; one call per change (T2) | Field order explanation → facets → verdict, plus `cannot_judge` (G4-S10). Order swap (G4-S11). k = 3 samples (G4-S12). Per-facet statements and leave-one-out precision (G4-S18). Two AIS questions (G4-S17). Separate judge model (G4-S16). |
| Trace | T1: atom exists, verbatim `evidence_quote`, reason per facet; `CoverageLink`, `FacetJustification.atom_ids` | Trace recall and trace precision as reported metrics (G4-S18). |
| Audit | `LLMCallRecord`, replay cache keyed by `request_hash`, `variant` for independent votes | `request_hash` covers provider, model, effort, prompt version, schema, prompts, variant; **`temperature` and the output limit are not part of it** (G4-S05). Stability report (G4-S21). |
| Blackboard | Append-only `BlackboardEntry`, `Stage`, `StageState` with `stale` | Declared triggers and a scheduler (G4-S01). Matrix view (G4-S02). Export bundle (G4-S03). |
| Repair | `repair_rounds = 3`, `Provenance.repair_round` | Closed action set and outcome label (G4-S07). Corrected/harmed/unchanged accounting (G4-S08). Stated weight of other opinions (G4-S09). |
| Review | `DecisionStatus`, `Decision`, `SignOff.change_set_hash` | Queue ordered by disagreement (G4-S13). The same two questions for humans as for the judge (G4-S17). |
| Auto-accept | `auto_accept_min_confidence` on the model's self-reported `ProfileChange.confidence` | None of the works read here supports a self-reported number as a calibrated signal; the evidence-based alternatives are vote agreement, judge agreement and order consistency (G4-S11 to G4-S13). This is our inference, not a finding of a cited paper. |
| Leakage | `exclude_namespaces`, `use_hints`, term-free atoms, `Atom.counterfactual_of` | Memorisation probe with a stored label (G4-S22). |
| Scoring | `ProfileElement`, `ElementSource` gold or generated, `DeltaStatus` | An "unjudged" outcome, pooled adjudication, three precision figures (G4-S23). Rank stability across reviewers (G4-S24). Judge validation table (G4-S20). |

---

## 6. Leads from the task description: confirmed or corrected

| Lead | Result |
|---|---|
| What debate studies conclude about debate versus voting, and the protocol they recommend | **Confirmed, with nuance.** Du et al.: debate beats a single agent; their final answer is itself a majority vote. Smit et al.: no protocol wins consistently; debate is not reliably better than self-consistency or ensembling and is sensitive to tuning; an agreement-level prompt helps. Choi et al.: majority voting explains most of the gain; debate alone is a martingale; it needs a bias toward correct answers. Practical protocol: vote by default. |
| LLM-as-judge methods, biases and mitigations | **Confirmed.** Position bias with swap as mitigation (FastChat, FairEval, both in code); evidence-first and multiple samples (FairEval); one criterion per prompt with form filling (G-Eval); batch-wise comparison (BatchEval); coarse scale, anchoring, perplexity bias (Stureborg). **Correction:** FastChat's swap does not remove the bias, it converts disagreement into a tie. |
| Definition of "attributable to identified sources" and citation recall and precision | **Confirmed.** **Correction:** ALCE precision does not ask for a minimal citation set; redundant supporting citations are allowed, and only citations that are neither sufficient alone nor needed jointly are penalised. Partial support is invisible to the automatic test. |
| How benchmark contamination is detected | **Partly corrected.** The cited paper is a position paper that defines levels and calls for measurement. The concrete detection protocol (ask the model to regenerate the benchmark; three labels; evidence) is in the authors' companion index and blog, and it is manual. |
| Non-determinism at temperature zero and practical controls | **Confirmed.** **Correction on versions:** the cited v5 (5 models, 10 runs, up to 15% accuracy variation, up to 70% best-to-worst gap) differs from the v2 PDF in the repository (5 runs, up to 10%). Controls are mostly *measurement* (TARr, TARa, spread); the follow-up notebooks add evidence on schemas and on single-job hosting. |
| Blackboard model; the 2026 workshop paper may be unfindable | **The paper text was not found; the system was.** The classics are confirmed at summary level. The 2026 paper is listed on the SDS 2026 agenda; its code is public and was read in full. Its orchestration is a fixed stage sequence over per-attribute records plus a selective discussion, not an event-driven scheduler in the Hearsay-II sense. |
| IR evaluation with incomplete or disagreeing judgments | **Confirmed.** Pooling gives fair comparisons and optimistic recall (Zobel); rankings are stable under assessor disagreement (Voorhees); measures should not treat unjudged as non-relevant (Buckley and Voorhees). |

Design tensions worth a sentence in the paper (ours):
evidence-first judging (FairEval, FastChat) versus the non-CoT recipe for numeric scores (Stureborg);
batch judging for calibration (BatchEval) versus anchoring within one generation (Stureborg);
discussion as a repair mechanism (SAST-Blackboard) versus the finding that undirected debate adds nothing in
expectation (Choi et al.), which is why discussion effects must be measured (G4-S08).

---

## 7. Bibliography notes for the author

- `atil2025nondeterminism`: the entry cites v5. The authors' repository ships only the v2 PDF under the older title.
  Search also lists a later workshop version in the ACL Anthology (`2025.eval4nlp-1.12`, title ending "in Hosted
  Environments"); if a peer-reviewed version is preferred, check that record (medium).
- `choi2025debate`: search returned a NeurIPS proceedings PDF
  (`proceedings.neurips.cc/paper_files/paper/2025/file/934252acd87f254d5d4672fbde283bd2-Paper-Conference.pdf`); the
  comment in the bib file about unchecked pages can be resolved there. The repository README confirms "NeurIPS 2025
  Spotlight" and gives the same BibTeX key.
- `smit2024mad`: the entry's author order (Smit, Grinsztajn, Duckworth, Barrett, Pretorius) matches the PMLR listing
  as returned by search; the repository's BibTeX (arXiv version) lists Duckworth before Grinsztajn. Keep the PMLR
  order for the ICML citation.
- `stureborg2024inconsistent`: a short poster version exists under a different title ("Limitations of Large Language
  Models as Automatic Evaluators", SouthNLP 2024). The entry correctly cites the arXiv paper.
- `wang2024fair`: the repository's BibTeX is the arXiv version with nine authors; the ACL 2024 version cited in the
  entry has eleven (search confirms pages 9440–9450).
- `sainz2023contamination`: the ACL Anthology BibTeX in the official repository matches the entry (pages
  10776–10787, DOI). One arXiv comment line mentions "EMNLP2024-Findings"; the Anthology record says 2023.
- `ouyang2025nondeterminism`: search gives TOSEM 34(2), Article 42, published January 2025. The repository still
  carries the earlier title "LLM is Like a Box of Chocolates".
- `chmielewski2026blackboard`: title and authors match the SDS 2026 agenda as returned by search. The CEUR volume
  was not confirmed. The public code repository (`github.com/U0iS112/654321`) has an anonymised-looking name; ask the
  authors which URL the paper cites before putting one in the text.
- `gao2023alce`: the numbers quoted in this note come from the preprint PDF in the repository; check them against
  the EMNLP version (pages 6465–6488) before citing a figure.
- `buckley2004incomplete`: if `bpref` values are ever computed, note the `bpref_bug` notice in `trec_eval`: the 2004
  paper used an earlier variant of the computation.

---

## 8. Not found or uncertain

Everything in this section is `verify:` material (confidence low): it was not confirmed from a source in this task
and must be checked against the paper before it is used.

- `chmielewski2026blackboard`: paper text, its own description of "signals", and all reported results. Hosts
  `dbis.rwth-aachen.de` and `ceur-ws.org` are blocked.
- `rashkin2023ais`: exact wording of the formal definition, annotator guidelines and agreement statistics (paper not
  read).
- `sainz2023contamination`: the names and definitions of all contamination levels (only "guideline" surfaced).
- `choi2025debate`: theorem statements, per-benchmark numbers and the exact definition of the intervention variants
  (secondary summaries only; not in the released code).
- `zheng2023judge`: per-judge consistency numbers; the few-shot and chain-of-thought judge variants (abstract-level
  only; the code shows swap and reference-guided judging).
- `wang2024fair`: the formula of the balanced position diversity entropy and the human-annotation budget.
- `liu2023geval`: whether the paper states the sampling temperature that the script uses (`temperature=2`).
- `stureborg2024inconsistent`: the full recipe list and inter-sample agreement values of the arXiv version (one
  search summary mentions Krippendorff's alpha 0.587 for GPT-4 against 0.659 for humans; unverified).
- `smit2024mad`, `du2024debate`: result tables (only README-level and project-page statements were read).
- `ouyang2025nondeterminism`: the paper's recommendations section; whether temperature 2 was part of the published
  study (the script lists `[0, 1, 2]`, the logs cover 0, 0.5 and 1).
- `atil2025nondeterminism`: v5 body text; the headline numbers are from the abstract as summarised by search.
- `erman1980hearsay`, `nii1986blackboard`: full texts; level names, the scheduler's rating function and the exact
  three-component wording are from secondary summaries.
- `zobel1998reliable`, `voorhees2000variations`: numeric results (overlap between assessors, Kendall's tau values,
  estimated numbers of unjudged relevant documents).
- `buckley2004incomplete`: the experiments that reduce the judgment sets and their correlation values.

---

## 9. Sources

Repositories (cloned, read locally):
- https://github.com/princeton-nlp/ALCE
- https://github.com/google-research-datasets/AIS
- https://github.com/lm-sys/FastChat (directory `fastchat/llm_judge`)
- https://github.com/i-Eval/FairEval
- https://github.com/nlpyang/geval
- https://github.com/ypw0102/BatchEval
- https://github.com/composable-models/llm_multiagent_debate and https://github.com/composable-models/llm_debate
- https://github.com/instadeepai/DebateLLM
- https://github.com/deeplearning-wisc/debate-or-vote
- https://github.com/U0iS112/654321 (SAST-Blackboard) and https://github.com/jundahuang9123/blackboard-workbench
- https://github.com/breckbaldwin/llm-stability
- https://github.com/ShuyinOuyang/LLM-is-a-box-of-chocolate
- https://github.com/hitz-zentroa/lm-contamination
- https://github.com/usnistgov/trec_eval
- https://raw.githubusercontent.com/southnlp/southnlp2024/main/papers/southnlp2024-poster-42.pdf

Pages returned by web search (summaries only, not opened):
- https://arxiv.org/abs/2305.14325 , https://proceedings.mlr.press/v235/du24e.html
- https://arxiv.org/abs/2311.17371 , https://proceedings.mlr.press/v235/smit24a.html
- https://arxiv.org/abs/2508.17536 , https://neurips.cc/virtual/2025/poster/116557 ,
  https://proceedings.neurips.cc/paper_files/paper/2025/file/934252acd87f254d5d4672fbde283bd2-Paper-Conference.pdf
- https://arxiv.org/abs/2306.05685
- https://arxiv.org/abs/2303.16634 , https://aclanthology.org/2023.emnlp-main.153
- https://arxiv.org/abs/2305.17926 , https://aclanthology.org/2024.acl-long.511
- https://arxiv.org/abs/2405.01724
- https://arxiv.org/abs/2401.00437 , https://aclanthology.org/2024.acl-long.846
- https://arxiv.org/abs/2112.12870 , https://aclanthology.org/2023.cl-4.2/ ,
  https://direct.mit.edu/coli/article/49/4/777/116438/Measuring-Attribution-in-Natural-Language
- https://arxiv.org/abs/2310.18018 , https://aclanthology.org/2023.findings-emnlp.722/
- https://arxiv.org/abs/2308.02828 , https://dl.acm.org/doi/10.1145/3697010
- https://arxiv.org/abs/2408.04667 , https://aclanthology.org/2025.eval4nlp-1.12
- https://dbis.rwth-aachen.de/SDS26/
- https://dl.acm.org/doi/10.1145/356810.356816 , https://ojs.aaai.org/index.php/aimagazine/article/view/537 ,
  http://i.stanford.edu/pub/cstr/reports/cs/tr/86/1123/CS-TR-86-1123.pdf
- https://people.eng.unimelb.edu.au/ammoffat/sigir98/abstracts/zobel.html
- https://www.nist.gov/publications/variations-relevance-judgments-and-measurement-retrieval-effectiveness
- https://ir.webis.de/anthology/2004.sigirconf_conference-2004.5/
