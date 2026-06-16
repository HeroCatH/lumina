# Lumina Phase 1: Project + Data Panel + CLI Skeleton

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation of Lumina: project creation with SQLite metadata, a flat filesystem layout, a Dataset abstraction with CSV/Parquet adapters, and a CLI to manage projects and datasets.

**Architecture:** A `Project` class wraps a local directory + SQLite database. `Dataset` adapters read local files and expose a uniform API. FastAPI serves dataset previews and statistics, and the React frontend renders the first Data Panel.

**Tech Stack:** Python 3.12, SQLite, pydantic, polars (optional for CSV/Parquet), FastAPI, React, TypeScript.

---

## File Structure

```
src/lumina/
├── __init__.py
├── api.py
├── cli.py
├── config.py              # default paths
├── core/
│   ├── __init__.py
│   ├── project.py         # Project class
│   └── project_manager.py # list/create/open/delete projects
├── storage/
│   ├── __init__.py
│   ├── db.py              # SQLite connection + schema
│   └── repositories.py    # CRUD for projects/datasets
├── datasets/
│   ├── __init__.py
│   ├── dataset.py         # Dataset class
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py        # DatasetAdapter protocol
│   │   ├── csv.py         # CSVAdapter (polars)
│   │   └── parquet.py     # ParquetAdapter (polars)
│   └── registry.py        # adapter dispatch
└── server.py              # extend with dataset endpoints

frontend/src/
├── panels/
│   └── DataPanel.tsx      # new data panel
└── App.tsx                # add project-aware routing

tests/
├── test_project.py
├── test_storage.py
├── test_dataset_csv.py
├── test_dataset_parquet.py
└── test_dataset_stats.py
```

---

## Task 1: Project Storage Layer

**Files:**
- Create: `src/lumina/config.py`
- Create: `src/lumina/storage/__init__.py`
- Create: `src/lumina/storage/db.py`
- Create: `src/lumina/storage/repositories.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing test for project repository**

```python
# tests/test_storage.py
from pathlib import Path
from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import ProjectRepository


def test_create_and_get_project(tmp_path):
    db_path = tmp_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("test_project", str(tmp_path))
    project = repo.get_by_name("test_project")
    assert project["name"] == "test_project"
    assert project["path"] == str(tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_storage.py::test_create_and_get_project -v`
Expected: FAIL with modules not found

- [ ] **Step 3: Write `src/lumina/config.py`**

```python
from pathlib import Path

DEFAULT_PROJECTS_ROOT = Path.home() / "lumina_projects"
DB_FILENAME = "lumina.db"
```

- [ ] **Step 4: Write `src/lumina/storage/db.py`**

```python
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    path TEXT,
    adapter_type TEXT NOT NULL,
    schema_json TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, name)
);
"""


def get_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def init_project_db(project_path: Path) -> sqlite3.Connection:
    db_path = project_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)
    return conn
```

- [ ] **Step 5: Write `src/lumina/storage/repositories.py`**

```python
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional


class ProjectRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, name: str, path: str) -> dict:
        project_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO projects (id, name, path) VALUES (?, ?, ?)",
            (project_id, name, path),
        )
        self._conn.commit()
        return {"id": project_id, "name": name, "path": path}

    def get_by_name(self, name: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM projects WHERE name = ?", (name,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def delete(self, name: str) -> bool:
        cur = self._conn.execute("DELETE FROM projects WHERE name = ?", (name,))
        self._conn.commit()
        return cur.rowcount > 0


class DatasetRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        project_id: str,
        name: str,
        path: str,
        adapter_type: str,
        schema_json: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> dict:
        dataset_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO datasets (id, project_id, name, path, adapter_type, schema_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (dataset_id, project_id, name, path, adapter_type, schema_json, metadata_json),
        )
        self._conn.commit()
        return {"id": dataset_id, "project_id": project_id, "name": name, "path": path, "adapter_type": adapter_type}

    def get_by_name(self, project_id: str, name: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM datasets WHERE project_id = ? AND name = ?",
            (project_id, name),
        ).fetchone()
        return dict(row) if row else None

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM datasets WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_storage.py::test_create_and_get_project -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/lumina/config.py src/lumina/storage tests/test_storage.py
git commit -m "feat: add SQLite storage layer for projects and datasets"
```

---

## Task 2: Project Python API and Manager

**Files:**
- Create: `src/lumina/core/__init__.py`
- Create: `src/lumina/core/project.py`
- Create: `src/lumina/core/project_manager.py`
- Modify: `src/lumina/api.py`
- Create: `tests/test_project.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_project.py
from pathlib import Path
from lumina.core.project_manager import ProjectManager


def test_create_and_open_project(tmp_path):
    manager = ProjectManager(root=tmp_path)
    project = manager.create("test_project")
    assert project.path.exists()
    assert (project.path / "lumina.db").exists()
    assert project.id

    same = manager.open("test_project")
    assert same.name == "test_project"
    assert same.path == project.path
    assert same.id == project.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_project.py::test_create_and_open_project -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/core/project.py`**

```python
from pathlib import Path
import sqlite3

from lumina.storage.db import init_project_db
from lumina.storage.repositories import DatasetRepository, ProjectRepository


class Project:
    def __init__(self, project_id: str, name: str, path: Path):
        self.id = project_id
        self.name = name
        self.path = Path(path)
        self._db_path = self.path / "lumina.db"
        self._conn = init_project_db(self.path)
        self.datasets = DatasetRepository(self._conn)

    def close(self) -> None:
        self._conn.close()

    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, path={self.path})"
```

- [ ] **Step 4: Write `src/lumina/core/project_manager.py`**

```python
from pathlib import Path
from typing import Optional

from lumina.config import DEFAULT_PROJECTS_ROOT
from lumina.core.project import Project
from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import ProjectRepository


class ProjectManager:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or DEFAULT_PROJECTS_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)
        self._global_db_path = self.root / "lumina.db"
        self._conn = get_db(self._global_db_path)
        init_schema(self._conn)
        self._repo = ProjectRepository(self._conn)

    def create(self, name: str, path: Optional[Path] = None) -> Project:
        if path is None:
            path = self.root / name
        path = Path(path).expanduser().resolve()
        if path.exists() and any(path.iterdir()):
            raise ValueError(f"Project directory already exists and is not empty: {path}")
        path.mkdir(parents=True, exist_ok=True)

        record = self._repo.create(name, str(path))
        return Project(project_id=record["id"], name=record["name"], path=Path(record["path"]))

    def open(self, name: str) -> Project:
        record = self._repo.get_by_name(name)
        if record is None:
            raise ValueError(f"Project not found: {name}")
        return Project(project_id=record["id"], name=record["name"], path=Path(record["path"]))

    def list(self) -> list[dict]:
        return self._repo.list_all()

    def delete(self, name: str) -> None:
        import shutil

        record = self._repo.get_by_name(name)
        if record is None:
            raise ValueError(f"Project not found: {name}")
        self._repo.delete(name)
        shutil.rmtree(record["path"], ignore_errors=True)

    def close(self) -> None:
        self._conn.close()
```

- [ ] **Step 5: Modify `src/lumina/api.py`**

Add project helper functions:

```python
from pathlib import Path
from typing import Optional

from lumina.core.project import Project
from lumina.core.project_manager import ProjectManager


def open_project(name: str, path: Optional[str] = None) -> Project:
    manager = ProjectManager()
    return manager.open(name)


def create_project(name: str, path: Optional[str] = None) -> Project:
    manager = ProjectManager()
    return manager.create(name, Path(path) if path else None)


def list_projects() -> list[dict]:
    manager = ProjectManager()
    return manager.list()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_project.py::test_create_and_open_project -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/lumina/core src/lumina/api.py tests/test_project.py
git commit -m "feat: add Project and ProjectManager with Python API"
```

---

## Task 3: Dataset Abstraction + CSV Adapter

**Files:**
- Create: `src/lumina/datasets/__init__.py`
- Create: `src/lumina/datasets/dataset.py`
- Create: `src/lumina/datasets/adapters/__init__.py`
- Create: `src/lumina/datasets/adapters/base.py`
- Create: `src/lumina/datasets/adapters/csv.py`
- Create: `src/lumina/datasets/registry.py`
- Modify: `src/lumina/core/project.py`
- Create: `tests/test_dataset_csv.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_dataset_csv.py
from pathlib import Path
from lumina.datasets.adapters.csv import CSVAdapter


def test_csv_adapter(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    adapter = CSVAdapter()
    df = adapter.load(csv_path)
    preview = adapter.preview(df, n=2)
    assert len(preview) == 2
    assert preview[0] == {"a": "1", "b": "2", "c": "3"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_dataset_csv.py::test_csv_adapter -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/datasets/adapters/base.py`**

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class DatasetAdapter(ABC):
    name: str = ""
    supported_extensions: list[str] = []

    @abstractmethod
    def load(self, path: Path) -> Any:
        raise NotImplementedError

    @abstractmethod
    def preview(self, data: Any, n: int = 10) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def schema(self, data: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def statistics(self, data: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def row_count(self, data: Any) -> int:
        raise NotImplementedError
```

- [ ] **Step 4: Write `src/lumina/datasets/adapters/csv.py`**

```python
from pathlib import Path
from typing import Any

from lumina.datasets.adapters.base import DatasetAdapter


class CSVAdapter(DatasetAdapter):
    name = "csv"
    supported_extensions = [".csv"]

    def load(self, path: Path) -> Any:
        import polars as pl

        return pl.read_csv(path)

    def preview(self, data: Any, n: int = 10) -> list[dict]:
        return data.head(n).to_dicts()

    def schema(self, data: Any) -> dict:
        return {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)}

    def statistics(self, data: Any) -> dict:
        numeric = data.select(data.select(pl.col(pl.NUMERIC_DTYPES)).columns)
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": data.columns,
            "numeric_summary": numeric.describe().to_dicts() if numeric.columns else [],
        }

    def row_count(self, data: Any) -> int:
        return len(data)
```

- [ ] **Step 5: Write `src/lumina/datasets/registry.py`**

```python
from pathlib import Path
from typing import Type

from lumina.datasets.adapters.base import DatasetAdapter
from lumina.datasets.adapters.csv import CSVAdapter


_ADAPTERS: dict[str, Type[DatasetAdapter]] = {
    CSVAdapter.name: CSVAdapter,
}


def register_adapter(adapter_cls: Type[DatasetAdapter]) -> None:
    _ADAPTERS[adapter_cls.name] = adapter_cls


def get_adapter(adapter_type: str) -> DatasetAdapter:
    if adapter_type not in _ADAPTERS:
        raise ValueError(f"Unknown dataset adapter: {adapter_type}")
    return _ADAPTERS[adapter_type]()


def detect_adapter(path: Path) -> str:
    suffix = path.suffix.lower()
    for name, cls in _ADAPTERS.items():
        if suffix in cls.supported_extensions:
            return name
    raise ValueError(f"Cannot detect adapter for path: {path}")
```

- [ ] **Step 6: Write `src/lumina/datasets/dataset.py`**

```python
from pathlib import Path
from typing import Any, Optional

from lumina.datasets.adapters.base import DatasetAdapter
from lumina.datasets.registry import detect_adapter, get_adapter


class Dataset:
    def __init__(
        self,
        name: str,
        path: Path,
        adapter_type: str,
        project_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.path = Path(path)
        self.adapter_type = adapter_type
        self.project_id = project_id
        self.metadata = metadata or {}
        self._adapter = get_adapter(adapter_type)
        self._data = self._adapter.load(self.path)

    def preview(self, n: int = 10) -> list[dict]:
        return self._adapter.preview(self._data, n)

    def schema(self) -> dict:
        return self._adapter.schema(self._data)

    def statistics(self) -> dict:
        return self._adapter.statistics(self._data)

    def row_count(self) -> int:
        return self._adapter.row_count(self._data)

    @classmethod
    def from_path(cls, name: str, path: str, adapter_type: Optional[str] = None) -> "Dataset":
        path_obj = Path(path)
        adapter = adapter_type or detect_adapter(path_obj)
        return cls(name=name, path=path_obj, adapter_type=adapter)
```

- [ ] **Step 7: Modify `src/lumina/core/project.py`**

```python
from pathlib import Path
from lumina.datasets.dataset import Dataset


class Project:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = Path(path)
        self._db_path = self.path / "lumina.db"
        self._conn = init_project_db(self.path)
        self.datasets = DatasetRepository(self._conn)

    def register_dataset(
        self,
        name: str,
        path: str,
        adapter_type: Optional[str] = None,
    ) -> Dataset:
        from lumina.datasets.registry import detect_adapter

        source = Path(path)
        if not source.is_absolute():
            source = (self.path / "datasets" / source).resolve()

        # Copy file into project if outside
        target = self.path / "datasets" / source.name
        if source.resolve() != target.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            import shutil

            shutil.copy2(source, target)

        adapter = adapter_type or detect_adapter(target)
        dataset = Dataset(name=name, path=target, adapter_type=adapter, project_id=None)
        schema = dataset.schema()
        import json

        self.datasets.create(
            project_id=self.id,
            name=name,
            path=str(target),
            adapter_type=adapter,
            schema_json=json.dumps(schema),
            metadata_json=json.dumps({"row_count": dataset.row_count()}),
        )
        return dataset
```

Note: This simplified `_project_id` is acceptable for Phase 1. We will improve in later phases.

- [ ] **Step 8: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_dataset_csv.py::test_csv_adapter -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add src/lumina/datasets src/lumina/core/project.py tests/test_dataset_csv.py
git commit -m "feat: add Dataset abstraction and CSV adapter"
```

---

## Task 4: Parquet Adapter

**Files:**
- Create: `src/lumina/datasets/adapters/parquet.py`
- Modify: `src/lumina/datasets/registry.py`
- Create: `tests/test_dataset_parquet.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_dataset_parquet.py
from pathlib import Path
import pytest

polars = pytest.importorskip("polars")

from lumina.datasets.adapters.parquet import ParquetAdapter


def test_parquet_adapter(tmp_path):
    path = tmp_path / "data.parquet"
    df = polars.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.write_parquet(path)

    adapter = ParquetAdapter()
    loaded = adapter.load(path)
    preview = adapter.preview(loaded, n=2)
    assert len(preview) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_dataset_parquet.py::test_parquet_adapter -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/datasets/adapters/parquet.py`**

```python
from pathlib import Path
from typing import Any

from lumina.datasets.adapters.base import DatasetAdapter


class ParquetAdapter(DatasetAdapter):
    name = "parquet"
    supported_extensions = [".parquet"]

    def load(self, path: Path) -> Any:
        import polars as pl

        return pl.read_parquet(path)

    def preview(self, data: Any, n: int = 10) -> list[dict]:
        return data.head(n).to_dicts()

    def schema(self, data: Any) -> dict:
        return {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)}

    def statistics(self, data: Any) -> dict:
        numeric = data.select(data.select(pl.col(pl.NUMERIC_DTYPES)).columns)
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": data.columns,
            "numeric_summary": numeric.describe().to_dicts() if numeric.columns else [],
        }

    def row_count(self, data: Any) -> int:
        return len(data)
```

- [ ] **Step 4: Modify `src/lumina/datasets/registry.py`**

```python
from lumina.datasets.adapters.csv import CSVAdapter
from lumina.datasets.adapters.parquet import ParquetAdapter


_ADAPTERS: dict[str, Type[DatasetAdapter]] = {
    CSVAdapter.name: CSVAdapter,
    ParquetAdapter.name: ParquetAdapter,
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_dataset_parquet.py::test_parquet_adapter -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/lumina/datasets/adapters/parquet.py src/lumina/datasets/registry.py tests/test_dataset_parquet.py
git commit -m "feat: add Parquet dataset adapter"
```

---

## Task 5: Dataset Statistics

**Files:**
- Modify: `src/lumina/datasets/adapters/csv.py`
- Modify: `src/lumina/datasets/adapters/parquet.py`
- Create: `tests/test_dataset_stats.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_dataset_stats.py
from pathlib import Path
from lumina.datasets.dataset import Dataset


def test_dataset_statistics(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,x\n4,5,y\n7,8,z\n")
    dataset = Dataset.from_path("test", str(csv_path))
    stats = dataset.statistics()
    assert stats["row_count"] == 3
    assert stats["column_count"] == 3
    assert "a" in stats["columns"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_dataset_stats.py::test_dataset_statistics -v`
Expected: FAIL

- [ ] **Step 3: Improve statistics output**

Update both CSV and Parquet adapters to include:

```python
def statistics(self, data: Any) -> dict:
    import polars as pl

    numeric = data.select(data.select(pl.col(pl.NUMERIC_DTYPES)).columns)
    return {
        "row_count": len(data),
        "column_count": len(data.columns),
        "columns": data.columns,
        "column_types": {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)},
        "numeric_summary": numeric.describe().to_dicts() if numeric.columns else [],
        "missing_counts": {name: data[name].null_count() for name in data.columns},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_dataset_stats.py::test_dataset_statistics -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/datasets/adapters tests/test_dataset_stats.py
git commit -m "feat: enrich dataset statistics with types and missing counts"
```

---

## Task 6: FastAPI Dataset Endpoints

**Files:**
- Modify: `src/lumina/server.py`
- Modify: `src/lumina/api.py`
- Create: `tests/test_server_datasets.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_server_datasets.py
from pathlib import Path
from fastapi.testclient import TestClient
from lumina.core.project import Project
from lumina.server import create_app


def test_dataset_preview_endpoint(tmp_path):
    project = Project(name="test", path=tmp_path)
    csv_path = tmp_path / "datasets" / "data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("a,b\n1,2\n3,4\n")
    project.register_dataset("data", str(csv_path))

    app = create_app(project)
    client = TestClient(app)
    response = client.get("/api/datasets/data/preview?n=2")
    assert response.status_code == 200
    assert len(response.json()["rows"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_server_datasets.py::test_dataset_preview_endpoint -v`
Expected: FAIL

- [ ] **Step 3: Modify `src/lumina/server.py`**

Change `create_app` to accept a `Project` and add dataset endpoints:

```python
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from lumina.core.project import Project
from lumina.graph import ModelGraph
from lumina.loaders import load_model


STATIC_DIR = Path(__file__).parent / "static"


def create_app(project: Optional[Project] = None, model: Optional[Any] = None) -> FastAPI:
    app = FastAPI(title="Lumina")

    @app.get("/api/projects/current")
    def get_current_project() -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        return {"name": project.name, "path": str(project.path)}

    @app.get("/api/datasets")
    def list_datasets() -> list[dict]:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        return project.datasets.list_by_project(project.id)

    @app.get("/api/datasets/{name}/preview")
    def preview_dataset(name: str, n: int = 10) -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        record = project.datasets.get_by_name(project.id, name)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Dataset {name} not found")
        from lumina.datasets.dataset import Dataset

        ds = Dataset(name=record["name"], path=Path(record["path"]), adapter_type=record["adapter_type"])
        return {"rows": ds.preview(n), "schema": ds.schema(), "statistics": ds.statistics()}

    # Existing model endpoints kept for backward compatibility
    if model is not None:
        graph = load_model(model)

        @app.get("/api/graph")
        def get_graph() -> dict:
            return {
                "nodes": [
                    {
                        "id": n.id,
                        "type": n.type,
                        "params": n.params,
                        "display_name": n.display_name or n.id,
                    }
                    for n in graph.nodes
                ],
                "edges": [{"source": e.source, "target": e.target} for e in graph.edges],
                "metadata": graph.metadata,
            }

        @app.get("/api/stats")
        def get_stats() -> dict:
            from lumina.analyzers.params import ParamAnalyzer

            return ParamAnalyzer().analyze(graph)

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app
```

- [ ] **Step 4: Modify `src/lumina/api.py`**

```python
def view_project(project: Project, port: int = 8080, open_browser: bool = True) -> None:
    app = create_app(project=project)
    if open_browser:
        webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_server_datasets.py::test_dataset_preview_endpoint -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/lumina/server.py src/lumina/api.py tests/test_server_datasets.py
git commit -m "feat: add FastAPI dataset preview endpoints"
```

---

## Task 7: Frontend Data Panel

**Files:**
- Create: `frontend/src/panels/DataPanel.tsx`
- Create: `frontend/src/hooks/useApi.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/types.ts`

- [ ] **Step 1: Add dataset types**

Modify `frontend/src/types.ts`:

```typescript
export interface DatasetInfo {
  id: string
  name: string
  adapter_type: string
  row_count?: number
}

export interface DatasetPreview {
  rows: Record<string, any>[]
  schema: Record<string, string>
  statistics: {
    row_count: number
    column_count: number
    columns: string[]
    column_types: Record<string, string>
    missing_counts: Record<string, number>
    numeric_summary: Record<string, any>[]
  }
}
```

- [ ] **Step 2: Create `frontend/src/hooks/useApi.ts`**

```typescript
import { DatasetInfo, DatasetPreview, ModelGraph, Stats } from '../types'

export async function fetchCurrentProject(): Promise<{ name: string; path: string }> {
  const res = await fetch('/api/projects/current')
  if (!res.ok) throw new Error('No project loaded')
  return res.json()
}

export async function fetchDatasets(): Promise<DatasetInfo[]> {
  const res = await fetch('/api/datasets')
  if (!res.ok) throw new Error('Failed to fetch datasets')
  return res.json()
}

export async function fetchDatasetPreview(name: string, n: number = 50): Promise<DatasetPreview> {
  const res = await fetch(`/api/datasets/${name}/preview?n=${n}`)
  if (!res.ok) throw new Error(`Failed to fetch dataset ${name}`)
  return res.json()
}
```

- [ ] **Step 3: Create `frontend/src/panels/DataPanel.tsx`**

```typescript
import { useEffect, useState } from 'react'
import { fetchDatasets, fetchDatasetPreview } from '../hooks/useApi'
import { DatasetInfo, DatasetPreview } from '../types'

export default function DataPanel() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    fetchDatasetPreview(selected).then(setPreview).catch((e) => setError(e.message))
  }, [selected])

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: 260, borderRight: '1px solid #e0e0e0', padding: 12 }}>
        <h3>Datasets</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {datasets.map((ds) => (
            <li
              key={ds.id}
              onClick={() => setSelected(ds.name)}
              style={{
                padding: '8px',
                cursor: 'pointer',
                background: ds.name === selected ? '#e6f7ff' : 'transparent',
              }}
            >
              <div>{ds.name}</div>
              <div style={{ fontSize: 12, color: '#888' }}>{ds.adapter_type}</div>
            </li>
          ))}
        </ul>
      </div>
      <div style={{ flex: 1, padding: 12, overflow: 'auto' }}>
        {preview ? (
          <div>
            <h3>{selected}</h3>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
              <StatCard label="Rows" value={preview.statistics.row_count} />
              <StatCard label="Columns" value={preview.statistics.column_count} />
            </div>
            <h4>Preview</h4>
            <table style={{ borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {preview.statistics.columns.map((col) => (
                    <th key={col} style={{ border: '1px solid #ddd', padding: 6 }}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx}>
                    {preview.statistics.columns.map((col) => (
                      <td key={col} style={{ border: '1px solid #ddd', padding: 6 }}>{String(row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Select a dataset to preview.</p>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: '1px solid #e0e0e0', borderRadius: 6, padding: 12, minWidth: 100 }}>
      <div style={{ fontSize: 12, color: '#888' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 600 }}>{value}</div>
    </div>
  )
}
```

- [ ] **Step 4: Modify `frontend/src/App.tsx`**

```typescript
import { useEffect, useState } from 'react'
import { fetchCurrentProject } from './hooks/useApi'
import DataPanel from './panels/DataPanel'

export default function App() {
  const [project, setProject] = useState<{ name: string; path: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCurrentProject()
      .then(setProject)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>
  if (!project) return <div style={{ padding: 20 }}>Loading project...</div>

  return (
    <div>
      <header style={{ padding: '12px 20px', borderBottom: '1px solid #e0e0e0' }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>Lumina</h1>
        <div style={{ fontSize: 12, color: '#666' }}>{project.name}</div>
      </header>
      <DataPanel />
    </div>
  )
}
```

- [ ] **Step 5: Build frontend**

Run:
```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/panels frontend/src/hooks frontend/src/App.tsx frontend/src/types.ts src/lumina/static
git commit -m "feat: add frontend DataPanel with dataset list and preview"
```

---

## Task 8: CLI Project and Data Commands

**Files:**
- Modify: `src/lumina/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli.py
from pathlib import Path
from lumina.cli import main


def test_cli_version(capsys):
    assert main(["version"]) == 0
    captured = capsys.readouterr()
    assert "lumina" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py::test_cli_version -v`
Expected: PASS (version already exists)

- [ ] **Step 3: Write CLI project create test**

```python
def test_cli_project_create(tmp_path):
    code = main(["project", "create", "cli_test", "--path", str(tmp_path / "cli_test")])
    assert code == 0
    assert (tmp_path / "cli_test" / "lumina.db").exists()
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py::test_cli_project_create -v`
Expected: FAIL

- [ ] **Step 5: Modify `src/lumina/cli.py`**

Replace the placeholder project create handler:

```python
def _handle_project_create(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    path = Path(args.path) if args.path else None
    project = manager.create(args.name, path)
    print(f"Created project: {project.name} at {project.path}")
    return 0
```

Add project list command:

```python
list_parser = project_sub.add_parser("list", help="List projects")
```

Handle it:

```python
elif args.command == "project" and args.project_command == "list":
    return _handle_project_list()
```

```python
def _handle_project_list() -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    for project in manager.list():
        print(f"{project['name']}\t{project['path']}")
    return 0
```

Add data add command:

```python
data_parser = subparsers.add_parser("data", help="Dataset management")
data_sub = data_parser.add_subparsers(dest="data_command")
add_data_parser = data_sub.add_parser("add", help="Add a dataset to the current project")
add_data_parser.add_argument("name", help="Dataset name")
add_data_parser.add_argument("path", help="Path to dataset file")
add_data_parser.add_argument("--adapter", help="Adapter type (auto-detect if omitted)")
add_data_parser.add_argument("--project", required=True, help="Project name")
```

Handle it:

```python
elif args.command == "data" and args.data_command == "add":
    return _handle_data_add(args)
```

```python
def _handle_data_add(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open(args.project)
    dataset = project.register_dataset(args.name, args.path, args.adapter)
    print(f"Added dataset: {dataset.name} ({dataset.adapter_type})")
    return 0
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/lumina/cli.py tests/test_cli.py
git commit -m "feat: extend CLI with project and dataset commands"
```

---

## Task 9: Integration and Documentation

**Files:**
- Modify: `README.md`
- Create: `examples/project_demo.py`
- Create: `examples/cli_demo.sh`

- [ ] **Step 1: Update `README.md`**

Add Phase 1 usage:

```markdown
## Project + Data Workflow

```bash
# Create project
lumina project create my_project

# Add dataset
lumina data add train data/train.csv --project my_project

# Open UI
lumina project open my_project
```

```python
import lumina

project = lumina.open_project("my_project")
project.register_dataset("train", "data/train.csv")

lumina.view_project(project, port=8080)
```
```

- [ ] **Step 2: Create `examples/project_demo.py`**

```python
import lumina
from pathlib import Path

# Create a demo project
project = lumina.create_project("demo_project")

# Create a sample CSV
csv_path = project.path / "datasets" / "sample.csv"
csv_path.parent.mkdir(parents=True, exist_ok=True)
csv_path.write_text("x,y,label\n1,2,A\n3,4,B\n5,6,A\n")

# Register dataset
project.register_dataset("sample", str(csv_path))

# Open UI
lumina.view_project(project, port=8080)
```

- [ ] **Step 3: Create `examples/cli_demo.sh`**

```bash
#!/bin/bash
set -e

lumina project create demo_project --path ./demo_project
lumina data add sample examples/sample_data.csv --project demo_project
lumina project open demo_project
```

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add README.md examples/project_demo.py examples/cli_demo.sh
git commit -m "docs: add Phase 1 project and data workflow examples"
```

---

## Spec Coverage Check

| Spec Section | Task |
|--------------|------|
| Project concept + directory layout | Task 1, Task 2 |
| SQLite schema | Task 1 |
| Dataset abstraction | Task 3 |
| CSV / Parquet adapters | Task 3, Task 4 |
| Data preview + statistics | Task 3, Task 5 |
| CLI project/data commands | Task 8 |
| FastAPI dataset endpoints | Task 6 |
| Frontend Data Panel | Task 7 |

---

## Phase 1 Completion Criteria

- [ ] `lumina project create/list/open/delete` works
- [ ] `lumina data add` works
- [ ] `lumina.open_project()` and `project.register_dataset()` work
- [ ] CSV and Parquet datasets can be previewed and analyzed
- [ ] FastAPI serves `/api/projects/current`, `/api/datasets`, `/api/datasets/{name}/preview`
- [ ] Frontend DataPanel shows dataset list, preview table, and statistics cards
- [ ] All tests pass
