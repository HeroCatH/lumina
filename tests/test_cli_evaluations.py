import re
import subprocess
import sys
from pathlib import Path

from lumina.core.project_manager import ProjectManager


EVAL_ID_RE = re.compile(
    r"Created evaluation: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)


def _extract_eval_id(stdout: str) -> str:
    match = EVAL_ID_RE.search(stdout)
    assert match, f"Could not find evaluation id in: {stdout}"
    return match.group(1)


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
    evaluation_id = _extract_eval_id(result.stdout)
    assert evaluation_id

    result = _run(["project", "eval", "list", "--project", "p1"])
    assert evaluation_id in result.stdout
    assert "eval-1" in result.stdout
    assert "classification" in result.stdout

    result = _run(
        ["project", "eval", "list", "--project", "p1", "--run-id", run["id"]]
    )
    assert evaluation_id in result.stdout


def test_cli_eval_create_with_regression_and_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    # Create a dataset record via Python to satisfy FK
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open("p1")
    dataset = project.datasets.create(
        project_id=project.id,
        name="ds",
        path="/tmp/ds.csv",
        adapter_type="csv",
    )
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )

    csv = tmp_path / "reg.csv"
    csv.write_text("id,true,pred\n0,1.0,1.1\n1,2.0,1.9\n")

    result = _run(
        [
            "project",
            "eval",
            "create",
            str(csv),
            "--project",
            "p1",
            "--run-id",
            run["id"],
            "--dataset-id",
            dataset["id"],
            "--task-type",
            "regression",
            "--name",
            "reg-eval",
        ]
    )
    assert "Created evaluation:" in result.stdout
    assert "regression" in result.stdout
    assert "mae" in result.stdout
    assert "reg-eval" in result.stdout


def test_cli_eval_create_infers_classification(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open("p1")
    run = project.experiments.runs.create(
        run_id="r1", project_id=project.id, name="run-1", source="sdk"
    )

    csv = tmp_path / "cls.csv"
    csv.write_text("id,true,pred\n0,0,0\n1,1,0\n2,1,1\n")

    result = _run(
        [
            "project",
            "eval",
            "create",
            str(csv),
            "--project",
            "p1",
            "--run-id",
            run["id"],
        ]
    )
    assert "Created evaluation:" in result.stdout
    assert "classification" in result.stdout
    assert "accuracy" in result.stdout


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
