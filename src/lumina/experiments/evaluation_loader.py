import csv
import json
from pathlib import Path
from typing import Literal


def _is_numeric(values: list[str]) -> bool:
    """Return True if every value in ``values`` can be parsed as a float."""
    try:
        [float(v) for v in values]
        return True
    except ValueError:
        return False


def _infer_task_type(true_values: list[str], pred_values: list[str]) -> Literal["classification", "regression"]:
    """Infer whether the predictions are for classification or regression.

    Heuristic:
      * If any value is not numeric, treat the task as classification.
      * If numeric values contain decimals (non-integer), treat the task as regression.
      * If all numeric values are integers with at most 20 unique values,
        treat the task as classification.
      * Otherwise (more than 20 unique integer values), treat the task as regression.

    This heuristic is simple and may misclassify ambiguous cases. Callers should
    pass ``task_type`` explicitly when the data type is known.
    """
    combined = true_values + pred_values
    if not _is_numeric(combined):
        return "classification"
    numeric = [float(v) for v in combined]
    if any(v != int(v) for v in numeric):
        return "regression"
    unique_count = len(set(numeric))
    if unique_count <= 20:
        return "classification"
    return "regression"


def _compute_classification_metrics(true_values: list[str], pred_values: list[str]) -> dict:
    """Compute accuracy, macro precision/recall/F1, per-class metrics and a confusion matrix."""
    from collections import Counter

    correct = sum(1 for t, p in zip(true_values, pred_values) if t == p)
    total = len(true_values)
    accuracy = correct / total if total else 0.0

    labels = sorted(set(true_values) | set(pred_values))
    confusion = {label: {l: 0 for l in labels} for label in labels}
    for t, p in zip(true_values, pred_values):
        confusion[t][p] += 1

    per_class = {}
    true_counts = Counter(true_values)
    pred_counts = Counter(pred_values)
    for label in labels:
        tp = sum(1 for t, p in zip(true_values, pred_values) if t == label and p == label)
        fp = pred_counts[label] - tp
        fn = true_counts[label] - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1}

    macro_precision = sum(c["precision"] for c in per_class.values()) / len(labels) if labels else 0.0
    macro_recall = sum(c["recall"] for c in per_class.values()) / len(labels) if labels else 0.0
    macro_f1 = sum(c["f1"] for c in per_class.values()) / len(labels) if labels else 0.0

    return {
        "accuracy": accuracy,
        "precision": macro_precision,
        "recall": macro_recall,
        "f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": confusion,
    }


def _compute_regression_metrics(true_values: list[str], pred_values: list[str]) -> dict:
    """Compute MAE, RMSE and R² for regression predictions.

    Returns ``None`` for R² when the ground truth is constant (``ss_tot == 0``),
    since the score is undefined in that case.
    """
    y_true = [float(v) for v in true_values]
    y_pred = [float(v) for v in pred_values]
    n = len(y_true)
    errors = [yt - yp for yt, yp in zip(y_true, y_pred)]
    mae = sum(abs(e) for e in errors) / n
    rmse = (sum(e ** 2 for e in errors) / n) ** 0.5
    mean_true = sum(y_true) / n
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    ss_tot = sum((yt - mean_true) ** 2 for yt in y_true)
    r2 = None if ss_tot == 0 else 1 - ss_res / ss_tot
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


class EvaluationLoader:
    REQUIRED_COLUMNS = {"id", "true", "pred"}

    @classmethod
    def load(cls, path: Path, task_type: str | None = None) -> dict:
        """Load a prediction CSV and return task type, metrics and per-sample predictions.

        The CSV must contain ``id``, ``true`` and ``pred`` columns. An optional
        ``confidence`` column is supported; non-numeric confidence values are
        returned as ``None`` instead of raising.

        Args:
            path: Path to the CSV file.
            task_type: Optional override (``"classification"`` or ``"regression"``).
                       When omitted, the task type is inferred from the values.
        """
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header")
            missing = cls.REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise ValueError(f"Missing required columns: {sorted(missing)}")
            rows = list(reader)

        ids = [r["id"] for r in rows]
        true_values = [r["true"] for r in rows]
        pred_values = [r["pred"] for r in rows]
        confidences = [r.get("confidence") for r in rows]

        inferred = task_type or _infer_task_type(true_values, pred_values)
        if inferred == "classification":
            metrics = _compute_classification_metrics(true_values, pred_values)
        elif inferred == "regression":
            metrics = _compute_regression_metrics(true_values, pred_values)
        else:
            raise ValueError(f"Unsupported task_type: {inferred}")

        predictions = []
        for i, row in enumerate(rows):
            confidence_value = confidences[i]
            parsed_confidence = None
            if confidence_value not in (None, ""):
                try:
                    parsed_confidence = float(confidence_value)
                except ValueError:
                    parsed_confidence = None

            predictions.append({
                "sample_id": ids[i],
                "true_value": true_values[i],
                "pred_value": pred_values[i],
                "confidence": parsed_confidence,
                "is_correct": int(true_values[i] == pred_values[i]),
            })

        return {
            "task_type": inferred,
            "metrics": json.dumps(metrics),
            "predictions": predictions,
        }
