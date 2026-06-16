from pathlib import Path
from typing import Any

import polars as pl

from lumina.datasets.adapters.base import DatasetAdapter


class ParquetAdapter(DatasetAdapter):
    name = "parquet"
    supported_extensions = [".parquet"]

    def load(self, path: Path) -> Any:
        return pl.read_parquet(path)

    def preview(self, data: Any, n: int = 10) -> list[dict]:
        return data.head(n).to_dicts()

    def schema(self, data: Any) -> dict:
        return {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)}

    def statistics(self, data: Any) -> dict:
        numeric = data.select(data.select(pl.selectors.numeric()).columns)
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": data.columns,
            "column_types": {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)},
            "numeric_summary": numeric.describe().to_dicts() if numeric.columns else [],
            "missing_counts": {name: data[name].null_count() for name in data.columns},
        }

    def row_count(self, data: Any) -> int:
        return len(data)
