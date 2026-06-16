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

    def __enter__(self) -> "Project":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, path={self.path})"
