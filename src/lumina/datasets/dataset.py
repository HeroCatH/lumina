from pathlib import Path
from typing import Optional

from lumina.datasets.registry import detect_adapter, get_adapter


class Dataset:
    def __init__(
        self,
        name: str,
        path: Path,
        adapter_type: str,
        project_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.path = Path(path)
        self.adapter_type = adapter_type
        self.project_id = project_id
        self.metadata = metadata or {}
        self._adapter = get_adapter(adapter_type)
        self._data = self._adapter.load(self.path)

    def preview(self, n: int = 10) -> list[dict]:
        return self._adapter.preview(self._data, n)

    def schema(self) -> dict:
        return self._adapter.schema(self._data)

    def statistics(self) -> dict:
        return self._adapter.statistics(self._data)

    def row_count(self) -> int:
        return self._adapter.row_count(self._data)

    @classmethod
    def from_path(cls, name: str, path: str, adapter_type: Optional[str] = None) -> "Dataset":
        path_obj = Path(path)
        adapter = adapter_type or detect_adapter(path_obj)
        return cls(name=name, path=path_obj, adapter_type=adapter)
