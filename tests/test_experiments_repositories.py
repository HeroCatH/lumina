import sqlite3
import uuid
from pathlib import Path

from lumina.storage.db import get_db, init_schema
from lumina.storage.repositories import RunRepository, MetricRepository, CheckpointRepository


def test_run_repository_crud(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_db(db_path)
    init_schema(conn)

    runs = RunRepository(conn)
    run_id = str(uuid.uuid4())
    runs.create(run_id=run_id, project_id=None, name="test", source="sdk")
    run = runs.get(run_id)
    assert run["name"] == "test"
    assert run["status"] == "running"

    metrics = MetricRepository(conn)
    metrics.create(run_id=run_id, step=1, name="loss", value=0.5)
    assert len(metrics.list_by_run(run_id)) == 1

    checkpoints = CheckpointRepository(conn)
    checkpoints.create(run_id=run_id, step=10, path="ckpt/step_10.pt")
    assert len(checkpoints.list_by_run(run_id)) == 1
