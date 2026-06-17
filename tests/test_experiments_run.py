from pathlib import Path

from lumina.core.project_manager import ProjectManager
from lumina.experiments.run import Run


def test_run_sdk_logs_and_finishes(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    project = manager.create("p1")

    run = Run.start(project=project, name="run-1")
    run.log("loss", 0.5, step=1)
    run.log("loss", 0.4, step=2)
    run.finish()

    metrics = project.experiments.metrics.list_by_run(run.id, name="loss")
    assert len(metrics) == 2
    assert metrics[-1]["value"] == 0.4

    record = project.experiments.runs.get(run.id)
    assert record["status"] == "finished"
