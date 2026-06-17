import hashlib
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

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
        log_dir = Path(log_dir).resolve()
        for file_path in log_dir.iterdir():
            if not file_path.is_file():
                continue
            for adapter in self._adapters:
                if not adapter.supports(file_path):
                    continue
                try:
                    content = file_path.read_bytes()
                    records = list(adapter.parse(file_path))
                except Exception:
                    # Roll back any partial state for this file and skip it
                    self._conn.rollback()
                    continue
                content_hash = hashlib.sha256(content).hexdigest()
                state = self._conn.execute(
                    "SELECT file_hash FROM sync_state WHERE run_id = ? AND file_path = ?",
                    (run_id, str(file_path)),
                ).fetchone()
                if state and state["file_hash"] == content_hash:
                    continue
                if records:
                    self._conn.execute(
                        "DELETE FROM metrics WHERE run_id = ? AND source_file = ?",
                        (run_id, str(file_path)),
                    )
                    self._conn.executemany(
                        "INSERT INTO metrics (run_id, step, name, value, source_file) VALUES (?, ?, ?, ?, ?)",
                        [
                            (run_id, r["step"], r["name"], r["value"], str(file_path))
                            for r in records
                        ],
                    )
                    count += len(records)
                self._conn.execute(
                    """
                    INSERT INTO sync_state (run_id, file_path, file_hash)
                    VALUES (?, ?, ?)
                    ON CONFLICT(run_id, file_path) DO UPDATE SET
                        file_hash = excluded.file_hash,
                        synced_at = CURRENT_TIMESTAMP
                    """,
                    (run_id, str(file_path), content_hash),
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
