from pathlib import Path
from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import ProjectRepository


def test_create_and_get_project(tmp_path):
    db_path = tmp_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("test_project", str(tmp_path))
    project = repo.get_by_name("test_project")
    assert project["name"] == "test_project"
    assert project["path"] == str(tmp_path)
