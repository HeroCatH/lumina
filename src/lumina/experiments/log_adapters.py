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


class LogParseError(Exception):
    def __init__(self, path: Path, message: str):
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


class JsonlLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".jsonl"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    yield {
                        "step": int(record["step"]),
                        "name": str(record["name"]),
                        "value": float(record["value"]),
                    }
                except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
                    raise LogParseError(path, f"invalid JSONL row: {line!r} ({exc})") from exc


class CsvLogAdapter(LogAdapter):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def parse(self, path: Path) -> Iterator[dict]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    yield {
                        "step": int(row["step"]),
                        "name": str(row["name"]),
                        "value": float(row["value"]),
                    }
                except (KeyError, ValueError, TypeError) as exc:
                    raise LogParseError(path, f"invalid CSV row: {row!r} ({exc})") from exc
