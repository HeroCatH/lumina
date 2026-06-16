from abc import ABC, abstractmethod
from typing import Any

from modelview.graph import ModelGraph


class Parser(ABC):
    @abstractmethod
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError
