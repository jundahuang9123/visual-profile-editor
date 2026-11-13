"""Deterministic plain-language renderings.

The same sentence is shown to the judging model, to the human reviewer and in
the generated documentation, so that all three read the identical statement
about a change and nobody has to read raw SHACL to review it.
"""
from __future__ import annotations

from ..contracts import BaseElement, Facets, ProfileChange
from ..knowledge import KnowledgeBase


def cardinality(facets: Facets) -> str:
    low = facets.min_count if facets.min_count is not None else 0
    high = "n" if facets.max_count is None else str(facets.max_count)
    return f"{low}..{high}"


def range_text(facets: Facets, kb: KnowledgeBase) -> str:
    if facets.range_class:
        return kb.curie(facets.range_class)
    if facets.range_datatype:
        return kb.curie(facets.range_datatype)
    if facets.node_kind:
        return {"Literal": "a literal", "IRI": "an IRI", "BlankNodeOrIRI": "a resource"}.get(facets.node_kind, facets.node_kind)
    return "any value"


def facets_text(facets: Facets, kb: KnowledgeBase) -> str:
    parts = [facets.obligation if facets.obligation != "unknown" else "obligation not stated",
             cardinality(facets), range_text(facets, kb)]
    if facets.controlled_vocabulary:
        shown = ", ".join(kb.curie(value) for value in facets.controlled_vocabulary[:4])
        more = f" (+{len(facets.controlled_vocabulary) - 4} more)" if len(facets.controlled_vocabulary) > 4 else ""
        parts.append(f"values from {shown}{more}")
    return "; ".join(parts)


def base_element_line(element: BaseElement, kb: KnowledgeBase) -> str:
    definition = f" - {element.definition}" if element.definition else ""
    return f'{kb.curie(element.path)} "{element.label}" [{facets_text(element.facets, kb)}]{definition}'


def verbalise_change(change: ProfileChange, kb: KnowledgeBase) -> str:
    """One or two sentences saying exactly what a change does to the profile."""
    target = kb.curie(change.target_class)
    if change.kind == "mint_class":
        parent = f", a kind of {kb.curie(change.super_class)}" if change.super_class else ""
        return f'New class {target} "{change.label}"{parent}: {change.definition or "no definition given"}'
    if change.kind == "reuse_class":
        return f"The existing class {target} is brought into the profile."
    path = kb.curie(change.path) if change.path else "?"
    if change.kind == "usage_note":
        return f"Usage note on {path} of {target}: {change.usage_note}"
    constraints = facets_text(change.facets, kb)
    if change.kind == "refine_property":
        def show(value: str | None) -> str:
            return ", ".join(kb.curie(part.strip()) for part in value.split(",")) if value else "not set"

        changed = [
            f"{item.facet} {show(item.base_value)} -> {show(item.new_value)}"
            for item in change.facet_justifications
            if (item.status not in ("unchanged", None) or item.base_value != item.new_value)
            and not (item.facet == "min_count" and item.new_value == "0" and item.base_value in (None, "0"))
        ]
        detail = "; ".join(changed) if changed else constraints
        return f"On {target}, the base property {path} is tightened: {detail}. Result: {constraints}."
    if change.kind == "mint_property":
        return (
            f'New property {path} "{change.label}" on {target} [{constraints}]: '
            f'{change.definition or "no definition given"}'
        )
    return f"The existing property {path} is added to {target} [{constraints}]."
