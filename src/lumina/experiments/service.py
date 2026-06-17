import hashlib
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Iterator, Optional

from lumina.experiments.log_adapters import CsvLogAdapter, JsonlLogAdapter
from lumina.storage.repositories import CheckpointRepository, MetricRepository, RunRepository


class ExperimentService:
    def __init__(self, conn: sqlite3.Connection, project_path: Path, project_id: Optional[str] = None):
        self._conn = conn
        self._project_path = Path(project_path)
        self._project_id = project_id
        self.runs = RunRepository(conn)
        self.metrics = MetricRepository(conn)
        self.checkpoints = CheckpointRepository(conn)
        self._adapters = [JsonlLogAdapter(), CsvLogAdapter()]

    def checkpoint_dir(self, run_id: str) -> Path:
        return self._project_path / "checkpoints" / run_id

    def sync_log_dir(self, log_dir: Path, run_id: str) -> int:
        count = 0
        for file_path in Path(log_dir).glob("*"):
            for adapter in self._adapters:
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
