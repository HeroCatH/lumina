import json
from pathlib import Path
import shutil
import sqlite3
from typing import Optional

from lumina.datasets.dataset import Dataset
from lumina.datasets.registry import detect_adapter
from lumina.storage.db import init_project_db
from lumina.storage.repositories import DatasetRepository, ProjectRepository


class Project:
    def __init__(self, project_id: str, name: str, path: Path):
        self.id = project_id
        self.name = name
        self.path = Path(path)
        self._db_path = self.path / "lumina.db"
        self._conn = init_project_db(self.path)
        self._ensure_project_row()
        self.datasets = DatasetRepository(self._conn)

    def _ensure_project_row(self) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO projects (id, name, path) VALUES (?, ?, ?)",
            (self.id, self.name, str(self.path)),
        )
        self._conn.commit()

    def register_dataset(
        self,
        name: str,
        path: str,
        adapter_type: Optional[str] = None,
    ) -> Dataset:
        source = Path(path)
        if not source.is_absolute():
            source = (self.path / "datasets" / source).resolve()
        else:
            source = source.resolve()

        datasets_dir = self.path / "datasets"
        try:
            relative_source = source.relative_to(datasets_dir)
        except ValueError:
            relative_source = source.name
        target = datasets_dir / relative_source

        if source != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        adapter = adapter_type or detect_adapter(target)
        dataset = Dataset(name=name, path=target, adapter_type=adapter, project_id=self.id)
        schema = dataset.schema()
        self.datasets.create(
            project_id=self.id,
            name=name,
            path=str(target),
            adapter_type=adapter,
            schema_json=json.dumps(schema),
            metadata_json=json.dumps({"row_count": dataset.row_count()}),
        )
        return dataset

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Project":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, path={self.path})"
