"""Compile LinkML (for the Visual Profile Editor) and DSV (for Dataspecer).

LinkML follows the editor's conventions: global slots carry the term's identity,
per-class ``slot_usage`` carries the profile's obligation and cardinality, and
annotations carry ``term_kind`` (base / profile / extension) plus the trace.

DSV follows the statements Dataspecer's own writer emits
(packages/data-specification-vocabulary/src/semantic-model/dsv-to-rdf.ts):
class profiles and property profiles with domain, range, cardinality and
requirement level. Base terms are profiled through ``dsv:class`` /
``dsv:property`` (the vocabulary term), because no DSV of the base is assumed.
"""
from __future__ import annotations

from typing import Any

import yaml
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF, RDFS, SKOS

from ..iri import local_name, to_local_name
from .model import ProfileView

DSV = Namespace("https://w3id.org/dsv#")
CARD = Namespace("https://w3id.org/dsv/cardinality#")
REQ = Namespace("https://w3id.org/dsv/requirement-level#")
ROLE = Namespace("https://w3id.org/dsv/class-role#")
PROF = Namespace("http://www.w3.org/ns/dx/prof/")


def _class_name(view: ProfileView, iri: str) -> str:
    curie = view.kb.curie(iri)
    prefix, _, local = curie.partition(":")
    return to_local_name(f"{prefix} {local}", upper_first=True) if local else to_local_name(local_name(iri), upper_first=True)


def compile_linkml(view: ProfileView) -> str:
    kb, project = view.kb, view.project
    classes: dict[str, Any] = {}
    slots: dict[str, Any] = {}

    def trace(change) -> dict[str, Any]:
        return {
            "covers_requirements": {"value": ", ".join(change.atom_ids)},
            "rationale": {"value": "; ".join(f"{l.atom_id}: {l.reason}" for l in change.covers)[:600]},
            "generated_from_change": {"value": change.id},
        }

    for target in view.target_classes():
        name = _class_name(view, target)
        minted = kb.is_minted(target)
        entry: dict[str, Any] = {
            "class_uri": kb.curie(target),
            "title": kb.base.class_label(target) if kb.base.has_class(target) else name,
            "annotations": {"term_kind": {"value": "extension" if minted else "profile"},
                            "profile_of": {"value": kb.curie(target)}},
            "slots": [],
            "slot_usage": {},
        }
        for change in view.class_changes:
            if change.target_class == target:
                entry["description"] = change.definition or None
                if change.super_class:
                    entry["is_a"] = _class_name(view, change.super_class)
                entry["annotations"].update(trace(change))
        classes[name] = {key: value for key, value in entry.items() if value is not None}

    for change in view.property_changes:
        slot = to_local_name(kb.curie(change.path).replace(":", " "))
        f = change.facets
        if slot not in slots:
            term = kb.term(change.path)
            slots[slot] = {
                "slot_uri": kb.curie(change.path),
                "title": change.label or (term.label if term else slot),
                "range": (kb.curie(f.range_class) if f.range_class else kb.curie(f.range_datatype) if f.range_datatype else "string"),
                "annotations": {"term_kind": {"value": "extension" if change.kind == "mint_property" else "base"}},
            }
            if change.definition:
                slots[slot]["description"] = change.definition
        cls = classes[_class_name(view, change.target_class)]
        cls["slots"].append(slot)
        usage: dict[str, Any] = {
            "required": f.obligation == "mandatory" or None,
            "multivalued": (f.max_count is None or f.max_count > 1) or None,
            "minimum_cardinality": f.min_count,
            "maximum_cardinality": f.max_count,
            "annotations": {
                "requirement_level": {"value": f.obligation},
                "change_kind": {"value": change.kind},
                **trace(change),
            },
        }
        cls["slot_usage"][slot] = {key: value for key, value in usage.items() if value is not None}

    schema = {
        "id": project.profile_namespace.rstrip("#/"),
        "name": to_local_name(project.profile_title or project.name),
        "title": project.profile_title or project.name,
        "description": f"Extension of {kb.base.info.title} generated from requirement atoms.",
        "prefixes": {"linkml": "https://w3id.org/linkml/", project.profile_prefix: project.profile_namespace,
                     **{p: kb.prefixes.namespace(p) for p in ("dcat", "dcterms", "foaf", "skos", "prov", "xsd")}},
        "default_prefix": project.profile_prefix,
        "default_range": "string",
        "imports": ["linkml:types"],
        "annotations": {"profile_of": {"value": kb.base.info.id}},
        "classes": classes,
        "slots": slots,
    }
    return yaml.safe_dump(schema, sort_keys=False, allow_unicode=True)


def _cardinality(low: int | None, high: int | None) -> URIRef:
    low_text = "1" if (low or 0) >= 1 else "0"
    high_text = "1" if high == 1 else "n"
    return CARD[f"{low_text}{high_text}"]


def compile_dsv(view: ProfileView) -> str:
    kb, project = view.kb, view.project
    ns = Namespace(project.profile_namespace)
    graph = Graph()
    for prefix, namespace in (("dsv", DSV), ("cardinality", CARD), ("requirement", REQ), ("role", ROLE),
                              ("prof", PROF), ("skos", SKOS), ("dct", DCTERMS), ("prov", PROV)):
        graph.bind(prefix, namespace)
    graph.bind(project.profile_prefix, project.profile_namespace)
    profile = URIRef(project.profile_namespace)
    graph.add((profile, RDF.type, PROF.Profile))
    graph.add((profile, RDF.type, DSV.ApplicationProfile))
    base_dsv = kb.base.dsv_application_profile()
    graph.add((profile, PROF.isProfileOf, URIRef(base_dsv or kb.base.info.homepage or kb.base.info.id)))

    class_profiles: dict[str, URIRef] = {}

    def class_profile(iri: str, role: str) -> URIRef:
        if iri in class_profiles:
            return class_profiles[iri]
        node = ns[f"{_class_name(view, iri)}Profile"]
        class_profiles[iri] = node
        graph.add((node, DCTERMS.isPartOf, profile))
        graph.add((node, RDF.type, DSV.TermProfile))
        graph.add((node, RDF.type, DSV.ClassProfile))
        base_profile = kb.base.dsv_class_profile(iri)
        if base_profile:
            # A profile of the base's class profile, as Dataspecer models extensions (e.g. DCAT-AP HVD).
            graph.add((node, DSV.profileOf, URIRef(base_profile)))
        else:
            graph.add((node, DSV["class"], URIRef(iri)))
        graph.add((node, DSV.classRole, ROLE[role]))
        label = kb.base.class_label(iri) if kb.base.has_class(iri) else local_name(iri)
        graph.add((node, SKOS.prefLabel, Literal(label, lang="en")))
        return node

    for target in view.target_classes():
        class_profile(target, "main")
    for change in view.class_changes:
        node = class_profile(change.target_class, "main")
        if change.definition:
            graph.add((node, SKOS.definition, Literal(change.definition, lang="en")))
        for link in change.covers:
            graph.add((node, PROV.wasDerivedFrom, URIRef(view.atom_iri(link.atom_id))))

    for change in view.property_changes:
        f = change.facets
        domain = class_profile(change.target_class, "main")
        node = ns[f"{_class_name(view, change.target_class)}.{local_name(change.path)}"]
        graph.add((node, DCTERMS.isPartOf, profile))
        graph.add((node, RDF.type, DSV.TermProfile))
        base_property = kb.base.dsv_property_profile(change.target_class, change.path)
        if base_property:
            graph.add((node, DSV.profileOf, URIRef(base_property)))
        else:
            graph.add((node, DSV.property, URIRef(change.path)))
        graph.add((node, DSV.domain, domain))
        graph.add((node, DSV.cardinality, _cardinality(f.min_count, f.max_count)))
        if f.obligation in ("mandatory", "recommended", "optional"):
            graph.add((node, DSV.requirementLevel, REQ[f.obligation]))
        graph.add((node, SKOS.prefLabel, Literal(change.label or local_name(change.path), lang="en")))
        if change.definition:
            graph.add((node, SKOS.definition, Literal(change.definition, lang="en")))
        if change.usage_note:
            graph.add((node, SKOS.scopeNote, Literal(change.usage_note, lang="en")))
        if f.range_datatype or f.node_kind == "Literal":
            graph.add((node, RDF.type, DSV.DatatypePropertyProfile))
            if f.range_datatype:
                graph.add((node, DSV.datatypePropertyRange, URIRef(f.range_datatype)))
        else:
            graph.add((node, RDF.type, DSV.ObjectPropertyProfile))
            if f.range_class:
                graph.add((node, DSV.objectPropertyRange, class_profile(f.range_class, "supportive")))
        for link in change.covers:
            graph.add((node, PROV.wasDerivedFrom, URIRef(view.atom_iri(link.atom_id))))
    _ = (BNode, RDFS)
    return graph.serialize(format="turtle")
