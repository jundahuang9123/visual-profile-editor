"""End to end with the offline provider: pipeline stages, decision policy, human actions, conformance, API."""
import os
import tempfile
from pathlib import Path

import pytest
from rdflib import Graph

os.environ.setdefault("RBDPE_WORKSPACE", tempfile.mkdtemp(prefix="rbdpe-test-"))

from profile_extensioner.contracts import Project  # noqa: E402
from profile_extensioner.engine.intake import parse_atom_set  # noqa: E402
from profile_extensioner.engine.pipeline import Pipeline  # noqa: E402
from profile_extensioner.llm.registry import Credentials  # noqa: E402
from profile_extensioner.store.blackboard import Store  # noqa: E402

DEMO = Path(__file__).resolve().parents[1] / "examples" / "materials-testing-lab" / "atoms.yaml"
DCT = "http://purl.org/dc/terms/"


@pytest.fixture(scope="module")
def pipeline():
    store = Store()
    store.save_project(Project(id="p1", name="Lab", profile_namespace="https://example.org/lab#", profile_prefix="lab"))
    store.replace_atoms("p1", parse_atom_set(DEMO.read_text(encoding="utf-8")).atoms)
    pipe = Pipeline(store, Credentials(), "p1")
    pipe.run_all()
    return pipe


def by_atom(pipe, atom_id):
    return [c for c in pipe.changes() if atom_id in c.atom_ids and c.decision.status != "superseded"]


def test_every_stage_ran_and_left_a_log(pipeline):
    states = pipeline.project.stage_states
    for stage in ("intake", "retrieve", "propose", "verify", "repair", "consolidate", "compile", "conformance"):
        assert states[stage] == "done", stage
    stages = {entry.stage for entry in pipeline.store.list_entries("p1", limit=10000)}
    assert {"intake", "retrieve", "propose", "verify", "compile", "conformance"} <= stages


def test_dispositions_against_the_base(pipeline):
    coverage = pipeline.coverage()
    assert coverage["lab-01"] == "covered_by_base"        # the base already makes the title mandatory
    assert coverage["lab-15"] == "out_of_scope"           # "portal" is not a class of the base
    assert "lab-02-cf" not in coverage                    # inactive counterfactual


def test_tightening_is_auto_accepted_and_traced(pipeline):
    [change] = by_atom(pipeline, "lab-03")
    assert change.kind == "refine_property" and change.path == DCT + "license"
    assert change.decision.status == "auto_accepted" and change.included
    assert change.covers[0].evidence_quote and change.covers[0].evidence_quote.lower() in pipeline.store.get_atom("p1", "lab-03").statement.lower()
    obligation = next(j for j in change.facet_justifications if j.facet == "obligation")
    assert (obligation.base_value, obligation.new_value, obligation.status) == ("recommended", "mandatory", "tightened")


def test_low_confidence_mints_wait_for_a_human(pipeline):
    mints = [c for c in pipeline.changes() if c.kind == "mint_property" and c.decision.status != "superseded"]
    assert mints and all(c.decision.status == "needs_review" for c in mints)
    assert all(c.mint and c.mint.reason_no_reuse for c in mints)
    assert all(c.path.startswith("https://example.org/lab#") for c in mints)


def test_artifacts_parse_and_carry_the_trace(pipeline):
    names = {a.name: a for a in pipeline.store.list_artifacts("p1")}
    assert {"extension.shacl.ttl", "extension.linkml.yaml", "extension.dsv.ttl", "trace-matrix.csv", "README.md"} <= set(names)
    shapes = Graph().parse(data=names["extension.shacl.ttl"].content, format="turtle")
    assert len(shapes) > 0
    assert "wasDerivedFrom" in names["extension.shacl.ttl"].content
    Graph().parse(data=names["extension.dsv.ttl"].content, format="turtle")
    assert "lab-03" in names["trace-matrix.csv"].content


def test_conformance_report(pipeline):
    report = pipeline.store.get_conformance("p1")
    assert report.verdict == "conformant"
    assert {c.id for c in report.checks} == {"C1", "C2", "C3", "C4", "C5", "C6", "C7"}
    assert report.delta_counts["loosened"] == 0


def test_human_review_signoff_and_staleness(pipeline):
    with pytest.raises(ValueError):
        pipeline.sign_off("junda")                          # open review items block the release
    for change in pipeline.changes():
        if change.decision.status == "needs_review":
            pipeline.decide(change.id, "accepted", "junda", "checked")
    assert pipeline.project.stage_states["conformance"] == "stale"
    with pytest.raises(ValueError):
        pipeline.sign_off("junda")                          # conformance must be re-run first
    pipeline.run_conformance()
    signoff = pipeline.sign_off("junda", "first release")
    assert signoff.change_set_hash
    readme = pipeline.store.get_artifact("p1", "README.md").content
    assert "Released by junda" in readme
    # a later decision withdraws the release
    some = next(c for c in pipeline.changes() if c.included)
    pipeline.decide(some.id, "rejected", "junda", "changed my mind")
    assert pipeline.project.signoff is None


def test_human_edit_creates_a_verified_new_version(pipeline):
    change = next(c for c in pipeline.changes() if c.kind == "refine_property" and c.included)
    edited = change.model_copy(deep=True)
    edited.facets.obligation = "optional"                   # would loosen the base -> V3 must say so
    new = pipeline.edit_change(change.id, edited, "junda", "testing a loosening")
    assert new.supersedes == change.id and new.decision.status == "accepted"
    assert any(r.check == "V3" and not r.passed for r in new.verification)
    assert pipeline.store.get_change("p1", change.id).decision.status == "superseded"


def test_api_flow():
    from fastapi.testclient import TestClient

    from profile_extensioner.api.app import app

    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    assert "dcat-ap-3.0.1" in {b["id"] for b in client.get("/api/base-profiles").json()}
    created = client.post("/api/projects", json={
        "name": "API demo", "example": "materials-testing-lab",
        "profile_namespace": "https://example.org/lab#", "profile_prefix": "lab"}).json()
    pid = created["id"]
    snap = client.post(f"/api/projects/{pid}/run", json={"from_stage": "intake"}).json()
    assert snap["conformance"]["verdict"] in ("conformant", "conformant_with_warnings")
    assert snap["verbalised"]
    status = client.post("/api/llm/key", json={"provider": "anthropic", "api_key": "sk-ant-test-secret"}).json()
    assert "sk-ant-test-secret" not in str(status)
    export = client.get(f"/api/projects/{pid}/export").json()
    assert "sk-ant-test-secret" not in str(export) and export["entries"]
    shacl = client.get(f"/api/projects/{pid}/artifacts/extension.shacl.ttl")
    assert shacl.status_code == 200 and "sh:" in shacl.text or "shacl" in shacl.text
    terms = client.get("/api/terms", params={"project_id": pid, "q": "licence"}).json()
    assert terms and terms[0]["curie"].startswith("dcterms:")
