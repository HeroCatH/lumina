from pathlib import Path

import pytest

from lumina.datasets.adapters.csv import CSVAdapter


def test_csv_adapter(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    adapter = CSVAdapter()
    df = adapter.load(csv_path)
    preview = adapter.preview(df, n=2)
    assert len(preview) == 2
    assert preview[0] == {"a": 1, "b": 2, "c": 3}


def test_csv_adapter_schema_reports_numeric_types(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    adapter = CSVAdapter()
    df = adapter.load(csv_path)
    schema = adapter.schema(df)
    assert schema == {"a": "Int64", "b": "Int64", "c": "Int64"}


def test_csv_adapter_statistics_numeric_summary(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    adapter = CSVAdapter()
    df = adapter.load(csv_path)
    stats = adapter.statistics(df)
    assert stats["row_count"] == 2
    assert stats["column_count"] == 3
    assert set(stats["columns"]) == {"a", "b", "c"}
    assert len(stats["numeric_summary"]) > 0


def test_csv_adapter_unsupported_extension():
    adapter = CSVAdapter()
    assert ".csv" in adapter.supported_extensions
    assert Path("data.txt").suffix not in adapter.supported_extensions
