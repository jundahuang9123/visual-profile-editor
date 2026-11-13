#!/usr/bin/env python3
"""Copy vocabulary files into backend/profile_extensioner/data/vocab/ and write its MANIFEST.json.

Input: a directory with one sub-directory per prefix and a MANIFEST.json listing prefix,
namespace, local_path, source URL, version/commit, sha256 and licence (as produced by the
vocabulary-sourcing step). N-Quads files are flattened to Turtle. Licences marked "verify:"
in the input manifest are carried over unchanged: check them before redistributing.

Usage: python scripts/vendor_vocabularies.py --source /path/to/vocab [--only dcat dcterms ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rdflib import Dataset, Graph

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend" / "profile_extensioner" / "data" / "vocab"
DEFAULT = ["dcat", "dcterms", "foaf", "skos", "prov", "vcard", "adms", "odrl", "spdx", "locn", "time", "dcatap", "eli"]
FORMATS = {".ttl": "turtle", ".rdf": "xml", ".owl": "xml", ".nq": "nquads", ".jsonld": "json-ld"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--only", nargs="*", default=DEFAULT)
    args = parser.parse_args(argv)
    manifest = json.loads((args.source / "MANIFEST.json").read_text(encoding="utf-8"))
    TARGET.mkdir(parents=True, exist_ok=True)
    out = []
    for entry in manifest["vocabularies"]:
        prefix = entry["prefix"]
        if prefix not in args.only:
            continue
        path = Path(entry["local_path"])
        fmt = FORMATS.get(path.suffix.lower(), "turtle")
        if fmt == "nquads":
            dataset = Dataset()
            dataset.parse(path, format="nquads")
            graph = Graph()
            for s, p, o, _ in dataset.quads():
                graph.add((s, p, o))
        else:
            graph = Graph().parse(path, format=fmt)
        name = f"{prefix}.ttl"
        (TARGET / name).write_text(graph.serialize(format="turtle"), encoding="utf-8")
        out.append({
            "prefix": prefix, "namespace": entry["namespace"], "file": name, "format": "turtle",
            "title": entry.get("title", ""), "source_url": entry.get("source_url", ""),
            "version": entry.get("source_commit") or entry.get("version", ""),
            "source_sha256": entry.get("sha256", ""),
            "licence": entry.get("licence") or entry.get("license", ""),
            "triples": len(graph),
            "sha256": hashlib.sha256((TARGET / name).read_bytes()).hexdigest(),
        })
        print(f"{prefix:8s} {len(graph):6d} triples  {entry.get('licence') or entry.get('license', '')}"[:150])
    (TARGET / "MANIFEST.json").write_text(json.dumps({"vocabularies": out}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
