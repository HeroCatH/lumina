import sqlite3
from pathlib import Path

import pytest

from lumina.config import DB_FILENAME
from lumina.storage.db import get_db, init_project_db, init_schema
from lumina.storage.repositories import DatasetRepository, ProjectRepository


def test_create_and_get_project(tmp_path):
    db_path = tmp_path / DB_FILENAME
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("test_project", str(tmp_path))
    project = repo.get_by_name("test_project")
    assert project["name"] == "test_project"
    assert project["path"] == str(tmp_path)


def test_project_list_all(tmp_path):
    db_path = tmp_path / DB_FILENAME
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("alpha", str(tmp_path / "alpha"))
    repo.create("beta", str(tmp_path / "beta"))
    projects = repo.list_all()
    assert {p["name"] for p in projects} == {"alpha", "beta"}


def test_project_delete(tmp_path):
    db_path = tmp_path / DB_FILENAME
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("to_delete", str(tmp_path))
    assert repo.delete("to_delete") is True
    assert repo.get_by_name("to_delete") is None
    assert repo.delete("missing") is False


def test_dataset_create_and_get_by_name(tmp_path):
    db_path = tmp_path / DB_FILENAME
    conn = get_db(db_path)
    init_schema(conn)
    project_repo = ProjectRepository(conn)
    dataset_repo = DatasetRepository(conn)
    project = project_repo.create("my_project", str(tmp_path))
    dataset = dataset_repo.create(
        project_id=project["id"],
        name="my_dataset",
        path=str(tmp_path / "data.csv"),
        adapter_type="csv",
    )
    fetched = dataset_repo.get_by_name(project["id"], "my_dataset")
    assert fetched["id"] == dataset["id"]
    assert fetched["name"] == "my_dataset"
    assert fetched["adapter_type"] == "csv"


def test_project_name_uniqueness(tmp_path):
    db_path = tmp_path / DB_FILENAME
    conn = get_db(db_path)
    init_schema(conn)
    repo = ProjectRepository(conn)
    repo.create("dup", str(tmp_path / "first"))
    with pytest.raises(sqlite3.IntegrityError):
        repo.create("dup", str(tmp_path / "second"))


def test_init_project_db_creates_parent_directories(tmp_path):
    project_path = tmp_path / "nested" / "project"
    conn = init_project_db(project_path)
    try:
        assert project_path.exists()
        assert (project_path / DB_FILENAME).exists()
    finally:
        conn.close()
