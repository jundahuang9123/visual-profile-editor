"""IRI helpers shared by the whole tool.

Internally every term is stored as an EXPANDED IRI. Compact names (CURIEs such
as ``dcat:Dataset``) are used only at the edges: what the LLM reads and writes,
what the workbench displays, and what a human types.
"""
from __future__ import annotations

import re

# Prefixes the tool knows out of the box. ``dct`` is accepted as an alias when
# expanding (DCAT-AP documents use it) but ``dcterms`` is what we write.
DEFAULT_PREFIXES: dict[str, str] = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcterms": "http://purl.org/dc/terms/",
    "dcatap": "http://data.europa.eu/r5r/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "prov": "http://www.w3.org/ns/prov#",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "adms": "http://www.w3.org/ns/adms#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "spdx": "http://spdx.org/rdf/terms#",
    "locn": "http://www.w3.org/ns/locn#",
    "eli": "http://data.europa.eu/eli/ontology#",
    "time": "http://www.w3.org/2006/time#",
    "dqv": "http://www.w3.org/ns/dqv#",
    "schema": "http://schema.org/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "sh": "http://www.w3.org/ns/shacl#",
    "dsv": "https://w3id.org/dsv#",
    "prof": "http://www.w3.org/ns/dx/prof/",
}

PREFIX_ALIASES: dict[str, str] = {"dct": "dcterms", "dc": "dcterms", "sdo": "schema"}

# Marker the LLM uses for a term that does not exist yet and must be minted in
# the profile's own namespace, e.g. ``NEW:constructionPhase``.
MINT_PREFIX = "NEW"

_CURIE_RE = re.compile(r"^([A-Za-z][\w.-]*):([^\s/][^\s]*)$")
_ABSOLUTE_RE = re.compile(r"^(https?://|urn:)", re.IGNORECASE)
_LOCAL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def is_absolute_iri(value: str | None) -> bool:
    return bool(value) and bool(_ABSOLUTE_RE.match(value.strip()))


def is_valid_local_name(value: str | None) -> bool:
    """A local name we are willing to mint (letters, digits, underscore; starts with a letter)."""
    return bool(value) and bool(_LOCAL_NAME_RE.match(value))


class Prefixes:
    """A prefix map: the defaults plus whatever a project binds (its own namespace)."""

    def __init__(self, extra: dict[str, str] | None = None) -> None:
        self._map: dict[str, str] = dict(DEFAULT_PREFIXES)
        for prefix, namespace in (extra or {}).items():
            self.bind(prefix, namespace)

    def bind(self, prefix: str, namespace: str) -> None:
        if not prefix or not namespace:
            raise ValueError("prefix and namespace are required")
        self._map[prefix] = namespace

    def as_dict(self) -> dict[str, str]:
        return dict(self._map)

    def namespace(self, prefix: str) -> str | None:
        return self._map.get(PREFIX_ALIASES.get(prefix, prefix))

    def expand(self, value: str | None) -> str | None:
        """Expand a CURIE to an IRI. Absolute IRIs pass through; unknown prefixes give None."""
        if not value:
            return None
        value = value.strip()
        if value.startswith("<") and value.endswith(">"):
            value = value[1:-1]
        if is_absolute_iri(value):
            return value
        match = _CURIE_RE.match(value)
        if not match:
            return None
        namespace = self.namespace(match.group(1))
        return f"{namespace}{match.group(2)}" if namespace else None

    def compact(self, iri: str | None) -> str:
        """Compact an IRI to a CURIE using the longest matching namespace; unknown IRIs pass through."""
        if not iri:
            return ""
        best: tuple[str, str] | None = None
        for prefix, namespace in self._map.items():
            if iri.startswith(namespace) and (best is None or len(namespace) > len(best[1])):
                best = (prefix, namespace)
        if best is None:
            return iri
        local = iri[len(best[1]):]
        return f"{best[0]}:{local}" if local else iri

    def prefix_of(self, iri: str | None) -> str | None:
        compacted = self.compact(iri)
        if compacted and compacted != iri and ":" in compacted:
            return compacted.split(":", 1)[0]
        return None


def split_iri(iri: str) -> tuple[str, str]:
    """Split an IRI into (namespace, local name) at the last '#' or '/'."""
    for separator in ("#", "/"):
        index = iri.rfind(separator)
        if index >= 0 and index < len(iri) - 1:
            return iri[: index + 1], iri[index + 1:]
    return iri, ""


def local_name(iri: str | None) -> str:
    if not iri:
        return ""
    if not is_absolute_iri(iri) and ":" in iri:
        return iri.split(":", 1)[1]
    return split_iri(iri)[1] or iri


def namespace_of(iri: str) -> str:
    return split_iri(iri)[0]


def words_of(name: str) -> list[str]:
    """Split a local name such as ``bibliographicCitation`` or ``has_part`` into lowercase words."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name or "")
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [word.lower() for word in re.split(r"[\s_\-./]+", spaced) if word]


def to_local_name(text: str, *, upper_first: bool = False) -> str:
    """Build a mintable camelCase local name from free text (``upper_first`` for classes)."""
    words = [word for word in re.split(r"[^A-Za-z0-9]+", text or "") if word]
    if not words:
        return "Term" if upper_first else "term"
    head = words[0][:1].upper() + words[0][1:] if upper_first else words[0][:1].lower() + words[0][1:]
    name = head + "".join(word[:1].upper() + word[1:] for word in words[1:])
    if not name[0].isalpha():
        name = ("C" if upper_first else "p") + name
    return name[:64]
