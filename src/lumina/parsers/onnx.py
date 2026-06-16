from typing import Any

from lumina.graph import ModelGraph
from lumina.parsers.base import Parser


class OnnxParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError("ONNX parser is planned for a later iteration")
