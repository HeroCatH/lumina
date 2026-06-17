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
