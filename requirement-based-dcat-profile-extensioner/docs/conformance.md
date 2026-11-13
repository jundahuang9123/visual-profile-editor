# Conformance of an extension to its base profile

The last automatic stage checks whether the generated extension still conforms
to the DCAT-AP release it extends. The rules come from the SEMIC DCAT-AP reuse
guidelines ("How to create your DCAT-AP profile", repository
`SEMICeu/DCAT-AP-reuse-guidelines`, commit `e958ded`, `index.html`) and from the
DCAT-AP specification; where a rule is our own interpretation it is marked
**derived**. Quotes are verbatim, line numbers refer to that `index.html`.

## The governing rule

> "these adjustments are possible, if they tighten existing constraints. It is not
> possible to loosen them under any conditions, as the result would no longer be
> compliant with DCAT-AP." (lines 376-379)

and

> "all DCAT-AP profiles must comply with the requirements and restrictions imposed by
> DCAT-AP, namely mandatory properties and controlled vocabularies that must be used
> with select properties" (lines 100-105)

Conformance is always relative to **one exact release**: DCAT-AP 3.0.1 itself relaxed
three cardinalities of 3.0.0 (its `CHANGELOG.md`), so the tool pins the release
(`data/base-profiles/<id>/profile.yaml` records repository, commit and SHA-256 of
every file).

## What the base is

* **Constraints** come from the official SHACL file of the release, unmodified
  (`shacl/dcat-ap-SHACL.ttl`, plus `ranges.ttl` for 3.0.1).
* **Obligation levels** (mandatory / recommended / optional) come from the
  specification's quick-reference table, because the SHACL file only carries the
  mandatory ones (`sh:minCount`). `scripts/build_base_profile.py` extracts them;
  for 3.0.1: 20 mandatory, 39 recommended, 72 optional properties.

## Rules checked (report ids)

| Id | Rule | Source |
|----|------|--------|
| C1 | Every constraint the extension states on a (class, property) is **added** (the base does not constrain it) or **tightened**: minimum not lowered, maximum not raised, obligation not lowered, range narrowed (subclass) never widened, value list a subset, node kind a subset. | RG lines 376-379, 398-400 ("tightened from 0..* to 1..*, which is a compliant change"), 1293, 1304, 1180-1181 ("Narrowing down the value space will not create any issues but extending it will.") |
| C2 | No constraint contradicts the base so that no data could satisfy both (minimum above the base maximum, a different datatype, disjoint node kinds or value lists). A different `sh:datatype` is treated as a contradiction even for an XSD subtype, because `sh:datatype` matches exactly and the base shape would reject the value. | derived; RG lines 1066, 1084 (range kind cannot change) |
| C3 | Minted terms live in the extension's own namespace and do not re-mint an existing term. | RG lines 471-474 ("we create our own in our own namespace ... along with its label, definition and possible domain and range") |
| C4 | Reused terms exist (no invented IRIs) and are reused as they are. | RG lines 291-292, 828-830 |
| C5 | Every element traces to at least one requirement atom. | RG lines 262-264 ("Use cases are intended to justify and explain relevant design decisions, in particular those that introduce new elements, tighten existing constraints ...") |
| C6 | The compiled shapes are valid SHACL (SHACL-SHACL via pySHACL `meta_shacl`). | W3C SHACL |
| C7 | **Witness data:** for every class the extension constrains, an instance satisfying all mandatory and recommended constraints of base + extension is generated and validated with pySHACL against (a) base + extension shapes and (b) the official base shapes alone. Data valid under the extension must be valid under the base. | derived (instance-level reading of RG-01) |

C1-C5 are static; C6-C7 run a SHACL engine. Any failing error-level rule makes the
verdict `non_conformant` and blocks the human sign-off.

## Why the published shapes cannot loosen, and why C1 is still needed

The extension's SHACL file contains only what the extension adds or tightens and
imports the base shapes, so data is validated against base AND extension (SHACL
shapes are conjunctive). Such a delta can never *relax* a base shape in SHACL. It
can still (i) document a looser obligation than the base (C1), (ii) contradict
the base so that nothing validates (C2, C7), or (iii) mint where it should reuse
(C3/C4, and check V4 during verification). The same comparison runs per change
during verification (check V3), so an illegal refinement is caught, repaired or
queued long before this final stage.

## Known limits

* Range narrowing is recognised only through `rdfs:subClassOf` axioms the
  vocabulary index knows; an unknown class relation is reported as
  `incomparable` (warning), not as legal.
* Controlled-vocabulary usage levels of DCAT-AP 3.0.1 (closed / at least one /
  recommended / may; RG lines 907-950) are not yet modelled.
* The witness generator invents minimal values; constraints it cannot satisfy
  (patterns, nested shapes) give a warning, not a failure.
