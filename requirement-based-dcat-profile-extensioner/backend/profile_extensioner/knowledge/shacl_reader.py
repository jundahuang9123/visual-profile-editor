"""Read SHACL shapes into constraints per (target class, property path).

This is the reader behind the base-profile registry and the conformance
checker. It generalises ``scripts/shacl_delta.py`` of the RQ2 work package 0
(same facets, same merge rules): several property shapes on the same
(class, path) are merged (largest minCount, smallest maxCount, strongest
severity, union of sh:class / sh:datatype, intersection of sh:in).

Constructs the reader does not interpret are never dropped silently: they are
listed in ``ShapeIndex.unhandled`` so that a report can say what was not checked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, SH

from ..contracts import Facets, NodeKind, Severity

SEVERITY_RANK: dict[str, int] = {"Info": 0, "Warning": 1, "Violation": 2}

# Each node kind as the set of term types it admits (I = IRI, B = blank node, L = literal).
NODE_KIND_SETS: dict[str, frozenset[str]] = {
    "IRI": frozenset("I"),
    "BlankNode": frozenset("B"),
    "Literal": frozenset("L"),
    "BlankNodeOrIRI": frozenset("BI"),
    "BlankNodeOrLiteral": frozenset("BL"),
    "IRIOrLiteral": frozenset("IL"),
}
ANY_NODE_KIND: frozenset[str] = frozenset("IBL")

UNHANDLED_PREDICATES = {
    SH["or"]: "sh:or",
    SH["and"]: "sh:and",
    SH.xone: "sh:xone",
    SH["not"]: "sh:not",
    SH.node: "sh:node",
    SH.sparql: "sh:sparql",
    SH.qualifiedValueShape: "sh:qualifiedValueShape",
}


def node_kind_for(kinds: frozenset[str]) -> str | None:
    """The SHACL node kind that admits exactly ``kinds`` (None for 'anything' or an empty set)."""
    for name, members in NODE_KIND_SETS.items():
        if members == kinds:
            return name
    return None


@dataclass
class ShapeFacets:
    """Merged constraints of all property shapes on one (target class, path)."""

    min_count: int | None = None
    max_count: int | None = None
    classes: set[str] = field(default_factory=set)
    datatypes: set[str] = field(default_factory=set)
    node_kind: str | None = None
    in_values: frozenset[str] | None = None
    pattern: str | None = None
    severity: str = "Violation"
    names: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    shape_ids: list[str] = field(default_factory=list)

    def copy(self) -> "ShapeFacets":
        return ShapeFacets(
            self.min_count, self.max_count, set(self.classes), set(self.datatypes), self.node_kind,
            self.in_values, self.pattern, self.severity, list(self.names), list(self.descriptions),
            list(self.shape_ids),
        )

    def merge(self, other: "ShapeFacets") -> None:
        if other.min_count is not None:
            self.min_count = max(self.min_count or 0, other.min_count)
        if other.max_count is not None:
            self.max_count = other.max_count if self.max_count is None else min(self.max_count, other.max_count)
        self.classes |= other.classes
        self.datatypes |= other.datatypes
        if other.node_kind:
            if self.node_kind is None:
                self.node_kind = other.node_kind
            else:
                both = NODE_KIND_SETS[self.node_kind] & NODE_KIND_SETS[other.node_kind]
                self.node_kind = node_kind_for(both) or self.node_kind
        if other.in_values is not None:
            self.in_values = other.in_values if self.in_values is None else self.in_values & other.in_values
        if other.pattern and not self.pattern:
            self.pattern = other.pattern
        if SEVERITY_RANK.get(other.severity, 2) > SEVERITY_RANK.get(self.severity, 2):
            self.severity = other.severity
        for value in other.names:
            if value not in self.names:
                self.names.append(value)
        for value in other.descriptions:
            if value not in self.descriptions:
                self.descriptions.append(value)
        for value in other.shape_ids:
            if value not in self.shape_ids:
                self.shape_ids.append(value)

    def to_facets(self, obligation: str = "unknown") -> Facets:
        return Facets(
            obligation=obligation,  # type: ignore[arg-type]
            min_count=self.min_count,
            max_count=self.max_count,
            range_class=sorted(self.classes)[0] if self.classes else None,
            range_datatype=sorted(self.datatypes)[0] if self.datatypes else None,
            node_kind=self.node_kind,  # type: ignore[arg-type]
            controlled_vocabulary=sorted(self.in_values) if self.in_values is not None else [],
            pattern=self.pattern,
        )

    @classmethod
    def from_facets(cls, facets: Facets, severity: Severity | str | None = None) -> "ShapeFacets":
        return cls(
            min_count=facets.min_count,
            max_count=facets.max_count,
            classes={facets.range_class} if facets.range_class else set(),
            datatypes={facets.range_datatype} if facets.range_datatype else set(),
            node_kind=facets.node_kind,
            in_values=frozenset(facets.controlled_vocabulary) if facets.controlled_vocabulary else None,
            pattern=facets.pattern,
            severity=str(severity or "Violation"),
        )


@dataclass
class TargetClass:
    iri: str
    label: str = ""
    description: str = ""
    shape_ids: list[str] = field(default_factory=list)


@dataclass
class ShapeIndex:
    elements: dict[tuple[str, str], ShapeFacets] = field(default_factory=dict)
    classes: dict[str, TargetClass] = field(default_factory=dict)
    unhandled: list[str] = field(default_factory=list)

    def paths_of(self, target_class: str) -> list[str]:
        return sorted(path for (cls, path) in self.elements if cls == target_class)

    def classes_using(self, path: str) -> list[str]:
        return sorted(cls for (cls, used) in self.elements if used == path)


def load_graph(paths: Iterable[str | Path]) -> Graph:
    graph = Graph()
    for path in paths:
        path = Path(path)
        graph.parse(path, format="json-ld" if path.suffix == ".jsonld" else "turtle")
    return graph


def _local(term: object) -> str:
    return str(term).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _int(graph: Graph, node: object, predicate: URIRef) -> int | None:
    value = graph.value(node, predicate)  # type: ignore[arg-type]
    if isinstance(value, Literal):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def value_text(term: object) -> str:
    """Stable text form of an RDF term: the IRI itself, or the quoted literal."""
    return str(term) if isinstance(term, URIRef) else f'"{term}"'


def _texts(graph: Graph, node: object, predicate: URIRef) -> list[str]:
    """Literal values of ``predicate``, English (or untagged) first."""
    values = [value for value in graph.objects(node, predicate) if isinstance(value, Literal)]  # type: ignore[arg-type]
    values.sort(key=lambda value: (0 if (value.language or "en").startswith("en") else 1, str(value)))
    return [str(value) for value in values]


def read_shapes(graph: Graph) -> ShapeIndex:
    """Normalise a shapes graph into facets per (target class, path)."""
    index = ShapeIndex()
    unhandled: list[str] = []
    attached: set[object] = set()

    node_shapes = set(graph.subjects(RDF.type, SH.NodeShape)) | set(graph.subjects(SH.property, None))
    for node_shape in node_shapes:
        targets = [target for target in graph.objects(node_shape, SH.targetClass) if isinstance(target, URIRef)]
        # Implicit class target: a node shape that is itself a class.
        if isinstance(node_shape, URIRef) and (
            (node_shape, RDF.type, RDFS.Class) in graph or (node_shape, RDF.type, OWL.Class) in graph
        ):
            targets.append(node_shape)
        label = value_text(node_shape) if isinstance(node_shape, URIRef) else "blank node shape"
        for predicate, name in UNHANDLED_PREDICATES.items():
            if (node_shape, predicate, None) in graph:
                unhandled.append(f"{name} on node shape {label}")
        for other_target, name in ((SH.targetNode, "sh:targetNode"), (SH.targetSubjectsOf, "sh:targetSubjectsOf"),
                                   (SH.targetObjectsOf, "sh:targetObjectsOf")):
            if (node_shape, other_target, None) in graph:
                unhandled.append(f"{name} on node shape {label}")
        if not targets:
            if (node_shape, SH.property, None) in graph:
                unhandled.append(f"node shape without sh:targetClass: {label}")
            continue

        for target in targets:
            info = index.classes.setdefault(str(target), TargetClass(iri=str(target)))
            names = _texts(graph, node_shape, SH.name) or _texts(graph, node_shape, RDFS.label)
            descriptions = _texts(graph, node_shape, SH.description) or _texts(graph, node_shape, RDFS.comment)
            info.label = info.label or (names[0] if names else "")
            info.description = info.description or (descriptions[0] if descriptions else "")
            if isinstance(node_shape, URIRef) and str(node_shape) not in info.shape_ids:
                info.shape_ids.append(str(node_shape))

        shape_severity = graph.value(node_shape, SH.severity)
        for prop in graph.objects(node_shape, SH.property):
            attached.add(prop)
            path = graph.value(prop, SH.path)
            if not isinstance(path, URIRef):
                unhandled.append(f"non-IRI sh:path in a property shape of {label}")
                continue
            for predicate, name in UNHANDLED_PREDICATES.items():
                if (prop, predicate, None) in graph:
                    unhandled.append(f"{name} on property shape {_local(path)} of {label}")
            facets = ShapeFacets(
                min_count=_int(graph, prop, SH.minCount),
                max_count=_int(graph, prop, SH.maxCount),
                classes={str(value) for value in graph.objects(prop, SH["class"]) if isinstance(value, URIRef)},
                datatypes={str(value) for value in graph.objects(prop, SH.datatype) if isinstance(value, URIRef)},
                names=_texts(graph, prop, SH.name),
                descriptions=_texts(graph, prop, SH.description),
                shape_ids=[str(prop)] if isinstance(prop, URIRef) else [],
            )
            node_kind = graph.value(prop, SH.nodeKind)
            if node_kind is not None and _local(node_kind) in NODE_KIND_SETS:
                facets.node_kind = _local(node_kind)
            in_list = graph.value(prop, SH["in"])
            if in_list is not None:
                facets.in_values = frozenset(value_text(value) for value in Collection(graph, in_list))
            pattern = graph.value(prop, SH.pattern)
            if isinstance(pattern, Literal):
                facets.pattern = str(pattern)
            severity = graph.value(prop, SH.severity) or shape_severity
            if severity is not None and _local(severity) in SEVERITY_RANK:
                facets.severity = _local(severity)
            for target in targets:
                key = (str(target), str(path))
                if key in index.elements:
                    index.elements[key].merge(facets)
                else:
                    index.elements[key] = facets.copy()

    for prop in set(graph.subjects(RDF.type, SH.PropertyShape)) - attached:
        name = value_text(prop) if not isinstance(prop, BNode) else "blank node"
        unhandled.append(f"property shape not attached via sh:property: {name}")
    index.unhandled = sorted(set(unhandled))
    return index


def normalise_node_kind(value: str | None) -> NodeKind | None:
    return value if value in NODE_KIND_SETS else None  # type: ignore[return-value]
