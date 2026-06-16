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
