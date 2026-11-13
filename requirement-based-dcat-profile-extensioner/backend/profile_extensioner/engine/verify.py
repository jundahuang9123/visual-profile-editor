"""Stage ``verify``: symbolic checks on every proposed change.

Checks (ids are stable; reports and the review queue are keyed to them):

    V1  every term exists (or is properly minted in the profile's namespace)
    V2  domain and range fit the vocabulary's declarations
    V3  legal refinement of the base: may tighten, never loosen or contradict
    V4  reuse before mint: a minted term states why no candidate fits
    V5  internal consistency of the constraints
    V6  the compiled shapes are valid SHACL            (run after compile, see ``check_shapes_valid``)
    T1  trace: the change cites existing atoms, quotes them verbatim, justifies every constraint
        it sets and is not stricter than the atoms' wording licenses
    B1  a "covered by the base" claim really holds     (on assessments, see ``verify_assessment``)

Severity ``error`` blocks a change (it goes to repair, then to the human);
``warning`` is shown to the reviewer; ``info`` is a note.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from rdflib import Graph

from ..conformance.refinement import compare_facets, compare_obligation
from ..contracts import (
    MODALITY_OBLIGATION,
    OBLIGATION_RANK,
    Atom,
    AtomAssessment,
    Candidate,
    CheckResult,
    ProfileChange,
    Project,
)
from ..iri import is_absolute_iri, is_valid_local_name, local_name, words_of
from ..knowledge import KnowledgeBase
from ..knowledge.shacl_reader import ShapeFacets

XSD = "http://www.w3.org/2001/XMLSchema#"
LITERAL_CLASSES = {
    "http://www.w3.org/2000/01/rdf-schema#Literal",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString",
}
KNOWN_DATATYPES = LITERAL_CLASSES | {
    XSD + name for name in (
        "string", "boolean", "decimal", "integer", "nonNegativeInteger", "positiveInteger", "int", "long",
        "float", "double", "date", "dateTime", "dateTimeStamp", "time", "gYear", "gYearMonth", "duration",
        "anyURI", "language", "hexBinary", "base64Binary", "token", "normalizedString",
    )
}
STRONG_CANDIDATE_SCORE = 6.0   # a candidate this close to the atom must be addressed before minting


@dataclass
class VerifyContext:
    kb: KnowledgeBase
    project: Project
    atoms: dict[str, Atom]
    changes: list[ProfileChange] = field(default_factory=list)          # the current change set
    candidates: dict[str, list[Candidate]] = field(default_factory=dict)  # atom id -> retrieved candidates

    def minted_classes(self) -> set[str]:
        return {c.target_class for c in self.changes if c.kind == "mint_class" and c.decision.status != "rejected"}

    def minted_properties(self) -> set[str]:
        return {c.path for c in self.changes if c.kind == "mint_property" and c.path and c.decision.status != "rejected"}

    def reused_classes(self) -> set[str]:
        return {c.target_class for c in self.changes if c.kind == "reuse_class" and c.decision.status != "rejected"}


def _ok(check: str, message: str = "") -> CheckResult:
    return CheckResult(check=check, passed=True, severity="info", message=message)


def _fail(check: str, message: str, severity: str = "error", **details: object) -> CheckResult:
    return CheckResult(check=check, passed=False, severity=severity, message=message, details=dict(details))  # type: ignore[arg-type]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


# ---------------------------------------------------------------------------
# V1 - terms exist
# ---------------------------------------------------------------------------


def check_terms_exist(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    kb, results = ctx.kb, []
    target = change.target_class

    def class_known(iri: str) -> bool:
        term = kb.term(iri)
        return kb.base.has_class(iri) or (term is not None and term.kind == "class") or iri in ctx.minted_classes()

    if not is_absolute_iri(target):
        results.append(_fail("V1", f"The target class '{target}' is not a known term.", term=target))
    elif change.kind == "mint_class":
        if not kb.is_minted(target):
            results.append(_fail("V1", f"A minted class must live in the profile namespace, not at {target}.", term=target))
        elif not is_valid_local_name(local_name(target)):
            results.append(_fail("V1", f"'{local_name(target)}' is not a usable local name.", term=target))
        elif kb.term(target) is not None:
            results.append(_fail("V1", f"{kb.curie(target)} already exists; reuse it instead of minting it.", term=target))
    elif not class_known(target):
        if kb.is_minted(target):
            results.append(_fail("V1", f"The class {kb.curie(target)} is used but no change mints it.", term=target))
        else:
            results.append(_fail("V1", f"The class {kb.curie(target)} is not in the vocabulary index (invented term).", term=target))

    if not change.is_class_change:
        path = change.path
        if not path or not is_absolute_iri(path):
            results.append(_fail("V1", f"The property '{path}' is not a known term.", term=path or ""))
        elif change.kind == "mint_property":
            if not kb.is_minted(path):
                results.append(_fail("V1", f"A minted property must live in the profile namespace, not at {path}.", term=path))
            elif not is_valid_local_name(local_name(path)):
                results.append(_fail("V1", f"'{local_name(path)}' is not a usable local name.", term=path))
            elif kb.term(path) is not None:
                results.append(_fail("V1", f"{kb.curie(path)} already exists; reuse it instead of minting it.", term=path))
        else:
            term = kb.term(path)
            if term is None and path not in ctx.minted_properties():
                results.append(_fail("V1", f"The property {kb.curie(path)} is not in the vocabulary index (invented term).", term=path))
            elif term is not None and term.kind != "property":
                results.append(_fail("V1", f"{kb.curie(path)} is a class, not a property.", term=path))
            elif term is not None and ctx.project.config.retrieval and change.provenance.author_type != "human":
                offered = {c.iri for atom_id in change.atom_ids for c in ctx.candidates.get(atom_id, [])}
                on_class = {element.path for element in kb.base.elements(target)} if kb.base.has_class(target) else set()
                if offered and path not in offered | on_class:
                    results.append(_fail(
                        "V1", f"{kb.curie(path)} exists but was not among the terms retrieved for the atom.",
                        severity="warning", term=path, problem="outside_candidates",
                    ))

    facets = change.facets
    if facets.range_class and not class_known(facets.range_class):
        if facets.range_class in KNOWN_DATATYPES:
            results.append(_fail("V1", f"{kb.curie(facets.range_class)} is a datatype but is given as a class range.", term=facets.range_class))
        else:
            results.append(_fail("V1", f"The range class {kb.curie(facets.range_class)} is not a known class.", term=facets.range_class))
    if facets.range_datatype and facets.range_datatype not in KNOWN_DATATYPES:
        results.append(_fail("V1", f"The datatype {kb.curie(facets.range_datatype)} is not a known datatype.", term=facets.range_datatype))
    for value in facets.controlled_vocabulary:
        if not is_absolute_iri(value):
            results.append(_fail("V1", f"The vocabulary value '{value}' is not an IRI.", severity="warning", term=value))
    for label, value in (("superclass", change.super_class), ("super-property", change.sub_property_of)):
        if value and kb.term(value) is None and value not in ctx.minted_classes() | ctx.minted_properties():
            results.append(_fail("V1", f"The {label} {kb.curie(value)} is not a known term.", term=value))
    return results or [_ok("V1", "all terms exist")]


# ---------------------------------------------------------------------------
# V2 - domain and range fit
# ---------------------------------------------------------------------------


def check_domain_range(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    kb, results = ctx.kb, []
    if change.is_class_change or change.kind in ("usage_note", "mint_property") or not change.path:
        return [_ok("V2", "not applicable")]
    term = kb.term(change.path)
    if term is None:
        return [_ok("V2", "term unknown; see V1")]

    # Domain: the declared domain must admit the target class, unless the base itself already uses the
    # property on this class (then the base has settled the question).
    if term.domain and kb.base.element(change.target_class, change.path) is None:
        fits = any(kb.is_subclass_of(change.target_class, declared) for declared in term.domain)
        if not fits:
            hierarchy_known = bool(kb.vocab.super_terms(change.target_class)) or change.target_class in term.domain
            results.append(_fail(
                "V2",
                f"{kb.curie(change.path)} is declared for {', '.join(kb.curie(d) for d in term.domain)}, "
                f"not for {kb.curie(change.target_class)}.",
                severity="error" if hierarchy_known else "warning",
                problem="domain_mismatch", declared=term.domain,
            ))

    # Range: a class range must be the declared range or narrower; a datatype needs a literal-valued property.
    declared_classes = [value for value in term.range if value not in KNOWN_DATATYPES]
    declared_literal = [value for value in term.range if value in KNOWN_DATATYPES]
    facets = change.facets
    if facets.range_class:
        if term.property_type == "datatype" or (declared_literal and not declared_classes):
            results.append(_fail(
                "V2", f"{kb.curie(change.path)} takes literal values; a class range does not fit.",
                problem="range_kind_mismatch",
            ))
        elif declared_classes and not any(kb.is_subclass_of(facets.range_class, declared) for declared in declared_classes):
            known = bool(kb.vocab.super_terms(facets.range_class))
            results.append(_fail(
                "V2",
                f"The range {kb.curie(facets.range_class)} is not within the declared range "
                f"{', '.join(kb.curie(d) for d in declared_classes)} of {kb.curie(change.path)}.",
                severity="error" if known else "warning", problem="range_mismatch", declared=declared_classes,
            ))
    if facets.range_datatype and (term.property_type == "object" or (declared_classes and not declared_literal)):
        results.append(_fail(
            "V2", f"{kb.curie(change.path)} relates resources; a literal datatype does not fit.",
            problem="range_kind_mismatch",
        ))
    return results or [_ok("V2", "domain and range fit")]


# ---------------------------------------------------------------------------
# V3 - legal refinement of the base
# ---------------------------------------------------------------------------


def check_refinement(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    """Also fills ``FacetJustification.status`` (the engine owns that field)."""
    kb = ctx.kb
    if change.is_class_change or change.kind == "usage_note" or not change.path:
        return [_ok("V3", "not applicable")]
    base_shape = kb.base.shape_facets(change.target_class, change.path)
    new_shape = ShapeFacets.from_facets(change.facets, change.severity)
    comparison = compare_facets(
        base_shape, new_shape, inherit_missing=True, is_subclass=kb.is_subclass_of, compare_severity=False
    )
    deltas = list(comparison.facets)
    obligation_delta = compare_obligation(
        kb.base.obligation(change.target_class, change.path) if base_shape is not None else None,
        change.facets.obligation,
    )
    if obligation_delta is not None:
        deltas.append(obligation_delta)

    status_by_facet = {delta.facet: delta.status for delta in deltas}
    status_by_facet.setdefault("range", status_by_facet.get("range_class") or status_by_facet.get("range_datatype") or "unchanged")
    for justification in change.facet_justifications:
        status = status_by_facet.get(justification.facet)
        if status in ("added", "tightened", "unchanged", "loosened"):
            justification.status = status  # type: ignore[assignment]
        elif status in ("conflict", "incomparable"):
            justification.status = "loosened" if status == "conflict" else "tightened"

    if base_shape is None:
        return [_ok("V3", "the base does not constrain this property on this class: an addition")]

    results = []
    bad = [delta for delta in deltas if delta.status in ("loosened", "conflict")]
    if bad:
        results.append(_fail(
            "V3",
            "Not a legal refinement of the base: " + "; ".join(
                f"{delta.facet} {delta.base_value or 'not set'} -> {delta.new_value or 'not set'} "
                f"({'contradicts the base' if delta.status == 'conflict' else 'loosens the base'}"
                f"{': ' + delta.note if delta.note else ''})"
                for delta in bad
            ),
            problem="illegal_refinement", facets=[delta.facet for delta in bad],
        ))
    for delta in deltas:
        if delta.status == "incomparable":
            results.append(_fail(
                "V3", f"{delta.facet}: {delta.new_value} cannot be shown to narrow the base value {delta.base_value} ({delta.note}).",
                severity="warning", problem="incomparable", facets=[delta.facet],
            ))
    effective = [delta for delta in deltas if delta.status in ("added", "tightened", "incomparable")]
    if not bad and not effective and change.kind == "refine_property":
        results.append(_fail(
            "V3", "The change does not tighten anything: the base already says this.",
            problem="no_effect", facets=[],
        ))
    return results or [_ok("V3", "tightens the base: " + ", ".join(delta.facet for delta in effective))]


# ---------------------------------------------------------------------------
# V4 - reuse before mint
# ---------------------------------------------------------------------------


def check_reuse_before_mint(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    kb = ctx.kb
    if change.kind not in ("mint_property", "mint_class"):
        return [_ok("V4", "not a minted term")]
    results = []
    if change.mint is None or not change.mint.reason_no_reuse.strip():
        results.append(_fail("V4", "A minted term must state why no existing term can be reused.", problem="no_justification"))
    if not change.label.strip() or not change.definition.strip():
        results.append(_fail("V4", "A minted term needs a label and a definition.", problem="undocumented"))

    # An existing term with the same name is the strongest sign that minting is not needed.
    minted_words = set(words_of(local_name(change.path or change.target_class))) or set(words_of(change.label))
    wanted_kind = "class" if change.kind == "mint_class" else "property"
    rejected = {item.iri for item in (change.mint.rejected_candidates if change.mint else [])}
    for hit in kb.vocab.search(change.label or local_name(change.path or change.target_class), kind=wanted_kind, limit=5):
        if kb.is_minted(hit.term.iri):
            continue
        if set(words_of(local_name(hit.term.iri))) == minted_words and hit.term.iri not in rejected:
            results.append(_fail(
                "V4", f"An existing term has this very name: {kb.curie(hit.term.iri)}. Reuse it, or say why it does not fit.",
                problem="same_name_exists", term=hit.term.iri,
            ))
            break
    strong = [
        candidate for atom_id in change.atom_ids for candidate in ctx.candidates.get(atom_id, [])
        if candidate.kind == wanted_kind and candidate.score >= STRONG_CANDIDATE_SCORE and candidate.iri not in rejected
    ]
    if strong:
        results.append(_fail(
            "V4",
            "Close candidates were retrieved but are not addressed: "
            + ", ".join(dict.fromkeys(kb.curie(candidate.iri) for candidate in strong)) + ".",
            severity="warning", problem="unaddressed_candidates",
        ))
    return results or [_ok("V4", "minting is justified")]


# ---------------------------------------------------------------------------
# V5 - internal consistency
# ---------------------------------------------------------------------------


def check_consistency(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    if change.is_class_change or change.kind == "usage_note":
        if change.kind == "usage_note" and not change.usage_note.strip():
            return [_fail("V5", "A usage note without text.", problem="empty_note")]
        return [_ok("V5", "not applicable")]
    facets, results = change.facets, []
    low, high = facets.min_count, facets.max_count
    if low is not None and low < 0 or high is not None and high < 1:
        results.append(_fail("V5", "Cardinalities must be non-negative and the maximum at least 1.", problem="cardinality"))
    if low is not None and high is not None and low > high:
        results.append(_fail("V5", f"The minimum {low} is greater than the maximum {high}.", problem="min_gt_max"))
    if facets.obligation == "mandatory" and not (low and low >= 1):
        results.append(_fail("V5", "A mandatory property needs a minimum cardinality of at least 1.", problem="mandatory_without_min"))
    if facets.obligation in ("recommended", "optional") and low and low >= 1:
        results.append(_fail(
            "V5", f"A minimum of {low} makes the property mandatory, but it is declared {facets.obligation}.",
            problem="min_without_mandatory",
        ))
    if facets.range_class and facets.range_datatype:
        results.append(_fail("V5", "A property cannot have both a class range and a datatype.", problem="two_ranges"))
    if facets.range_datatype and facets.node_kind not in (None, "Literal"):
        results.append(_fail("V5", f"A datatype range needs node kind Literal, not {facets.node_kind}.", problem="node_kind"))
    if facets.range_class and facets.node_kind == "Literal":
        results.append(_fail("V5", "A class range cannot have node kind Literal.", problem="node_kind"))
    if change.kind == "mint_property" and not (facets.range_class or facets.range_datatype):
        results.append(_fail("V5", "The minted property has no range; say what kind of value it takes.",
                             severity="warning", problem="no_range"))
    return results or [_ok("V5", "constraints are consistent")]


# ---------------------------------------------------------------------------
# T1 - trace
# ---------------------------------------------------------------------------


def check_trace(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    results = []
    if not change.covers:
        return [_fail("T1", "The change covers no requirement atom: nothing justifies it.", problem="no_atom")]
    licensed_levels = []
    for link in change.covers:
        atom = ctx.atoms.get(link.atom_id)
        if atom is None:
            results.append(_fail("T1", f"The change cites atom '{link.atom_id}', which does not exist.", problem="unknown_atom"))
            continue
        licensed_levels.append(MODALITY_OBLIGATION[atom.modality])
        if not link.reason.strip():
            results.append(_fail("T1", f"No reason is given for covering atom {atom.id}.", problem="no_reason"))
        quote = _normalise(link.evidence_quote).strip(" .\"'")
        if not quote:
            results.append(_fail("T1", f"No quote from atom {atom.id} supports the change.", problem="quote_not_verbatim"))
        elif quote not in _normalise(atom.statement):
            results.append(_fail(
                "T1", f"The quote is not a verbatim part of atom {atom.id}: \"{link.evidence_quote}\".",
                problem="quote_not_verbatim",
            ))
    if licensed_levels and not change.is_class_change and change.kind != "usage_note":
        licensed = max(licensed_levels, key=lambda level: OBLIGATION_RANK[level])
        if OBLIGATION_RANK[change.facets.obligation] > OBLIGATION_RANK[licensed]:
            results.append(_fail(
                "T1",
                f"The change makes the property {change.facets.obligation}, but the wording of its atoms "
                f"licenses at most {licensed}.",
                problem="obligation_exceeds_modality", licensed=licensed,
            ))
    for justification in change.facet_justifications:
        if not justification.reason.strip():
            results.append(_fail("T1", f"The constraint '{justification.facet}' has no reason.", problem="facet_without_reason"))
    return results or [_ok("T1", "every constraint traces to an atom")]


# ---------------------------------------------------------------------------
# Running the checks
# ---------------------------------------------------------------------------

CHECKS = (check_terms_exist, check_domain_range, check_refinement, check_reuse_before_mint, check_consistency, check_trace)


def verify_change(change: ProfileChange, ctx: VerifyContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in CHECKS:
        results.extend(check(change, ctx))
    return results


def verify_change_set(changes: list[ProfileChange], ctx: VerifyContext) -> dict[str, list[CheckResult]]:
    """Verify every live change, plus the checks that only make sense on the set as a whole."""
    ctx.changes = changes
    live = [change for change in changes if change.decision.status not in ("rejected", "superseded")]
    results = {change.id: verify_change(change, ctx) for change in live}
    by_element: dict[tuple[str, str], list[ProfileChange]] = {}
    for change in live:
        if change.path and change.kind != "usage_note":
            by_element.setdefault((change.target_class, change.path), []).append(change)
    for (target, path), group in by_element.items():
        if len(group) > 1:
            for change in group:
                results[change.id].append(_fail(
                    "V5", f"{len(group)} changes constrain {ctx.kb.curie(path)} on {ctx.kb.curie(target)}; "
                          "there must be one element per class and property.",
                    problem="duplicate_element", change_ids=[other.id for other in group],
                ))
    return results


def verify_assessment(assessment: AtomAssessment, atom: Atom, kb: KnowledgeBase) -> list[CheckResult]:
    """B1: a claim that the base already covers an atom must name base elements that are strong enough."""
    if assessment.disposition != "covered_by_base":
        return []
    if not assessment.covered_by:
        return [_fail("B1", "The atom is said to be covered by the base, but no base element is named.", problem="no_element")]
    licensed = MODALITY_OBLIGATION[atom.modality]
    results = []
    for ref in assessment.covered_by:
        element = kb.base.element(ref.target_class, ref.path) if ref.path else None
        if element is None:
            results.append(_fail(
                "B1", f"The base does not define {kb.curie(ref.path)} on {kb.curie(ref.target_class)}.", problem="not_in_base",
            ))
        elif OBLIGATION_RANK[element.facets.obligation] < OBLIGATION_RANK[licensed]:
            results.append(_fail(
                "B1",
                f"The base makes {kb.curie(ref.path)} only {element.facets.obligation}; the atom's wording asks for {licensed}.",
                problem="base_too_weak", licensed=licensed,
            ))
    return results or [_ok("B1", "the base covers the atom")]


def check_shapes_valid(turtle: str) -> CheckResult:
    """V6: the compiled shapes parse and conform to the SHACL shapes for SHACL."""
    try:
        shapes = Graph().parse(data=turtle, format="turtle")
    except Exception as exc:  # rdflib raises several parser error types
        return _fail("V6", f"The compiled shapes do not parse: {exc}", problem="parse")
    try:
        from pyshacl import validate

        # An empty data graph + meta_shacl validates the SHAPES graph against SHACL-SHACL.
        validate(Graph(), shacl_graph=shapes, meta_shacl=True, advanced=False, inference="none")
    except Exception as exc:  # ShapeLoadError, ConstraintLoadError, ReportableRuntimeError, ...
        return _fail("V6", f"The compiled shapes are not valid SHACL: {str(exc)[:600]}", problem="shacl_shacl")
    return _ok("V6", f"{len(shapes)} triples; valid against the SHACL shapes for SHACL")


def has_errors(results: list[CheckResult]) -> bool:
    return any(not result.passed and result.severity == "error" for result in results)
