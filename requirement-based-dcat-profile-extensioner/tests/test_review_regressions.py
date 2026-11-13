"""Regressions for the bugs an independent code review found (one test per finding)."""
from pathlib import Path

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import SH

from profile_extensioner.compile.model import build_view
from profile_extensioner.compile.shacl import compile_shacl_graph
from profile_extensioner.contracts import CoverageLink, Decision, Facets, ProfileChange, Project
from profile_extensioner.engine.consolidate import consolidate
from profile_extensioner.engine.intake import parse_atom_set
from profile_extensioner.engine.pipeline import Pipeline
from profile_extensioner.llm.registry import Credentials
from profile_extensioner.store.blackboard import Store

DEMO = Path(__file__).resolve().parents[1] / "examples" / "materials-testing-lab" / "atoms.yaml"
DCAT, DCT = "http://www.w3.org/ns/dcat#", "http://purl.org/dc/terms/"


@pytest.fixture()
def pipe():
    store = Store()
    store.save_project(Project(id="p1", name="Lab", profile_namespace="https://example.org/lab#", profile_prefix="lab"))
    store.replace_atoms("p1", parse_atom_set(DEMO.read_text(encoding="utf-8")).atoms)
    pipeline = Pipeline(store, Credentials(), "p1")
    pipeline.run_all()
    return pipeline


def live(pipe):
    return [c for c in pipe.changes() if c.decision.status != "superseded"]


def release(pipe):
    for change in live(pipe):
        if change.decision.status == "needs_review":
            pipe.decide(change.id, "accepted", "rev")
    pipe.run_conformance()
    return pipe.sign_off("rev")


def test_stale_pipeline_copy_cannot_restore_a_withdrawn_signoff(pipe):
    release(pipe)
    runner = Pipeline(pipe.store, Credentials(), "p1")        # a run starts with its own copy
    some = next(c for c in live(pipe) if c.included)
    pipe.decide(some.id, "rejected", "rev")                     # meanwhile a person withdraws the release
    runner.run_compile()
    assert pipe.store.get_project("p1").signoff is None


def test_human_undecided_is_not_overwritten_by_verify(pipe):
    change = next(c for c in live(pipe) if c.decision.status == "auto_accepted")
    pipe.decide(change.id, "needs_review", "rev")
    pipe.run_verify()
    assert pipe.store.get_change("p1", change.id).decision.status == "needs_review"


def test_machine_withdrawal_does_not_block_reproposal(pipe):
    change = next(c for c in live(pipe) if c.atom_ids == ["lab-09"])
    change.decision = Decision(status="rejected", decided_by="llm:mock/rules-v1", note="withdrawn")
    pipe.store.save_change("p1", change)
    pipe.run_propose(["lab-09"])
    assert any(c.atom_ids == ["lab-09"] and c.decision.status == "proposed" for c in live(pipe))


def test_reproposing_one_atom_keeps_changes_that_cover_others(pipe):
    merged = next(c for c in live(pipe) if c.atom_ids == ["lab-07"])
    merged.covers.append(CoverageLink(atom_id="lab-08", reason="also", evidence_quote="publication"))
    pipe.store.save_change("p1", merged)
    pipe.run_propose(["lab-07"])
    assert pipe.store.get_change("p1", merged.id).decision.status != "superseded"


def test_consolidate_never_folds_away_human_decisions_or_different_value_lists():
    def change(cid, values, decided_by="rule:policy"):
        return ProfileChange(id=cid, kind="refine_property", target_class=DCAT + "Dataset", path=DCT + "accrualPeriodicity",
                             facets=Facets(obligation="optional", controlled_vocabulary=values),
                             covers=[CoverageLink(atom_id=cid, reason="r")],
                             decision=Decision(status="accepted" if decided_by.startswith("human") else "auto_accepted",
                                               decided_by=decided_by))
    changes, conflicts = consolidate([change("a", ["http://x/1"]), change("b", ["http://x/2"])])
    assert conflicts and "value list" in conflicts[0].description
    assert all(c.decision.status != "superseded" for c in changes)
    changes, conflicts = consolidate([change("a", [], "human:rev"), change("b", [], "human:rev")])
    assert conflicts and all(c.decision.status == "accepted" for c in changes)


def test_signoff_stays_current_and_reruns_withdraw_it(pipe):
    release(pipe)
    states = pipe.store.get_project("p1").stage_states
    assert states["conformance"] == "done" and states["review"] == "done"
    pipe.run_verify()                                           # a machine stage re-ran after release
    assert pipe.store.get_project("p1").signoff is None


def test_superseded_changes_cannot_be_decided_and_edit_ids_are_unique(pipe):
    change = next(c for c in live(pipe) if c.kind == "refine_property" and c.included)
    first = pipe.edit_change(change.id, change, "rev")
    with pytest.raises(ValueError):
        pipe.decide(change.id, "accepted", "rev")
    second = pipe.edit_change(first.id, first, "rev")
    assert second.id != first.id and second.supersedes == first.id


def test_only_recommended_is_advisory_in_shacl(pipe):
    change = ProfileChange(id="x", kind="refine_property", target_class=DCAT + "Dataset", path=DCT + "accrualPeriodicity",
                           facets=Facets(obligation="recommended", max_count=1, controlled_vocabulary=["http://x/1"]),
                           covers=[CoverageLink(atom_id="lab-01", reason="r")], decision=Decision(status="accepted", decided_by="human:rev"))
    view = build_view(pipe.project, pipe.kb, pipe.store.list_atoms("p1"), [change])
    graph = compile_shacl_graph(view)
    shapes = list(graph.subjects(SH.path, URIRef(DCT + "accrualPeriodicity")))
    binding = [s for s in shapes if (s, SH["in"], None) in graph]
    advisory = [s for s in shapes if (s, SH.severity, SH.Warning) in graph]
    assert binding and (binding[0], SH.severity, SH.Violation) in graph and (binding[0], SH.minCount, None) not in graph
    assert advisory and (advisory[0], SH.minCount, None) in graph
