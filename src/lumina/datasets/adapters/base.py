from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class DatasetAdapter(ABC):
    name: str = ""
    supported_extensions: list[str] = []

    @abstractmethod
    def load(self, path: Path) -> Any:
        raise NotImplementedError

    @abstractmethod
    def preview(self, data: Any, n: int = 10) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def schema(self, data: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def statistics(self, data: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def row_count(self, data: Any) -> int:
        raise NotImplementedError
