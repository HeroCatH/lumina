from pathlib import Path

from lumina.core.project_manager import ProjectManager
from lumina.experiments.log_adapters import JsonlLogAdapter


def test_sync_log_dir_imports_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text(
        '{"step":1,"name":"loss","value":0.5}\n{"step":2,"name":"loss","value":0.4}\n'
    )

    run = project.experiments.register_log_dir(log_dir, name="file-run")
    metrics = project.experiments.metrics.list_by_run(run["id"], name="loss")
    assert len(metrics) == 2

    # Re-sync should not duplicate
    count = project.experiments.sync_log_dir(log_dir, run["id"])
    assert count == 0
    metrics = project.experiments.metrics.list_by_run(run["id"], name="loss")
    assert len(metrics) == 2

    # Modify file and re-sync should update
    (log_dir / "metrics.jsonl").write_text('{"step":3,"name":"loss","value":0.1}\n')
    count = project.experiments.sync_log_dir(log_dir, run["id"])
    assert count == 1
    metrics = project.experiments.metrics.list_by_run(run["id"], name="loss")
    assert len(metrics) == 1
    assert metrics[0]["step"] == 3
