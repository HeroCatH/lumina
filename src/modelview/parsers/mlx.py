from typing import Any

from modelview.graph import ModelGraph, Node, Edge
from modelview.parsers.base import Parser


class MlxParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        import mlx.nn as nn

        if not isinstance(model, nn.Module):
            raise ValueError(f"Expected mlx.nn.Module, got {type(model)}")

        nodes = []
        edges = []
        prev_id: str | None = None

        for name, module in model.named_modules():
            if name == "":
                continue
            node = Node(
                id=name,
                type=module.__class__.__name__,
                params=self._extract_params(module),
                display_name=f"{name} ({module.__class__.__name__})",
            )
            nodes.append(node)
            if prev_id is not None:
                edges.append(Edge(source=prev_id, target=name))
            prev_id = name

        return ModelGraph(nodes=nodes, edges=edges, metadata={"framework": "mlx"})

    def _extract_params(self, module: Any) -> dict:
        params = {}
        for key, value in module.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, (int, float, str, bool, tuple, list)):
                params[key] = value
        return params
