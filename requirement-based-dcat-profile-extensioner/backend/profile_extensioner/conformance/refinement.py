"""Is a set of constraints a legal refinement of the base's constraints?

One function, used in three places: the verifier (check V3 on a single proposed
change), the delta computation (ProfileElement.delta_status) and the final
conformance report.

Per facet the result is one of

* ``added``         the base does not constrain this facet; the profile now does
* ``tightened``     stricter than the base
* ``unchanged``     same as the base (or not mentioned, when missing means "inherit")
* ``loosened``      weaker than the base: never legal for a profile of the base
* ``conflict``      cannot hold together with the base (for example min 2 against the base's max 1,
                    or a different datatype): data could not satisfy both
* ``incomparable``  a different value whose relation to the base's value is unknown
                    (for example a range class that is not known to be a subclass)

Two reading modes:

* ``inherit_missing=True``  for a CHANGE: a facet the change does not mention keeps the base value.
* ``inherit_missing=False`` for two complete shape sets (the classic delta): a facet that the
  profile no longer states has been dropped, which is a loosening.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from ..knowledge.shacl_reader import ANY_NODE_KIND, NODE_KIND_SETS, SEVERITY_RANK, ShapeFacets

FacetStatus = Literal["added", "tightened", "unchanged", "loosened", "conflict", "incomparable"]
SubClassTest = Callable[[str, str], bool]   # (sub, super) -> True if sub is the same as or a subclass of super


@dataclass
class FacetDelta:
    facet: str            # min_count, max_count, range_class, range_datatype, node_kind, controlled_vocabulary, severity
    base_value: str | None
    new_value: str | None
    status: FacetStatus
    note: str = ""


@dataclass
class Comparison:
    status: Literal["added", "tightened", "unchanged", "loosened"]
    facets: list[FacetDelta]

    @property
    def loosened(self) -> list[FacetDelta]:
        return [delta for delta in self.facets if delta.status == "loosened"]

    @property
    def conflicts(self) -> list[FacetDelta]:
        return [delta for delta in self.facets if delta.status == "conflict"]

    @property
    def incomparable(self) -> list[FacetDelta]:
        return [delta for delta in self.facets if delta.status == "incomparable"]

    @property
    def is_legal(self) -> bool:
        return not self.loosened and not self.conflicts

    def notes(self) -> list[str]:
        """Compact notes in the style of the WP0 delta tool (``tightened: minCount, in``)."""
        notes = []
        for status in ("loosened", "conflict", "tightened", "added", "incomparable"):
            names = [delta.facet for delta in self.facets if delta.status == status]
            if names:
                notes.append(f"{status}: {', '.join(names)}")
        return notes


def _show(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (set, frozenset, list, tuple)):
        return ", ".join(sorted(str(item) for item in value)) if value else None
    return str(value)


def compare_facets(
    base: ShapeFacets | None,
    new: ShapeFacets,
    *,
    inherit_missing: bool = True,
    is_subclass: SubClassTest | None = None,
    compare_severity: bool = True,
) -> Comparison:
    """Classify ``new`` against ``base`` facet by facet."""
    if base is None:
        added = [
            FacetDelta(name, None, _show(value), "added")
            for name, value in (
                ("min_count", new.min_count), ("max_count", new.max_count), ("range_class", new.classes),
                ("range_datatype", new.datatypes), ("node_kind", new.node_kind),
                ("controlled_vocabulary", new.in_values),
            )
            if _show(value) is not None
        ]
        return Comparison("added", added)

    deltas: list[FacetDelta] = []

    def add(facet: str, base_value: object, new_value: object, status: FacetStatus, note: str = "") -> None:
        deltas.append(FacetDelta(facet, _show(base_value), _show(new_value), status, note))

    # -- cardinality ---------------------------------------------------------
    base_min, new_min = base.min_count or 0, new.min_count
    if new_min is None:
        if not inherit_missing and base_min > 0:
            add("min_count", base_min, None, "loosened", "the minimum cardinality of the base was dropped")
    elif new_min > base_min:
        if base.max_count is not None and new_min > base.max_count:
            add("min_count", base_min, new_min, "conflict", f"minimum {new_min} exceeds the base maximum {base.max_count}")
        else:
            add("min_count", base_min, new_min, "tightened")
    elif new_min < base_min:
        add("min_count", base_min, new_min, "loosened", f"the base requires at least {base_min}")

    base_max, new_max = base.max_count, new.max_count
    if new_max is None:
        if not inherit_missing and base_max is not None:
            add("max_count", base_max, None, "loosened", "the maximum cardinality of the base was dropped")
    elif base_max is None:
        if new_max < base_min:
            add("max_count", None, new_max, "conflict", f"maximum {new_max} is below the base minimum {base_min}")
        else:
            add("max_count", None, new_max, "added")
    elif new_max < base_max:
        if new_max < base_min:
            add("max_count", base_max, new_max, "conflict", f"maximum {new_max} is below the base minimum {base_min}")
        else:
            add("max_count", base_max, new_max, "tightened")
    elif new_max > base_max:
        add("max_count", base_max, new_max, "loosened", f"the base allows at most {base_max}")

    # -- range: class --------------------------------------------------------
    if new.classes != base.classes:
        if not new.classes:
            if not inherit_missing:
                add("range_class", base.classes, None, "loosened", "the class constraint of the base was dropped")
        elif not base.classes:
            add("range_class", None, new.classes, "added")
        elif new.classes > base.classes:
            add("range_class", base.classes, new.classes, "tightened", "further class constraint in addition to the base's")
        elif is_subclass is not None and all(any(is_subclass(n, b) for b in base.classes) for n in new.classes):
            add("range_class", base.classes, new.classes, "tightened", "narrowed to a subclass of the base range")
        elif is_subclass is not None and all(any(is_subclass(b, n) for n in new.classes) for b in base.classes):
            add("range_class", base.classes, new.classes, "loosened", "widened to a superclass of the base range")
        else:
            add(
                "range_class", base.classes, new.classes, "incomparable",
                "not known to be a subclass of the base range; values would have to satisfy both",
            )

    # -- range: datatype -----------------------------------------------------
    if new.datatypes != base.datatypes:
        if not new.datatypes:
            if not inherit_missing:
                add("range_datatype", base.datatypes, None, "loosened", "the datatype constraint of the base was dropped")
        elif not base.datatypes:
            add("range_datatype", None, new.datatypes, "added")
        else:
            add("range_datatype", base.datatypes, new.datatypes, "conflict", "a literal cannot have two different datatypes")

    # -- node kind -----------------------------------------------------------
    base_kinds = NODE_KIND_SETS.get(base.node_kind or "", ANY_NODE_KIND)
    if new.node_kind is None:
        if not inherit_missing and base.node_kind is not None:
            add("node_kind", base.node_kind, None, "loosened", "the node kind constraint of the base was dropped")
    else:
        new_kinds = NODE_KIND_SETS.get(new.node_kind, ANY_NODE_KIND)
        if new_kinds != base_kinds:
            if not (new_kinds & base_kinds):
                add("node_kind", base.node_kind, new.node_kind, "conflict", "no value can have both node kinds")
            elif new_kinds < base_kinds:
                add("node_kind", base.node_kind, new.node_kind, "added" if base.node_kind is None else "tightened")
            elif new_kinds > base_kinds:
                add("node_kind", base.node_kind, new.node_kind, "loosened", "admits values the base excludes")
            else:
                add("node_kind", base.node_kind, new.node_kind, "incomparable", "only the overlap of both node kinds stays valid")

    # -- controlled vocabulary (sh:in) --------------------------------------
    if new.in_values != base.in_values:
        if new.in_values is None:
            if not inherit_missing:
                add("controlled_vocabulary", base.in_values, None, "loosened", "the value list of the base was dropped")
        elif base.in_values is None:
            add("controlled_vocabulary", None, new.in_values, "added")
        elif new.in_values <= base.in_values:
            add("controlled_vocabulary", base.in_values, new.in_values, "tightened")
        elif not (new.in_values & base.in_values):
            add("controlled_vocabulary", base.in_values, new.in_values, "conflict", "no value is allowed by both lists")
        else:
            add("controlled_vocabulary", base.in_values, new.in_values, "loosened", "allows values the base does not list")

    # -- severity ------------------------------------------------------------
    if compare_severity and new.severity != base.severity:
        base_rank, new_rank = SEVERITY_RANK.get(base.severity, 2), SEVERITY_RANK.get(new.severity, 2)
        if new_rank > base_rank:
            add("severity", base.severity, new.severity, "tightened")
        elif new_rank < base_rank:
            add("severity", base.severity, new.severity, "loosened", "a weaker severity than the base")

    statuses = {delta.status for delta in deltas}
    if statuses & {"loosened", "conflict"}:
        overall: Literal["added", "tightened", "unchanged", "loosened"] = "loosened"
    elif statuses & {"tightened", "added", "incomparable"}:
        overall = "tightened"
    else:
        overall = "unchanged"
    return Comparison(overall, deltas)


OBLIGATION_ORDER = {"unknown": 0, "optional": 1, "recommended": 2, "mandatory": 3}


def compare_obligation(base: str | None, new: str | None) -> FacetDelta | None:
    """Obligation levels are documentation-level constraints: mandatory > recommended > optional."""
    if not new or new == "unknown":
        return None
    if not base or base == "unknown":
        return FacetDelta("obligation", None, new, "added")
    if OBLIGATION_ORDER[new] > OBLIGATION_ORDER[base]:
        return FacetDelta("obligation", base, new, "tightened")
    if OBLIGATION_ORDER[new] < OBLIGATION_ORDER[base]:
        return FacetDelta("obligation", base, new, "loosened", f"the base makes this {base}")
    return FacetDelta("obligation", base, new, "unchanged")
