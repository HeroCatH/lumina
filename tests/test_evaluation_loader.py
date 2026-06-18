import json
from pathlib import Path

import pytest

from lumina.experiments.evaluation_loader import EvaluationLoader


def test_classification_metrics(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n2,dog,dog,0.8\n3,cat,dog,0.7\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "classification"
    metrics = json.loads(result["metrics"])
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert "confusion_matrix" in metrics
    assert metrics["confusion_matrix"]["cat"]["cat"] == 1
    assert len(result["predictions"]) == 4
    assert result["predictions"][0]["is_correct"] == 1
    assert result["predictions"][1]["is_correct"] == 0
    assert result["predictions"][0]["confidence"] == 0.9


def test_regression_metrics(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n2,3.0,3.2\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "regression"
    metrics = json.loads(result["metrics"])
    assert "mae" in metrics
    assert "rmse" in metrics
    assert metrics["r2"] is not None


def test_task_type_override(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1,2\n1,2,3\n")

    result = EvaluationLoader.load(csv, task_type="regression")
    assert result["task_type"] == "regression"


def test_invalid_task_type(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1,2\n")

    with pytest.raises(ValueError, match="Unsupported task_type"):
        EvaluationLoader.load(csv, task_type="unknown")


def test_missing_columns(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,pred\n0,cat\n")

    with pytest.raises(ValueError, match="Missing required columns"):
        EvaluationLoader.load(csv)


def test_confidence_tolerates_invalid_value(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred,confidence\n0,cat,cat,high\n")

    result = EvaluationLoader.load(csv)
    assert result["predictions"][0]["confidence"] is None


def test_regression_is_correct_uses_numeric_comparison(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1.0,1.00\n1,2.0,2.0\n")

    result = EvaluationLoader.load(csv, task_type="regression")
    assert result["predictions"][0]["is_correct"] == 1


def test_decimal_values_infer_regression(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n3,3.0,3.0\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "regression"


def test_empty_csv_raises(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n")

    with pytest.raises(ValueError):
        EvaluationLoader.load(csv)
