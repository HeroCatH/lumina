from lumina import create_project, start_run


def test_api_start_run(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
    project = create_project("p1", path=str(tmp_path / "p1"))
    run = start_run(project=project, name="api-run")
    run.log("loss", 0.1, step=1)
    assert run.id is not None
