from fastapi.testclient import TestClient

from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def test_list_runs_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )
    project.experiments.metrics.create(run_id="r1", step=1, name="loss", value=0.5)

    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/runs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"
