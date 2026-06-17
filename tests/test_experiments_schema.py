from lumina.storage.db import get_db, init_schema


def test_experiment_schema_is_created(tmp_path):
    db_path = tmp_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"projects", "datasets", "runs", "metrics", "checkpoints"}.issubset(tables)

    runs_cols = {row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()}
    assert {"id", "project_id", "name", "status", "source", "log_dir"} <= runs_cols

    metrics_cols = {row[1] for row in conn.execute("PRAGMA table_info(metrics)").fetchall()}
    assert {"run_id", "step", "name", "value", "source_file"} <= metrics_cols

    checkpoints_cols = {row[1] for row in conn.execute("PRAGMA table_info(checkpoints)").fetchall()}
    assert {"run_id", "step", "path"} <= checkpoints_cols
