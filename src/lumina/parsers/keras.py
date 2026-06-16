from typing import Any

from lumina.graph import ModelGraph
from lumina.parsers.base import Parser


class KerasParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError("Keras parser is planned for a later iteration")
