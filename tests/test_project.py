import uuid
from pathlib import Path

import pytest

from lumina.api import create_project, list_projects, open_project
from lumina.core.project import Project
from lumina.core.project_manager import ProjectManager


def test_create_and_open_project(tmp_path):
    manager = ProjectManager(root=tmp_path)
    project = manager.create("test_project")
    assert project.path.exists()
    assert (project.path / "lumina.db").exists()
    assert project.id

    same = manager.open("test_project")
    assert same.name == "test_project"
    assert same.path == project.path
    assert same.id == project.id


def test_manager_list(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        manager.create("alpha")
        manager.create("beta")
        projects = manager.list()
        names = {p["name"] for p in projects}
        assert names == {"alpha", "beta"}


def test_manager_delete(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("to_delete")
        assert project.path.exists()
        manager.delete("to_delete")
        assert not project.path.exists()
        with pytest.raises(ValueError):
            manager.open("to_delete")


def test_api_create_project(tmp_path):
    name = f"api_project_{uuid.uuid4().hex[:8]}"
    project = create_project(name, path=str(tmp_path))
    assert isinstance(project, Project)
    assert project.name == name
    assert project.path.exists()
    assert project.path == tmp_path / name


def test_api_open_project(tmp_path):
    name = f"api_open_{uuid.uuid4().hex[:8]}"
    create_project(name, path=str(tmp_path))
    project = open_project(name, path=str(tmp_path))
    assert project.name == name


def test_api_list_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    name_one = f"one_{uuid.uuid4().hex[:8]}"
    name_two = f"two_{uuid.uuid4().hex[:8]}"
    create_project(name_one, path=str(tmp_path))
    create_project(name_two, path=str(tmp_path))
    projects = list_projects()
    names = {p["name"] for p in projects}
    assert {name_one, name_two}.issubset(names)


def test_api_open_nonexistent_project(tmp_path):
    name = f"exists_{uuid.uuid4().hex[:8]}"
    create_project(name, path=str(tmp_path))
    with pytest.raises(ValueError, match="Project not found"):
        open_project(f"does_not_exist_{uuid.uuid4().hex[:8]}", path=str(tmp_path))


def test_api_create_duplicate_project(tmp_path):
    name = f"dup_{uuid.uuid4().hex[:8]}"
    create_project(name, path=str(tmp_path))
    with pytest.raises(ValueError, match="already exists"):
        create_project(name, path=str(tmp_path))


def test_api_create_with_custom_path(tmp_path):
    name = f"custom_path_project_{uuid.uuid4().hex[:8]}"
    custom_root = tmp_path / name
    project = create_project(name, path=str(custom_root))
    assert project.path == custom_root / name
    assert project.path.exists()


def test_api_open_with_custom_path(tmp_path):
    name = f"custom_path_open_{uuid.uuid4().hex[:8]}"
    custom_root = tmp_path / f"root_{uuid.uuid4().hex[:8]}"
    with ProjectManager(root=custom_root) as manager:
        manager.create(name)
    project = open_project(name, path=str(custom_root))
    assert project.name == name


def test_project_context_manager(tmp_path):
    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("ctx_project")
        with project as p:
            assert p.name == "ctx_project"
