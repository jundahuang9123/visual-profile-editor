"""The vocabulary index: every reusable class and property the tool knows.

Built offline from vendored vocabulary files (``data/vocab/MANIFEST.json``) and
topped up with the terms a base profile uses. The Retrieve step searches it;
the verifier asks it whether a term exists (V1), what its domain and range are
(V2) and whether one class specialises another (V3).

Search is lexical on purpose (labels, local names, definitions; BM25-style
scoring): it is transparent, deterministic and needs no model or network.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

from ..contracts import Term
from ..iri import Prefixes, local_name, namespace_of, words_of

SCHEMA_DOMAIN = (URIRef("http://schema.org/domainIncludes"), URIRef("https://schema.org/domainIncludes"),
                 URIRef("http://purl.org/dc/dcam/domainIncludes"))
SCHEMA_RANGE = (URIRef("http://schema.org/rangeIncludes"), URIRef("https://schema.org/rangeIncludes"),
                URIRef("http://purl.org/dc/dcam/rangeIncludes"))

CLASS_TYPES = (RDFS.Class, OWL.Class)
PROPERTY_TYPES = {
    RDF.Property: "unknown",
    OWL.ObjectProperty: "object",
    OWL.DatatypeProperty: "datatype",
    OWL.AnnotationProperty: "annotation",
}

STOPWORDS = frozenset(
    "a an the of to in on for and or by with from as at is are be been its it this that which who whom "
    "each every any all must should may shall can could will would need needs have has had do does "
    "able about into than then there their they them one more most such state states stated".split()
)


class VocabularyInfo(BaseModel):
    prefix: str
    namespace: str
    title: str = ""
    source: str = ""
    version: str = ""
    licence: str = ""
    file: str = ""
    class_count: int = 0
    property_count: int = 0


@dataclass
class SearchHit:
    term: Term
    score: float
    matched: list[str] = field(default_factory=list)


_SPELLING = (("licenc", "licens"), ("catalogu", "catalog"), ("organis", "organiz"), ("isation", "ization"))
_SUFFIXES = (
    "izations", "ization", "ations", "ation", "ments", "ment", "ities", "ity", "ings", "ing",
    "ions", "ion", "ors", "ers", "ies", "ied", "or", "er", "es", "ed", "al", "s", "e",
)


def stem(word: str) -> str:
    """A small suffix stripper that conflates the word families of plain requirement wording
    (cite / citation, contributed / contributor / contributions, licence / licenses, files / file).
    The stems are not words; all that matters is that related forms meet."""
    for british, american in _SPELLING:
        word = word.replace(british, american)
    for _ in range(3):
        for suffix in _SUFFIXES:
            if not word.endswith(suffix) or len(word) - len(suffix) < 3:
                continue
            if suffix == "s" and word.endswith(("ss", "us", "is")):
                continue
            word = word[: len(word) - len(suffix)]
            if suffix in ("ies", "ied"):
                word += "i"
            break
        else:
            break
    if len(word) > 3 and word.endswith("y"):
        word = word[:-1] + "i"
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiouls":
        word = word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    words: list[str] = []
    for chunk in re.split(r"[^A-Za-z0-9]+", text or ""):
        words.extend(words_of(chunk))
    return [stem(word) for word in words if len(word) > 1 and word not in STOPWORDS]


def _english(graph: Graph, subject: URIRef, predicates: Sequence[URIRef]) -> str:
    best = ""
    for predicate in predicates:
        for value in graph.objects(subject, predicate):
            if not isinstance(value, Literal):
                continue
            language = value.language or ""
            if language.startswith("en"):
                return " ".join(str(value).split())
            if not best and not language:
                best = " ".join(str(value).split())
    return best


def terms_from_graph(graph: Graph, namespace: str, prefix: str, source: str = "") -> list[Term]:
    """Extract the classes and properties that live in ``namespace`` from a vocabulary graph."""
    kinds: dict[URIRef, tuple[str, str]] = {}
    for class_type in CLASS_TYPES:
        for subject in graph.subjects(RDF.type, class_type):
            if isinstance(subject, URIRef):
                kinds.setdefault(subject, ("class", "unknown"))
    for property_type, flavour in PROPERTY_TYPES.items():
        for subject in graph.subjects(RDF.type, property_type):
            if isinstance(subject, URIRef):
                previous = kinds.get(subject)
                if previous is None or previous[0] == "property" and previous[1] == "unknown":
                    kinds[subject] = ("property", flavour)
    terms: list[Term] = []
    for subject, (kind, flavour) in kinds.items():
        iri = str(subject)
        if not iri.startswith(namespace) or len(iri) <= len(namespace):
            continue
        domain = {str(o) for o in graph.objects(subject, RDFS.domain) if isinstance(o, URIRef)}
        range_ = {str(o) for o in graph.objects(subject, RDFS.range) if isinstance(o, URIRef)}
        for predicate in SCHEMA_DOMAIN:
            domain |= {str(o) for o in graph.objects(subject, predicate) if isinstance(o, URIRef)}
        for predicate in SCHEMA_RANGE:
            range_ |= {str(o) for o in graph.objects(subject, predicate) if isinstance(o, URIRef)}
        super_predicate = RDFS.subClassOf if kind == "class" else RDFS.subPropertyOf
        supers = {str(o) for o in graph.objects(subject, super_predicate) if isinstance(o, URIRef)}
        deprecated = any(str(value).lower() == "true" for value in graph.objects(subject, OWL.deprecated))
        terms.append(
            Term(
                iri=iri,
                kind=kind,  # type: ignore[arg-type]
                label=_english(graph, subject, (RDFS.label, SKOS.prefLabel)) or " ".join(words_of(local_name(iri))),
                definition=_english(graph, subject, (SKOS.definition, RDFS.comment, DCTERMS.description)),
                vocabulary=prefix,
                domain=sorted(domain),
                range=sorted(range_),
                super_terms=sorted(supers),
                property_type=flavour if kind == "property" else "unknown",  # type: ignore[arg-type]
                deprecated=deprecated,
                source=source,
            )
        )
    return sorted(terms, key=lambda term: term.iri)


class VocabularyIndex:
    def __init__(self, terms: Iterable[Term] = (), vocabularies: Iterable[VocabularyInfo] = ()) -> None:
        self._terms: dict[str, Term] = {}
        self._vocabularies: dict[str, VocabularyInfo] = {info.prefix: info for info in vocabularies}
        self._dirty = True
        self._postings: dict[str, dict[str, float]] = {}
        self._idf: dict[str, float] = {}
        self._supers: dict[str, set[str]] = {}
        self.add_terms(terms)

    # -- loading ------------------------------------------------------------

    @classmethod
    def load(cls, vocab_dir: Path, *, exclude_namespaces: Sequence[str] = ()) -> "VocabularyIndex":
        """Load every vocabulary listed in ``MANIFEST.json`` under ``vocab_dir``.

        Namespaces in ``exclude_namespaces`` are left out entirely (leakage control:
        a run must not see the namespace of the profile it is asked to reconstruct).
        """
        manifest_path = vocab_dir / "MANIFEST.json"
        if not manifest_path.exists():
            return cls()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        index = cls()
        for entry in manifest.get("vocabularies", []):
            namespace = entry["namespace"]
            if any(namespace.startswith(excluded) for excluded in exclude_namespaces):
                continue
            graph = Graph()
            for file_name in entry.get("files") or [entry.get("file")]:
                if not file_name:
                    continue
                path = vocab_dir / file_name
                if path.exists():
                    graph.parse(path, format=entry.get("format") or _guess_format(path))
            terms = terms_from_graph(graph, namespace, entry["prefix"], source=str(entry.get("file") or ""))
            index.add_terms(terms)
            index._vocabularies[entry["prefix"]] = VocabularyInfo(
                prefix=entry["prefix"],
                namespace=namespace,
                title=entry.get("title", ""),
                source=entry.get("source_url", ""),
                version=str(entry.get("version", "")),
                licence=entry.get("licence", ""),
                file=str(entry.get("file") or ""),
                class_count=sum(1 for term in terms if term.kind == "class"),
                property_count=sum(1 for term in terms if term.kind == "property"),
            )
        return index

    def add_terms(self, terms: Iterable[Term], *, overwrite: bool = False) -> None:
        """Add terms; by default a term that is already known keeps its richer vocabulary entry."""
        for term in terms:
            known = self._terms.get(term.iri)
            if known is None or overwrite:
                self._terms[term.iri] = term
            else:
                # Fill gaps of the known entry from the new one (e.g. a base profile's wording).
                if not known.label and term.label:
                    known.label = term.label
                if not known.definition and term.definition:
                    known.definition = term.definition
                if not known.range and term.range:
                    known.range = list(term.range)
        self._dirty = True

    def register_vocabulary(self, info: VocabularyInfo) -> None:
        self._vocabularies.setdefault(info.prefix, info)

    # -- lookup -------------------------------------------------------------

    def get(self, iri: str | None) -> Term | None:
        return self._terms.get(iri) if iri else None

    def __contains__(self, iri: object) -> bool:
        return iri in self._terms

    def __len__(self) -> int:
        return len(self._terms)

    def terms(self, *, vocabulary: str | None = None, kind: str | None = None) -> list[Term]:
        return [
            term for term in self._terms.values()
            if (vocabulary is None or term.vocabulary == vocabulary) and (kind is None or term.kind == kind)
        ]

    def vocabularies(self) -> list[VocabularyInfo]:
        counts: dict[str, Counter] = defaultdict(Counter)
        for term in self._terms.values():
            counts[term.vocabulary][term.kind] += 1
        result = []
        for prefix in sorted(set(self._vocabularies) | set(counts)):
            info = self._vocabularies.get(prefix) or VocabularyInfo(prefix=prefix, namespace="")
            if not info.namespace:
                sample = next((term for term in self._terms.values() if term.vocabulary == prefix), None)
                info = info.model_copy(update={"namespace": namespace_of(sample.iri) if sample else ""})
            result.append(
                info.model_copy(update={"class_count": counts[prefix]["class"], "property_count": counts[prefix]["property"]})
            )
        return result

    # -- hierarchy ----------------------------------------------------------

    def _build_hierarchy(self) -> None:
        direct = {iri: set(term.super_terms) for iri, term in self._terms.items()}
        closure: dict[str, set[str]] = {}

        def ancestors(iri: str, seen: frozenset[str]) -> set[str]:
            if iri in closure:
                return closure[iri]
            found: set[str] = set()
            for parent in direct.get(iri, ()):
                if parent in seen:
                    continue
                found.add(parent)
                found |= ancestors(parent, seen | {iri})
            closure[iri] = found
            return found

        for iri in direct:
            ancestors(iri, frozenset())
        self._supers = closure

    def super_terms(self, iri: str) -> set[str]:
        self._refresh()
        return set(self._supers.get(iri, ()))

    def is_subclass_of(self, sub: str, sup: str) -> bool:
        """Reflexive and transitive. Everything is a subclass of rdfs:Resource / owl:Thing."""
        if sub == sup or sup in (str(RDFS.Resource), str(OWL.Thing)):
            return True
        return sup in self.super_terms(sub)

    def is_subproperty_of(self, sub: str, sup: str) -> bool:
        return sub == sup or sup in self.super_terms(sub)

    # -- search -------------------------------------------------------------

    def _refresh(self) -> None:
        if not self._dirty:
            return
        postings: dict[str, dict[str, float]] = defaultdict(dict)
        for iri, term in self._terms.items():
            weights: Counter = Counter()
            for token in tokenize(term.label):
                weights[token] += 3.0
            for token in tokenize(local_name(iri)):
                weights[token] += 2.0
            for token in tokenize(term.definition):
                weights[token] += 1.0
            length = 1.0 + math.log(1.0 + sum(weights.values()))
            for token, weight in weights.items():
                postings[token][iri] = weight / length
        total = max(len(self._terms), 1)
        self._idf = {token: math.log(1.0 + total / len(docs)) for token, docs in postings.items()}
        self._postings = dict(postings)
        self._build_hierarchy()
        self._dirty = False

    def score_text(
        self, query: Sequence[str], *, label: str = "", name: str = "", definition: str = ""
    ) -> tuple[float, list[str]]:
        """Score an ad-hoc description (for example a base element in the wording its class uses)
        against query tokens, with the same field weights and term rarity as ``search``."""
        self._refresh()
        weights: Counter = Counter()
        for token in tokenize(label):
            weights[token] += 3.0
        for token in tokenize(name):
            weights[token] += 2.0
        for token in tokenize(definition):
            weights[token] += 1.0
        if not weights:
            return 0.0, []
        length = 1.0 + math.log(1.0 + sum(weights.values()))
        rare = math.log(1.0 + max(len(self._terms), 1))
        matched = [token for token in dict.fromkeys(query) if token in weights]
        score = sum(self._idf.get(token, rare) * weights[token] / length for token in matched)
        score *= 1.0 + 0.25 * (len(matched) - 1) if matched else 0.0
        return round(score, 4), matched

    def search(self, text: str, *, kind: str | None = None, limit: int = 10) -> list[SearchHit]:
        """Rank terms against free text. Deterministic: ties are broken by IRI."""
        self._refresh()
        query = list(dict.fromkeys(tokenize(text)))
        scores: Counter = Counter()
        matched: dict[str, list[str]] = defaultdict(list)
        for token in query:
            for iri, weight in self._postings.get(token, {}).items():
                scores[iri] += self._idf.get(token, 0.0) * weight
                matched[iri].append(token)
        hits = []
        for iri, score in scores.items():
            term = self._terms[iri]
            if kind is not None and term.kind != kind:
                continue
            if term.deprecated:
                score *= 0.5
            # Reward terms that answer several query words, not one word many times.
            score *= 1.0 + 0.25 * (len(set(matched[iri])) - 1)
            hits.append(SearchHit(term=term, score=round(score, 4), matched=sorted(set(matched[iri]))))
        hits.sort(key=lambda hit: (-hit.score, hit.term.iri))
        return hits[:limit]


def _guess_format(path: Path) -> str:
    return {".ttl": "turtle", ".rdf": "xml", ".owl": "xml", ".xml": "xml", ".jsonld": "json-ld",
            ".nt": "nt", ".n3": "n3"}.get(path.suffix.lower(), "turtle")


def prefix_for(iri: str, prefixes: Prefixes) -> str:
    return prefixes.prefix_of(iri) or namespace_of(iri)
