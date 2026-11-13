"""The base profile an extension is built on.

A base profile is a directory under ``data/base-profiles/<id>/``:

    profile.yaml      identity, source and licence, which shape files to read, plain-word subjects
    shacl/*.ttl       the OFFICIAL shapes of the profile, unmodified
    obligations.yaml  optional: mandatory / recommended / optional per (class, property), taken
                      from the specification text (SHACL carries only the mandatory ones)

The constraints come from the official shapes, so "the base says X" always
means "the published shapes say X".
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, URIRef

from ..contracts import BaseClass, BaseElement, BaseProfileInfo, Term
from ..iri import Prefixes, local_name, words_of
from .shacl_reader import ShapeFacets, ShapeIndex, load_graph, read_shapes

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Plain words an atom may use for its subject -> local name of the class. Profile-specific
# words can be added in profile.yaml under ``subjects``.
DEFAULT_SUBJECTS: dict[str, str] = {
    "dataset": "dcat:Dataset",
    "data set": "dcat:Dataset",
    "distribution": "dcat:Distribution",
    "file": "dcat:Distribution",
    "catalogue": "dcat:Catalog",
    "catalog": "dcat:Catalog",
    "data catalogue": "dcat:Catalog",
    "data catalog": "dcat:Catalog",
    "data service": "dcat:DataService",
    "service": "dcat:DataService",
    "catalogue record": "dcat:CatalogRecord",
    "catalog record": "dcat:CatalogRecord",
    "record": "dcat:CatalogRecord",
    "dataset series": "dcat:DatasetSeries",
    "series": "dcat:DatasetSeries",
    "agent": "foaf:Agent",
    "publisher": "foaf:Agent",
    "organisation": "foaf:Agent",
    "organization": "foaf:Agent",
}


class BaseProfile:
    def __init__(
        self,
        info: BaseProfileInfo,
        index: ShapeIndex,
        shapes: Graph,
        *,
        obligations: dict[tuple[str, str], str] | None = None,
        class_obligations: dict[str, str] | None = None,
        class_labels: dict[str, str] | None = None,
        subjects: dict[str, str] | None = None,
        main_classes: list[str] | None = None,
        prefixes: Prefixes | None = None,
    ) -> None:
        self.info = info
        self.index = index
        self._shapes = shapes
        self._obligations = obligations or {}
        self._class_obligations = class_obligations or {}
        self._class_labels = class_labels or {}
        self._subjects = {key.lower(): value for key, value in (subjects or {}).items()}
        self.main_classes = main_classes or []
        self.prefixes = prefixes or Prefixes()
        self.info.class_count = len(index.classes)
        self.info.element_count = len(index.elements)

    # -- loading ------------------------------------------------------------

    @classmethod
    def load(cls, base_profile_id: str, data_dir: Path | None = None) -> "BaseProfile":
        root = (data_dir or DATA_DIR) / "base-profiles" / base_profile_id
        config_path = root / "profile.yaml"
        if not config_path.exists():
            raise KeyError(f"unknown base profile: {base_profile_id}")
        config: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        prefixes = Prefixes(config.get("prefixes") or {})
        shape_files = [root / name for name in (config.get("shapes") or {}).get("constraints", [])]
        shapes = load_graph(shape_files)
        if config.get("implicit_class_targets"):
            # SHACL implicit class targets need the shape IRI to be an rdfs:Class; the 1.1 files omit that triple.
            # Added in memory only: the vendored files stay byte-identical to the official ones.
            from rdflib.namespace import RDF, RDFS, SH

            for shape in set(shapes.subjects(RDF.type, SH.NodeShape)):
                if isinstance(shape, URIRef) and (shape, SH.property, None) in shapes and (shape, SH.targetClass, None) not in shapes:
                    shapes.add((shape, RDF.type, RDFS.Class))
        index = read_shapes(shapes)

        obligations: dict[tuple[str, str], str] = {}
        class_obligations: dict[str, str] = {}
        class_labels: dict[str, str] = {}
        obligations_file = root / str(config.get("obligations") or "obligations.yaml")
        if obligations_file.exists():
            data = yaml.safe_load(obligations_file.read_text(encoding="utf-8")) or {}
            for class_curie, entry in (data.get("classes") or {}).items():
                class_iri = prefixes.expand(class_curie) or class_curie
                if entry.get("label"):
                    class_labels[class_iri] = entry["label"]
                if entry.get("obligation"):
                    class_obligations[class_iri] = entry["obligation"]
                for path_curie, level in (entry.get("properties") or {}).items():
                    obligations[(class_iri, prefixes.expand(path_curie) or path_curie)] = level

        subjects = dict(DEFAULT_SUBJECTS)
        subjects.update(config.get("subjects") or {})
        dsv_index: dict = {}
        if config.get("dsv_index") and (root / config["dsv_index"]).exists():
            import json

            dsv_index = json.loads((root / config["dsv_index"]).read_text(encoding="utf-8"))
        info = BaseProfileInfo(
            id=str(config.get("id") or base_profile_id),
            title=str(config.get("title") or base_profile_id),
            version=str(config.get("version") or ""),
            description=str(config.get("description") or ""),
            homepage=str(config.get("homepage") or ""),
            licence=str(config.get("licence") or ""),
            shape_files=[str(path.relative_to(root)) for path in shape_files],
        )
        loaded = cls(
            info, index, shapes,
            obligations=obligations,
            class_obligations=class_obligations,
            class_labels=class_labels,
            subjects={word: prefixes.expand(curie) or curie for word, curie in subjects.items()},
            main_classes=[prefixes.expand(curie) or curie for curie in config.get("main_classes") or []],
            prefixes=prefixes,
        )
        loaded.dsv_index = dsv_index
        return loaded

    dsv_index: dict = {}

    def dsv_class_profile(self, class_iri: str) -> str | None:
        """IRI of the base's DSV class profile for ``class_iri`` (None when no DSV of the base is bundled)."""
        return (self.dsv_index.get("classes") or {}).get(class_iri)

    def dsv_property_profile(self, class_iri: str, path: str) -> str | None:
        return (self.dsv_index.get("properties") or {}).get(f"{class_iri} {path}")

    def dsv_application_profile(self) -> str | None:
        return self.dsv_index.get("application_profile")

    # -- classes ------------------------------------------------------------

    def has_class(self, iri: str | None) -> bool:
        return bool(iri) and iri in self.index.classes

    def class_label(self, iri: str) -> str:
        return self._class_labels.get(iri) or self.index.classes.get(iri, None) and self.index.classes[iri].label or " ".join(
            words_of(local_name(iri))
        ).capitalize()

    def classes(self) -> list[BaseClass]:
        ordered = [iri for iri in self.main_classes if iri in self.index.classes]
        ordered += sorted(iri for iri in self.index.classes if iri not in ordered)
        return [
            BaseClass(
                iri=iri,
                label=self.class_label(iri),
                definition=self.index.classes[iri].description,
                obligation=self._class_obligations.get(iri, "unknown"),  # type: ignore[arg-type]
            )
            for iri in ordered
        ]

    def class_for_subject(self, subject: str | None) -> str | None:
        """Map an atom's plain-word subject to a class of this profile (None if there is no match)."""
        if not subject:
            return None
        word = " ".join(subject.lower().split())
        candidates = [word]
        if word.endswith("s"):
            candidates.append(word[:-1])
        for candidate in candidates:
            iri = self._subjects.get(candidate)
            if iri and iri in self.index.classes:
                return iri
        for iri in self.index.classes:   # fall back to the class's own label or local name
            names = {self.class_label(iri).lower(), " ".join(words_of(local_name(iri)))}
            if any(candidate in names for candidate in candidates):
                return iri
        return None

    # -- elements -----------------------------------------------------------

    def obligation(self, target_class: str, path: str) -> str:
        level = self._obligations.get((target_class, path))
        if level:
            return level
        facets = self.index.elements.get((target_class, path))
        if facets is not None and (facets.min_count or 0) >= 1:
            return "mandatory"
        return "unknown"

    def shape_facets(self, target_class: str, path: str) -> ShapeFacets | None:
        return self.index.elements.get((target_class, path))

    def element(self, target_class: str, path: str) -> BaseElement | None:
        facets = self.index.elements.get((target_class, path))
        if facets is None:
            return None
        return BaseElement(
            target_class=target_class,
            path=path,
            facets=facets.to_facets(self.obligation(target_class, path)),
            label=facets.names[0] if facets.names else " ".join(words_of(local_name(path))),
            definition=facets.descriptions[0] if facets.descriptions else "",
            severity=facets.severity,  # type: ignore[arg-type]
            source=facets.shape_ids[0] if facets.shape_ids else "",
        )

    def elements(self, target_class: str | None = None) -> list[BaseElement]:
        keys = sorted(key for key in self.index.elements if target_class is None or key[0] == target_class)
        return [element for key in keys if (element := self.element(*key)) is not None]

    def classes_using(self, path: str) -> list[str]:
        return self.index.classes_using(path)

    def uses_term(self, iri: str) -> bool:
        return iri in self.index.classes or any(path == iri for (_, path) in self.index.elements)

    def namespaces(self) -> set[str]:
        from ..iri import namespace_of

        return {namespace_of(iri) for iri in self.index.classes} | {namespace_of(path) for (_, path) in self.index.elements}

    # -- as terms for the vocabulary index ------------------------------------

    def terms(self) -> list[Term]:
        """Every class and property the profile uses, described in the profile's own words.

        These top up the vocabulary index, so a term the base uses is always
        retrievable even when its vocabulary file is not vendored.
        """
        terms: dict[str, Term] = {}
        for iri, info in self.index.classes.items():
            terms[iri] = Term(
                iri=iri, kind="class", label=self.class_label(iri), definition=info.description,
                vocabulary=self.prefixes.prefix_of(iri) or "", source=f"base profile {self.info.id}",
            )
        for (target_class, path), facets in self.index.elements.items():
            term = terms.get(path)
            if term is None:
                term = terms[path] = Term(
                    iri=path, kind="property",
                    label=facets.names[0] if facets.names else " ".join(words_of(local_name(path))),
                    definition=facets.descriptions[0] if facets.descriptions else "",
                    vocabulary=self.prefixes.prefix_of(path) or "", source=f"base profile {self.info.id}",
                    property_type="datatype" if facets.datatypes or facets.node_kind == "Literal" else
                    ("object" if facets.classes else "unknown"),
                )
            for value in sorted(facets.classes | facets.datatypes):
                if value not in term.range:
                    term.range.append(value)
        return list(terms.values())

    # -- shapes for validation ----------------------------------------------

    def shapes_graph(self) -> Graph:
        """The official constraint shapes (a copy is NOT made: do not mutate)."""
        return self._shapes


def list_base_profiles(data_dir: Path | None = None) -> list[BaseProfileInfo]:
    root = (data_dir or DATA_DIR) / "base-profiles"
    if not root.exists():
        return []
    infos = []
    for config_path in sorted(root.glob("*/profile.yaml")):
        infos.append(load_base_profile(config_path.parent.name, data_dir).info)
    return infos


@lru_cache(maxsize=8)
def _load_cached(base_profile_id: str, data_dir: str) -> BaseProfile:
    return BaseProfile.load(base_profile_id, Path(data_dir) if data_dir else None)


def load_base_profile(base_profile_id: str, data_dir: Path | None = None) -> BaseProfile:
    """Load (and cache) a base profile. The result is shared: treat it as read-only."""
    return _load_cached(base_profile_id, str(data_dir or ""))
