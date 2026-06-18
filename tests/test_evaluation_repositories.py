import sqlite3
import uuid
from pathlib import Path

import pytest

from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import (
    DatasetRepository,
    EvaluationRepository,
    PredictionRepository,
    ProjectRepository,
    RunRepository,
)


def make_db(tmp_path: Path) -> tuple:
    db_path = tmp_path / "test.db"
    conn = get_db(db_path)
    init_schema(conn)
    run_repo = RunRepository(conn)
    eval_repo = EvaluationRepository(conn)
    pred_repo = PredictionRepository(conn)
    return conn, run_repo, eval_repo, pred_repo


def _create_run(run_repo: RunRepository, run_id: str = "run-1") -> dict:
    return run_repo.create(run_id=run_id, project_id=None, name="test-run")


def test_create_evaluation_without_predictions(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-1"
    record = eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-one",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{"accuracy": 0.9}',
    )

    assert record["id"] == evaluation_id
    assert record["run_id"] == "run-1"
    assert record["dataset_id"] is None
    assert record["name"] == "eval-one"
    assert record["task_type"] == "classification"
    assert record["predictions_path"] == "/tmp/preds.json"
    assert record["metrics"] == '{"accuracy": 0.9}'
    assert "created_at" in record


def test_create_evaluation_with_predictions(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-2"
    predictions = [
        {"sample_id": "s1", "true_value": "a", "pred_value": "a", "confidence": 0.9, "is_correct": 1},
        {"sample_id": "s2", "true_value": "b", "pred_value": "c", "confidence": 0.6, "is_correct": 0},
    ]
    record = eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-two",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{"accuracy": 0.5}',
        predictions=predictions,
    )

    assert record["id"] == evaluation_id
    stored = pred_repo.list_by_evaluation(evaluation_id)
    assert len(stored) == 2
    assert stored[0]["sample_id"] == "s1"
    assert stored[1]["sample_id"] == "s2"
    assert stored[0]["is_correct"] == 1
    assert stored[1]["is_correct"] == 0


def test_create_evaluation_with_predictions_without_confidence(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    predictions = [
        {"sample_id": "s1", "true_value": "0", "pred_value": "0", "is_correct": 1},
        {"sample_id": "s2", "true_value": "1", "pred_value": "0", "is_correct": 0},
    ]
    evaluation = eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=None,
        name="no-conf",
        task_type="classification",
        predictions_path="/tmp/no_conf.csv",
        metrics_json='{"accuracy": 0.5}',
        predictions=predictions,
    )

    preds = PredictionRepository(_conn).list_by_evaluation(evaluation["id"])
    assert len(preds) == 2
    assert preds[0]["confidence"] is None
    assert preds[1]["confidence"] is None


def test_get_evaluation(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-get"
    eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-get",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )

    found = eval_repo.get(evaluation_id)
    assert found is not None
    assert found["name"] == "eval-get"

    missing = eval_repo.get("does-not-exist")
    assert missing is None


def test_list_by_run(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo, run_id="run-a")
    _create_run(run_repo, run_id="run-b")

    eval_repo.create(
        evaluation_id="eval-a1",
        run_id="run-a",
        dataset_id=None,
        name="first",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )
    eval_repo.create(
        evaluation_id="eval-a2",
        run_id="run-a",
        dataset_id=None,
        name="second",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )
    eval_repo.create(
        evaluation_id="eval-b1",
        run_id="run-b",
        dataset_id=None,
        name="other-run",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )

    # Force deterministic ordering without sleeping.
    _conn.execute(
        "UPDATE evaluations SET created_at = ? WHERE id = ?",
        ("2026-01-01 00:00:00", "eval-a1"),
    )
    _conn.execute(
        "UPDATE evaluations SET created_at = ? WHERE id = ?",
        ("2026-01-02 00:00:00", "eval-a2"),
    )
    _conn.commit()

    results = eval_repo.list_by_run("run-a")
    assert [r["id"] for r in results] == ["eval-a2", "eval-a1"]

    # Exclusion check: unrelated run's evaluation is not included.
    assert not any(r["id"] == "eval-b1" for r in results)


def test_delete_evaluation_cascades_predictions(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-delete"
    predictions = [
        {"sample_id": "s1", "true_value": "a", "pred_value": "a", "confidence": 0.9, "is_correct": 1},
    ]
    eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-delete",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
        predictions=predictions,
    )

    assert pred_repo.count_by_evaluation(evaluation_id) == 1
    deleted = eval_repo.delete(evaluation_id)
    assert deleted is True
    assert eval_repo.get(evaluation_id) is None
    assert pred_repo.count_by_evaluation(evaluation_id) == 0

    deleted_again = eval_repo.delete(evaluation_id)
    assert deleted_again is False


def test_prediction_create_many_count_accuracy(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-preds"
    eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-preds",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )

    predictions = [
        {"sample_id": "s1", "true_value": "a", "pred_value": "a", "confidence": 0.9, "is_correct": 1},
        {"sample_id": "s2", "true_value": "b", "pred_value": "a", "confidence": 0.4, "is_correct": 0},
        {"sample_id": "s3", "true_value": "c", "pred_value": "c", "confidence": 0.8, "is_correct": 1},
    ]
    inserted = pred_repo.create_many(evaluation_id, predictions)
    assert inserted == 3

    count = pred_repo.count_by_evaluation(evaluation_id)
    assert count == 3

    accuracy = pred_repo.accuracy_for_evaluation(evaluation_id)
    assert accuracy == pytest.approx(2 / 3)

    # Verify ordering by id
    stored = pred_repo.list_by_evaluation(evaluation_id)
    assert [r["sample_id"] for r in stored] == ["s1", "s2", "s3"]


def test_prediction_accuracy_none_when_empty(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-empty"
    eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-empty",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )

    assert pred_repo.accuracy_for_evaluation(evaluation_id) is None
    assert pred_repo.count_by_evaluation(evaluation_id) == 0


def test_prediction_create_single(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-single"
    eval_repo.create(
        evaluation_id=evaluation_id,
        run_id="run-1",
        dataset_id=None,
        name="eval-single",
        task_type="classification",
        predictions_path="/tmp/preds.json",
        metrics_json='{}',
    )

    record = pred_repo.create(
        evaluation_id=evaluation_id,
        sample_id="x",
        true_value="yes",
        pred_value="no",
        confidence=0.75,
        is_correct=0,
    )
    assert record["evaluation_id"] == evaluation_id
    assert record["sample_id"] == "x"
    assert record["true_value"] == "yes"
    assert record["pred_value"] == "no"
    assert record["confidence"] == pytest.approx(0.75)
    assert record["is_correct"] == 0
    assert "id" in record


def test_create_evaluation_rolls_back_on_bad_predictions(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = "eval-bad-preds"
    bad_predictions = [
        {"sample_id": "s1", "true_value": "0", "pred_value": "0", "is_correct": 1},
        {"sample_id": "s2"},  # missing keys
    ]

    with pytest.raises(ValueError):
        eval_repo.create(
            evaluation_id=evaluation_id,
            run_id="run-1",
            dataset_id=None,
            name="bad",
            task_type="classification",
            predictions_path="/tmp/bad.csv",
            metrics_json='{"accuracy": 0.5}',
            predictions=bad_predictions,
        )

    assert eval_repo.get(evaluation_id) is None
    assert pred_repo.list_by_evaluation(evaluation_id) == []


def test_list_by_dataset(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    projects = ProjectRepository(_conn)
    project = projects.create(name="test-project", path="/tmp/proj")

    datasets = DatasetRepository(_conn)
    dataset1 = datasets.create(
        project_id=project["id"],
        name="ds1",
        path="/tmp/ds1.csv",
        adapter_type="csv",
    )
    dataset2 = datasets.create(
        project_id=project["id"],
        name="ds2",
        path="/tmp/ds2.csv",
        adapter_type="csv",
    )

    e1 = eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=dataset1["id"],
        name="eval1",
        task_type="classification",
        predictions_path="/tmp/e1.csv",
        metrics_json='{"accuracy": 0.8}',
    )
    eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=dataset2["id"],
        name="eval2",
        task_type="classification",
        predictions_path="/tmp/e2.csv",
        metrics_json='{"accuracy": 0.9}',
    )
    eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=None,
        name="eval3",
        task_type="classification",
        predictions_path="/tmp/e3.csv",
        metrics_json='{"accuracy": 0.95}',
    )

    results = eval_repo.list_by_dataset(dataset1["id"])
    assert len(results) == 1
    assert results[0]["id"] == e1["id"]


def test_list_by_project(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)

    projects = ProjectRepository(_conn)
    project1 = projects.create(name="proj1", path="/tmp/proj1")
    project2 = projects.create(name="proj2", path="/tmp/proj2")

    run1_id = str(uuid.uuid4())
    run2_id = str(uuid.uuid4())
    run_repo.create(run_id=run1_id, project_id=project1["id"], name="test1", source="sdk")
    run_repo.create(run_id=run2_id, project_id=project2["id"], name="test2", source="sdk")

    e1 = eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id=run1_id,
        dataset_id=None,
        name="eval1",
        task_type="classification",
        predictions_path="/tmp/e1.csv",
        metrics_json='{"accuracy": 0.8}',
    )
    eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id=run2_id,
        dataset_id=None,
        name="eval2",
        task_type="classification",
        predictions_path="/tmp/e2.csv",
        metrics_json='{"accuracy": 0.9}',
    )

    results = eval_repo.list_by_project(project1["id"])
    assert len(results) == 1
    assert results[0]["id"] == e1["id"]


def test_create_evaluation_rolls_back_after_partial_prediction_insert(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation_id = str(uuid.uuid4())
    bad_predictions = [
        {"sample_id": "s1", "true_value": "0", "pred_value": "0", "is_correct": 1},
        {"sample_id": "s2", "true_value": "1", "pred_value": "1", "is_correct": 1},
        {"sample_id": "s3"},  # missing keys; fails after two valid rows
    ]

    with pytest.raises(ValueError):
        eval_repo.create(
            evaluation_id=evaluation_id,
            run_id="run-1",
            dataset_id=None,
            name="bad",
            task_type="classification",
            predictions_path="/tmp/bad.csv",
            metrics_json='{"accuracy": 0.5}',
            predictions=bad_predictions,
        )

    assert eval_repo.get(evaluation_id) is None
    assert pred_repo.list_by_evaluation(evaluation_id) == []


def test_prediction_create_with_none_confidence(tmp_path):
    _conn, run_repo, eval_repo, _pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation = eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=None,
        name="eval",
        task_type="classification",
        predictions_path="/tmp/eval.csv",
        metrics_json='{"accuracy": 1.0}',
    )

    preds = PredictionRepository(_conn)
    pred = preds.create(
        evaluation_id=evaluation["id"],
        sample_id="s1",
        true_value="0",
        pred_value="0",
        confidence=None,
        is_correct=1,
    )
    assert pred["confidence"] is None


def test_create_evaluation_fails_for_missing_run(tmp_path):
    _conn, _run_repo, eval_repo, _pred_repo = make_db(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        eval_repo.create(
            evaluation_id=str(uuid.uuid4()),
            run_id="nonexistent-run",
            dataset_id=None,
            name="orphan",
            task_type="classification",
            predictions_path="/tmp/eval.csv",
            metrics_json='{"accuracy": 1.0}',
        )


def test_prediction_create_many_empty_list(tmp_path):
    _conn, run_repo, eval_repo, pred_repo = make_db(tmp_path)
    _create_run(run_repo)

    evaluation = eval_repo.create(
        evaluation_id=str(uuid.uuid4()),
        run_id="run-1",
        dataset_id=None,
        name="eval",
        task_type="classification",
        predictions_path="/tmp/eval.csv",
        metrics_json='{"accuracy": 1.0}',
    )

    count = pred_repo.create_many(evaluation_id=evaluation["id"], predictions=[])
    assert count == 0
    assert pred_repo.count_by_evaluation(evaluation["id"]) == 0
