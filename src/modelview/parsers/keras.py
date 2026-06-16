from typing import Any

from modelview.graph import ModelGraph
from modelview.parsers.base import Parser


class KerasParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError("Keras parser is planned for a later iteration")
