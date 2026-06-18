import hashlib
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from lumina.experiments.evaluation_loader import EvaluationLoader
from lumina.experiments.log_adapters import CsvLogAdapter, JsonlLogAdapter, LogParseError, TensorBoardLogAdapter
from lumina.storage.repositories import CheckpointRepository, EvaluationRepository, MetricRepository, PredictionRepository, RunRepository


class EvaluationService:
    def __init__(self, conn: sqlite3.Connection, project_path: Path):
        self._conn = conn
        self._project_path = Path(project_path)
        self._repo = EvaluationRepository(conn)
        self._predictions = PredictionRepository(conn)

    def create(
        self,
        run_id: str,
        predictions_path: Path | str,
        dataset_id: Optional[str] = None,
        name: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> dict:
        source_path = Path(predictions_path)
        if not source_path.exists() or not source_path.is_file():
            raise ValueError(f"Predictions file does not exist: {predictions_path}")

        evaluation_id = str(uuid.uuid4())
        eval_dir = self._project_path / "evaluations" / evaluation_id
        eval_dir.mkdir(parents=True, exist_ok=True)

        local_predictions_path = eval_dir / "predictions.csv"
        shutil.copy2(source_path, local_predictions_path)

        loaded = EvaluationLoader.load(local_predictions_path, task_type=task_type)

        if name is None:
            name = source_path.name

        return self._repo.create(
            evaluation_id=evaluation_id,
            run_id=run_id,
            dataset_id=dataset_id,
            name=name,
            task_type=loaded["task_type"],
            predictions_path=str(local_predictions_path),
            metrics_json=loaded["metrics"],
            predictions=loaded["predictions"],
        )

    def get(self, evaluation_id: str, include_predictions: bool = False) -> Optional[dict]:
        evaluation = self._repo.get(evaluation_id)
        if evaluation is None:
            return None
        if include_predictions:
            evaluation["predictions"] = self._predictions.list_by_evaluation(evaluation_id)
        return evaluation

    def list_by_project(self, project_id: str) -> list[dict]:
        return self._repo.list_by_project(project_id)

    def list_by_run(self, run_id: str) -> list[dict]:
        return self._repo.list_by_run(run_id)

    def delete(self, evaluation_id: str) -> bool:
        deleted = self._repo.delete(evaluation_id)
        eval_dir = self._project_path / "evaluations" / evaluation_id
        if eval_dir.exists():
            shutil.rmtree(eval_dir)
        return deleted


class ExperimentService:
    def __init__(self, conn: sqlite3.Connection, project_path: Path, project_id: Optional[str] = None):
        self._conn = conn
        self._project_path = Path(project_path)
        self._project_id = project_id
        self.runs = RunRepository(conn)
        self.metrics = MetricRepository(conn)
        self.checkpoints = CheckpointRepository(conn)
        self.evaluations = EvaluationService(conn, project_path)
        self._adapters = [JsonlLogAdapter(), CsvLogAdapter(), TensorBoardLogAdapter()]

    def checkpoint_dir(self, run_id: str) -> Path:
        return self._project_path / "checkpoints" / run_id

    def sync_log_dir(self, log_dir: Path, run_id: str) -> int:
        count = 0
        log_dir = Path(log_dir).resolve()
        current_files = set()
        for file_path in log_dir.rglob("*"):
            if not file_path.is_file():
                continue
            current_files.add(str(file_path))
            for adapter in self._adapters:
                if not adapter.supports(file_path):
                    continue
                try:
                    content = file_path.read_bytes()
                    records = list(adapter.parse(file_path))
                except LogParseError:
                    # Skip files that fail to parse; other callers may choose to report them
                    continue
                content_hash = hashlib.sha256(content).hexdigest()
                state = self._conn.execute(
                    "SELECT file_hash FROM sync_state WHERE run_id = ? AND file_path = ?",
                    (run_id, str(file_path)),
                ).fetchone()
                if state and state["file_hash"] == content_hash:
                    continue
                self._conn.execute("SAVEPOINT file_sync")
                try:
                    self._conn.execute(
                        "DELETE FROM metrics WHERE run_id = ? AND source_file = ?",
                        (run_id, str(file_path)),
                    )
                    if records:
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
                    self._conn.execute("RELEASE file_sync")
                    self._conn.commit()
                except (sqlite3.Error, OSError):
                    self._conn.execute("ROLLBACK TO file_sync")
                    self._conn.execute("RELEASE file_sync")
                    continue
        # Clean up metrics/sync_state for files removed from the log dir
        known_files = {
            row["file_path"]
            for row in self._conn.execute(
                "SELECT file_path FROM sync_state WHERE run_id = ?", (run_id,)
            ).fetchall()
        }
        for removed_file in known_files - current_files:
            self._conn.execute(
                "DELETE FROM metrics WHERE run_id = ? AND source_file = ?",
                (run_id, removed_file),
            )
            self._conn.execute(
                "DELETE FROM sync_state WHERE run_id = ? AND file_path = ?",
                (run_id, removed_file),
            )
            self._conn.commit()
        return count

    def sync_log_dir_for_run(self, run_id: str) -> int:
        run = self.runs.get(run_id)
        if run is None or run["log_dir"] is None:
            raise ValueError("Run has no log directory")
        return self.sync_log_dir(Path(run["log_dir"]), run_id)

    def register_log_dir(self, log_dir: Path, name: Optional[str] = None) -> dict:
        log_dir = Path(log_dir).resolve()
        if not log_dir.exists() or not log_dir.is_dir():
            raise ValueError(f"Log directory does not exist: {log_dir}")
        run_id = str(uuid.uuid4())
        self.runs.create(
            run_id=run_id,
            project_id=self._project_id,
            name=name or log_dir.name,
            source="auto",
            log_dir=str(log_dir),
        )
        try:
            self.sync_log_dir(log_dir, run_id)
        except Exception:
            self.runs.delete(run_id)
            raise
        return self.runs.get(run_id)

    def get_checkpoint(self, checkpoint_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        return dict(row) if row else None
