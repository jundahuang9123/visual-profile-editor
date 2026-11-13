"""The offline provider: deterministic rules instead of a model.

It answers the same three tasks as a hosted model (propose, repair, judge) from
the machine-readable ``context`` that accompanies every prompt. It needs no key
and no network, which makes it the provider of the test-suite and of demos, and
it doubles as the "rules only" baseline against which model runs are compared.

Its judgement is purely lexical, so its output is a baseline to be reviewed, not
a modelling authority: it reuses a candidate only when the wording overlaps
clearly, and mints otherwise.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from ..contracts import OBLIGATION_RANK, LLMSettings
from ..engine.retrieve import GENERIC_WORDS
from ..engine.schemas import (
    AtomDecisionOut,
    AttributionOut,
    CoverageOut,
    FacetReasonOut,
    ProposedChangeOut,
    RejectedOut,
    RepairOut,
)
from ..iri import to_local_name
from ..knowledge.vocab_index import STOPWORDS, tokenize
from .base import Completion, LLMError

BASE_MATCH_SCORE = 3.0     # a base element on the class at or above this score carries the information
REUSE_MATCH_SCORE = 4.0    # any other property at or above this score is reused
XSD = "http://www.w3.org/2001/XMLSchema#"

DATATYPE_CUES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("number of", "count of", "how many", "amount of"), "xsd:integer"),
    (("date", "day on which", "when "), "xsd:date"),
    (("address", "link", "url", "web page", "website"), "xsd:anyURI"),
    (("whether", "is or is not", "yes or no"), "xsd:boolean"),
    (("uncertainty", "percentage", "ratio", "temperature", "weight", "length"), "xsd:decimal"),
)


class MockProvider:
    name = "mock"

    def __init__(self, base_match_score: float = BASE_MATCH_SCORE, reuse_match_score: float = REUSE_MATCH_SCORE) -> None:
        self.base_match_score = base_match_score
        self.reuse_match_score = reuse_match_score

    def default_model(self) -> str:
        return "rules-v1"

    def list_models(self) -> list[str]:
        return ["rules-v1"]

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        model: str,
        settings: LLMSettings,
        context: dict[str, Any] | None = None,
    ) -> Completion:
        if not context:
            raise LLMError("The offline provider needs the structured context of the request.")
        if schema is AtomDecisionOut:
            answer: BaseModel = self._propose(context)
        elif schema is RepairOut:
            answer = self._repair(context)
        elif schema is AttributionOut:
            answer = self._judge(context)
        else:
            raise LLMError(f"The offline provider cannot answer schema {schema.__name__}.")
        return Completion(text=answer.model_dump_json(), model=model, stop_reason="end_turn")

    # -- propose ------------------------------------------------------------

    def _propose(self, context: dict[str, Any]) -> AtomDecisionOut:
        atom = context["atom"]
        statement: str = atom["statement"]
        licensed: str = context["licensed_obligation"]
        class_curie: str | None = context.get("resource_class_curie")
        properties = [c for c in context.get("candidates", []) if c["kind"] == "property"]
        need = _information_needed(statement)
        reading = f"Each {atom['subject']} needs to record: {need}."

        if not class_curie:
            return AtomDecisionOut(
                atom_id=atom["id"], reading=reading, information_needed=need, disposition="out_of_scope",
                disposition_reason=(
                    f"The subject '{atom['subject']}' is not a class of the base profile, so the atom is not a "
                    "requirement on the metadata of a catalogued resource."
                ),
                resource_class=None, covered_by=[], changes=[],
            )

        query_size = max(1, int(context.get("query_size") or 1))

        def carries(candidate: dict[str, Any], threshold: float) -> bool:
            """A clear match: a good score that rests on a fair share of the atom's words, or a
            weaker score that covers at least half of them."""
            share = len(candidate.get("matched") or []) / query_size
            score = candidate["score"]
            return (score >= threshold and share >= 0.25) or (score >= threshold / 2 and share >= 0.5)

        on_class = [c for c in properties if c.get("in_base_on_class") and carries(c, self.base_match_score)]
        others = [c for c in properties if not c.get("in_base_on_class") and carries(c, self.reuse_match_score)]
        best_base = on_class[0] if on_class else None
        if best_base is not None:
            # Minimal change first: among near-equal matches prefer one the base already makes strong enough.
            for candidate in on_class:
                level = (candidate.get("base_facets") or {}).get("obligation", "unknown")
                if candidate["score"] >= 0.85 * best_base["score"] and OBLIGATION_RANK[level] >= OBLIGATION_RANK[licensed]:
                    best_base = candidate
                    break
        best_other = others[0] if others else None

        compound = "compound" in context.get("lint_codes", [])
        coverage = "partial" if compound else "full"
        quote = statement

        if best_base is not None:
            base_obligation = (best_base.get("base_facets") or {}).get("obligation", "unknown")
            if OBLIGATION_RANK[base_obligation] >= OBLIGATION_RANK[licensed]:
                return AtomDecisionOut(
                    atom_id=atom["id"], reading=reading, information_needed=need, disposition="covered_by_base",
                    disposition_reason=(
                        f"The base already defines {best_base['curie']} on {class_curie} as {base_obligation}, "
                        f"which is at least as strong as '{atom['modality']}' requires."
                    ),
                    resource_class=class_curie, covered_by=[best_base["curie"]], changes=[],
                )
            reason = f"The atom says '{atom['modality']}', the base only makes {best_base['curie']} {base_obligation}."
            facet_reasons = [FacetReasonOut(facet="obligation", reason=reason)]
            if licensed == "mandatory":
                facet_reasons.append(FacetReasonOut(facet="min_count", reason="A mandatory property needs at least one value."))
            change = ProposedChangeOut(
                kind="refine_property", target_class=class_curie, path=best_base["curie"], label=None, definition=None,
                usage_note=None, obligation=licensed, min_count=1 if licensed == "mandatory" else None, max_count=None,
                range=None, range_kind="unspecified", node_kind=None, controlled_vocabulary=[], super_term=None,
                covers=[CoverageOut(atom_id=atom["id"], reason=reason, evidence_quote=quote, coverage=coverage)],
                facet_reasons=facet_reasons, reason_no_reuse=None,
                rejected_candidates=_rejected(properties, best_base["curie"]),
                rationale=f"Tighten the existing base property {best_base['curie']} instead of adding a new one.",
                confidence=_confidence(best_base["score"], self.base_match_score),
            )
            return _needs_change(atom, reading, need, class_curie, [change])

        if best_other is not None:
            reason = f"{best_other['curie']} ('{best_other['label']}') carries the information the atom asks for."
            facet_reasons = [FacetReasonOut(facet="obligation", reason=f"The atom says '{atom['modality']}'.")]
            if licensed == "mandatory":
                facet_reasons.append(FacetReasonOut(facet="min_count", reason="A mandatory property needs at least one value."))
            change = ProposedChangeOut(
                kind="reuse_property", target_class=class_curie, path=best_other["curie"], label=None, definition=None,
                usage_note=None, obligation=licensed, min_count=1 if licensed == "mandatory" else None, max_count=None,
                range=None, range_kind="unspecified", node_kind=None, controlled_vocabulary=[], super_term=None,
                covers=[CoverageOut(atom_id=atom["id"], reason=reason, evidence_quote=quote, coverage=coverage)],
                facet_reasons=facet_reasons, reason_no_reuse=None,
                rejected_candidates=_rejected(properties, best_other["curie"]),
                rationale=f"Reuse the existing term {best_other['curie']}; no new term is needed.",
                confidence=_confidence(best_other["score"], self.reuse_match_score),
            )
            return _needs_change(atom, reading, need, class_curie, [change])

        # Nothing reusable carries the information: mint a property (unless one was already minted for it).
        local = to_local_name(need)
        for pending in context.get("pending", []):
            if pending.get("kind") == "mint_property" and (pending.get("path") or "").endswith(f"#{local}"):
                local = (pending.get("path") or "").rsplit("#", 1)[-1]
        datatype = _datatype_for(need)
        reason = f"The atom asks for '{need}', which no retrieved term carries."
        facet_reasons = [
            FacetReasonOut(facet="obligation", reason=f"The atom says '{atom['modality']}'."),
            FacetReasonOut(facet="range", reason=f"The wording suggests a value of type {datatype}."),
        ]
        if licensed == "mandatory":
            facet_reasons.append(FacetReasonOut(facet="min_count", reason="A mandatory property needs at least one value."))
        change = ProposedChangeOut(
            kind="mint_property", target_class=class_curie, path=f"NEW:{local}", label=need,
            definition=f"The {need} of the {atom['subject']}.", usage_note=None,
            obligation=licensed, min_count=1 if licensed == "mandatory" else None, max_count=None,
            range=datatype, range_kind="datatype", node_kind="Literal", controlled_vocabulary=[], super_term=None,
            covers=[CoverageOut(atom_id=atom["id"], reason=reason, evidence_quote=quote, coverage=coverage)],
            facet_reasons=facet_reasons,
            reason_no_reuse=(
                "No retrieved term matches the wording of the atom closely enough "
                f"(best lexical score {properties[0]['score']:.1f})." if properties
                else "No term was retrieved for the wording of the atom."
            ),
            rejected_candidates=_rejected(properties, None),
            rationale="No base element and no vocabulary term carries this information, so a term is minted.",
            confidence=0.45,
        )
        return _needs_change(atom, reading, need, class_curie, [change])

    # -- repair -------------------------------------------------------------

    def _repair(self, context: dict[str, Any]) -> RepairOut:
        change: dict[str, Any] = context["change"]
        failures: list[dict[str, Any]] = context["failures"]
        atoms: list[dict[str, Any]] = context["atoms"]
        licensed: str = context["licensed_obligation"]
        base_facets: dict[str, Any] | None = context.get("base_facets")
        codes = {failure["check"] for failure in failures}
        notes: list[str] = []
        try:
            out = ProposedChangeOut.model_validate_json(context["proposed_json"])
        except ValueError:
            return RepairOut(action="withdraw", note="The proposed change could not be read back.", change=None)

        if codes & {"V1", "V2"}:
            return RepairOut(action="withdraw", note="The change uses a term that does not exist or does not fit; "
                                                     "rules cannot choose another one.", change=None)
        for failure in failures:
            details = failure.get("details") or {}
            if failure["check"] == "T1" and details.get("problem") == "obligation_exceeds_modality":
                out.obligation = licensed  # type: ignore[assignment]
                if licensed != "mandatory":
                    out.min_count = None
                notes.append(f"obligation lowered to {licensed}, the strongest the atoms license")
            if failure["check"] == "T1" and details.get("problem") == "quote_not_verbatim" and atoms:
                for link in out.covers:
                    statement = next((a["statement"] for a in atoms if a["id"] == link.atom_id), atoms[0]["statement"])
                    link.evidence_quote = statement
                notes.append("evidence quotes replaced by the atoms' own wording")
            if failure["check"] == "V3" and base_facets:
                for facet in details.get("facets", []):
                    if facet == "obligation":
                        out.obligation = base_facets["obligation"]
                    elif facet == "min_count":
                        out.min_count = base_facets.get("min_count")
                    elif facet == "max_count":
                        out.max_count = base_facets.get("max_count")
                    elif facet in ("range_class", "range_datatype", "range"):
                        out.range, out.range_kind = None, "unspecified"
                    elif facet == "node_kind":
                        out.node_kind = None
                    elif facet == "controlled_vocabulary":
                        out.controlled_vocabulary = []
                notes.append("constraints that loosened or contradicted the base were reset to the base")
            if failure["check"] == "V5":
                if out.obligation == "mandatory" and not out.min_count:
                    out.min_count = 1
                if out.min_count is not None and out.max_count is not None and out.min_count > out.max_count:
                    out.max_count = None
                notes.append("cardinalities made consistent")
            if failure["check"] == "V4" and not (out.reason_no_reuse or "").strip():
                out.reason_no_reuse = "No retrieved term matches the wording of the atom."
                notes.append("mint justification added")
        if not notes:
            return RepairOut(action="withdraw", note="Rules cannot repair these violations: " + ", ".join(sorted(codes)), change=None)
        return RepairOut(action="revise", note="; ".join(dict.fromkeys(notes)), change=out)

    # -- judge --------------------------------------------------------------

    def _judge(self, context: dict[str, Any]) -> AttributionOut:
        change: dict[str, Any] = context["change"]
        atoms: list[dict[str, Any]] = context["atoms"]
        licensed: str = context["licensed_obligation"]
        facets = change.get("facets") or {}
        range_iri = facets.get("range_class") or ""
        described = set(tokenize(" ".join([
            change.get("label") or "", change.get("definition") or "",
            (change.get("path") or "").rsplit("#", 1)[-1].rsplit("/", 1)[-1],
            range_iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1],
        ])))
        asked = set()
        for atom in atoms:
            asked |= {token for token in tokenize(atom["statement"]) if token not in GENERIC_WORDS}
        overlap = sorted(described & asked)
        obligation = (change.get("facets") or {}).get("obligation", "unknown")
        if OBLIGATION_RANK.get(obligation, 0) > OBLIGATION_RANK[licensed]:
            return AttributionOut(
                verdict="partially_supported",
                explanation=f"The atoms license at most '{licensed}', the change sets '{obligation}'.",
                unsupported_facets=["obligation"],
            )
        if not overlap:
            return AttributionOut(
                verdict="unsupported",
                explanation="The wording of the atoms and the description of the term have no words in common.",
                unsupported_facets=[],
            )
        partial = any(link.get("coverage") == "partial" for link in change.get("covers", []))
        return AttributionOut(
            verdict="partially_supported" if partial else "supported",
            explanation=f"Shared wording: {', '.join(overlap[:6])}." + (" Only part of an atom is answered." if partial else ""),
            unsupported_facets=[],
        )


def _needs_change(atom: dict[str, Any], reading: str, need: str, class_curie: str,
                  changes: list[ProposedChangeOut]) -> AtomDecisionOut:
    return AtomDecisionOut(
        atom_id=atom["id"], reading=reading, information_needed=need, disposition="needs_change",
        disposition_reason="The base profile does not satisfy the atom as worded.",
        resource_class=class_curie, covered_by=[], changes=changes,
    )


def _rejected(properties: list[dict[str, Any]], chosen: str | None) -> list[RejectedOut]:
    return [
        RejectedOut(term=candidate["curie"], reason=f"weaker lexical match (score {candidate['score']:.1f})")
        for candidate in properties if candidate["curie"] != chosen
    ][:3]


def _confidence(score: float, threshold: float) -> float:
    return round(min(0.9, 0.5 + 0.1 * (score / threshold)), 2)


def _datatype_for(statement: str) -> str:
    lowered = f" {statement.lower()} "
    for cues, datatype in DATATYPE_CUES:
        if any(cue in lowered for cue in cues):
            return datatype
    return "xsd:string"


_LEADING = re.compile(
    r"^.*?\b(?:must|shall|should|may|can|needs? to|has to|have to)\b\s+(?:be able to\s+)?"
    r"(?:state|name|indicate|provide|give|record|list|identify|link to|describe|specify|include|contain|have|carry)?\s*",
    re.IGNORECASE,
)


def _information_needed(statement: str) -> str:
    """The noun phrase after the modal verb, trimmed to a handful of content words."""
    rest = _LEADING.sub("", " ".join(statement.split()).rstrip("."), count=1) or statement
    rest = re.split(r"\b(?:and|that|which|who|under which|in which)\b", rest, maxsplit=1)[0]
    words = [word for word in re.split(r"[^A-Za-z0-9]+", rest) if word and word.lower() not in STOPWORDS]
    content = [word for word in words if not (set(tokenize(word)) <= GENERIC_WORDS)]
    return " ".join((content or words)[:4]).lower() or "required information"
