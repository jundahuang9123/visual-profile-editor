"""Intake (lint, subject mapping, parsing) and retrieval on the demo atoms."""
from pathlib import Path

import pytest

from profile_extensioner.contracts import Atom
from profile_extensioner.engine.intake import lint_atom, parse_atom_set, run_intake, worded_modality
from profile_extensioner.engine.retrieve import query_tokens, retrieve_candidates
from profile_extensioner.knowledge import load_knowledge_base

DEMO = Path(__file__).resolve().parents[1] / "examples" / "materials-testing-lab" / "atoms.yaml"
DCAT = "http://www.w3.org/ns/dcat#"
DCT = "http://purl.org/dc/terms/"


@pytest.fixture(scope="module")
def kb():
    return load_knowledge_base("dcat-ap-3.0.1", profile_namespace="https://example.org/lab#", profile_prefix="lab")


@pytest.fixture(scope="module")
def demo():
    return parse_atom_set(DEMO.read_text(encoding="utf-8"))


def codes(atom: Atom) -> set[str]:
    return {issue.code for issue in lint_atom(atom)}


def test_demo_atom_set_follows_the_contract(demo):
    assert demo.benchmark_id == "demo-materials-testing-lab" and demo.base_profile_ids == ["dcat-ap-3.0.1"]
    assert len(demo.atoms) == 16 and len({atom.id for atom in demo.atoms}) == 16
    assert [atom.id for atom in demo.atoms if not atom.active] == ["lab-02-cf"]
    for atom in demo.atoms:
        assert not {"contains_iri", "contains_prefixed_name"} & codes(atom), atom.id


def test_lint_enforces_term_free_atoms():
    assert "contains_iri" in codes(Atom(id="x", statement="Datasets must use http://purl.org/dc/terms/license ."))
    assert "contains_prefixed_name" in codes(Atom(id="x", statement="Each dataset must have a dct:license value."))
    assert "subject_not_plain" in codes(Atom(id="x", statement="A dataset must have a title.", subject="dcat:Dataset"))


def test_lint_flags_compound_and_modality_problems():
    assert "compound" in codes(Atom(id="x", statement="A dataset must state its uncertainty and the calibration date.", modality="must"))
    assert "compound" not in codes(Atom(id="x", statement="Each distribution must state the format of its file.", modality="must"))
    assert "modality_mismatch" in codes(Atom(id="x", statement="A dataset should have a title.", modality="must"))
    assert "modality_unspecified" in codes(Atom(id="x", statement="Datasets carry a short title."))
    # a modal verb inside a relative clause does not change the modality of the main clause
    statement = "Each distribution must state the licence under which the file may be reused."
    assert worded_modality(statement) == "must"
    assert "modality_mismatch" not in codes(Atom(id="x", statement=statement, modality="must"))


def test_parse_accepts_contract_list_and_plain_statements():
    as_list = parse_atom_set('[{"id": "a", "statement": "A dataset must have a title.", "modality": "must"}]')
    assert as_list.atoms[0].modality == "must" and as_list.atoms[0].subject == "dataset"
    plain = parse_atom_set("atoms:\n  - Every dataset needs a licence.\n  - Files state their format.\n")
    assert [atom.id for atom in plain.atoms] == ["atom-001", "atom-002"]
    with pytest.raises(ValueError):
        parse_atom_set("atoms:\n  - {id: a, statement: one}\n  - {id: a, statement: two}\n")
    with pytest.raises(ValueError):
        parse_atom_set("title: nothing here")


def test_intake_maps_subjects_and_blocks_contract_violations(kb, demo):
    by_id = {assessment.atom_id: assessment for assessment in run_intake(demo.atoms, kb)}
    assert by_id["lab-03"].resource_class == DCAT + "Distribution"
    assert by_id["lab-13"].resource_class == DCAT + "Catalog"
    assert by_id["lab-15"].resource_class is None
    assert "subject_unmapped" in {issue.code for issue in by_id["lab-15"].lint}
    blocked = run_intake([Atom(id="bad", statement="Datasets must use dct:license for licences.")], kb)[0]
    assert blocked.disposition == "unclear"


def test_generic_requirement_words_do_not_drive_retrieval():
    focused, everything = query_tokens(Atom(id="x", statement="Every dataset must name the organisation responsible for it."))
    assert set(focused) < set(everything) and not {"dataset", "nam"} & set(focused)


@pytest.mark.parametrize("atom_id, expected_first", [
    ("lab-01", "dcterms:title"),
    ("lab-02", "dcterms:publisher"),
    ("lab-03", "dcterms:license"),
    ("lab-05", "dcat:byteSize"),
    ("lab-13", "dcterms:publisher"),
    ("lab-14", "dcat:endpointURL"),
])
def test_base_elements_are_retrieved_first_with_their_constraints(kb, demo, atom_id, expected_first):
    atom = next(atom for atom in demo.atoms if atom.id == atom_id)
    assessment = run_intake([atom], kb)[0]
    first = retrieve_candidates(atom, assessment, kb, top_k=5)[0]
    assert first.curie == expected_first and first.in_base_on_class and first.rank == 1
    assert first.base_facets is not None and first.base_facets.obligation in {"mandatory", "recommended", "optional"}
    assert "base profile defines it" in first.why


def test_a_matching_range_class_brings_in_its_property(kb, demo):
    atom = next(atom for atom in demo.atoms if atom.id == "lab-06")   # "... the testing standard ..."
    candidates = retrieve_candidates(atom, run_intake([atom], kb)[0], kb, top_k=5)
    conforms_to = next(candidate for candidate in candidates if candidate.curie == "dcterms:conformsTo")
    assert conforms_to.in_base_on_class and conforms_to.base_facets.obligation == "optional"
    assert any(candidate.curie == "dcterms:Standard" and candidate.kind == "class" for candidate in candidates)


def test_retrieval_is_deterministic_and_bounded(kb, demo):
    atom = demo.atoms[2]
    assessment = run_intake([atom], kb)[0]
    first = retrieve_candidates(atom, assessment, kb, top_k=3)
    again = retrieve_candidates(atom, assessment, kb, top_k=3)
    assert [c.iri for c in first] == [c.iri for c in again]
    assert sum(1 for c in first if c.kind == "property") <= 3
    assert [c.rank for c in first] == list(range(1, len(first) + 1))
