from pathlib import Path

from fastapi.testclient import TestClient
from lumina.core.project import Project
from lumina.server import create_app


def test_dataset_preview_endpoint(tmp_path):
    project = Project(project_id="test-id", name="test", path=tmp_path)
    csv_path = tmp_path / "datasets" / "data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("a,b\n1,2\n3,4\n")
    project.register_dataset("data", str(csv_path))

    app = create_app(project=project)
    client = TestClient(app)
    response = client.get("/api/datasets/data/preview?n=2")
    assert response.status_code == 200
    assert len(response.json()["rows"]) == 2


def test_current_project_endpoint(tmp_path):
    project = Project(project_id="test-id", name="test", path=tmp_path)
    app = create_app(project=project)
    client = TestClient(app)

    response = client.get("/api/projects/current")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "test"
    assert body["path"] == str(tmp_path)


def test_list_datasets_endpoint(tmp_path):
    project = Project(project_id="test-id", name="test", path=tmp_path)
    csv_path = tmp_path / "datasets" / "data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("a,b\n1,2\n3,4\n")
    project.register_dataset("data", str(csv_path))

    app = create_app(project=project)
    client = TestClient(app)

    response = client.get("/api/datasets")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "data"
    assert "path" in body[0]
    assert "adapter_type" in body[0]


def test_preview_nonexistent_dataset_returns_404(tmp_path):
    project = Project(project_id="test-id", name="test", path=tmp_path)
    app = create_app(project=project)
    client = TestClient(app)

    response = client.get("/api/datasets/missing/preview")
    assert response.status_code == 404
