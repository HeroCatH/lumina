from typing import Any

from lumina.graph import ModelGraph
from lumina.parsers.base import Parser


class PytorchParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        import torch

        nodes = []
        edges = []
        prev_id = None

        for name, module in model.named_modules():
            if name == "":
                continue
            node = self._make_node(name, module)
            nodes.append(node)
            if prev_id is not None:
                edges.append(self._make_edge(prev_id, name))
            prev_id = name

        return ModelGraph(nodes=nodes, edges=edges, metadata={"framework": "pytorch"})

    def _make_node(self, name: str, module: Any) -> Any:
        from lumina.graph import Node

        return Node(
            id=name,
            type=module.__class__.__name__,
            params=self._extract_params(module),
            display_name=f"{name} ({module.__class__.__name__})",
        )

    def _make_edge(self, source: str, target: str) -> Any:
        from lumina.graph import Edge

        return Edge(source=source, target=target)

    def _extract_params(self, module: Any) -> dict:
        params = {}
        for key, value in module.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, (int, float, str, bool, tuple, list)):
                params[key] = value
        return params
