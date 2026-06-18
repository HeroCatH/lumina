import sqlite3
import uuid
from pathlib import Path
from typing import Optional


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

    def delete(self, run_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        self._conn.commit()
        return cur.rowcount > 0


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


class EvaluationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._predictions = PredictionRepository(conn)

    def create(
        self,
        evaluation_id: str,
        run_id: str,
        dataset_id: Optional[str],
        name: Optional[str],
        task_type: str,
        predictions_path: str,
        metrics_json: str,
        predictions: Optional[list[dict]] = None,
    ) -> dict:
        self._conn.execute(
            """
            INSERT INTO evaluations (id, run_id, dataset_id, name, task_type, predictions_path, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (evaluation_id, run_id, dataset_id, name, task_type, predictions_path, metrics_json),
        )
        if predictions:
            self._predictions.create_many(evaluation_id, predictions)
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)).fetchone()
        return dict(row)

    def get(self, evaluation_id: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)).fetchone()
        return dict(row) if row else None

    def list_by_run(self, run_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM evaluations WHERE run_id = ? ORDER BY created_at DESC",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_dataset(self, dataset_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM evaluations WHERE dataset_id = ? ORDER BY created_at DESC",
            (dataset_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, evaluation_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
        self._conn.commit()
        return cur.rowcount > 0


class PredictionRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(
        self,
        evaluation_id: str,
        sample_id: str,
        true_value: str,
        pred_value: str,
        confidence: Optional[float],
        is_correct: int,
    ) -> dict:
        cur = self._conn.execute(
            """
            INSERT INTO predictions (evaluation_id, sample_id, true_value, pred_value, confidence, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (evaluation_id, sample_id, true_value, pred_value, confidence, is_correct),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM predictions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def create_many(self, evaluation_id: str, predictions: list[dict]) -> int:
        params = [
            (
                evaluation_id,
                p["sample_id"],
                p["true_value"],
                p["pred_value"],
                p["confidence"],
                p["is_correct"],
            )
            for p in predictions
        ]
        self._conn.executemany(
            """
            INSERT INTO predictions (evaluation_id, sample_id, true_value, pred_value, confidence, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            params,
        )
        self._conn.commit()
        return len(params)

    def list_by_evaluation(self, evaluation_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM predictions WHERE evaluation_id = ? ORDER BY id ASC",
            (evaluation_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_evaluation(self, evaluation_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM predictions WHERE evaluation_id = ?",
            (evaluation_id,),
        ).fetchone()
        return row["cnt"]

    def accuracy_for_evaluation(self, evaluation_id: str) -> Optional[float]:
        row = self._conn.execute(
            """
            SELECT
                SUM(is_correct) AS correct,
                COUNT(*) AS total
            FROM predictions
            WHERE evaluation_id = ?
            """,
            (evaluation_id,),
        ).fetchone()
        total = row["total"]
        if total == 0:
            return None
        return row["correct"] / total
