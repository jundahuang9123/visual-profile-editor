"""Stage ``consolidate``: one element per (class, property), duplicates merged, conflicts surfaced.

Several atoms often ask for the same element. Their changes are folded into one
change that covers all of them; the strongest licensed constraint wins and every
reason is kept. Two changes that cannot be merged (for example different ranges
for the same property) become a ``Conflict`` for the human.
"""
from __future__ import annotations

from ..contracts import OBLIGATION_RANK, Conflict, Decision, FacetJustification, ProfileChange, stable_id


def _key(change: ProfileChange) -> tuple[str, str, str] | None:
    if change.kind == "usage_note":
        return None
    if change.is_class_change:
        return ("class", change.target_class, "")
    return ("property", change.target_class, change.path or "")


def _range(change: ProfileChange) -> str | None:
    return change.facets.range_class or change.facets.range_datatype


def consolidate(changes: list[ProfileChange]) -> tuple[list[ProfileChange], list[Conflict]]:
    """Returns the full list (merged-away changes are marked ``superseded``) and the open conflicts."""
    live = [c for c in changes if c.decision.status not in ("rejected", "superseded")]
    groups: dict[tuple[str, str, str], list[ProfileChange]] = {}
    for change in live:
        key = _key(change)
        if key is not None:
            groups.setdefault(key, []).append(change)

    conflicts: list[Conflict] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        ranges = {_range(c) for c in group if _range(c)}
        if len(ranges) > 1:
            conflicts.append(Conflict(
                id=stable_id("conflict", *key),
                change_ids=[c.id for c in group],
                atom_ids=sorted({a for c in group for a in c.atom_ids}),
                description=f"{len(group)} changes give different ranges for the same element: {', '.join(sorted(ranges))}.",
            ))
            continue
        # Keep the change a human decided on, else the strongest, else the first.
        group.sort(key=lambda c: (
            c.decision.status != "accepted",
            -OBLIGATION_RANK[c.facets.obligation],
            -c.confidence,
        ))
        keeper, others = group[0], group[1:]
        for other in others:
            for link in other.covers:
                if link.atom_id not in keeper.atom_ids:
                    keeper.covers.append(link)
            keeper_facets = {j.facet for j in keeper.facet_justifications}
            for justification in other.facet_justifications:
                if justification.facet in keeper_facets:
                    for mine in keeper.facet_justifications:
                        if mine.facet == justification.facet:
                            mine.atom_ids = sorted(set(mine.atom_ids) | set(justification.atom_ids))
                else:
                    keeper.facet_justifications.append(FacetJustification(**justification.model_dump()))
            f, o = keeper.facets, other.facets
            if OBLIGATION_RANK[o.obligation] > OBLIGATION_RANK[f.obligation]:
                f.obligation = o.obligation
                keeper.severity = other.severity
            if o.min_count is not None and (f.min_count is None or o.min_count > f.min_count):
                f.min_count = o.min_count
            if o.max_count is not None and (f.max_count is None or o.max_count < f.max_count):
                f.max_count = o.max_count
            if not _range(keeper) and _range(other):
                f.range_class, f.range_datatype = o.range_class, o.range_datatype
            keeper.merged_from.append(other.id)
            keeper.engine_notes.append(f"merged {other.id} (same element, atoms {', '.join(other.atom_ids)})")
            other.decision = Decision(status="superseded", decided_by="rule:consolidate",
                                      note=f"merged into {keeper.id}")
    return changes, conflicts
