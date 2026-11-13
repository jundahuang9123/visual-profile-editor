"""Stage ``retrieve``: the reusable terms the proposer may choose from, per atom.

Retrieval bounds term choice: the proposer picks from what is retrieved here
(or mints, and then has to say why none of these fits). Three sources are
merged, in this order of trust:

1. elements the BASE profile already defines on the atom's class, scored in the
   wording the base uses for that class (they decide "covered by base" and
   "refine");
2. properties from the vocabulary index, scored lexically and adjusted by
   whether their declared domain fits the class;
3. a few classes, as possible ranges or as classes to bring into the profile.

Everything is deterministic and explained (``Candidate.why``).
"""
from __future__ import annotations

from ..contracts import Atom, AtomAssessment, Candidate
from ..iri import local_name
from ..knowledge import KnowledgeBase
from ..knowledge.vocab_index import tokenize

# Verbs and nouns that occur in almost every requirement and say nothing about WHICH
# information is needed. They are removed from the query (the full wording is still
# used as a fallback when too little is found without them).
GENERIC_WORDS = frozenset(tokenize(
    "state states name names indicate indicates provide provides give gives record records list lists "
    "identify identifies link links describe describes specify specifies include includes contain contains "
    "mention declare show tell document capture express carry make available able possible "
    "dataset datasets distribution distributions catalogue catalog data service resource metadata information "
    "kind kinds type types every each"
))
STRUCTURAL_VOCABULARIES = frozenset({"rdf", "rdfs", "owl", "sh", "xsd"})

BASE_ON_CLASS_BOOST = 1.6     # the base already constrains this path on the atom's class
BASE_ELSEWHERE_BOOST = 1.15   # the base uses the term, on another class
DOMAIN_FIT_BOOST = 1.25       # the vocabulary declares a domain that fits the class
DOMAIN_MISFIT_FACTOR = 0.4    # the vocabulary declares a domain that does not fit
# Vocabularies made for a specific domain (legislation, software licences, rights policies, time,
# addresses) match generic requirement words by accident; they are offered, but ranked lower.
SPECIALISED_VOCABULARIES = {"eli": 0.4, "spdx": 0.4, "odrl": 0.5, "time": 0.6, "locn": 0.6, "vcard": 0.5}
# Reuse ladder: a base element on the atom's class that matches reasonably well is offered before
# vocabulary terms (reuse the base element > tighten it > reuse another term > mint).
BASE_FIRST_SHARE = 0.35
RANGE_MATCH_FACTOR = 0.8      # a base property found through its range class
MAX_CLASS_CANDIDATES = 3


def query_tokens(atom: Atom) -> tuple[list[str], list[str]]:
    """(focused tokens, all tokens) of an atom's statement. Generic requirement wording is dropped
    from the focused tokens unless nothing else is left."""
    everything = list(dict.fromkeys(tokenize(atom.statement)))
    focused = [token for token in everything if token not in GENERIC_WORDS]
    return focused or everything, everything


def _domain_fit(kb: KnowledgeBase, domain: list[str], resource_class: str | None) -> bool | None:
    """True/False when the term declares a domain and we know the class; None when it cannot be judged."""
    if not domain or not resource_class:
        return None
    return any(kb.is_subclass_of(resource_class, declared) for declared in domain)


def retrieve_candidates(
    atom: Atom,
    assessment: AtomAssessment | None,
    kb: KnowledgeBase,
    *,
    top_k: int = 8,
    use_hints: bool = False,
) -> list[Candidate]:
    resource_class = assessment.resource_class if assessment else kb.base.class_for_subject(atom.subject)
    focused, everything = query_tokens(atom)
    scored: dict[str, Candidate] = {}

    # 1. Base elements on the atom's class, in the wording the base uses for that class.
    if resource_class:
        for element in kb.base.elements(resource_class):
            score, matched = kb.vocab.score_text(
                focused, label=element.label, name=local_name(element.path), definition=element.definition
            )
            if score <= 0:
                continue
            term = kb.term(element.path)
            scored[element.path] = Candidate(
                iri=element.path,
                curie=kb.curie(element.path),
                kind="property",
                label=element.label,
                definition=element.definition,
                vocabulary=kb.prefixes.prefix_of(element.path) or "",
                domain=list(term.domain) if term else [],
                range=[value for value in (element.facets.range_class, element.facets.range_datatype) if value],
                score=round(score * BASE_ON_CLASS_BOOST, 4),
                in_base_on_class=True,
                base_classes=kb.base.classes_using(element.path),
                base_facets=element.facets,
                matched=list(matched),
                why=f"base profile defines it on {kb.curie(resource_class)}; matched: {', '.join(matched)}",
            )

    # 2. Properties of the vocabulary index.
    def add_property_hits(tokens: list[str], weight: float) -> None:
        for hit in kb.vocab.search(" ".join(tokens), kind="property", limit=top_k * 4):
            term = hit.term
            if term.vocabulary in STRUCTURAL_VOCABULARIES or term.iri in scored:
                continue
            score, reasons = hit.score * weight, [f"matched: {', '.join(hit.matched)}"]
            prior = SPECIALISED_VOCABULARIES.get(term.vocabulary)
            if prior is not None:
                score *= prior
                reasons.append(f"specialised vocabulary ({term.vocabulary})")
            used_on = kb.base.classes_using(term.iri)
            if used_on:
                score *= BASE_ELSEWHERE_BOOST
                reasons.append(f"used by the base on {', '.join(kb.curie(cls) for cls in used_on[:3])}")
            fit = _domain_fit(kb, term.domain, resource_class)
            if fit is True:
                score *= DOMAIN_FIT_BOOST
                reasons.append("declared domain fits the class")
            elif fit is False:
                score *= DOMAIN_MISFIT_FACTOR
                reasons.append(f"declared domain is {', '.join(kb.curie(d) for d in term.domain[:2])}")
            if term.deprecated:
                reasons.append("deprecated")
            # The base may define the path on this very class in words that did not match the atom.
            on_class = kb.base.element(resource_class, term.iri) if resource_class else None
            if on_class is not None:
                score *= BASE_ON_CLASS_BOOST / BASE_ELSEWHERE_BOOST
                reasons.insert(0, f"base profile defines it on {kb.curie(resource_class)}")
            scored[term.iri] = Candidate(
                iri=term.iri, curie=kb.curie(term.iri), kind="property",
                label=on_class.label if on_class else term.label,
                definition=on_class.definition if on_class else term.definition,
                vocabulary=term.vocabulary, domain=list(term.domain), range=list(term.range),
                score=round(score, 4), in_base_on_class=on_class is not None, base_classes=used_on,
                base_facets=on_class.facets if on_class else None, matched=list(hit.matched),
                why="; ".join(reasons),
            )

    add_property_hits(focused, 1.0)

    # 3. A few classes (possible ranges, or classes to bring into the profile).
    classes: list[Candidate] = []
    for hit in kb.vocab.search(" ".join(focused), kind="class", limit=MAX_CLASS_CANDIDATES * 3):
        term = hit.term
        if term.vocabulary in STRUCTURAL_VOCABULARIES or term.deprecated:
            continue
        in_base = kb.base.has_class(term.iri)
        prior = 1.0 if in_base else SPECIALISED_VOCABULARIES.get(term.vocabulary, 1.0)
        classes.append(Candidate(
            iri=term.iri, curie=kb.curie(term.iri), kind="class", label=term.label, definition=term.definition,
            vocabulary=term.vocabulary, score=round(hit.score * (BASE_ELSEWHERE_BOOST if in_base else prior), 4),
            base_classes=[term.iri] if in_base else [], matched=list(hit.matched),
            why=f"matched: {', '.join(hit.matched)}" + ("; class of the base profile" if in_base else ""),
        ))
    classes = sorted(classes, key=lambda candidate: (-candidate.score, candidate.iri))[:MAX_CLASS_CANDIDATES]

    # A matching class often points at the property that leads to it: when the base already has a
    # property on the atom's class whose range is that class, offer the property too.
    if resource_class:
        for class_candidate in classes:
            for element in kb.base.elements(resource_class):
                if element.facets.range_class != class_candidate.iri:
                    continue
                via_range = round(class_candidate.score * RANGE_MATCH_FACTOR, 4)
                known = scored.get(element.path)
                if known is not None:
                    if via_range > known.score:
                        known.score = via_range
                        known.matched = sorted(set(known.matched) | set(class_candidate.matched))
                        known.why += f"; its range {class_candidate.curie} matched the atom"
                    continue
                term = kb.term(element.path)
                scored[element.path] = Candidate(
                    iri=element.path, curie=kb.curie(element.path), kind="property", label=element.label,
                    definition=element.definition, vocabulary=kb.prefixes.prefix_of(element.path) or "",
                    domain=list(term.domain) if term else [], range=[class_candidate.iri],
                    score=via_range, in_base_on_class=True,
                    base_classes=kb.base.classes_using(element.path), base_facets=element.facets,
                    matched=list(class_candidate.matched),
                    why=f"base profile defines it on {kb.curie(resource_class)}; its range {class_candidate.curie} "
                        f"matched the atom",
                )

    best = max((candidate.score for candidate in scored.values()), default=0.0)
    properties = sorted(scored.values(), key=lambda candidate: (
        0 if candidate.in_base_on_class and candidate.score >= BASE_FIRST_SHARE * best else 1,
        -candidate.score, candidate.iri,
    ))[:top_k]

    # Optional: vocabulary terms an upstream extraction observed. Off by default (answer-in-input risk).
    hinted: list[Candidate] = []
    if use_hints:
        known = {candidate.iri for candidate in properties + classes}
        for hint in atom.hints:
            iri = kb.expand(hint)
            term = kb.term(iri)
            if term is None or term.iri in known:
                continue
            hinted.append(Candidate(
                iri=term.iri, curie=kb.curie(term.iri), kind=term.kind, label=term.label, definition=term.definition,
                vocabulary=term.vocabulary, domain=list(term.domain), range=list(term.range), score=0.0,
                base_classes=kb.base.classes_using(term.iri), why="observed upstream (hint)",
            ))

    candidates = properties + classes + hinted
    for rank, candidate in enumerate(candidates, start=1):
        candidate.rank = rank
    return candidates
