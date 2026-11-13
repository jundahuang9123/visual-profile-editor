"""The symbolic knowledge base: vocabulary index + base profile + the project's own namespace."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from ..contracts import Term
from ..iri import MINT_PREFIX, Prefixes, is_absolute_iri, is_valid_local_name
from .base_profile import DATA_DIR, BaseProfile, list_base_profiles, load_base_profile
from .vocab_index import SearchHit, VocabularyIndex, VocabularyInfo

__all__ = [
    "DATA_DIR", "BaseProfile", "KnowledgeBase", "SearchHit", "VocabularyIndex", "VocabularyInfo",
    "list_base_profiles", "load_base_profile", "load_knowledge_base",
]


@dataclass
class KnowledgeBase:
    """Everything symbolic a run may consult. One instance per project (cheap: the heavy parts are shared)."""

    vocab: VocabularyIndex
    base: BaseProfile
    prefixes: Prefixes
    profile_namespace: str
    profile_prefix: str

    def curie(self, iri: str | None) -> str:
        return self.prefixes.compact(iri)

    def expand(self, value: str | None) -> str | None:
        """Expand a CURIE or a ``NEW:localName`` marker; absolute IRIs pass through; None if not expandable."""
        if not value:
            return None
        value = value.strip()
        if value.startswith(f"{MINT_PREFIX}:"):
            local = value.split(":", 1)[1].strip()
            return f"{self.profile_namespace}{local}" if is_valid_local_name(local) else None
        if is_absolute_iri(value):
            return value
        return self.prefixes.expand(value)

    def is_mint_marker(self, value: str | None) -> bool:
        return bool(value) and value.strip().startswith(f"{MINT_PREFIX}:")

    def is_minted(self, iri: str | None) -> bool:
        """True for an IRI in the profile's own namespace."""
        return bool(iri) and iri.startswith(self.profile_namespace)

    def term(self, iri: str | None) -> Term | None:
        return self.vocab.get(iri)

    def is_subclass_of(self, sub: str, sup: str) -> bool:
        return self.vocab.is_subclass_of(sub, sup)


@lru_cache(maxsize=8)
def _shared_index(base_profile_id: str, data_dir: str, excluded: tuple[str, ...]) -> VocabularyIndex:
    root = Path(data_dir) if data_dir else DATA_DIR
    index = VocabularyIndex.load(root / "vocab", exclude_namespaces=excluded)
    base = load_base_profile(base_profile_id, Path(data_dir) if data_dir else None)
    base_terms = [
        term for term in base.terms()
        if not any(term.iri.startswith(namespace) for namespace in excluded)
    ]
    index.add_terms(base_terms)
    return index


def load_knowledge_base(
    base_profile_id: str,
    *,
    profile_namespace: str,
    profile_prefix: str,
    exclude_namespaces: Sequence[str] = (),
    data_dir: Path | None = None,
) -> KnowledgeBase:
    """Assemble the knowledge base for one project.

    ``exclude_namespaces`` hides whole namespaces from the vocabulary index (the
    held-out-answer rule of benchmark runs). The base profile itself is never hidden.
    """
    base = load_base_profile(base_profile_id, data_dir)
    index = _shared_index(base_profile_id, str(data_dir or ""), tuple(sorted(exclude_namespaces)))
    prefixes = Prefixes(base.prefixes.as_dict())
    prefixes.bind(profile_prefix, profile_namespace)
    return KnowledgeBase(
        vocab=index, base=base, prefixes=prefixes,
        profile_namespace=profile_namespace, profile_prefix=profile_prefix,
    )
