#!/usr/bin/env python3
"""Turn an RQ1 reference set (requirements-benchmark-references, reference-sets-v3/<case>.json)
into an atom set for this tool (the A-gold input of the RQ2 plan).

Only what the RQ2 atom contract allows is copied: id, the standard-form statement, the subject
(standard_form.resource), the modality and a source locator. Evaluator fields (relation to the
base, reuse rules, anchor quotes, evidence labels, overlaps) are NOT copied: they would put
the answer into the input. By default only the atoms scored by default are taken.

The output is a local file for a run; do not commit reference-derived atom sets to this repository.

Modality: the reference sets record the SOURCE's kind of statement, not must/should/may. The
mapping below is conservative; everything else becomes "unspecified" (strongest licensed
obligation: recommended).

Usage: python scripts/import_rq1_reference.py <case.json> <out.yaml> [--all] [--base dcat-ap-1.1]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

MODALITY = {
    "explicit_requirement": "must",
    "mandatory": "must",
    "recommendation": "should",
    "recommended": "should",
    "optional": "may",
}
BASES = {"DCAT-AP 1.1": "dcat-ap-1.1", "DCAT-AP 3.0.0": "dcat-ap-3.0.0", "DCAT-AP 3.0.1": "dcat-ap-3.0.1"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reference", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--all", action="store_true", help="take every content atom, not only those scored by default")
    parser.add_argument("--base", help="base profile id (default: from the reference set's 'base' field)")
    args = parser.parse_args(argv)

    data = json.loads(args.reference.read_text(encoding="utf-8"))
    base = args.base or BASES.get(str(data.get("base")).strip())
    atoms = []
    for atom in data["atoms"]:
        if not (atom.get("scored_by_default") if not args.all else atom.get("stratum") == "content"):
            continue
        form = atom.get("standard_form") or {}
        subject = str(form.get("resource") or "dataset").split(" or ")[0].strip().lower() or "dataset"
        atoms.append({
            "id": atom["id"],
            "statement": atom["statement"],
            "subject": subject,
            "modality": MODALITY.get(str(atom.get("modality") or "").lower(), "unspecified"),
            "source_reference": {"document": str(data.get("case") or args.reference.stem),
                                 "locator": str(atom.get("source_locator") or "")},
        })
    out = {
        "title": f"{data.get('case', args.reference.stem)} reference atoms (RQ1 reference-sets-v3)",
        "description": "Imported by scripts/import_rq1_reference.py; evaluator fields removed.",
        "benchmark_id": str(data.get("case") or args.reference.stem),
        "base_profile_ids": [base] if base else [],
        "atoms": atoms,
    }
    args.out.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"{len(atoms)} atoms -> {args.out} (base {base})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
