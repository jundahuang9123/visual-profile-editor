"""The included change set as a profile: what every compiler reads.

All artefacts (SHACL, LinkML, DSV, documentation, trace matrix, delta) are
compiled deterministically from this one view, so they cannot disagree.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts import ELEMENT_KIND, Atom, ProfileChange, ProfileDelta, ProfileElement, Project
from ..knowledge import KnowledgeBase


@dataclass
class ProfileView:
    project: Project
    kb: KnowledgeBase
    atoms: dict[str, Atom]
    changes: list[ProfileChange] = field(default_factory=list)   # included changes only

    @property
    def property_changes(self) -> list[ProfileChange]:
        return [c for c in self.changes if c.path and not c.is_class_change and c.kind != "usage_note"]

    @property
    def class_changes(self) -> list[ProfileChange]:
        return [c for c in self.changes if c.is_class_change]

    @property
    def notes(self) -> list[ProfileChange]:
        return [c for c in self.changes if c.kind == "usage_note"]

    def target_classes(self) -> list[str]:
        ordered: list[str] = []
        for change in self.class_changes + self.property_changes:
            if change.target_class not in ordered:
                ordered.append(change.target_class)
        return ordered

    def atom_iri(self, atom_id: str) -> str:
        return f"{self.project.profile_namespace.rstrip('#/')}/requirement/{atom_id}"

    def shape_iri(self, target_class: str) -> str:
        return f"{self.project.profile_namespace}{self.kb.curie(target_class).replace(':', '_')}Shape"


def build_view(project: Project, kb: KnowledgeBase, atoms: list[Atom], changes: list[ProfileChange]) -> ProfileView:
    included = [c for c in changes if c.included]
    return ProfileView(project=project, kb=kb, atoms={a.id: a for a in atoms}, changes=included)


def build_delta(view: ProfileView) -> ProfileDelta:
    """The profile as ``ProfileElement``s (the RQ2 scoring contract)."""
    kb, elements = view.kb, []
    for change in view.class_changes:
        elements.append(ProfileElement(
            id=change.id, target_class=change.target_class, kind="class_addition", delta_status="added",
            source="generated", source_atom_ids=change.atom_ids,
        ))
    for change in view.property_changes:
        kind = ELEMENT_KIND[change.kind]
        if kind is None:
            continue
        f = change.facets
        base = kb.base.shape_facets(change.target_class, change.path or "")
        statuses = {j.status for j in change.facet_justifications}
        elements.append(ProfileElement(
            id=change.id, target_class=change.target_class, path=change.path, kind=kind,  # type: ignore[arg-type]
            obligation=f.obligation, min_count=f.min_count, max_count=f.max_count,
            range_class=f.range_class, range_datatype=f.range_datatype, node_kind=f.node_kind,
            controlled_vocabulary=list(f.controlled_vocabulary), severity=change.severity,
            delta_status="added" if base is None else ("loosened" if "loosened" in statuses else "tightened"),
            source="generated", source_atom_ids=change.atom_ids,
        ))
    return ProfileDelta(
        profile_id=view.project.id, base_profile_ids=[view.project.base_profile_id],
        source="generated", elements=elements,
    )
