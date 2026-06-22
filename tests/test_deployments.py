from fastapi.testclient import TestClient

from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def _write_predictions_csv(path):
    path.write_text("id,true,pred\n1,cat,cat\n2,dog,dog\n3,cat,dog\n")


def _setup_project(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )
    predictions_path = tmp_path / "predictions.csv"
    _write_predictions_csv(predictions_path)
    evaluation = project.experiments.evaluations.create(
        run_id="r1",
        predictions_path=str(predictions_path),
        name="eval-1",
    )
    return project, run, evaluation


def test_create_deployment_from_evaluation(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)

    res = client.post(
        "/api/deployments",
        json={"target": "local", "evaluation_id": evaluation["id"], "config": {"port": 8000}},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["target"] == "local"
    assert data["evaluation_id"] == evaluation["id"]
    assert data["run_id"] == run["id"]
    assert data["status"] == "pending"


def test_list_deployments_by_evaluation(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    project.experiments.deployments.create(target="cloud", evaluation_id=evaluation["id"])

    app = create_app(project=project)
    client = TestClient(app)

    res = client.get(f"/api/deployments?evaluation_id={evaluation['id']}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["target"] == "cloud"


def test_delete_deployment(tmp_path, monkeypatch):
    project, _, evaluation = _setup_project(tmp_path, monkeypatch)
    deployment = project.experiments.deployments.create(target="local", evaluation_id=evaluation["id"])

    app = create_app(project=project)
    client = TestClient(app)

    res = client.delete(f"/api/deployments/{deployment['id']}")
    assert res.status_code == 200
    assert res.json() == {"deleted": True}

    res = client.get(f"/api/deployments/{deployment['id']}")
    assert res.status_code == 404


def test_create_deployment_requires_target(tmp_path, monkeypatch):
    project, _, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/deployments", json={"target": "", "evaluation_id": evaluation["id"]})
    assert res.status_code == 400


def test_create_deployment_rejects_missing_evaluation(tmp_path, monkeypatch):
    project, _, _ = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/deployments", json={"target": "local", "evaluation_id": "missing"})
    assert res.status_code == 400
