import json
from pathlib import Path

from lumina.experiments.evaluation_loader import EvaluationLoader


def test_classification_metrics(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n2,dog,dog,0.8\n3,cat,dog,0.7\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "classification"
    metrics = json.loads(result["metrics"])
    assert "accuracy" in metrics
    assert metrics["accuracy"] == 0.5
    assert len(result["predictions"]) == 4


def test_regression_metrics(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n2,3.0,3.2\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "regression"
    metrics = json.loads(result["metrics"])
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
