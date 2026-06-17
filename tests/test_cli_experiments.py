def test_cli_project_logs_add(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "lumina", "project", "create", "p1"], check=True)
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "metrics.jsonl").write_text('{"step":1,"name":"loss","value":0.5}\n')

    result = subprocess.run(
        [sys.executable, "-m", "lumina", "project", "logs", "add", str(log_dir), "--project", "p1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
