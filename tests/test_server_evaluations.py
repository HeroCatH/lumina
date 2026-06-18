import json
from pathlib import Path

from fastapi.testclient import TestClient

from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def _write_predictions_csv(path: Path):
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


def test_list_evaluations_by_project(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/evaluations")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == evaluation["id"]


def test_list_evaluations_by_run(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get(f"/api/evaluations?run_id={run['id']}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["run_id"] == run["id"]

    res = client.get("/api/evaluations?run_id=missing")
    assert res.status_code == 404
    assert res.json()["detail"] == "Run not found"


def test_create_evaluation_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )
    predictions_path = tmp_path / "predictions.csv"
    _write_predictions_csv(predictions_path)

    app = create_app(project=project)
    client = TestClient(app)
    res = client.post(
        "/api/evaluations",
        json={
            "run_id": run["id"],
            "predictions_path": str(predictions_path),
            "dataset_id": None,
            "name": "created-eval",
            "task_type": "classification",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["run_id"] == run["id"]
    assert data["name"] == "created-eval"
    assert data["task_type"] == "classification"


def test_get_evaluation_endpoint(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)

    res = client.get(f"/api/evaluations/{evaluation['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == evaluation["id"]
    assert "predictions" not in data

    res = client.get(f"/api/evaluations/{evaluation['id']}?include_predictions=true")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == evaluation["id"]
    assert "predictions" in data
    assert len(data["predictions"]) == 3

    res = client.get("/api/evaluations/missing")
    assert res.status_code == 404
    assert res.json()["detail"] == "Evaluation not found"


def test_delete_evaluation_endpoint(tmp_path, monkeypatch):
    project, run, evaluation = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)

    res = client.delete(f"/api/evaluations/{evaluation['id']}")
    assert res.status_code == 200
    assert res.json() == {"deleted": True}

    res = client.get(f"/api/evaluations/{evaluation['id']}")
    assert res.status_code == 404

    res = client.delete("/api/evaluations/missing")
    assert res.status_code == 404
    assert res.json()["detail"] == "Evaluation not found"


def test_evaluation_endpoints_require_project(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    res = client.get("/api/evaluations")
    assert res.status_code == 404
    assert res.json()["detail"] == "No project loaded"

    res = client.post("/api/evaluations", json={"run_id": "r1", "predictions_path": "/tmp/x.csv"})
    assert res.status_code == 404
    assert res.json()["detail"] == "No project loaded"

    res = client.get("/api/evaluations/e1")
    assert res.status_code == 404
    assert res.json()["detail"] == "No project loaded"

    res = client.delete("/api/evaluations/e1")
    assert res.status_code == 404
    assert res.json()["detail"] == "No project loaded"


def test_create_evaluation_rejects_missing_predictions_file(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )

    app = create_app(project=project)
    client = TestClient(app)
    res = client.post(
        "/api/evaluations",
        json={
            "run_id": run["id"],
            "predictions_path": str(tmp_path / "does_not_exist.csv"),
        },
    )
    assert res.status_code == 400


def test_create_evaluation_rejects_missing_run(tmp_path, monkeypatch):
    project, _, _ = _setup_project(tmp_path, monkeypatch)
    predictions_csv = tmp_path / "predictions.csv"
    predictions_csv.write_text("id,true,pred\n0,0,0\n")

    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/evaluations", json={
        "run_id": "missing-run",
        "predictions_path": str(predictions_csv),
    })
    assert res.status_code == 400
    assert "run" in res.json()["detail"].lower() or "not found" in res.json()["detail"].lower()


def test_create_evaluation_with_dataset_and_regression(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    csv = tmp_path / "reg.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n")

    # Create a dataset record to satisfy FK
    dataset = project.datasets.create(
        project_id=project.id,
        name="ds",
        path="/tmp/ds.csv",
        adapter_type="csv",
    )

    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/evaluations", json={
        "run_id": run["id"],
        "predictions_path": str(csv),
        "dataset_id": dataset["id"],
        "task_type": "regression",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["task_type"] == "regression"
    assert data["dataset_id"] == dataset["id"]
    metrics = json.loads(data["metrics"])
    assert "mae" in metrics


def test_create_evaluation_rejects_invalid_task_type(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,0,0\n")

    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/evaluations", json={
        "run_id": run["id"],
        "predictions_path": str(csv),
        "task_type": "invalid",
    })
    assert res.status_code == 422


def test_create_evaluation_rejects_malformed_csv(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("id,true\n0,0\n")

    app = create_app(project=project)
    client = TestClient(app)

    res = client.post("/api/evaluations", json={
        "run_id": run["id"],
        "predictions_path": str(bad_csv),
    })
    assert res.status_code == 400


