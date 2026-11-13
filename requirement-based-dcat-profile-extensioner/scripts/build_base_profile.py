#!/usr/bin/env python3
"""Build a base-profile directory from a checkout of the official SEMICeu/DCAT-AP repository.

For one release it
  * copies the official SHACL files UNMODIFIED (and records their SHA-256),
  * reads the obligation level (mandatory / recommended / optional) of every
    property from the "quick reference" table of the release's specification
    HTML, because the SHACL files only carry the mandatory ones (sh:minCount),
  * writes profile.yaml (identity, source commit, licence, shape files).

Usage:
  python scripts/build_base_profile.py --semic-repo /path/to/DCAT-AP --release 3.0.1

The output goes to backend/profile_extensioner/data/base-profiles/dcat-ap-<release>/.
Nothing is downloaded: the repository checkout is the only input.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from profile_extensioner.iri import Prefixes  # noqa: E402

# Which files of a release hold the constraint shapes, and which hold range-only shapes.
RELEASE_FILES = {
    "1.1": {"zip": "shacl-201706.zip", "constraints": ["shacl-201706/dcat-ap.shapes.ttl"], "ranges": []},
    "3.0.1": {"constraints": ["shacl/dcat-ap-SHACL.ttl"], "ranges": ["shacl/ranges.ttl"]},
    "3.0.0": {"constraints": ["shacl/dcat-ap-SHACL.ttl"], "ranges": []},
}
MAIN_CLASSES = ["dcat:Catalog", "dcat:Dataset", "dcat:Distribution", "dcat:DataService",
                "dcat:DatasetSeries", "dcat:CatalogRecord"]


def strip_tags(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def read_quick_reference(spec_html: str) -> list[dict[str, str]]:
    """Rows of the quick-reference table: class label, class IRI, obligation, property label, property IRI."""
    start = spec_html.index('id="table-quickoverview"')
    table = spec_html[start: spec_html.index("</table>", start)]
    rows = []
    for row in re.findall(r"<tr>\s*(<td>.*?)</tr>", table, flags=re.S):
        cells = re.findall(r"<td>(.*?)</td>", row, flags=re.S)
        if len(cells) != 5:
            continue
        class_label, class_iri, obligation, property_label, property_iri = (strip_tags(cell) for cell in cells)
        if not property_iri or obligation.lower() not in {"mandatory", "recommended", "optional"}:
            continue
        rows.append({
            "class_label": class_label, "class_iri": class_iri, "obligation": obligation.lower(),
            "property_label": property_label, "property_iri": property_iri,
        })
    return rows


CLASS_LABELS_1_1 = {
    "Data Catalogue": "dcat:Catalog", "Catalogue": "dcat:Catalog", "Catalogue Record": "dcat:CatalogRecord",
    "Dataset": "dcat:Dataset", "Distribution": "dcat:Distribution", "Agent": "foaf:Agent",
    "Category Scheme": "skos:ConceptScheme", "Category": "skos:Concept", "Licence Document": "dct:LicenseDocument",
    "Checksum": "spdx:Checksum", "Identifier": "adms:Identifier", "Period of Time": "dct:PeriodOfTime",
}


def read_obligations_1_1(rdf_text: str) -> list[dict[str, str]]:
    """DCAT-AP 1.1 states obligations in each property's vann:usageNote ("Mandatory property. ...") and the
    class in its rdfs:label ("Data Catalogue - description")."""
    rows = []
    for block in re.findall(r'<rdf:Description rdf:about="([^"]+)">(.*?)</rdf:Description>', rdf_text, flags=re.S):
        about, body = block
        note = re.search(r"<vann:usageNote[^>]*>\s*(Mandatory|Recommended|Optional) property", body)
        label = re.search(r"<rdfs:label[^>]*>([^<]+)</rdfs:label>", body)
        if not note or not label or " - " not in label.group(1):
            continue
        class_label, property_label = (part.strip() for part in label.group(1).split(" - ", 1))
        class_curie = {key.lower(): value for key, value in CLASS_LABELS_1_1.items()}.get(class_label.lower())
        if class_curie is None:
            print(f"warning: unknown class label {class_label!r} for {about}", file=sys.stderr)
            continue
        rows.append({"class_label": class_label, "class_iri": Prefixes().expand(class_curie), "obligation": note.group(1).lower(),
                     "property_label": property_label, "property_iri": about})
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--semic-repo", required=True, type=Path, help="checkout of github.com/SEMICeu/DCAT-AP")
    parser.add_argument("--release", required=True, choices=sorted(RELEASE_FILES))
    parser.add_argument("--out", type=Path, default=ROOT / "backend" / "profile_extensioner" / "data" / "base-profiles")
    args = parser.parse_args(argv)

    release_dir = args.semic_repo / "releases" / args.release
    files = RELEASE_FILES[args.release]
    target = args.out / f"dcat-ap-{args.release}"
    (target / "shacl").mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "-C", str(args.semic_repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False).stdout.strip()

    sources = []
    if files.get("zip"):
        import zipfile

        archive = release_dir / files["zip"]
        sources.append({"path": f"releases/{args.release}/{files['zip']}", "sha256": sha256(archive)})
        with zipfile.ZipFile(archive) as bundle:
            for relative in files["constraints"] + files["ranges"]:
                (target / "shacl" / Path(relative).name).write_bytes(bundle.read(relative))
        spec_path = release_dir / f"dcat-ap_{args.release}.rdf"
        rows = read_obligations_1_1(spec_path.read_text(encoding="utf-8"))
    else:
        for relative in files["constraints"] + files["ranges"]:
            source = release_dir / relative
            shutil.copyfile(source, target / "shacl" / source.name)
            sources.append({"path": f"releases/{args.release}/{relative}", "sha256": sha256(source)})
        spec_path = release_dir / "index.html"
        rows = read_quick_reference(spec_path.read_text(encoding="utf-8"))
    prefixes = Prefixes()
    classes: dict[str, dict] = {}
    for row in rows:
        entry = classes.setdefault(prefixes.compact(row["class_iri"]), {"label": row["class_label"], "properties": {}})
        entry["properties"][prefixes.compact(row["property_iri"])] = row["obligation"]
    counts = {level: sum(1 for row in rows if row["obligation"] == level) for level in ("mandatory", "recommended", "optional")}

    header = (
        f"# Obligation level of every property of DCAT-AP {args.release}, per class.\n"
        f"# Generated by scripts/build_base_profile.py from the quick-reference table of\n"
        f"# releases/{args.release}/{spec_path.name} (SEMICeu/DCAT-AP @ {commit[:12]}, sha256 {sha256(spec_path)[:16]}...).\n"
        f"# {counts['mandatory']} mandatory, {counts['recommended']} recommended, {counts['optional']} optional. Do not edit by hand.\n"
    )
    (target / "obligations.yaml").write_text(
        header + yaml.safe_dump({"classes": classes}, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    profile = {
        "id": f"dcat-ap-{args.release}",
        "title": f"DCAT-AP {args.release}",
        "version": args.release,
        "description": "DCAT Application Profile for data portals in Europe (SEMIC).",
        "homepage": f"https://semiceu.github.io/DCAT-AP/releases/{args.release}/" if not files.get("zip") else "",
        "licence": "CC-BY-4.0",
        "source": {
            "repository": "https://github.com/SEMICeu/DCAT-AP",
            "commit": commit,
            "files": sources + [{"path": f"releases/{args.release}/{spec_path.name}", "sha256": sha256(spec_path)}],
        },
        "shapes": {
            "constraints": [f"shacl/{Path(name).name}" for name in files["constraints"]],
            "ranges": [f"shacl/{Path(name).name}" for name in files["ranges"]],
        },
        "obligations": "obligations.yaml",
        "main_classes": MAIN_CLASSES,
    }
    if files.get("zip"):
        # 1.1 shapes use implicit class targets (shape IRI = class IRI) without typing the IRI as a class.
        profile["implicit_class_targets"] = True
    (target / "profile.yaml").write_text(
        "# Generated by scripts/build_base_profile.py. The shape files are the official ones, unmodified.\n"
        + yaml.safe_dump(profile, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"{target}: {len(classes)} classes, {len(rows)} properties {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
