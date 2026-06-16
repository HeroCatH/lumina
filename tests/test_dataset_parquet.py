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
