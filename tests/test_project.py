from pathlib import Path
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
