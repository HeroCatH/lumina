import json
from pathlib import Path

from fastapi.testclient import TestClient

from lumina.core.project_manager import ProjectManager
from lumina.server import create_app


def test_evaluations_end_to_end_classification(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("p1")
        run = project.experiments.runs.create(
            run_id="run-1", project_id=project.id, name="run-1", source="sdk"
        )

        csv = tmp_path / "pred.csv"
        csv.write_text("id,true,pred,confidence\n0,0,0,0.9\n1,1,0,0.6\n2,1,1,0.8\n3,2,2,0.95\n")

        app = create_app(project=project)
        client = TestClient(app)

        res = client.post("/api/evaluations", json={
            "run_id": run["id"],
            "predictions_path": str(csv),
            "name": "cls-eval",
        })
        assert res.status_code == 201
        evaluation = res.json()
        assert evaluation["run_id"] == run["id"]
        assert evaluation["task_type"] == "classification"
        assert evaluation["name"] == "cls-eval"

        metrics = json.loads(evaluation["metrics"])
        assert metrics["accuracy"] == 0.75

        res = client.get("/api/evaluations")
        assert res.status_code == 200
        assert len(res.json()) == 1

        res = client.get(f"/api/evaluations/{evaluation['id']}?include_predictions=true")
        assert res.status_code == 200
        detail = res.json()
        assert detail["id"] == evaluation["id"]
        assert len(detail["predictions"]) == 4
        assert detail["predictions"][0]["is_correct"] == 1

        res = client.delete(f"/api/evaluations/{evaluation['id']}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        res = client.get("/api/evaluations")
        assert res.status_code == 200
        assert res.json() == []


def test_evaluations_end_to_end_regression(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("p1")
        run = project.experiments.runs.create(
            run_id="run-1", project_id=project.id, name="run-1", source="sdk"
        )

        csv = tmp_path / "reg.csv"
        csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n2,3.0,3.2\n")

        app = create_app(project=project)
        client = TestClient(app)

        res = client.post("/api/evaluations", json={
            "run_id": run["id"],
            "predictions_path": str(csv),
            "task_type": "regression",
        })
        assert res.status_code == 201
        evaluation = res.json()
        assert evaluation["task_type"] == "regression"
        metrics = json.loads(evaluation["metrics"])
        assert "mae" in metrics
        assert "rmse" in metrics

        res = client.get(f"/api/evaluations/{evaluation['id']}")
        assert res.status_code == 200
        detail = res.json()
        assert "predictions" not in detail
