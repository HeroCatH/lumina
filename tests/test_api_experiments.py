from lumina import create_project, open_project, start_run


def test_create_project(tmp_path):
    project = create_project("p1", root=str(tmp_path / "p1"))
    assert project.name == "p1"
    assert project.path.exists()


def test_open_project(tmp_path):
    create_project("p1", root=str(tmp_path / "p1"))
    project = open_project("p1", root=str(tmp_path / "p1"))
    assert project.name == "p1"


def test_start_run_logs_and_finishes(tmp_path):
    project = create_project("p1", root=str(tmp_path / "p1"))
    run = start_run(project=project, name="api-run")
    run.log("loss", 0.1, step=1)
    run.finish()

    record = project.experiments.runs.get(run.id)
    assert record is not None
    assert record["name"] == "api-run"
    assert record["status"] == "finished"

    metrics = project.experiments.metrics.list_by_run(run.id, name="loss")
    assert len(metrics) == 1
    assert metrics[0]["value"] == 0.1


def test_start_run_default_name(tmp_path):
    project = create_project("p1", root=str(tmp_path / "p1"))
    run = start_run(project=project)
    assert run.id is not None
