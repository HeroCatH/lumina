import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator


class LogAdapter(ABC):
    @abstractmethod
    def supports(self, path: Path) -> bool:
        ...

    @abstractmethod
    def parse(self, path: Path) -> Iterator[dict]:
        ...


class JsonlLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix == ".jsonl"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                yield {
                    "step": int(record["step"]),
                    "name": str(record["name"]),
                    "value": float(record["value"]),
                }


class CsvLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix == ".csv"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {
                    "step": int(row["step"]),
                    "name": str(row["name"]),
                    "value": float(row["value"]),
                }
