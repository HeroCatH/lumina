import csv
import uuid
from pathlib import Path

import pytest

from lumina.experiments.service import EvaluationService
from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import ProjectRepository, RunRepository


def _write_predictions_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "true", "pred", "confidence"])
        writer.writeheader()
        writer.writerows(rows)


def _setup_db_and_run(project_path: Path):
    conn = get_db(project_path / "test.db")
    init_schema(conn)
    projects = ProjectRepository(conn)
    project = projects.create(name="test-project", path=str(project_path))
    runs = RunRepository(conn)
    run_id = str(uuid.uuid4())
    runs.create(run_id=run_id, project_id=project["id"], name="test-run", source="sdk")
    return conn, project["id"], run_id


def test_evaluation_service_create(tmp_path: Path):
    conn, project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    predictions_file = tmp_path / "preds.csv"
    _write_predictions_csv(
        predictions_file,
        [
            {"id": "s1", "true": "a", "pred": "a", "confidence": "0.9"},
            {"id": "s2", "true": "b", "pred": "a", "confidence": "0.4"},
        ],
    )

    evaluation = service.create(run_id=run_id, predictions_path=predictions_file)

    assert "id" in evaluation
    assert evaluation["run_id"] == run_id
    assert evaluation["dataset_id"] is None
    assert evaluation["name"] == "preds.csv"
    assert evaluation["task_type"] == "classification"
    assert evaluation["predictions_path"].endswith(f"evaluations/{evaluation['id']}/predictions.csv")
    assert "metrics" in evaluation
    assert "created_at" in evaluation

    local_path = tmp_path / "evaluations" / evaluation["id"] / "predictions.csv"
    assert local_path.exists()


def test_evaluation_service_create_with_name_and_task_type(tmp_path: Path):
    conn, _project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    predictions_file = tmp_path / "preds.csv"
    _write_predictions_csv(
        predictions_file,
        [
            {"id": "s1", "true": "1.5", "pred": "1.4", "confidence": ""},
            {"id": "s2", "true": "2.0", "pred": "2.1", "confidence": ""},
        ],
    )

    evaluation = service.create(
        run_id=run_id,
        predictions_path=predictions_file,
        name="my-eval",
        task_type="regression",
    )

    assert evaluation["name"] == "my-eval"
    assert evaluation["task_type"] == "regression"


def test_evaluation_service_get(tmp_path: Path):
    conn, _project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    predictions_file = tmp_path / "preds.csv"
    _write_predictions_csv(
        predictions_file,
        [
            {"id": "s1", "true": "a", "pred": "a", "confidence": "0.9"},
        ],
    )

    evaluation = service.create(run_id=run_id, predictions_path=predictions_file)

    found = service.get(evaluation["id"])
    assert found is not None
    assert found["id"] == evaluation["id"]
    assert "predictions" not in found

    with_predictions = service.get(evaluation["id"], include_predictions=True)
    assert with_predictions is not None
    assert len(with_predictions["predictions"]) == 1
    assert with_predictions["predictions"][0]["sample_id"] == "s1"

    missing = service.get("does-not-exist")
    assert missing is None


def test_evaluation_service_list_by_project_and_run(tmp_path: Path):
    conn, project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    predictions_file = tmp_path / "preds.csv"
    _write_predictions_csv(
        predictions_file,
        [
            {"id": "s1", "true": "a", "pred": "a", "confidence": "0.9"},
        ],
    )

    evaluation = service.create(run_id=run_id, predictions_path=predictions_file)

    by_project = service.list_by_project(project_id)
    assert len(by_project) == 1
    assert by_project[0]["id"] == evaluation["id"]

    by_run = service.list_by_run(run_id)
    assert len(by_run) == 1
    assert by_run[0]["id"] == evaluation["id"]


def test_evaluation_service_delete(tmp_path: Path):
    conn, _project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    predictions_file = tmp_path / "preds.csv"
    _write_predictions_csv(
        predictions_file,
        [
            {"id": "s1", "true": "a", "pred": "a", "confidence": "0.9"},
        ],
    )

    evaluation = service.create(run_id=run_id, predictions_path=predictions_file)
    evaluation_id = evaluation["id"]
    eval_dir = tmp_path / "evaluations" / evaluation_id

    assert eval_dir.exists()
    assert service.get(evaluation_id) is not None

    deleted = service.delete(evaluation_id)
    assert deleted is True
    assert service.get(evaluation_id) is None
    assert not eval_dir.exists()

    deleted_again = service.delete(evaluation_id)
    assert deleted_again is False


def test_evaluation_service_create_missing_file(tmp_path: Path):
    conn, _project_id, run_id = _setup_db_and_run(tmp_path)
    service = EvaluationService(conn, tmp_path)

    with pytest.raises(ValueError):
        service.create(run_id=run_id, predictions_path=tmp_path / "missing.csv")
