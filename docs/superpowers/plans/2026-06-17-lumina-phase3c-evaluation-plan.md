# Lumina Phase 3-C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add model evaluation against datasets: read a predictions CSV, compute classification/regression metrics, store results, expose API/CLI, and render a cyberpunk-styled Evaluate Panel.

**Architecture:** A new `EvaluationService` wraps evaluation loading, metric calculation, and storage. It lives alongside `ExperimentService` on the `Project`. Predictions CSVs are parsed into the `predictions` table; metrics are stored as JSON in `evaluations`. FastAPI exposes CRUD endpoints; the React frontend fetches and visualizes.

**Tech Stack:** Python 3.12, SQLite, FastAPI, scikit-learn (optional, for metrics), React + TypeScript.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `src/lumina/storage/db.py` | Add `evaluations` and `predictions` tables |
| `src/lumina/storage/repositories.py` | Add `EvaluationRepository`, `PredictionRepository` |
| `src/lumina/experiments/evaluation_loader.py` | Parse predictions CSV, detect task type, compute metrics |
| `src/lumina/experiments/evaluation_service.py` | Orchestrate repository storage and project-relative paths |
| `src/lumina/experiments/service.py` | Attach `EvaluationService` as `project.experiments.evaluations` |
| `src/lumina/server.py` | Add `/api/evaluations/*` endpoints |
| `src/lumina/cli.py` | Add `project eval create/list` commands |
| `frontend/src/types.ts` | Add `Evaluation`, `Prediction`, `Metrics` types |
| `frontend/src/api.ts` | Add `fetchEvaluations`, `createEvaluation`, `fetchPredictions` |
| `frontend/src/panels/EvaluatePanel.tsx` | New cyberpunk evaluation panel |
| `frontend/src/App.tsx` | Add Evaluate tab toggle |
| `tests/test_evaluation_*.py` | Unit, API, CLI, integration tests |

---

### Task 1: Database schema for evaluations and predictions

**Files:**
- Modify: `src/lumina/storage/db.py`
- Test: `tests/test_evaluation_schema.py`

- [ ] **Step 1: Write the failing test**

```python
from lumina.storage.db import get_db, init_schema


def test_evaluation_schema_is_created(tmp_path):
    db_path = tmp_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"evaluations", "predictions"}.issubset(tables)

    eval_cols = {row[1] for row in conn.execute("PRAGMA table_info(evaluations)").fetchall()}
    assert {"id", "run_id", "dataset_id", "name", "task_type", "predictions_path", "metrics"} <= eval_cols

    pred_cols = {row[1] for row in conn.execute("PRAGMA table_info(predictions)").fetchall()}
    assert {"evaluation_id", "sample_id", "true_value", "pred_value", "confidence", "is_correct"} <= pred_cols
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_evaluation_schema.py -v`
Expected: FAIL (assertions fail)

- [ ] **Step 3: Add tables to SCHEMA**

Append to `src/lumina/storage/db.py` SCHEMA:

```sql
CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    dataset_id TEXT REFERENCES datasets(id) ON DELETE SET NULL,
    name TEXT,
    task_type TEXT NOT NULL,
    predictions_path TEXT NOT NULL,
    metrics TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id TEXT NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    sample_id TEXT NOT NULL,
    true_value TEXT NOT NULL,
    pred_value TEXT NOT NULL,
    confidence REAL,
    is_correct INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_evaluation ON predictions(evaluation_id);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_evaluation_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/storage/db.py tests/test_evaluation_schema.py
git commit -m "feat: add evaluations and predictions schema"
```

---

### Task 2: Evaluation loader and metrics calculation

**Files:**
- Create: `src/lumina/experiments/evaluation_loader.py`
- Test: `tests/test_evaluation_loader.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_evaluation_loader.py -v`
Expected: FAIL (module undefined)

- [ ] **Step 3: Implement loader**

Create `src/lumina/experiments/evaluation_loader.py`:

```python
import csv
import json
from pathlib import Path
from typing import Literal


def _is_numeric(values: list[str]) -> bool:
    try:
        [float(v) for v in values]
        return True
    except ValueError:
        return False


def _infer_task_type(true_values: list[str], pred_values: list[str]) -> Literal["classification", "regression"]:
    combined = true_values + pred_values
    if not _is_numeric(combined):
        return "classification"
    numeric = [float(v) for v in combined]
    unique_count = len(set(numeric))
    if unique_count <= 20:
        return "classification"
    return "regression"


def _compute_classification_metrics(true_values: list[str], pred_values: list[str]) -> dict:
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
    y_true = [float(v) for v in true_values]
    y_pred = [float(v) for v in pred_values]
    n = len(y_true)
    errors = [yt - yp for yt, yp in zip(y_true, y_pred)]
    mae = sum(abs(e) for e in errors) / n
    rmse = (sum(e ** 2 for e in errors) / n) ** 0.5
    mean_true = sum(y_true) / n
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    ss_tot = sum((yt - mean_true) ** 2 for yt in y_true)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


class EvaluationLoader:
    REQUIRED_COLUMNS = {"id", "true", "pred"}

    @classmethod
    def load(cls, path: Path, task_type: str | None = None) -> dict:
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
            predictions.append({
                "sample_id": ids[i],
                "true_value": true_values[i],
                "pred_value": pred_values[i],
                "confidence": float(confidences[i]) if confidences[i] not in (None, "") else None,
                "is_correct": int(true_values[i] == pred_values[i]),
            })

        return {
            "task_type": inferred,
            "metrics": json.dumps(metrics),
            "predictions": predictions,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_evaluation_loader.py -v`
Expected: PASS

- [ ] **Step 5: Add regression test**

Append to `tests/test_evaluation_loader.py`:

```python
def test_regression_metrics(tmp_path):
    csv = tmp_path / "pred.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n2,3.0,3.2\n")

    result = EvaluationLoader.load(csv)
    assert result["task_type"] == "regression"
    metrics = json.loads(result["metrics"])
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_evaluation_loader.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/lumina/experiments/evaluation_loader.py tests/test_evaluation_loader.py
git commit -m "feat: add evaluation loader with classification and regression metrics"
```

---

### Task 3: Repository layer for evaluations and predictions

**Files:**
- Modify: `src/lumina/storage/repositories.py`
- Test: `tests/test_evaluation_repositories.py`

- [ ] **Step 1: Write the failing test**

```python
import uuid
from pathlib import Path

from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import EvaluationRepository, PredictionRepository


def test_evaluation_repository_crud(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_db(db_path)
    init_schema(conn)

    eval_repo = EvaluationRepository(conn)
    eval_id = str(uuid.uuid4())
    eval_repo.create(
        eval_id=eval_id,
        run_id="run-1",
        dataset_id="ds-1",
        name="eval-1",
        task_type="classification",
        predictions_path="preds.csv",
        metrics='{"accuracy": 0.9}',
    )
    record = eval_repo.get(eval_id)
    assert record["name"] == "eval-1"

    pred_repo = PredictionRepository(conn)
    pred_repo.create_many(eval_id, [
        {"sample_id": "0", "true_value": "cat", "pred_value": "cat", "confidence": 0.9, "is_correct": 1},
    ])
    assert len(pred_repo.list_by_evaluation(eval_id)) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_evaluation_repositories.py -v`
Expected: FAIL (classes undefined)

- [ ] **Step 3: Implement repositories**

Append to `src/lumina/storage/repositories.py`:

```python
class EvaluationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        eval_id: str,
        run_id: str,
        dataset_id: Optional[str],
        name: str,
        task_type: str,
        predictions_path: str,
        metrics: str,
    ) -> dict:
        self._conn.execute(
            """
            INSERT INTO evaluations (id, run_id, dataset_id, name, task_type, predictions_path, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (eval_id, run_id, dataset_id, name, task_type, predictions_path, metrics),
        )
        self._conn.commit()
        return self.get(eval_id)

    def get(self, eval_id: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,)).fetchone()
        return dict(row) if row else None

    def list_by_run(self, run_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM evaluations WHERE run_id = ? ORDER BY created_at DESC",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT evaluations.* FROM evaluations
            JOIN runs ON evaluations.run_id = runs.id
            WHERE runs.project_id = ?
            ORDER BY evaluations.created_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class PredictionRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create_many(self, evaluation_id: str, predictions: list[dict]) -> int:
        if not predictions:
            return 0
        self._conn.executemany(
            """
            INSERT INTO predictions (evaluation_id, sample_id, true_value, pred_value, confidence, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    evaluation_id,
                    p["sample_id"],
                    p["true_value"],
                    p["pred_value"],
                    p.get("confidence"),
                    p["is_correct"],
                )
                for p in predictions
            ],
        )
        self._conn.commit()
        return len(predictions)

    def list_by_evaluation(self, evaluation_id: str, limit: Optional[int] = None) -> list[dict]:
        query = "SELECT * FROM predictions WHERE evaluation_id = ? ORDER BY is_correct ASC, sample_id ASC"
        params = [evaluation_id]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_evaluation_repositories.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/storage/repositories.py tests/test_evaluation_repositories.py
git commit -m "feat: add evaluation and prediction repositories"
```

---

### Task 4: EvaluationService

**Files:**
- Create: `src/lumina/experiments/evaluation_service.py`
- Modify: `src/lumina/experiments/service.py`
- Test: `tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from lumina.core.project_manager import ProjectManager
from lumina.experiments.evaluation_service import EvaluationService


def test_evaluation_service_create(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(run_id="run-1", project_id=project.id, name="run-1")

    preds = tmp_path / "predictions.csv"
    preds.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n")

    service = EvaluationService(project._conn, project.path)
    ev = service.create_evaluation(
        run_id="run-1",
        dataset_id=None,
        name="eval-1",
        predictions_path=str(preds),
    )
    assert ev["task_type"] == "classification"
    assert len(service.list_by_project(project.id)) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_evaluation_service.py -v`
Expected: FAIL (class undefined)

- [ ] **Step 3: Implement EvaluationService**

Create `src/lumina/experiments/evaluation_service.py`:

```python
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from lumina.experiments.evaluation_loader import EvaluationLoader
from lumina.storage.repositories import EvaluationRepository, PredictionRepository


class EvaluationService:
    def __init__(self, conn: sqlite3.Connection, project_path: Path):
        self._conn = conn
        self._project_path = Path(project_path)
        self.evaluations = EvaluationRepository(conn)
        self.predictions = PredictionRepository(conn)

    def create_evaluation(
        self,
        run_id: str,
        dataset_id: Optional[str],
        name: Optional[str],
        predictions_path: str,
        task_type: Optional[str] = None,
    ) -> dict:
        eval_id = str(uuid.uuid4())
        path = Path(predictions_path).resolve()
        if not path.exists():
            raise ValueError(f"Predictions file not found: {predictions_path}")
        if not path.is_file():
            raise ValueError(f"Predictions path is not a file: {predictions_path}")

        rel_path = path.relative_to(self._project_path)
        loaded = EvaluationLoader.load(path, task_type=task_type)

        ev = self.evaluations.create(
            eval_id=eval_id,
            run_id=run_id,
            dataset_id=dataset_id,
            name=name or f"eval-{eval_id[:8]}",
            task_type=loaded["task_type"],
            predictions_path=str(rel_path),
            metrics=loaded["metrics"],
        )
        self.predictions.create_many(eval_id, loaded["predictions"])
        return ev

    def list_by_project(self, project_id: str) -> list[dict]:
        return self.evaluations.list_by_project(project_id)

    def get(self, eval_id: str) -> Optional[dict]:
        return self.evaluations.get(eval_id)

    def get_predictions(self, eval_id: str, limit: Optional[int] = None) -> list[dict]:
        return self.predictions.list_by_evaluation(eval_id, limit=limit)
```

- [ ] **Step 4: Wire into ExperimentService**

Modify `src/lumina/experiments/service.py`:

Add import:

```python
from lumina.experiments.evaluation_service import EvaluationService
```

Add in `ExperimentService.__init__`:

```python
        self.evaluations = EvaluationService(conn, self._project_path)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_evaluation_service.py -v`
Expected: PASS

Run full suite: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/lumina/experiments/evaluation_service.py src/lumina/experiments/service.py tests/test_evaluation_service.py
git commit -m "feat: add EvaluationService and wire into Project"
```

---

### Task 5: FastAPI endpoints for evaluations

**Files:**
- Modify: `src/lumina/server.py`
- Test: `tests/test_server_evaluations.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from lumina.core.project_manager import ProjectManager
from lumina.server import create_app


def test_create_evaluation_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    project.experiments.runs.create(run_id="run-1", project_id=project.id, name="run-1")

    preds = tmp_path / "predictions.csv"
    preds.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n")

    app = create_app(project=project)
    client = TestClient(app)
    res = client.post(
        "/api/evaluations",
        json={
            "run_id": "run-1",
            "dataset_name": "",
            "name": "eval-1",
            "predictions_path": str(preds),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["task_type"] == "classification"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_server_evaluations.py::test_create_evaluation_endpoint -v`
Expected: FAIL (endpoint returns 404)

- [ ] **Step 3: Implement endpoints**

Append to `src/lumina/server.py` after the existing experiment endpoints block (before model endpoints comment):

```python
    @app.post("/api/evaluations")
    def create_evaluation(payload: dict) -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        run_id = payload.get("run_id")
        dataset_name = payload.get("dataset_name")
        name = payload.get("name")
        predictions_path = payload.get("predictions_path")
        task_type = payload.get("task_type")
        if not run_id or not predictions_path:
            raise HTTPException(status_code=400, detail="run_id and predictions_path are required")
        if project.experiments.runs.get(run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        dataset_id = None
        if dataset_name:
            ds = project.datasets.get_by_name(project.id, dataset_name)
            if ds is None:
                raise HTTPException(status_code=404, detail=f"Dataset {dataset_name} not found")
            dataset_id = ds["id"]
        try:
            return project.experiments.evaluations.create_evaluation(
                run_id=run_id,
                dataset_id=dataset_id,
                name=name,
                predictions_path=predictions_path,
                task_type=task_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/evaluations")
    def list_evaluations() -> list[dict]:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        return project.experiments.evaluations.list_by_project(project.id)

    @app.get("/api/evaluations/{eval_id}")
    def get_evaluation(eval_id: str) -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        ev = project.experiments.evaluations.get(eval_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        return ev

    @app.get("/api/evaluations/{eval_id}/predictions")
    def list_predictions(eval_id: str, limit: Optional[int] = Query(None, ge=1)) -> list[dict]:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        if project.experiments.evaluations.get(eval_id) is None:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        return project.experiments.evaluations.get_predictions(eval_id, limit=limit)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_server_evaluations.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/server.py tests/test_server_evaluations.py
git commit -m "feat: add evaluation API endpoints"
```

---

### Task 6: CLI commands for evaluations

**Files:**
- Modify: `src/lumina/cli.py`
- Test: `tests/test_cli_evaluations.py`

- [ ] **Step 1: Write the failing test**

```python
import subprocess
import sys
from pathlib import Path


def test_cli_eval_create_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    subprocess.run([sys.executable, "-m", "lumina", "project", "create", "p1"], check=True)

    manager = __import__("lumina.core.project_manager", fromlist=["ProjectManager"]).ProjectManager()
    project = manager.create("p1")
    project.experiments.runs.create(run_id="run-1", project_id=project.id, name="run-1")

    preds = tmp_path / "predictions.csv"
    preds.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n")

    result = subprocess.run(
        [
            sys.executable, "-m", "lumina", "project", "eval", "create",
            "--project", "p1",
            "--run", "run-1",
            "--predictions", str(preds),
            "--name", "baseline",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    result = subprocess.run(
        [sys.executable, "-m", "lumina", "project", "eval", "list", "--project", "p1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
    assert "baseline" in result.stdout
```

Wait — the first `project create p1` already creates the project; the second Python `manager.create("p1")` will fail due to name uniqueness. Adjust to open the project instead:

```python
    manager = __import__("lumina.core.project_manager", fromlist=["ProjectManager"]).ProjectManager()
    project = manager.open("p1")
    project.experiments.runs.create(run_id="run-1", project_id=project.id, name="run-1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_evaluations.py::test_cli_eval_create_and_list -v`
Expected: FAIL (subcommand missing)

- [ ] **Step 3: Implement CLI commands**

In `src/lumina/cli.py`, add after the runs subparser:

```python
    eval_parser = project_sub.add_parser("eval", help="Evaluation management")
    eval_sub = eval_parser.add_subparsers(dest="eval_command")

    eval_create_parser = eval_sub.add_parser("create", help="Create an evaluation")
    eval_create_parser.add_argument("--project", required=True, help="Project name")
    eval_create_parser.add_argument("--run", required=True, help="Run ID")
    eval_create_parser.add_argument("--dataset", help="Dataset name")
    eval_create_parser.add_argument("--predictions", required=True, help="Path to predictions CSV")
    eval_create_parser.add_argument("--name", help="Evaluation name")
    eval_create_parser.add_argument("--task-type", choices=["classification", "regression"], help="Force task type")

    eval_list_parser = eval_sub.add_parser("list", help="List evaluations")
    eval_list_parser.add_argument("--project", required=True, help="Project name")
```

Add dispatch branch:

```python
    elif args.command == "project" and args.project_command == "eval":
        if args.eval_command == "create":
            return _handle_eval_create(args)
        elif args.eval_command == "list":
            return _handle_eval_list(args)
```

Add handlers:

```python
def _handle_eval_create(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    try:
        manager = ProjectManager()
        project = manager.open(args.project)
        dataset_id = None
        if args.dataset:
            ds = project.datasets.get_by_name(project.id, args.dataset)
            if ds is None:
                print(f"Error: dataset {args.dataset} not found", file=sys.stderr)
                return 1
            dataset_id = ds["id"]
        ev = project.experiments.evaluations.create_evaluation(
            run_id=args.run,
            dataset_id=dataset_id,
            name=args.name,
            predictions_path=args.predictions,
            task_type=args.task_type,
        )
        print(f"Created evaluation: {ev['id']} ({ev['name']}) [{ev['task_type']}]")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _handle_eval_list(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    try:
        manager = ProjectManager()
        project = manager.open(args.project)
        for ev in project.experiments.evaluations.list_by_project(project.id):
            print(f"{ev['id']}\t{ev['name']}\t{ev['task_type']}\t{ev['created_at']}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_evaluations.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/cli.py tests/test_cli_evaluations.py
git commit -m "feat: add evaluation CLI commands"
```

---

### Task 7: Frontend types and API helpers

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add types**

Append to `frontend/src/types.ts`:

```typescript
export interface Evaluation {
  id: string
  run_id: string
  dataset_id?: string
  name: string
  task_type: string
  predictions_path: string
  metrics: Record<string, any>
  created_at: string
}

export interface Prediction {
  id: number
  evaluation_id: string
  sample_id: string
  true_value: string
  pred_value: string
  confidence?: number
  is_correct: number
}
```

- [ ] **Step 2: Add API helpers**

Append to `frontend/src/api.ts`:

```typescript
import { Evaluation, Prediction } from './types'

export async function fetchEvaluations(): Promise<Evaluation[]> {
  const res = await fetch('/api/evaluations')
  if (!res.ok) throw new Error('Failed to fetch evaluations')
  return res.json()
}

export async function createEvaluation(payload: {
  run_id: string
  dataset_name?: string
  name?: string
  predictions_path: string
  task_type?: string
}): Promise<Evaluation> {
  const res = await fetch('/api/evaluations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create evaluation')
  return res.json()
}

export async function fetchPredictions(evalId: string, limit?: number): Promise<Prediction[]> {
  const query = limit ? `?limit=${limit}` : ''
  const res = await fetch(`/api/evaluations/${evalId}/predictions${query}`)
  if (!res.ok) throw new Error('Failed to fetch predictions')
  return res.json()
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts
git commit -m "feat: add evaluation types and API helpers"
```

---

### Task 8: EvaluatePanel UI (cyberpunk)

**Files:**
- Create: `frontend/src/panels/EvaluatePanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create EvaluatePanel**

Create `frontend/src/panels/EvaluatePanel.tsx`:

```tsx
import { useEffect, useMemo, useState } from 'react'
import { createEvaluation, fetchEvaluations, fetchPredictions } from '../api'
import { Evaluation, Prediction } from '../types'

export default function EvaluatePanel() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [inFlight, setInFlight] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const loading = inFlight > 0
  const selectedEval = useMemo(
    () => evaluations.find((e) => e.id === selectedEvalId) || null,
    [evaluations, selectedEvalId]
  )

  useEffect(() => {
    setInFlight((n) => n + 1)
    fetchEvaluations()
      .then((es) => {
        setEvaluations(es)
        setSelectedEvalId((current) => (current === null && es.length > 0 ? es[0].id : current))
      })
      .catch((err) => setError(err.message))
      .finally(() => setInFlight((n) => Math.max(0, n - 1)))
  }, [])

  useEffect(() => {
    if (!selectedEvalId) return
    setInFlight((n) => n + 1)
    setError(null)
    let stale = false
    fetchPredictions(selectedEvalId, 50)
      .then((ps) => {
        if (!stale) setPredictions(ps)
      })
      .catch((err) => {
        if (!stale) setError(err.message)
      })
      .finally(() => setInFlight((n) => Math.max(0, n - 1)))
    return () => {
      stale = true
    }
  }, [selectedEvalId])

  const handleCreate = async (payload: {
    run_id: string
    dataset_name?: string
    name?: string
    predictions_path: string
  }) => {
    setError(null)
    setInFlight((n) => n + 1)
    try {
      const ev = await createEvaluation(payload)
      setEvaluations((prev) => [ev, ...prev])
      setSelectedEvalId(ev.id)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setInFlight((n) => Math.max(0, n - 1))
    }
  }

  const isClassification = selectedEval?.task_type === 'classification'
  const metrics = selectedEval?.metrics || {}

  return (
    <div style={{ height: '100%', background: '#050505', color: '#e5e7eb', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 8, height: 8, background: '#00ff9d', borderRadius: '50%', boxShadow: '0 0 10px #00ff9d' }} />
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#00ff9d', letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'monospace' }}>
              EVALUATE {selectedEval ? `// ${selectedEval.name}` : ''}
            </div>
            <div style={{ fontSize: 10, color: '#666', marginTop: 2, fontFamily: 'monospace' }}>
              {selectedEval ? `${selectedEval.task_type} · ${selectedEval.predictions_path}` : 'NO EVALUATION SELECTED'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            value={selectedEvalId || ''}
            onChange={(e) => setSelectedEvalId(e.target.value)}
            style={{ padding: '8px 12px', background: '#0a0a0a', border: '1px solid #333', color: '#00ff9d', fontFamily: 'monospace', fontSize: 12 }}
          >
            {evaluations.map((ev) => (
              <option key={ev.id} value={ev.id}>{ev.name}</option>
            ))}
          </select>
          <button
            onClick={() => handleCreate({ run_id: 'run-1', predictions_path: '/demo/predictions.csv' })}
            style={{ padding: '8px 18px', border: '1px solid #00ff9d', background: 'transparent', color: '#00ff9d', fontFamily: 'monospace', fontSize: 12, cursor: 'pointer' }}
          >
            + NEW_EVAL
          </button>
        </div>
      </div>

      <div style={{ padding: 20, flex: 1, overflow: 'auto' }}>
        {error && <div style={{ color: '#ff00ff', fontFamily: 'monospace', fontSize: 12, marginBottom: 12 }}>{error}</div>}
        {loading && <div style={{ color: '#666', fontFamily: 'monospace', fontSize: 12, marginBottom: 12 }}>LOADING...</div>}

        {selectedEval && (
          <>
            <MetricCards metrics={metrics} isClassification={isClassification} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginTop: 16 }}>
              <div style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', padding: 20 }}>
                <div style={{ fontSize: 11, color: '#00ff9d', fontFamily: 'monospace', letterSpacing: '0.1em', marginBottom: 16 }}>
                  // {isClassification ? 'CONFUSION_MATRIX' : 'RESIDUAL_PLOT'}
                </div>
                {isClassification ? <ConfusionMatrix matrix={metrics.confusion_matrix} /> : <ResidualPlaceholder />}
              </div>
              <div style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', padding: 16 }}>
                <div style={{ fontSize: 11, color: '#ff00ff', fontFamily: 'monospace', letterSpacing: '0.1em', marginBottom: 12 }}>// MISCLASSIFIED</div>
                <PredictionList predictions={predictions.filter((p) => !p.is_correct)} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function MetricCards({ metrics, isClassification }: { metrics: Record<string, any>; isClassification: boolean }) {
  const items = isClassification
    ? [
        { label: 'ACCURACY', value: metrics.accuracy, color: '#00ff9d' },
        { label: 'PRECISION', value: metrics.precision, color: '#ff00ff' },
        { label: 'RECALL', value: metrics.recall, color: '#00ccff' },
        { label: 'F1_SCORE', value: metrics.f1, color: '#ffff00' },
      ]
    : [
        { label: 'MAE', value: metrics.mae, color: '#00ff9d' },
        { label: 'RMSE', value: metrics.rmse, color: '#ff00ff' },
        { label: 'R2', value: metrics.r2, color: '#00ccff' },
      ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
      {items.map((item) => (
        <div key={item.label} style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', padding: 16, position: 'relative' }}>
          <div style={{ fontSize: 9, color: item.color, fontFamily: 'monospace', letterSpacing: '0.15em' }}>{item.label}</div>
          <div style={{ fontSize: 32, fontWeight: 800, color: '#fff', fontFamily: 'monospace', marginTop: 8 }}>
            {typeof item.value === 'number' ? item.value.toFixed(2) : '-'}
          </div>
          <div style={{ position: 'absolute', top: 0, right: 0, width: 30, height: 1, background: item.color }} />
        </div>
      ))}
    </div>
  )
}

function ConfusionMatrix({ matrix }: { matrix: Record<string, Record<string, number>> | undefined }) {
  if (!matrix) return null
  const labels = Object.keys(matrix)
  const maxVal = Math.max(...labels.flatMap((t) => labels.map((p) => matrix[t][p])), 1)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
      {labels.map((trueLabel) => (
        <div key={trueLabel} style={{ display: 'flex', gap: 3 }}>
          {labels.map((predLabel) => {
            const val = matrix[trueLabel][predLabel]
            const intensity = val / maxVal
            return (
              <div
                key={predLabel}
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 4,
                  background: `rgba(0, 255, 157, ${0.1 + intensity * 0.9})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: intensity > 0.5 ? '#000' : '#00ff9d',
                  fontFamily: 'monospace',
                  fontSize: 14,
                  fontWeight: 800,
                  boxShadow: intensity > 0.5 ? '0 0 16px rgba(0,255,157,0.25)' : 'none',
                }}
              >
                {val}
              </div>
            )
          })}
        </div>
      ))}
      <div style={{ display: 'flex', gap: 40, marginTop: 12, fontFamily: 'monospace', fontSize: 10, color: '#666' }}>
        {labels.map((l) => <span key={l}>{l.toUpperCase()}</span>)}
      </div>
    </div>
  )
}

function ResidualPlaceholder() {
  return (
    <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontFamily: 'monospace', fontSize: 12 }}>
      [RESIDUAL PLOT PLACEHOLDER]
    </div>
  )
}

function PredictionList({ predictions }: { predictions: Prediction[] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {predictions.slice(0, 10).map((p) => (
        <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 10, background: 'rgba(255,0,255,0.08)', borderLeft: '2px solid #ff00ff' }}>
          <div>
            <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#fff' }}>
              #{p.sample_id} <span style={{ color: '#888' }}>{p.true_value}</span> <span style={{ color: '#ff00ff' }}>→</span> {p.pred_value}
            </div>
          </div>
          {p.confidence !== undefined && (
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: '#ff00ff' }}>{p.confidence.toFixed(2)}</div>
          )}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Wire into App**

Modify `frontend/src/App.tsx`:

- Import:

```tsx
import EvaluatePanel from './panels/EvaluatePanel'
```

- Update mode state type:

```tsx
const [mode, setMode] = useState<'project' | 'model' | 'experiments' | 'evaluate' | null>(null)
```

- Add Evaluate button in each mode's header block. For example in `mode === 'experiments'`:

```tsx
            <button onClick={() => setMode('evaluate')}>Evaluate</button>
```

And in `mode === 'evaluate'`:

```tsx
            <button onClick={() => setMode('project')}>Data View</button>
            <button onClick={() => setMode('model')}>Model View</button>
            <button onClick={() => setMode('experiments')}>Experiments</button>
```

- Update panel render:

```tsx
      {mode === 'project' ? (
        <DataPanel />
      ) : mode === 'experiments' ? (
        <ExperimentsPanel />
      ) : mode === 'evaluate' ? (
        <EvaluatePanel />
      ) : (
        <ModelPanel />
      )}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 4: Commit**

```bash
git add frontend/src/panels/EvaluatePanel.tsx frontend/src/App.tsx
git commit -m "feat: add cyberpunk EvaluatePanel"
```

Then rebuild and commit static assets:

```bash
cd frontend && npm run build
cd /Users/hehang/Hworkplace && git add src/lumina/static/ && git commit -m "chore: rebuild static assets for EvaluatePanel"
```

---

### Task 9: Full integration test and final verification

**Files:**
- Create: `tests/test_evaluation_integration.py`

- [ ] **Step 1: Write integration test**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from lumina.core.project_manager import ProjectManager
from lumina.server import create_app


def test_evaluation_integration(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("p1")
        project.experiments.runs.create(run_id="run-1", project_id=project.id, name="run-1")

        preds = tmp_path / "predictions.csv"
        preds.write_text("id,true,pred,confidence\n0,cat,cat,0.9\n1,dog,cat,0.6\n2,dog,dog,0.8\n3,cat,dog,0.7\n")

        app = create_app(project=project)
        client = TestClient(app)

        res = client.post(
            "/api/evaluations",
            json={"run_id": "run-1", "predictions_path": str(preds), "name": "integration-test"},
        )
        assert res.status_code == 200
        ev = res.json()
        assert ev["task_type"] == "classification"
        assert ev["metrics"]["accuracy"] == 0.5

        res = client.get("/api/evaluations")
        assert res.status_code == 200
        assert len(res.json()) == 1

        res = client.get(f"/api/evaluations/{ev['id']}/predictions")
        assert res.status_code == 200
        assert len(res.json()) == 4
```

- [ ] **Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_evaluation_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Build frontend**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 5: Commit**

```bash
git add tests/test_evaluation_integration.py
git commit -m "test: add evaluation integration test"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| evaluations / predictions schema | Task 1 |
| CSV loader + task detection + metrics | Task 2 |
| Repository layer | Task 3 |
| EvaluationService | Task 4 |
| API endpoints | Task 5 |
| CLI commands | Task 6 |
| Frontend types/API | Task 7 |
| Cyberpunk EvaluatePanel | Task 8 |
| Integration + verification | Task 9 |

## Placeholder Scan

- No TBD/TODO/fill-in-details.
- Every code step contains concrete implementation code.
- Every test step contains concrete test code.
- Type names are consistent across tasks.
