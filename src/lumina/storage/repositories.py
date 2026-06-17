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
