from abc import ABC, abstractmethod
from typing import Any, Dict

from modelview.graph import ModelGraph


class Analyzer(ABC):
    @abstractmethod
    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError
