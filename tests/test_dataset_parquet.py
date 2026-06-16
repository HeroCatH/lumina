from pathlib import Path
import pytest

polars = pytest.importorskip("polars")

from lumina.datasets.adapters.parquet import ParquetAdapter


def test_parquet_adapter(tmp_path):
    path = tmp_path / "data.parquet"
    df = polars.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.write_parquet(path)

    adapter = ParquetAdapter()
    loaded = adapter.load(path)
    preview = adapter.preview(loaded, n=2)
    assert len(preview) == 2


def test_parquet_adapter_schema_reports_types(tmp_path):
    path = tmp_path / "data.parquet"
    df = polars.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.write_parquet(path)

    adapter = ParquetAdapter()
    loaded = adapter.load(path)
    schema = adapter.schema(loaded)
    assert schema == {"a": "Int64", "b": "String"}


def test_parquet_adapter_statistics_numeric_summary(tmp_path):
    path = tmp_path / "data.parquet"
    df = polars.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.write_parquet(path)

    adapter = ParquetAdapter()
    loaded = adapter.load(path)
    stats = adapter.statistics(loaded)
    assert stats["row_count"] == 3
    assert stats["column_count"] == 2
    assert set(stats["columns"]) == {"a", "b"}
    assert len(stats["numeric_summary"]) > 0
    assert "column_types" not in stats
    assert "missing_counts" not in stats


def test_parquet_adapter_row_count(tmp_path):
    path = tmp_path / "data.parquet"
    df = polars.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.write_parquet(path)

    adapter = ParquetAdapter()
    loaded = adapter.load(path)
    assert adapter.row_count(loaded) == 3


def test_parquet_adapter_supported_extensions():
    adapter = ParquetAdapter()
    assert ".parquet" in adapter.supported_extensions
    assert Path("data.txt").suffix not in adapter.supported_extensions
