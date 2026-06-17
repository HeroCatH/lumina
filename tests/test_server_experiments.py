from pathlib import Path

from fastapi.testclient import TestClient

from lumina.server import create_app
from lumina.core.project_manager import ProjectManager


def _setup_project(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )
    project.experiments.metrics.create(run_id="r1", step=1, name="loss", value=0.5)
    ckpt_source = tmp_path / "model.pt"
    ckpt_source.write_bytes(b"ckpt")
    ckpt_path = project.path / "checkpoints" / "r1" / "step_1.pt"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    ckpt_path.write_bytes(ckpt_source.read_bytes())
    project.experiments.checkpoints.create(run_id="r1", step=1, path=str(ckpt_path.relative_to(project.path)))
    return project, run, ckpt_path


def test_list_runs_endpoint(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/runs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"


def test_get_run_endpoint(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/runs/r1")
    assert res.status_code == 200
    assert res.json()["id"] == "r1"

    res = client.get("/api/runs/missing")
    assert res.status_code == 404


def test_list_metrics_endpoint(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/metrics?run_id=r1")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.get("/api/metrics?run_id=missing")
    assert res.status_code == 404


def test_list_checkpoints_endpoint(tmp_path, monkeypatch):
    project, run, _ = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    res = client.get("/api/checkpoints?run_id=r1")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.get("/api/checkpoints?run_id=missing")
    assert res.status_code == 404


def test_download_checkpoint_endpoint(tmp_path, monkeypatch):
    project, run, ckpt_dest = _setup_project(tmp_path, monkeypatch)
    app = create_app(project=project)
    client = TestClient(app)
    checkpoint_id = project.experiments.checkpoints.list_by_run(run["id"])[0]["id"]
    res = client.get(f"/api/checkpoints/{checkpoint_id}/download")
    assert res.status_code == 200
    assert res.content == b"ckpt"

    res = client.get("/api/checkpoints/99999/download")
    assert res.status_code == 404


def test_register_log_dir_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')

    app = create_app(project=project)
    client = TestClient(app)
    res = client.post(f"/api/projects/{project.id}/logs?log_dir={log_dir}&name=log-run")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "log-run"
    assert data["source"] == "auto"

    res = client.post(f"/api/projects/wrong-id/logs?log_dir={log_dir}")
    assert res.status_code == 404


def test_sync_log_dir_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')
    run = project.experiments.register_log_dir(log_dir, name="log-run")

    app = create_app(project=project)
    client = TestClient(app)
    res = client.post(f"/api/projects/{project.id}/logs/sync?run_id={run['id']}")
    assert res.status_code == 200
    assert res.json()["synced"] == 0


def test_experiment_endpoints_require_project(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    res = client.get("/api/runs")
    assert res.status_code == 404
    assert res.json()["detail"] == "No project loaded"
