"""Compile the extension's SHACL shapes.

The output holds ONLY what the extension adds or tightens (one node shape per
target class) and imports the base shapes, so the full profile is
base + extension. Obligation follows the DCAT-AP convention: mandatory ->
``sh:minCount 1`` (Violation); recommended -> ``sh:minCount 1`` with severity
Warning; optional -> no minimum. Every property shape names the requirement
atoms it was derived from (``prov:wasDerivedFrom``) and why (``sh:description``).
"""
from __future__ import annotations

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, PROV, RDF, RDFS, SH, SKOS, XSD

from .model import ProfileView

SEVERITY = {"Violation": SH.Violation, "Warning": SH.Warning, "Info": SH.Info}


def compile_shacl_graph(view: ProfileView, *, include_trace: bool = True) -> Graph:
    kb, project = view.kb, view.project
    graph = Graph()
    for prefix, namespace in kb.prefixes.as_dict().items():
        graph.bind(prefix, namespace)
    graph.bind(project.profile_prefix, project.profile_namespace)
    profile = URIRef(project.profile_namespace.rstrip("#/") + "/shapes")
    graph.add((profile, RDF.type, OWL.Ontology))
    graph.add((profile, RDFS.label, Literal(f"{project.profile_title or project.name} - SHACL shapes", lang="en")))
    graph.add((profile, DCTERMS.description, Literal(
        f"Constraints this extension adds to or tightens on {kb.base.info.title}. "
        "Validate data against these shapes together with the base shapes.", lang="en")))
    if kb.base.info.homepage:
        graph.add((profile, OWL.imports, URIRef(kb.base.info.homepage)))

    for target in view.target_classes():
        shape = URIRef(view.shape_iri(target))
        graph.add((shape, RDF.type, SH.NodeShape))
        graph.add((shape, SH.targetClass, URIRef(target)))
        graph.add((shape, SH.name, Literal(kb.base.class_label(target) if kb.base.has_class(target)
                                         else kb.curie(target), lang="en")))
        for change in view.class_changes:
            if change.target_class == target and include_trace:
                for link in change.covers:
                    graph.add((shape, PROV.wasDerivedFrom, URIRef(view.atom_iri(link.atom_id))))

        for change in [c for c in view.property_changes if c.target_class == target]:
            f = change.facets
            prop = URIRef(f"{shape}/{kb.curie(change.path).replace(':', '_')}")
            graph.add((shape, SH.property, prop))
            graph.add((prop, RDF.type, SH.PropertyShape))
            graph.add((prop, SH.path, URIRef(change.path)))
            graph.add((prop, SH.name, Literal(change.label or kb.curie(change.path), lang="en")))
            if f.obligation in ("mandatory", "recommended"):
                graph.add((prop, SH.minCount, Literal(max(1, f.min_count or 1))))
            elif f.min_count:
                graph.add((prop, SH.minCount, Literal(f.min_count)))
            if f.max_count is not None:
                graph.add((prop, SH.maxCount, Literal(f.max_count)))
            if f.range_class:
                graph.add((prop, SH["class"], URIRef(f.range_class)))
            if f.range_datatype:
                graph.add((prop, SH.datatype, URIRef(f.range_datatype)))
            if f.node_kind:
                graph.add((prop, SH.nodeKind, SH[f.node_kind]))
            if f.controlled_vocabulary:
                head = BNode()
                Collection(graph, head, [URIRef(v) for v in f.controlled_vocabulary])
                graph.add((prop, SH["in"], head))
            if f.pattern:
                graph.add((prop, SH.pattern, Literal(f.pattern)))
            severity = "Warning" if f.obligation == "recommended" else ("Info" if f.obligation == "optional" else "Violation")
            graph.add((prop, SH.severity, SEVERITY[severity]))
            if include_trace:
                reason = "; ".join(f"{link.atom_id}: {link.reason}" for link in change.covers)
                graph.add((prop, SH.description, Literal(f"{change.kind.replace('_', ' ')}. {reason}", lang="en")))
                for link in change.covers:
                    graph.add((prop, PROV.wasDerivedFrom, URIRef(view.atom_iri(link.atom_id))))
            if change.usage_note:
                graph.add((prop, SKOS.scopeNote, Literal(change.usage_note, lang="en")))
    return graph


def compile_shacl(view: ProfileView) -> str:
    return compile_shacl_graph(view).serialize(format="turtle")


def compile_vocabulary(view: ProfileView) -> str:
    """RDFS/OWL definitions of the terms the extension mints (empty graph when it mints nothing)."""
    kb, project = view.kb, view.project
    graph = Graph()
    graph.bind(project.profile_prefix, project.profile_namespace)
    for prefix in ("rdfs", "owl", "skos", "prov", "dcat", "dcterms", "xsd"):
        graph.bind(prefix, kb.prefixes.namespace(prefix))
    ontology = URIRef(project.profile_namespace.rstrip("#/"))
    graph.add((ontology, RDF.type, OWL.Ontology))
    graph.add((ontology, RDFS.label, Literal(f"{project.profile_title or project.name} - vocabulary", lang="en")))
    for change in view.changes:
        if change.kind == "mint_class":
            term = URIRef(change.target_class)
            graph.add((term, RDF.type, OWL.Class))
            if change.super_class:
                graph.add((term, RDFS.subClassOf, URIRef(change.super_class)))
        elif change.kind == "mint_property" and change.path:
            term = URIRef(change.path)
            literal = bool(change.facets.range_datatype) or change.facets.node_kind == "Literal"
            graph.add((term, RDF.type, OWL.DatatypeProperty if literal else OWL.ObjectProperty))
            graph.add((term, RDFS.domain, URIRef(change.target_class)))
            rng = change.facets.range_datatype or change.facets.range_class
            if rng:
                graph.add((term, RDFS.range, URIRef(rng)))
            if change.sub_property_of:
                graph.add((term, RDFS.subPropertyOf, URIRef(change.sub_property_of)))
        else:
            continue
        graph.add((term, RDFS.label, Literal(change.label, lang="en")))
        if change.definition:
            graph.add((term, RDFS.comment, Literal(change.definition, lang="en")))
            graph.add((term, SKOS.definition, Literal(change.definition, lang="en")))
        if change.mint:
            graph.add((term, SKOS.editorialNote, Literal(f"Minted because: {change.mint.reason_no_reuse}", lang="en")))
        for link in change.covers:
            graph.add((term, PROV.wasDerivedFrom, URIRef(view.atom_iri(link.atom_id))))
    return graph.serialize(format="turtle")


_ = (Namespace, XSD)  # re-exported names used by other compilers
