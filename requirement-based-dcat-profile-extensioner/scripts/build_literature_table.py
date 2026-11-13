#!/usr/bin/env python3
"""Regenerate docs/literature-steps.md from the verified research result (JSON) and the
implementation status below. The status is ours and must be kept current by hand.

Usage: python scripts/build_literature_table.py <groups.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

I, P, N = "implemented", "partial", "planned"
STATUS = {
    "G1-S01": (P, "compound / term / modality lint; no paraphrase clustering"),
    "G1-S02": (P, "one index record per term; base elements listed first; no source-excerpt list"),
    "G1-S03": (I, "one propose call per atom; deterministic consolidate"),
    "G1-S04": (I, "numbered procedure; reading and information_needed stored"),
    "G1-S05": (I, "disposition covered_by_base, re-checked by B1"),
    "G1-S06": (I, "named sections, mistakes footer, versioned prompts (Claude takes no temperature)"),
    "G1-S07": (P, "closed candidate list in the prompt; terms outside it flagged (V1 warning)"),
    "G1-S08": (I, "reuse ladder; a mint needs reason_no_reuse (V4)"),
    "G1-S09": (I, "immutable base; only typed deltas"),
    "G1-S10": (I, "typed ProfileChange; the engine owns IRIs and SHACL"),
    "G1-S11": (P, "set-level verification after merging; no per-change SHACL scratch copy"),
    "G1-S12": (P, "C7 witness for the whole extension; per-atom witness planned"),
    "G1-S13": (I, "repair stage, correction section, bounded rounds"),
    "G1-S14": (P, "T2 judge verdicts; no corrected fragment"),
    "G1-S15": (I, "engine/verbalise.py shared by judge, reviewer and documentation"),
    "G1-S16": (I, "evidence on every card; Undecided option; decisions logged"),
    "G1-S17": (P, "[HUMAN FEEDBACK] prompt section and notes; no feedback codes"),
    "G1-S18": (I, "covers + facet justifications; T1 is an error; prov:wasDerivedFrom"),
    "G1-S19": (I, "V3 per change, C1/C2 per extension"),
    "G1-S20": (N, ""), "G1-S21": (P, "extension rate and coverage metrics"), "G1-S22": (N, "evaluator"),
    "G1-S23": (I, "term-free lint; namespaces hidden from the index"),
    "G1-S24": (P, "pipeline switches (retrieval, judge, votes, automatic acceptance)"), "G1-S25": (N, ""),
    "G2-S01": (P, "atom contract and coverage status"), "G2-S02": (P, "intake lint"), "G2-S03": (N, ""),
    "G2-S04": (P, "out_of_scope disposition"), "G2-S05": (N, ""), "G2-S06": (N, ""),
    "G2-S07": (I, "reuse ladder in prompt, retrieval and V4"), "G2-S08": (I, "reading / information_needed per atom"),
    "G2-S09": (I, "versioned prompts; call records keep the prompts"), "G2-S10": (I, "independent votes per atom; repair"),
    "G2-S11": (P, "merging of identical elements only"), "G2-S12": (P, "decision log with notes"),
    "G2-S13": (I, "repair scoped to the failed checks of one change"), "G2-S14": (I, "repair_rounds"),
    "G2-S15": (I, "supersedes lineage; full JSON export"), "G2-S16": (P, "full / partial coverage with a mandatory reason"),
    "G2-S17": (P, "C7 positive witness"), "G2-S18": (N, ""), "G2-S19": (N, ""), "G2-S20": (N, ""), "G2-S21": (N, ""),
    "G2-S22": (P, "metrics panel"), "G2-S23": (N, ""),
    "G2-S24": (I, "proposer / repairer / judge roles; no free conversation"), "G2-S25": (I, "stage stepper with a sign-off gate"),
    "G3-S01": (I, "reuse base element > tighten > reuse term > mint"), "G3-S02": (I, "V3 / C1"),
    "G3-S03": (P, "range kind and subclass checks"), "G3-S04": (N, "controlled-vocabulary levels not modelled"),
    "G3-S05": (P, "T2 judge"), "G3-S06": (P, "minting in the own namespace with label and definition"), "G3-S07": (N, ""),
    "G3-S08": (P, "usage note field"), "G3-S09": (I, "extension.shacl.ttl imports the base"), "G3-S10": (I, "C1-C7"),
    "G3-S11": (P, "positive witness only"), "G3-S12": (I, "stable atom ids and back-links"), "G3-S13": (N, "unverified"),
    "G3-S14": (I, "information_needed first, then mapping"), "G3-S15": (P, "review queue and log"), "G3-S16": (N, ""),
    "G3-S17": (P, "documentation lists every change with base -> new"), "G3-S18": (N, ""),
    "G3-S19": (I, "coverage status per atom"), "G3-S20": (N, ""), "G3-S21": (N, ""), "G3-S22": (N, ""), "G3-S23": (N, ""),
    "G3-S24": (P, "domain-specific vocabularies down-weighted"), "G3-S25": (P, "extension rate"),
    "G4-S01": (I, "blackboard store, stages as knowledge sources, pipeline control"), "G4-S02": (P, "votes recorded per change"),
    "G4-S03": (I, "export with log and model calls"), "G4-S04": (I, "symbolic checks before the judge"),
    "G4-S05": (P, "replay cache; no sampling settings on Claude"), "G4-S06": (I, "independent votes with majority"),
    "G4-S07": (N, ""), "G4-S08": (N, ""), "G4-S09": (N, ""), "G4-S10": (P, "typed verdict with explanation"),
    "G4-S11": (N, ""), "G4-S12": (N, ""), "G4-S13": (N, ""), "G4-S14": (N, ""), "G4-S15": (N, ""), "G4-S16": (N, ""),
    "G4-S17": (P, "T1 verbatim quote + T2 judge"), "G4-S18": (N, ""), "G4-S19": (N, ""), "G4-S20": (N, ""),
    "G4-S21": (N, ""), "G4-S22": (N, ""), "G4-S23": (N, ""), "G4-S24": (N, ""),
}
TITLES = {
    "G1-ontology-generation": "Ontology generation and evaluation with LLMs",
    "G2-requirements-engineering": "Requirements engineering",
    "G3-application-profile-practice": "Application-profile practice (DCAT-AP and its extensions)",
    "G4-llm-reliability": "Reliability of LLM decisions",
}


def main(path: str) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    counts = {I: 0, P: 0, N: 0}
    rows: list[str] = []
    for group in data["groups"]:
        flags = " ".join(group["overreach_flags"])
        rows.append(f"\n## {TITLES[group['id']]}\n")
        if group["papers_not_found"]:
            rows.append(f"Not found: {', '.join(group['papers_not_found'])}.\n")
        rows.append("| Step | From | What they did | Verdict | Ours | Here |\n|---|---|---|---|---|---|")
        for step in group["steps"]:
            state, note = STATUS[step["id"]]
            counts[state] += 1
            what = step["what_they_did"].replace("|", "/").replace("\n", " ")
            if len(what) > 420:
                what = what[:417].rsplit(" ", 1)[0] + " ..."
            ours = "yes" if step["id"] in flags else ""
            here = state + (f": {note}" if note else "")
            rows.append(f"| **{step['id']}** {step['name']} | {', '.join(step['from_keys'])} | {what} | "
                        f"{step['verdict'].replace('_', ' ')} | {ours} | {here} |")
    head = [
        "# Key steps taken from the literature", "",
        "Steps extracted from the papers of the RQ1 bibliography (`bibliography.2026-11-11a.bib`); each was re-checked "
        "independently by a sceptic agent against primary sources and code repositories.",
        "**Verdict**: fact-check of \"what they did\" (partially confirmed = the text was corrected; unverified = no "
        "independent support found). **Ours** = the adaptation goes beyond what the source prescribes, so it is our "
        "design, not the paper's claim. **Here** = state in this tool. Evidence, quotes and repository paths: "
        "`docs/research/` (one report per group and its verification report).", "",
        f"Summary: {sum(counts.values())} steps; {counts[I]} implemented, {counts[P]} partly, {counts[N]} planned.",
    ]
    out = Path(__file__).resolve().parents[1] / "docs" / "literature-steps.md"
    out.write_text("\n".join(head + rows) + "\n", encoding="utf-8")
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
