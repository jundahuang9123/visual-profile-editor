"""The blackboard store keeps current state per object and an append-only log."""
from profile_extensioner.contracts import (
    Atom,
    AtomAssessment,
    BlackboardEntry,
    Candidate,
    CoverageLink,
    Decision,
    LLMCallRecord,
    ProfileChange,
    Project,
)
from profile_extensioner.store.blackboard import Store


def make_change(change_id: str, status: str = "proposed") -> ProfileChange:
    return ProfileChange(
        id=change_id,
        kind="reuse_property",
        target_class="http://www.w3.org/ns/dcat#Dataset",
        path="http://purl.org/dc/terms/bibliographicCitation",
        covers=[CoverageLink(atom_id="a1", reason="citation", evidence_quote="cite a dataset")],
        decision=Decision(status=status),  # type: ignore[arg-type]
    )


def test_project_roundtrip_and_listing():
    store = Store()
    store.save_project(Project(id="p1", name="Demo"))
    store.save_project(Project(id="p2", name="Other"))
    assert store.get_project("p1").name == "Demo"
    assert {project.id for project in store.list_projects()} == {"p1", "p2"}
    store.delete_project("p2")
    assert store.get_project("p2") is None


def test_atoms_keep_their_order_and_can_be_replaced():
    store = Store()
    atoms = [Atom(id=f"a{index}", statement=f"statement {index}") for index in range(5)]
    store.replace_atoms("p1", atoms)
    assert [atom.id for atom in store.list_atoms("p1")] == ["a0", "a1", "a2", "a3", "a4"]
    store.replace_atoms("p1", atoms[:2])
    assert [atom.id for atom in store.list_atoms("p1")] == ["a0", "a1"]


def test_changes_hide_superseded_by_default():
    store = Store()
    store.save_change("p1", make_change("c1", "superseded"))
    store.save_change("p1", make_change("c2", "auto_accepted"))
    assert [change.id for change in store.list_changes("p1")] == ["c2"]
    assert len(store.list_changes("p1", include_superseded=True)) == 2
    updated = store.get_change("p1", "c2")
    updated.decision.status = "accepted"
    store.save_change("p1", updated)
    assert store.get_change("p1", "c2").decision.status == "accepted"
    assert [change.id for change in store.list_changes("p1", include_superseded=True)] == ["c1", "c2"]


def test_entries_are_append_only_and_filterable():
    store = Store()
    first = store.append_entry("p1", BlackboardEntry(stage="propose", kind="proposal", subject_type="atom", subject_id="a1"))
    second = store.append_entry("p1", BlackboardEntry(stage="verify", kind="check", subject_type="change", subject_id="c1"))
    assert second.seq > first.seq
    assert [entry.kind for entry in store.list_entries("p1")] == ["proposal", "check"]
    assert [entry.kind for entry in store.list_entries("p1", stage="verify")] == ["check"]
    assert [entry.kind for entry in store.list_entries("p1", after_seq=first.seq)] == ["check"]
    assert store.list_entries("p1", subject_type="atom", subject_id="a1")[0].id == first.id


def test_assessments_candidates_and_call_cache():
    store = Store()
    store.save_assessment("p1", AtomAssessment(atom_id="a1", disposition="covered_by_base"))
    assert store.get_assessment("p1", "a1").disposition == "covered_by_base"
    store.save_candidates("p1", "a1", [Candidate(iri="http://purl.org/dc/terms/title", curie="dcterms:title", kind="property")])
    assert store.all_candidates("p1")["a1"][0].curie == "dcterms:title"
    store.add_llm_call("p1", LLMCallRecord(request_hash="h1", status="error", response_text=""))
    assert store.find_cached_call("h1") is None
    store.add_llm_call("p1", LLMCallRecord(request_hash="h1", status="ok", response_text="{}"))
    assert store.find_cached_call("h1").response_text == "{}"


def test_export_holds_state_and_log():
    store = Store()
    store.save_project(Project(id="p1", name="Demo"))
    store.replace_atoms("p1", [Atom(id="a1", statement="s")])
    store.save_change("p1", make_change("c1"))
    store.append_entry("p1", BlackboardEntry(stage="intake", kind="note"))
    exported = store.export_project("p1")
    assert exported["project"]["name"] == "Demo"
    assert len(exported["atoms"]) == 1 and len(exported["changes"]) == 1 and len(exported["entries"]) == 1
