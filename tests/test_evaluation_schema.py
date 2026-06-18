from lumina.storage.db import get_db, init_schema


def test_evaluation_schema_is_created(tmp_path):
    db_path = tmp_path / "lumina.db"
    conn = get_db(db_path)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"evaluations", "predictions"}.issubset(tables)

    eval_cols = {row[1] for row in conn.execute("PRAGMA table_info(evaluations)").fetchall()}
    assert {"id", "run_id", "dataset_id", "name", "task_type", "predictions_path", "metrics"} <= eval_cols

    pred_cols = {row[1] for row in conn.execute("PRAGMA table_info(predictions)").fetchall()}
    assert {"evaluation_id", "sample_id", "true_value", "pred_value", "confidence", "is_correct"} <= pred_cols
