from pathlib import Path
from lumina.cli import main


def test_cli_version(capsys):
    assert main(["version"]) == 0
    captured = capsys.readouterr()
    assert "lumina" in captured.out


def test_cli_project_create(tmp_path):
    code = main(["project", "create", "cli_test", "--path", str(tmp_path / "cli_test")])
    assert code == 0
    assert (tmp_path / "cli_test" / "lumina.db").exists()
