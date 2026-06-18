import subprocess
import sys
from pathlib import Path

from lumina.core.project_manager import ProjectManager


def _run(argv, check=True):
    result = subprocess.run(
        [sys.executable, "-m", "lumina", *argv],
        capture_output=True,
        text=True,
    )
    if check:
        assert result.returncode == 0, result.stderr
    return result


def _write_predictions_csv(path: Path):
    path.write_text("id,true,pred\n1,cat,cat\n2,dog,dog\n3,cat,dog\n")


def test_cli_project_eval_create_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    manager = ProjectManager()
    project = manager.open("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )

    predictions_path = tmp_path / "predictions.csv"
    _write_predictions_csv(predictions_path)

    result = _run(
        [
            "project",
            "eval",
            "create",
            str(predictions_path),
            "--project",
            "p1",
            "--run-id",
            run["id"],
            "--name",
            "eval-1",
            "--task-type",
            "classification",
        ]
    )
    assert "Created evaluation" in result.stdout
    evaluation_id = result.stdout.strip().split()[2]
    assert evaluation_id

    result = _run(["project", "eval", "list", "--project", "p1"])
    assert evaluation_id in result.stdout
    assert "eval-1" in result.stdout
    assert "classification" in result.stdout

    result = _run(
        ["project", "eval", "list", "--project", "p1", "--run-id", run["id"]]
    )
    assert evaluation_id in result.stdout


def test_cli_project_eval_create_rejects_missing_predictions_file(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    manager = ProjectManager()
    project = manager.open("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )

    result = _run(
        [
            "project",
            "eval",
            "create",
            str(tmp_path / "does_not_exist.csv"),
            "--project",
            "p1",
            "--run-id",
            run["id"],
        ],
        check=False,
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_cli_project_eval_create_rejects_missing_run(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    predictions_path = tmp_path / "predictions.csv"
    _write_predictions_csv(predictions_path)

    result = _run(
        [
            "project",
            "eval",
            "create",
            str(predictions_path),
            "--project",
            "p1",
            "--run-id",
            "missing-run",
        ],
        check=False,
    )
    assert result.returncode == 1
    assert "Run not found" in result.stderr


def test_cli_project_eval_list_rejects_missing_run(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    result = _run(
        ["project", "eval", "list", "--project", "p1", "--run-id", "missing-run"],
        check=False,
    )
    assert result.returncode == 1
    assert "Run not found" in result.stderr
