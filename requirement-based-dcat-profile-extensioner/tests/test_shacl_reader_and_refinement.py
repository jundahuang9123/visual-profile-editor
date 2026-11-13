"""SHACL reader and refinement comparison (generalised from the RQ2 WP0 delta tool)."""
from pathlib import Path

import pytest

from profile_extensioner.conformance.refinement import compare_facets, compare_obligation
from profile_extensioner.knowledge.shacl_reader import ShapeFacets, load_graph, read_shapes

FIXTURES = Path(__file__).parent / "fixtures" / "shapes"
DCAT = "http://www.w3.org/ns/dcat#"
DCT = "http://purl.org/dc/terms/"
EX = "http://example.org/profile#"


@pytest.fixture(scope="module")
def base():
    return read_shapes(load_graph([FIXTURES / "base.ttl"]))


@pytest.fixture(scope="module")
def profile():
    return read_shapes(load_graph([FIXTURES / "profile.ttl"]))


def delta(base, profile, cls, path):
    """Classic delta between two complete shape sets."""
    return compare_facets(base.elements.get((cls, path)), profile.elements[(cls, path)], inherit_missing=False)


def test_reader_indexes_by_class_and_path(base):
    assert base.elements[(DCAT + "Dataset", DCT + "title")].min_count == 1
    assert base.elements[(DCAT + "Dataset", DCT + "title")].node_kind == "Literal"
    assert base.elements[(DCAT + "Dataset", DCAT + "keyword")].severity == "Warning"
    assert set(base.classes) == {DCAT + "Dataset", DCAT + "Distribution"}
    assert base.paths_of(DCAT + "Distribution") == [DCT + "format"]
    assert base.classes_using(DCT + "format") == [DCAT + "Distribution"]


def test_unhandled_constructs_are_reported(profile):
    text = " | ".join(profile.unhandled)
    assert "sh:or" in text and "non-IRI sh:path" in text and "without sh:targetClass" in text


def test_unchanged_added_and_class_addition(base, profile):
    assert delta(base, profile, DCAT + "Dataset", DCT + "title").status == "unchanged"
    citation = delta(base, profile, DCAT + "Dataset", DCT + "bibliographicCitation")
    assert citation.status == "added"
    assert {d.facet for d in citation.facets} == {"min_count", "range_datatype"}
    assert EX + "Assessment" in profile.classes and EX + "Assessment" not in base.classes
    assert delta(base, profile, EX + "Assessment", DCT + "date").status == "added"


@pytest.mark.parametrize("cls, path, facet", [
    ("Dataset", "issued", "min_count"),
    ("Dataset", "accrualPeriodicity", "node_kind"),
    ("Distribution", "format", "controlled_vocabulary"),
])
def test_tightened(base, profile, cls, path, facet):
    comparison = delta(base, profile, DCAT + cls, DCT + path)
    assert comparison.status == "tightened" and comparison.is_legal
    assert [d.facet for d in comparison.facets if d.status == "tightened"] == [facet]


def test_loosened_severity_is_flagged(base, profile):
    comparison = delta(base, profile, DCAT + "Dataset", DCAT + "keyword")
    assert comparison.status == "loosened" and not comparison.is_legal
    assert comparison.loosened[0].facet == "severity"


def test_change_mode_inherits_what_it_does_not_mention():
    base = ShapeFacets(min_count=1, max_count=1, classes={"http://x/A"}, node_kind="IRI")
    change = ShapeFacets(min_count=1)   # mentions only the minimum
    assert compare_facets(base, change, inherit_missing=True).status == "unchanged"
    dropped = compare_facets(base, change, inherit_missing=False)
    assert dropped.status == "loosened"
    assert {d.facet for d in dropped.loosened} == {"max_count", "range_class", "node_kind"}


def test_cardinality_loosening_and_conflicts():
    base = ShapeFacets(min_count=1, max_count=1)
    assert compare_facets(base, ShapeFacets(min_count=0)).loosened[0].facet == "min_count"
    assert compare_facets(base, ShapeFacets(max_count=5)).loosened[0].facet == "max_count"
    assert compare_facets(base, ShapeFacets(min_count=2)).conflicts[0].facet == "min_count"
    assert compare_facets(ShapeFacets(min_count=2), ShapeFacets(max_count=1)).conflicts[0].facet == "max_count"
    optional = ShapeFacets()
    tightened = compare_facets(optional, ShapeFacets(min_count=1, max_count=1))
    assert tightened.status == "tightened" and tightened.is_legal


def test_range_class_uses_subclass_knowledge():
    base = ShapeFacets(classes={"http://x/Agent"})
    narrower = ShapeFacets(classes={"http://x/Organisation"})
    is_subclass = lambda sub, sup: sub == sup or (sub, sup) == ("http://x/Organisation", "http://x/Agent")
    assert compare_facets(base, narrower, is_subclass=is_subclass).facets[0].status == "tightened"
    assert compare_facets(narrower, base, is_subclass=is_subclass).facets[0].status == "loosened"
    unknown = compare_facets(base, ShapeFacets(classes={"http://x/Thing"}), is_subclass=is_subclass)
    assert unknown.facets[0].status == "incomparable" and unknown.is_legal


def test_datatype_and_node_kind_conflicts():
    xsd = "http://www.w3.org/2001/XMLSchema#"
    clash = compare_facets(ShapeFacets(datatypes={xsd + "date"}), ShapeFacets(datatypes={xsd + "string"}))
    assert clash.conflicts[0].facet == "range_datatype"
    kinds = compare_facets(ShapeFacets(node_kind="Literal"), ShapeFacets(node_kind="IRI"))
    assert kinds.conflicts[0].facet == "node_kind"
    wider = compare_facets(ShapeFacets(node_kind="IRI"), ShapeFacets(node_kind="BlankNodeOrIRI"))
    assert wider.loosened[0].facet == "node_kind"


def test_value_lists():
    base = ShapeFacets(in_values=frozenset({"a", "b"}))
    assert compare_facets(base, ShapeFacets(in_values=frozenset({"a"}))).status == "tightened"
    assert compare_facets(base, ShapeFacets(in_values=frozenset({"a", "c"}))).loosened[0].facet == "controlled_vocabulary"
    assert compare_facets(base, ShapeFacets(in_values=frozenset({"z"}))).conflicts[0].facet == "controlled_vocabulary"


def test_obligation_levels():
    assert compare_obligation("recommended", "mandatory").status == "tightened"
    assert compare_obligation("mandatory", "optional").status == "loosened"
    assert compare_obligation(None, "recommended").status == "added"
    assert compare_obligation("optional", "optional").status == "unchanged"
    assert compare_obligation("mandatory", "unknown") is None


def test_facets_roundtrip_to_contract():
    shape = ShapeFacets(min_count=1, max_count=3, classes={"http://x/B", "http://x/A"}, node_kind="IRI",
                        in_values=frozenset({"http://v/2", "http://v/1"}))
    facets = shape.to_facets("mandatory")
    assert facets.range_class == "http://x/A" and facets.controlled_vocabulary == ["http://v/1", "http://v/2"]
    back = ShapeFacets.from_facets(facets, "Violation")
    assert back.min_count == 1 and back.max_count == 3 and back.node_kind == "IRI" and back.classes == {"http://x/A"}
