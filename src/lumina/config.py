import os
from pathlib import Path

DB_FILENAME = "lumina.db"


def get_projects_root() -> Path:
    return Path(os.environ.get("LUMINA_PROJECTS_ROOT", Path.home() / "lumina_projects"))


DEFAULT_PROJECTS_ROOT = get_projects_root()
