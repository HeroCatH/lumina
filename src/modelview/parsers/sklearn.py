from typing import Any

from modelview.graph import ModelGraph
from modelview.parsers.base import Parser


class SklearnParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError("sklearn parser is planned for a later iteration")
