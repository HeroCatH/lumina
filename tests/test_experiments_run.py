from pathlib import Path

from lumina.core.project_manager import ProjectManager
from lumina.experiments.run import Run


def test_run_sdk_logs_and_finishes(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    with manager.create("p1") as project:
        run = Run.start(project=project, name="run-1")
        run.log("loss", 0.5, step=1)
        run.log("loss", 0.4, step=2)
        run.finish()

        metrics = project.experiments.metrics.list_by_run(run.id, name="loss")
        assert len(metrics) == 2
        assert metrics[-1]["value"] == 0.4

        record = project.experiments.runs.get(run.id)
        assert record["status"] == "finished"


def test_run_save_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    manager = ProjectManager()
    with manager.create("p1") as project:
        source = tmp_path / "model.pt"
        source.write_bytes(b"fake checkpoint")

        run = Run.start(project=project, name="run-ckpt")
        dest = run.save_checkpoint(str(source), step=10)

        assert dest.exists()
        assert dest.read_bytes() == b"fake checkpoint"

        checkpoints = project.experiments.checkpoints.list_by_run(run.id)
        assert len(checkpoints) == 1
        assert checkpoints[0]["step"] == 10
