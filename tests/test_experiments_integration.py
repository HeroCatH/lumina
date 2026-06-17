from pathlib import Path

from fastapi.testclient import TestClient

from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def test_experiments_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    # SDK path
    run = project.experiments.runs.create(
        run_id="run-sdk", project_id=project.id, name="sdk-run", source="sdk"
    )
    project.experiments.metrics.create(run_id="run-sdk", step=1, name="loss", value=0.9)
    project.experiments.metrics.create(run_id="run-sdk", step=2, name="loss", value=0.7)

    # File path
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text(
        '{"step":1,"name":"accuracy","value":0.6}\n{"step":2,"name":"accuracy","value":0.8}\n'
    )
    project.experiments.register_log_dir(log_dir, name="file-run")

    app = create_app(project=project)
    client = TestClient(app)

    runs = client.get("/api/runs").json()
    assert len(runs) == 2

    file_run = next(r for r in runs if r["source"] == "auto")
    metrics = client.get(f"/api/metrics?run_id={file_run['id']}").json()
    assert len(metrics) == 2
