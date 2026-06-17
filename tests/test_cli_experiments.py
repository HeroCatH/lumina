import subprocess
import sys
from pathlib import Path


def _run(argv, check=True):
    result = subprocess.run(
        [sys.executable, "-m", "lumina", *argv],
        capture_output=True,
        text=True,
    )
    if check:
        assert result.returncode == 0, result.stderr
    return result


def test_cli_project_logs_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')

    result = _run(["project", "logs", "add", str(log_dir), "--project", "p1"])
    assert "Registered log run:" in result.stdout

    result = _run(["project", "runs", "list", "--project", "p1"])
    assert "loss" not in result.stdout  # runs list shows metadata, not metric names
    assert "logs" in result.stdout


def test_cli_project_logs_sync(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')

    result = _run(["project", "logs", "add", str(log_dir), "--project", "p1"])
    run_id = result.stdout.strip().split()[3]

    result = _run(["project", "logs", "sync", "--project", "p1", "--run-id", run_id])
    assert "Synced 0 metrics" in result.stdout

    # Modify file and sync again
    (log_dir / "metrics.jsonl").write_text('{"step":2,"name":"loss","value":0.4}\n')
    result = _run(["project", "logs", "sync", "--project", "p1", "--run-id", run_id])
    assert "Synced 1 metrics" in result.stdout


def test_cli_project_logs_add_rejects_missing_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])
    result = _run(
        ["project", "logs", "add", "/does/not/exist", "--project", "p1"],
        check=False,
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_cli_project_logs_sync_rejects_bad_run(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    _run(["project", "create", "p1"])
    result = _run(
        ["project", "logs", "sync", "--project", "p1", "--run-id", "missing"],
        check=False,
    )
    assert result.returncode == 1
