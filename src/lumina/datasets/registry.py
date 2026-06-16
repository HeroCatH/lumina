from pathlib import Path
from typing import Type

from lumina.datasets.adapters.base import DatasetAdapter
from lumina.datasets.adapters.csv import CSVAdapter


_ADAPTERS: dict[str, Type[DatasetAdapter]] = {
    CSVAdapter.name: CSVAdapter,
}


def register_adapter(adapter_cls: Type[DatasetAdapter]) -> None:
    _ADAPTERS[adapter_cls.name] = adapter_cls


def get_adapter(adapter_type: str) -> DatasetAdapter:
    if adapter_type not in _ADAPTERS:
        raise ValueError(f"Unknown dataset adapter: {adapter_type}")
    return _ADAPTERS[adapter_type]()


def detect_adapter(path: Path) -> str:
    suffix = path.suffix.lower()
    for name, cls in _ADAPTERS.items():
        if suffix in cls.supported_extensions:
            return name
    raise ValueError(f"Cannot detect adapter for path: {path}")
