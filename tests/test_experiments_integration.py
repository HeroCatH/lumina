def test_experiments_end_to_end(tmp_path):
    from lumina.core.project_manager import ProjectManager
    from lumina.server import create_app
    from fastapi.testclient import TestClient

    with ProjectManager(root=tmp_path) as manager:
        project = manager.create("p1")

        # SDK path: create run and metrics directly
        run = project.experiments.runs.create(
            run_id="run-sdk", project_id=project.id, name="sdk-run", source="sdk"
        )
        project.experiments.metrics.create(run_id="run-sdk", step=1, name="loss", value=0.9)
        project.experiments.metrics.create(run_id="run-sdk", step=2, name="loss", value=0.7)

        # File path: register external log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "metrics.jsonl").write_text(
            '{"step":1,"name":"accuracy","value":0.6}\n'
            '{"step":2,"name":"accuracy","value":0.8}\n'
        )
        project.experiments.register_log_dir(log_dir, name="file-run")

        app = create_app(project=project)
        client = TestClient(app)

        # List runs
        res = client.get("/api/runs")
        assert res.status_code == 200
        runs = res.json()
        assert len(runs) == 2
        sdk_run = next(r for r in runs if r["source"] == "sdk")
        file_run = next(r for r in runs if r["source"] == "auto")
        assert sdk_run["name"] == "sdk-run"
        assert file_run["name"] == "file-run"

        # Get run by id
        res = client.get(f"/api/runs/{sdk_run['id']}")
        assert res.status_code == 200
        assert res.json()["name"] == "sdk-run"

        # Get metrics for file run
        res = client.get(f"/api/metrics?run_id={file_run['id']}")
        assert res.status_code == 200
        metrics = res.json()
        assert len(metrics) == 2
        assert metrics[0]["name"] == "accuracy"
        assert metrics[0]["value"] == 0.6

        # Filter metrics by name for SDK run
        res = client.get(f"/api/metrics?run_id={sdk_run['id']}&name=loss")
        assert res.status_code == 200
        loss_metrics = res.json()
        assert len(loss_metrics) == 2
        assert all(m["name"] == "loss" for m in loss_metrics)

        # Create a checkpoint and download it
        ckpt_source = tmp_path / "model.pt"
        ckpt_source.write_bytes(b"fake checkpoint")
        ckpt_path = project.path / "checkpoints" / sdk_run["id"] / "step_1.pt"
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        ckpt_path.write_bytes(ckpt_source.read_bytes())
        project.experiments.checkpoints.create(
            run_id=sdk_run["id"], step=1, path=str(ckpt_path.relative_to(project.path))
        )

        res = client.get("/api/checkpoints?run_id=run-sdk")
        assert res.status_code == 200
        checkpoints = res.json()
        assert len(checkpoints) == 1
        assert checkpoints[0]["step"] == 1

        res = client.get(f"/api/checkpoints/{checkpoints[0]['id']}/download")
        assert res.status_code == 200
        assert res.content == b"fake checkpoint"

        # Sync logs via API
        res = client.post(f"/api/projects/{project.id}/logs/sync?run_id={file_run['id']}")
        assert res.status_code == 200
        assert res.json()["synced"] == 0
