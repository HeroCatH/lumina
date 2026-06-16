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
