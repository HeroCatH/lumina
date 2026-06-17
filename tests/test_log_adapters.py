import json
from pathlib import Path

from lumina.experiments.log_adapters import JsonlLogAdapter, CsvLogAdapter


def test_jsonl_adapter(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    with open(log_file, "w") as f:
        f.write(json.dumps({"step": 1, "name": "loss", "value": 0.5}) + "\n")
        f.write(json.dumps({"step": 2, "name": "loss", "value": 0.4}) + "\n")

    adapter = JsonlLogAdapter()
    records = list(adapter.parse(log_file))
    assert len(records) == 2
    assert records[1] == {"step": 2, "name": "loss", "value": 0.4}


def test_csv_adapter(tmp_path):
    log_file = tmp_path / "metrics.csv"
    log_file.write_text("step,name,value\n1,loss,0.5\n2,loss,0.4\n")

    adapter = CsvLogAdapter()
    records = list(adapter.parse(log_file))
    assert len(records) == 2
    assert records[1] == {"step": 2, "name": "loss", "value": 0.4}
