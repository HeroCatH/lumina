# Lumina Phase 3-A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add experiment/run tracking to Lumina: SDK logging, external log directory syncing, checkpoint management, API/CLI, and a browser-based Experiments Panel.

**Architecture:** Runs, metrics, and checkpoints live in the existing SQLite project database. A Python SDK writes directly to the DB, while log adapters (JSONL/CSV/TensorBoard) scan external directories and import into the same schema. FastAPI exposes endpoints for the React frontend, and the CLI adds `project logs` and `project runs` commands.

**Tech Stack:** Python 3.12, FastAPI, SQLite, React + TypeScript, optional `tensorboard`.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `src/lumina/storage/db.py` | Add `runs`, `metrics`, `checkpoints` tables to project DB schema |
| `src/lumina/storage/repositories.py` | Add `RunRepository`, `MetricRepository`, `CheckpointRepository` |
| `src/lumina/experiments/__init__.py` | Package exports |
| `src/lumina/experiments/run.py` | `Run` SDK object: `log`, `finish`, `save_checkpoint` |
| `src/lumina/experiments/service.py` | `ExperimentService`: create runs, sync logs, list checkpoints |
| `src/lumina/experiments/log_adapters.py` | Adapters for JSONL, CSV, and optional TensorBoard events |
| `src/lumina/core/project.py` | Attach `experiments` service to `Project` |
| `src/lumina/api.py` | Add `start_run` helper; keep `open_project` etc. |
| `src/lumina/server.py` | Add `/api/runs`, `/api/metrics`, `/api/checkpoints`, `/api/projects/{id}/logs/*` endpoints |
| `src/lumina/cli.py` | Add `project logs add`, `project logs sync`, `project runs list` |
| `frontend/src/types.ts` | Add `Run`, `Metric`, `Checkpoint` types |
| `frontend/src/api.ts` | Add fetch helpers for experiment endpoints |
| `frontend/src/panels/ExperimentsPanel.tsx` | New panel: run list, metric curves, checkpoint list |
| `frontend/src/App.tsx` | Add Experiments tab toggle |
| `tests/test_experiments*.py` | Unit, API, CLI tests |

---

### Task 1: Database schema for runs, metrics, checkpoints

**Files:**
- Modify: `src/lumina/storage/db.py`
- Test: `tests/test_experiments_schema.py`

- [ ] **Step 1: Write the failing test**

```python
from lumina.storage.db import SCHEMA

def test_schema_includes_experiment_tables():
    assert "CREATE TABLE IF NOT EXISTS runs" in SCHEMA
    assert "CREATE TABLE IF NOT EXISTS metrics" in SCHEMA
    assert "CREATE TABLE IF NOT EXISTS checkpoints" in SCHEMA
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_experiments_schema.py -v`
Expected: FAIL (assertions fail)

- [ ] **Step 3: Add tables to SCHEMA**

Edit `src/lumina/storage/db.py` and append to `SCHEMA`:

```python
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT,
    status TEXT DEFAULT 'running',
    source TEXT DEFAULT 'sdk',
    log_dir TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step INTEGER,
    name TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step INTEGER,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_experiments_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/storage/db.py tests/test_experiments_schema.py
git commit -m "feat: add runs, metrics, checkpoints schema"
```

---

### Task 2: Repository layer for experiments

**Files:**
- Modify: `src/lumina/storage/repositories.py`
- Test: `tests/test_experiments_repositories.py`

- [ ] **Step 1: Write the failing test**

```python
import sqlite3
import uuid
from pathlib import Path

from lumina.storage.db import get_db
from lumina.storage.repositories import RunRepository, MetricRepository, CheckpointRepository

def test_run_repository_crud(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_db(db_path)
    from lumina.storage.db import init_schema
    init_schema(conn)

    runs = RunRepository(conn)
    run_id = str(uuid.uuid4())
    runs.create(run_id=run_id, project_id=None, name="test", source="sdk")
    run = runs.get(run_id)
    assert run["name"] == "test"
    assert run["status"] == "running"

    metrics = MetricRepository(conn)
    metrics.create(run_id=run_id, step=1, name="loss", value=0.5)
    assert len(metrics.list_by_run(run_id)) == 1

    checkpoints = CheckpointRepository(conn)
    checkpoints.create(run_id=run_id, step=10, path="ckpt/step_10.pt")
    assert len(checkpoints.list_by_run(run_id)) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_experiments_repositories.py -v`
Expected: FAIL (classes undefined)

- [ ] **Step 3: Implement repositories**

Append to `src/lumina/storage/repositories.py`:

```python
class RunRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        run_id: str,
        project_id: Optional[str],
        name: str,
        status: str = "running",
        source: str = "sdk",
        log_dir: Optional[str] = None,
    ) -> dict:
        self._conn.execute(
            """
            INSERT INTO runs (id, project_id, name, status, source, log_dir)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, project_id, name, status, source, log_dir),
        )
        self._conn.commit()
        return self.get(run_id)

    def get(self, run_id: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM runs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, run_id: str, status: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, run_id),
        )
        self._conn.commit()


class MetricRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, run_id: str, step: int, name: str, value: float) -> dict:
        cur = self._conn.execute(
            "INSERT INTO metrics (run_id, step, name, value) VALUES (?, ?, ?, ?)",
            (run_id, step, name, value),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM metrics WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_by_run(self, run_id: str, name: Optional[str] = None) -> list[dict]:
        if name:
            rows = self._conn.execute(
                "SELECT * FROM metrics WHERE run_id = ? AND name = ? ORDER BY step ASC",
                (run_id, name),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM metrics WHERE run_id = ? ORDER BY step ASC",
                (run_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_names_by_run(self, run_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT name FROM metrics WHERE run_id = ? ORDER BY name",
            (run_id,),
        ).fetchall()
        return [r["name"] for r in rows]


class CheckpointRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, run_id: str, step: int, path: str) -> dict:
        cur = self._conn.execute(
            "INSERT INTO checkpoints (run_id, step, path) VALUES (?, ?, ?)",
            (run_id, step, path),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM checkpoints WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_by_run(self, run_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM checkpoints WHERE run_id = ? ORDER BY step ASC",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_experiments_repositories.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/storage/repositories.py tests/test_experiments_repositories.py
git commit -m "feat: add experiment repositories"
```

---

### Task 3: ExperimentService and Run SDK object

**Files:**
- Create: `src/lumina/experiments/__init__.py`
- Create: `src/lumina/experiments/service.py`
- Create: `src/lumina/experiments/run.py`
- Modify: `src/lumina/core/project.py`
- Test: `tests/test_experiments_run.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from lumina.core.project_manager import ProjectManager
from lumina.experiments.run import Run


def test_run_sdk_logs_and_finishes(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    run = Run.start(project=project, name="run-1")
    run.log("loss", 0.5, step=1)
    run.log("loss", 0.4, step=2)
    run.finish()

    metrics = project.experiments.metrics.list_by_run(run.id, name="loss")
    assert len(metrics) == 2
    assert metrics[-1]["value"] == 0.4

    record = project.experiments.runs.get(run.id)
    assert record["status"] == "finished"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_experiments_run.py -v`
Expected: FAIL (modules undefined)

- [ ] **Step 3: Implement service and Run**

Create `src/lumina/experiments/service.py`:

```python
import sqlite3
from pathlib import Path
from typing import Optional

from lumina.storage.repositories import CheckpointRepository, MetricRepository, RunRepository


class ExperimentService:
    def __init__(self, conn: sqlite3.Connection, project_path: Path, project_id: Optional[str] = None):
        self._conn = conn
        self._project_path = Path(project_path)
        self._project_id = project_id
        self.runs = RunRepository(conn)
        self.metrics = MetricRepository(conn)
        self.checkpoints = CheckpointRepository(conn)

    def checkpoint_dir(self, run_id: str) -> Path:
        return self._project_path / "checkpoints" / run_id
```

Create `src/lumina/experiments/run.py`:

```python
import uuid
from pathlib import Path
from typing import Any, Optional

from lumina.core.project import Project
from lumina.experiments.service import ExperimentService


class Run:
    def __init__(self, run_id: str, project: Optional[Project], service: ExperimentService):
        self.id = run_id
        self._project = project
        self._service = service

    @classmethod
    def start(cls, project: Optional[Project] = None, name: Optional[str] = None) -> "Run":
        service = project.experiments if project else _raise_project_required()
        run_id = str(uuid.uuid4())
        service.runs.create(
            run_id=run_id,
            project_id=project.id if project else None,
            name=name or run_id[:8],
            status="running",
            source="sdk",
        )
        return cls(run_id=run_id, project=project, service=service)

    def log(self, name: str, value: float, step: int) -> None:
        self._service.metrics.create(run_id=self.id, step=step, name=name, value=value)

    def save_checkpoint(self, source_path: str, step: int) -> Path:
        if self._project is None:
            raise RuntimeError("save_checkpoint requires a project-bound run")
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Checkpoint source not found: {source_path}")
        dest_dir = self._service.checkpoint_dir(self.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"step_{step}{src.suffix}"
        dest.write_bytes(src.read_bytes())
        rel_path = dest.relative_to(self._project.path)
        self._service.checkpoints.create(run_id=self.id, step=step, path=str(rel_path))
        return dest

    def finish(self) -> None:
        self._service.runs.update_status(self.id, "finished")


def _raise_project_required() -> Any:
    raise RuntimeError("A project is required. Use lumina.open_project() first.")
```

Create `src/lumina/experiments/__init__.py`:

```python
from lumina.experiments.run import Run
from lumina.experiments.service import ExperimentService

__all__ = ["Run", "ExperimentService"]
```

Modify `src/lumina/core/project.py` to attach service:

```python
from lumina.experiments.service import ExperimentService
```

And in `Project.__init__` after `self.datasets = ...` add:

```python
        self.experiments = ExperimentRepository(self._conn, self.path, self.id)
```

Wait — the repository wrapper is `ExperimentService`. Use that. Add:

```python
        self.experiments = ExperimentService(self._conn, self.path, self.id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_experiments_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/experiments src/lumina/core/project.py tests/test_experiments_run.py
git commit -m "feat: add Run SDK and ExperimentService"
```

---

### Task 4: Log adapters for JSONL and CSV

**Files:**
- Create: `src/lumina/experiments/log_adapters.py`
- Modify: `src/lumina/experiments/service.py`
- Test: `tests/test_log_adapters.py`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path

from lumina.experiments.log_adapters import JsonlLogAdapter, CsvLogAdapter


def test_jsonl_adapter(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    with open(log_file, "w") as f:
        f.write(json.dumps({"step": 1, "name": "loss", "value": 0.5}) + "\n")
        f.write(json.dumps({"step": 2, "name": "loss", "value": 0.4}) + "\n")

    adapter = JsonlLogAdapter()
    records = list(adapter.parse(log_file))
    assert len(records) == 2
    assert records[1] == {"step": 2, "name": "loss", "value": 0.4}


def test_csv_adapter(tmp_path):
    log_file = tmp_path / "metrics.csv"
    log_file.write_text("step,name,value\n1,loss,0.5\n2,loss,0.4\n")

    adapter = CsvLogAdapter()
    records = list(adapter.parse(log_file))
    assert len(records) == 2
    assert records[1] == {"step": 2, "name": "loss", "value": 0.4}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_log_adapters.py -v`
Expected: FAIL (adapter classes undefined)

- [ ] **Step 3: Implement adapters**

Create `src/lumina/experiments/log_adapters.py`:

```python
import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator


class LogAdapter(ABC):
    @abstractmethod
    def supports(self, path: Path) -> bool:
        ...

    @abstractmethod
    def parse(self, path: Path) -> Iterator[dict]:
        ...


class JsonlLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix == ".jsonl"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                yield {
                    "step": int(record["step"]),
                    "name": str(record["name"]),
                    "value": float(record["value"]),
                }


class CsvLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix == ".csv"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {
                    "step": int(row["step"]),
                    "name": str(row["name"]),
                    "value": float(row["value"]),
                }
```

Add a sync method to `ExperimentService` in `src/lumina/experiments/service.py`:

```python
import hashlib
import os

from lumina.experiments.log_adapters import JsonlLogAdapter, CsvLogAdapter


class ExperimentService:
    def __init__(...):
        ...
        self._adapters = [JsonlLogAdapter(), CsvLogAdapter()]

    def sync_log_dir(self, log_dir: Path, run_id: str) -> int:
        count = 0
        for adapter in self._adapters:
            for file_path in Path(log_dir).glob("*"):
                if not adapter.supports(file_path):
                    continue
                file_hash = hashlib.sha256(
                    f"{file_path}:{os.path.getmtime(file_path)}".encode()
                ).hexdigest()
                existing = self._conn.execute(
                    "SELECT 1 FROM sync_state WHERE file_hash = ?", (file_hash,)
                ).fetchone()
                if existing:
                    continue
                for record in adapter.parse(file_path):
                    self.metrics.create(
                        run_id=run_id, step=record["step"], name=record["name"], value=record["value"]
                    )
                    count += 1
                self._conn.execute(
                    "INSERT INTO sync_state (file_hash) VALUES (?)", (file_hash,)
                )
                self._conn.commit()
        return count
```

This requires a `sync_state` table. Add it in Task 1 or here. To keep this task self-contained, add it now by editing `src/lumina/storage/db.py`:

```sql
CREATE TABLE IF NOT EXISTS sync_state (
    file_hash TEXT PRIMARY KEY,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_log_adapters.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/experiments/log_adapters.py src/lumina/experiments/service.py src/lumina/storage/db.py tests/test_log_adapters.py
git commit -m "feat: add JSONL and CSV log adapters"
```

---

### Task 5: Optional TensorBoard events adapter

**Files:**
- Modify: `src/lumina/experiments/log_adapters.py`
- Modify: `src/lumina/experiments/service.py`
- Test: `tests/test_tensorboard_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from pathlib import Path


def test_tensorboard_adapter_available():
    from lumina.experiments.log_adapters import TensorBoardLogAdapter

    adapter = TensorBoardLogAdapter()
    assert adapter.supports(Path("events.out.tfevents.123"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_tensorboard_adapter.py -v`
Expected: FAIL (class undefined)

- [ ] **Step 3: Implement TensorBoard adapter**

Append to `src/lumina/experiments/log_adapters.py`:

```python
class TensorBoardLogAdapter(LogAdapter):
    def __init__(self):
        try:
            from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
            self._EventAccumulator = EventAccumulator
            self._available = True
        except Exception:
            self._available = False

    def supports(self, path: Path) -> bool:
        return "tfevents" in path.name

    def parse(self, path: Path) -> Iterator[dict]:
        if not self._available:
            raise RuntimeError("tensorboard is not installed; install it to parse tfevents files")
        acc = self._EventAccumulator(str(path))
        acc.Reload()
        tags = acc.Tags().get("scalars", [])
        for tag in tags:
            events = acc.Scalars(tag)
            for e in events:
                yield {"step": int(e.step), "name": tag, "value": float(e.value)}
```

Add it to the adapters list in `ExperimentService`:

```python
from lumina.experiments.log_adapters import JsonlLogAdapter, CsvLogAdapter, TensorBoardLogAdapter

        self._adapters = [JsonlLogAdapter(), CsvLogAdapter(), TensorBoardLogAdapter()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_tensorboard_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/experiments/log_adapters.py src/lumina/experiments/service.py tests/test_tensorboard_adapter.py
git commit -m "feat: add optional TensorBoard events adapter"
```

---

### Task 6: FastAPI endpoints for experiments

**Files:**
- Modify: `src/lumina/server.py`
- Modify: `src/lumina/experiments/service.py` (add `register_log_dir`)
- Test: `tests/test_server_experiments.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from lumina.server import create_app
from lumina.core.project import Project


def test_list_runs_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    from lumina.core.project_manager import ProjectManager
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )
    project.experiments.metrics.create(run_id="r1", step=1, name="loss", value=0.5)

    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/runs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_server_experiments.py::test_list_runs_endpoint -v`
Expected: FAIL (endpoint returns 404)

- [ ] **Step 3: Implement endpoints**

Add to `src/lumina/experiments/service.py`:

```python
    def register_log_dir(self, log_dir: Path, name: Optional[str] = None) -> dict:
        run_id = str(uuid.uuid4())
        log_dir = Path(log_dir).resolve()
        self.runs.create(
            run_id=run_id,
            project_id=self._project_id,
            name=name or log_dir.name,
            source="auto",
            log_dir=str(log_dir),
        )
        self.sync_log_dir(log_dir, run_id)
        return self.runs.get(run_id)
```

Add to `src/lumina/server.py` inside `create_app` when `project` is not None:

```python
    if project is not None:
        @app.get("/api/runs")
        def list_runs() -> list[dict]:
            return project.experiments.runs.list_by_project(project.id)

        @app.get("/api/runs/{run_id}")
        def get_run(run_id: str) -> dict:
            run = project.experiments.runs.get(run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="Run not found")
            return run

        @app.get("/api/metrics")
        def list_metrics(run_id: str, name: Optional[str] = None) -> list[dict]:
            return project.experiments.metrics.list_by_run(run_id, name=name)

        @app.get("/api/checkpoints")
        def list_checkpoints(run_id: str) -> list[dict]:
            return project.experiments.checkpoints.list_by_run(run_id)

        @app.get("/api/checkpoints/{checkpoint_id}/download")
        def download_checkpoint(checkpoint_id: int):
            import mimetypes
            row = project.experiments._conn.execute(
                "SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Checkpoint not found")
            file_path = project.path / row["path"]
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Checkpoint file missing")
            from fastapi.responses import FileResponse
            return FileResponse(
                path=str(file_path),
                filename=file_path.name,
                media_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
            )

        @app.post("/api/projects/{project_id}/logs")
        def register_log_dir(project_id: str, log_dir: str, name: Optional[str] = None) -> dict:
            if project_id != project.id:
                raise HTTPException(status_code=404, detail="Project not found")
            return project.experiments.register_log_dir(Path(log_dir), name=name)

        @app.post("/api/projects/{project_id}/logs/sync")
        def sync_log_dir(project_id: str, run_id: str) -> dict:
            if project_id != project.id:
                raise HTTPException(status_code=404, detail="Project not found")
            run = project.experiments.runs.get(run_id)
            if run is None or run["log_dir"] is None:
                raise HTTPException(status_code=400, detail="Run has no log directory")
            count = project.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
            return {"synced": count}

        @app.post("/api/projects/current/logs/sync")
        def sync_current_log_dir(run_id: str) -> dict:
            if project is None:
                raise HTTPException(status_code=404, detail="No project loaded")
            run = project.experiments.runs.get(run_id)
            if run is None or run["log_dir"] is None:
                raise HTTPException(status_code=400, detail="Run has no log directory")
            count = project.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
            return {"synced": count}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_server_experiments.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/server.py src/lumina/experiments/service.py tests/test_server_experiments.py
git commit -m "feat: add experiment API endpoints"
```

---

### Task 7: CLI commands for logs and runs

**Files:**
- Modify: `src/lumina/cli.py`
- Test: `tests/test_cli_experiments.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_project_logs_add(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "lumina", "project", "create", "p1"], check=True)
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')

    result = subprocess.run(
        [sys.executable, "-m", "lumina", "project", "logs", "add", str(log_dir), "--project", "p1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_experiments.py::test_cli_project_logs_add -v`
Expected: FAIL (subcommand missing)

- [ ] **Step 3: Implement CLI commands**

In `src/lumina/cli.py`, add under `project_sub`:

```python
    logs_parser = project_sub.add_parser("logs", help="Experiment log management")
    logs_sub = logs_parser.add_subparsers(dest="logs_command")

    logs_add_parser = logs_sub.add_parser("add", help="Register an external log directory")
    logs_add_parser.add_argument("path", help="Path to log directory")
    logs_add_parser.add_argument("--project", required=True, help="Project name")
    logs_add_parser.add_argument("--name", help="Run name")

    logs_sync_parser = logs_sub.add_parser("sync", help="Sync external logs")
    logs_sync_parser.add_argument("--project", required=True, help="Project name")
    logs_sync_parser.add_argument("--run-id", required=True, help="Run ID to sync")

    runs_parser = project_sub.add_parser("runs", help="List experiment runs")
    runs_sub = runs_parser.add_subparsers(dest="runs_command")
    runs_list_parser = runs_sub.add_parser("list", help="List runs")
    runs_list_parser.add_argument("--project", required=True, help="Project name")
```

Add dispatch branches:

```python
    elif args.command == "project" and args.project_command == "logs":
        if args.logs_command == "add":
            return _handle_logs_add(args)
        elif args.logs_command == "sync":
            return _handle_logs_sync(args)
    elif args.command == "project" and args.project_command == "runs":
        if args.runs_command == "list":
            return _handle_runs_list(args)
```

Add handlers:

```python
def _handle_logs_add(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open(args.project)
    run = project.experiments.register_log_dir(Path(args.path), name=args.name)
    print(f"Registered log run: {run['id']} ({run['name']})")
    return 0


def _handle_logs_sync(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open(args.project)
    count = project.experiments.sync_log_dir_for_run(args.run_id)
    print(f"Synced {count} metrics")
    return 0


def _handle_runs_list(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open(args.project)
    for run in project.experiments.runs.list_by_project(project.id):
        print(f"{run['id']}\t{run['name']}\t{run['status']}\t{run['created_at']}")
    return 0
```

Add helper to `ExperimentService`:

```python
    def sync_log_dir_for_run(self, run_id: str) -> int:
        run = self.runs.get(run_id)
        if run is None or run["log_dir"] is None:
            raise ValueError("Run has no log directory")
        return self.sync_log_dir(Path(run["log_dir"]), run_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_experiments.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/cli.py tests/test_cli_experiments.py
git commit -m "feat: add experiment CLI commands"
```

---

### Task 8: Python API helpers

**Files:**
- Modify: `src/lumina/api.py`
- Modify: `src/lumina/__init__.py`
- Test: `tests/test_api_experiments.py`

- [ ] **Step 1: Write the failing test**

```python
from lumina import create_project, start_run


def test_api_start_run(tmp_path):
    project = create_project("p1", root=str(tmp_path / "p1"))
    run = start_run(project=project, name="api-run")
    run.log("loss", 0.1, step=1)
    assert run.id is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_api_experiments.py -v`
Expected: FAIL (start_run undefined)

- [ ] **Step 3: Implement API helpers**

Add to `src/lumina/api.py`:

```python
from lumina.experiments.run import Run


def create_project(name: str, root: Optional[str] = None) -> Project:
    with ProjectManager(root=Path(root) if root else None) as manager:
        return manager.create(name)


def start_run(project: Project, name: Optional[str] = None) -> Run:
    return Run.start(project=project, name=name)
```

Modify `src/lumina/__init__.py`:

```python
from lumina.api import (
    view,
    view_project,
    analyze,
    export_config,
    generate_code,
    open_project,
    create_project,
    list_projects,
    start_run,
)
from lumina.core.project import Project
from lumina.core.project_manager import ProjectManager
from lumina.experiments.run import Run

__all__ = [
    "view",
    "view_project",
    "analyze",
    "export_config",
    "generate_code",
    "Project",
    "ProjectManager",
    "Run",
    "open_project",
    "create_project",
    "list_projects",
    "start_run",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_api_experiments.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/api.py src/lumina/__init__.py tests/test_api_experiments.py
git commit -m "feat: expose start_run in Python API"
```

---

### Task 9: Frontend types and API helpers

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Write the types and API helpers**

Add to `frontend/src/types.ts`:

```typescript
export interface Run {
  id: string
  name: string
  status: string
  source: string
  log_dir?: string
  created_at: string
  updated_at: string
}

export interface Metric {
  id: number
  run_id: string
  step: number
  name: string
  value: number
  timestamp: string
}

export interface Checkpoint {
  id: number
  run_id: string
  step: number
  path: string
  created_at: string
}
```

Add to `frontend/src/api.ts`:

```typescript
import { Run, Metric, Checkpoint } from './types'

export async function fetchRuns(): Promise<Run[]> {
  const res = await fetch('/api/runs')
  if (!res.ok) throw new Error('Failed to fetch runs')
  return res.json()
}

export async function fetchMetrics(runId: string, name?: string): Promise<Metric[]> {
  const query = name ? `?run_id=${runId}&name=${name}` : `?run_id=${runId}`
  const res = await fetch(`/api/metrics${query}`)
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

export async function fetchCheckpoints(runId: string): Promise<Checkpoint[]> {
  const res = await fetch(`/api/checkpoints?run_id=${runId}`)
  if (!res.ok) throw new Error('Failed to fetch checkpoints')
  return res.json()
}

export async function syncLogs(runId: string): Promise<{ synced: number }> {
  const res = await fetch(`/api/projects/current/logs/sync?run_id=${runId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to sync logs')
  return res.json()
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: builds without TypeScript errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts
git commit -m "feat: add experiment types and API helpers"
```

---

### Task 10: ExperimentsPanel UI

**Files:**
- Create: `frontend/src/panels/ExperimentsPanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create panel component**

Create `frontend/src/panels/ExperimentsPanel.tsx`:

```tsx
import { useEffect, useMemo, useState } from 'react'
import { fetchCheckpoints, fetchMetrics, fetchRuns, syncLogs } from '../api'
import { Checkpoint, Metric, Run } from '../types'

export default function ExperimentsPanel() {
  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [metricName, setMetricName] = useState<string>('')

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId) || null,
    [runs, selectedRunId]
  )

  useEffect(() => {
    fetchRuns().then((rs) => {
      setRuns(rs)
      if (rs.length > 0 && !selectedRunId) setSelectedRunId(rs[0].id)
    })
  }, [selectedRunId])

  useEffect(() => {
    if (!selectedRunId) return
    fetchMetrics(selectedRunId).then(setMetrics)
    fetchCheckpoints(selectedRunId).then(setCheckpoints)
  }, [selectedRunId])

  const metricNames = useMemo(
    () => Array.from(new Set(metrics.map((m) => m.name))),
    [metrics]
  )

  const filteredMetrics = useMemo(() => {
    if (!metricName) return metrics
    return metrics.filter((m) => m.name === metricName)
  }, [metrics, metricName])

  const handleSync = async () => {
    if (!selectedRunId) return
    await syncLogs(selectedRunId)
    const updated = await fetchMetrics(selectedRunId)
    setMetrics(updated)
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 240, borderRight: '1px solid #e0e0e0', padding: 12, overflow: 'auto' }}>
        <h3>Runs</h3>
        {runs.map((run) => (
          <div
            key={run.id}
            onClick={() => setSelectedRunId(run.id)}
            style={{
              padding: 8,
              marginBottom: 6,
              borderRadius: 4,
              cursor: 'pointer',
              background: run.id === selectedRunId ? '#dbeafe' : '#f3f4f6',
            }}
          >
            <div style={{ fontWeight: 'bold', fontSize: 13 }}>{run.name}</div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>
              {run.status} • {run.source}
            </div>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={handleSync}>Sync logs</button>
          <select value={metricName} onChange={(e) => setMetricName(e.target.value)}>
            <option value="">All metrics</option>
            {metricNames.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          {selectedRun && <span style={{ fontSize: 12, color: '#6b7280' }}>{selectedRun.name}</span>}
        </div>
        <MetricCurve metrics={filteredMetrics} />
        <CheckpointList checkpoints={checkpoints} />
      </div>
    </div>
  )
}

function MetricCurve({ metrics }: { metrics: Metric[] }) {
  const byName: Record<string, Metric[]> = {}
  metrics.forEach((m) => {
    if (!byName[m.name]) byName[m.name] = []
    byName[m.name].push(m)
  })

  return (
    <div style={{ flex: 1, border: '1px solid #e0e0e0', borderRadius: 6, padding: 12 }}>
      <h4 style={{ margin: '0 0 12px' }}>Metrics</h4>
      {Object.entries(byName).map(([name, values]) => (
        <div key={name} style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 'bold', marginBottom: 4 }}>{name}</div>
          <SimpleLine data={values} />
        </div>
      ))}
    </div>
  )
}

function SimpleLine({ data }: { data: Metric[] }) {
  const sorted = [...data].sort((a, b) => a.step - b.step)
  const values = sorted.map((d) => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 400
  const height = 80
  const points = sorted.map((d, i) => {
    const x = (i / (sorted.length - 1 || 1)) * width
    const y = height - ((d.value - min) / range) * height
    return `${x},${y}`
  })

  return (
    <svg width={width} height={height} style={{ background: '#f9fafb' }}>
      <polyline fill="none" stroke="#3b82f6" strokeWidth={2} points={points.join(' ')} />
    </svg>
  )
}

function CheckpointList({ checkpoints }: { checkpoints: Checkpoint[] }) {
  return (
    <div style={{ height: 160, border: '1px solid #e0e0e0', borderRadius: 6, padding: 12, overflow: 'auto' }}>
      <h4 style={{ margin: '0 0 12px' }}>Checkpoints</h4>
      <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '1px solid #e0e0e0' }}>
            <th>Step</th>
            <th>Path</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {checkpoints.map((ckpt) => (
            <tr key={ckpt.id}>
              <td>{ckpt.step}</td>
              <td>{ckpt.path}</td>
              <td>
                <a href={`/api/checkpoints/${ckpt.id}/download`} download>
                  Download
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Wire into App**

Modify `frontend/src/App.tsx`:

```tsx
import ExperimentsPanel from './panels/ExperimentsPanel'

const [mode, setMode] = useState<'project' | 'model' | 'experiments' | null>(null)
```

Add experiment button and panel render:

```tsx
        {mode === 'project' && (
          <>
            <button onClick={() => setMode('model')}>Model View</button>
            <button onClick={() => setMode('experiments')}>Experiments</button>
          </>
        )}
        {mode === 'experiments' && (
          <button onClick={() => setMode('project')}>Data View</button>
        )}
```

```tsx
      {mode === 'project' ? <DataPanel /> : mode === 'experiments' ? <ExperimentsPanel /> : <ModelPanel />}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: builds without errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/panels/ExperimentsPanel.tsx frontend/src/App.tsx
git commit -m "feat: add ExperimentsPanel UI"
```

---

### Task 11: Full integration test and final verification

**Files:**
- Create: `tests/test_experiments_integration.py`
- Modify: none

- [ ] **Step 1: Write integration test**

```python
from pathlib import Path

from fastapi.testclient import TestClient
from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def test_experiments_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    # SDK path
    run = project.experiments.runs.create(
        run_id="run-sdk", project_id=project.id, name="sdk-run", source="sdk"
    )
    project.experiments.metrics.create(run_id="run-sdk", step=1, name="loss", value=0.9)
    project.experiments.metrics.create(run_id="run-sdk", step=2, name="loss", value=0.7)

    # File path
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text(
        '{"step":1,"name":"accuracy","value":0.6}\n{"step":2,"name":"accuracy","value":0.8}\n'
    )
    project.experiments.register_log_dir(log_dir, name="file-run")

    app = create_app(project=project)
    client = TestClient(app)

    runs = client.get("/api/runs").json()
    assert len(runs) == 2

    file_run = next(r for r in runs if r["source"] == "auto")
    metrics = client.get(f"/api/metrics?run_id={file_run['id']}").json()
    assert len(metrics) == 2
```

- [ ] **Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_experiments_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Build frontend**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 5: Commit**

```bash
git add tests/test_experiments_integration.py
git commit -m "test: add experiments integration test"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| `runs` / `metrics` / `checkpoints` schema | Task 1 |
| Repository layer | Task 2 |
| SDK: `start_run`, `log`, `finish` | Task 3 |
| Checkpoint management | Task 3 |
| JSONL/CSV log adapters | Task 4 |
| TensorBoard adapter | Task 5 |
| FastAPI endpoints | Task 6 |
| CLI commands | Task 7 |
| Python API helpers | Task 8 |
| Frontend types/API | Task 9 |
| ExperimentsPanel UI | Task 10 |
| Integration + verification | Task 11 |

## Placeholder Scan

- No TBD/TODO/fill-in-details steps.
- Every code step includes concrete implementation code.
- Every test step includes concrete test code.
- Type names (`Run`, `ExperimentService`, `MetricRepository`, etc.) are consistent across tasks.
