import json
from pathlib import Path

import pytest

from lumina.experiments.log_adapters import CsvLogAdapter, JsonlLogAdapter, LogParseError


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


def test_jsonl_adapter_skips_blank_lines(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    log_file.write_text(
        '{"step": 1, "name": "loss", "value": 0.5}\n\n{"step": 2, "name": "loss", "value": 0.4}\n'
    )
    records = list(JsonlLogAdapter().parse(log_file))
    assert len(records) == 2


def test_jsonl_adapter_raises_on_bad_row(tmp_path):
    log_file = tmp_path / "metrics.jsonl"
    log_file.write_text('{"step": 1, "value": 0.5}\n')
    with pytest.raises(LogParseError):
        list(JsonlLogAdapter().parse(log_file))


def test_csv_adapter_case_insensitive_suffix(tmp_path):
    log_file = tmp_path / "metrics.CSV"
    log_file.write_text("step,name,value\n1,loss,0.5\n")
    assert CsvLogAdapter().supports(log_file)


def test_adapter_ignores_unsupported_file(tmp_path):
    log_file = tmp_path / "notes.txt"
    log_file.write_text("hello")
    assert not JsonlLogAdapter().supports(log_file)
    assert not CsvLogAdapter().supports(log_file)
