from typing import Any

from modelview.graph import ModelGraph
from modelview.parsers.base import Parser


class OnnxParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        raise NotImplementedError("ONNX parser is planned for a later iteration")
