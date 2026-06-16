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
