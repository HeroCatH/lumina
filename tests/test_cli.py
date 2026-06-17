from pathlib import Path
from lumina.cli import main


def test_cli_version(capsys):
    assert main(["version"]) == 0
    captured = capsys.readouterr()
    assert "lumina" in captured.out


def test_cli_project_create(monkeypatch, tmp_path):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    code = main(["project", "create", "cli_test", "--path", str(tmp_path / "cli_test")])
    assert code == 0
    assert (tmp_path / "cli_test" / "lumina.db").exists()


def test_cli_project_list(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    main(["project", "create", "alpha", "--path", str(tmp_path / "alpha")])
    main(["project", "create", "beta", "--path", str(tmp_path / "beta")])
    code = main(["project", "list"])
    assert code == 0
    captured = capsys.readouterr()
    assert "alpha" in captured.out
    assert "beta" in captured.out


def test_cli_data_add(monkeypatch, tmp_path):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    main(["project", "create", "my_project", "--path", str(tmp_path / "my_project")])

    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n")

    code = main(["data", "add", "sample", str(csv_path), "--project", "my_project"])
    assert code == 0


def test_cli_model_analyze(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    from lumina.parsers.simple import SimpleModel

    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    import pickle
    model_path = tmp_path / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    code = main(["model", "analyze", "--model", str(model_path), "--input-shape", "1,10"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Params:" in captured.out
    assert "FLOPs:" in captured.out
