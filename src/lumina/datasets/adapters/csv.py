from pathlib import Path
from typing import Any

from lumina.datasets.adapters.base import DatasetAdapter


class CSVAdapter(DatasetAdapter):
    name = "csv"
    supported_extensions = [".csv"]

    def load(self, path: Path) -> Any:
        import polars as pl

        return pl.read_csv(path, infer_schema_length=0)

    def preview(self, data: Any, n: int = 10) -> list[dict]:
        return data.head(n).to_dicts()

    def schema(self, data: Any) -> dict:
        return {name: str(dtype) for name, dtype in zip(data.columns, data.dtypes)}

    def statistics(self, data: Any) -> dict:
        import polars as pl

        numeric = data.select(data.select(pl.col(pl.NUMERIC_DTYPES)).columns)
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": data.columns,
            "numeric_summary": numeric.describe().to_dicts() if numeric.columns else [],
        }

    def row_count(self, data: Any) -> int:
        return len(data)
