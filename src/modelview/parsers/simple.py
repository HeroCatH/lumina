from typing import Any

from modelview.graph import ModelGraph, Node, Edge
from modelview.parsers.base import Parser


class SimpleModel:
    """A framework-agnostic model description for testing and demos.

    Example:
        model = SimpleModel([
            {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64}},
            {"type": "ReLU", "params": {}},
            {"type": "Linear", "params": {"in_features": 64, "out_features": 10}},
        ])
    """

    def __init__(self, layers: list[dict[str, Any]]):
        self.layers = layers


class SimpleParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        if isinstance(model, SimpleModel):
            layers = model.layers
        elif isinstance(model, list):
            layers = model
        elif isinstance(model, dict) and "layers" in model:
            layers = model["layers"]
        else:
            raise ValueError(f"Unsupported simple model type: {type(model)}")

        nodes = []
        edges = []
        prev_id: str | None = None

        for idx, layer in enumerate(layers):
            layer_type = layer.get("type", f"layer_{idx}")
            node_id = str(idx)
            node = Node(
                id=node_id,
                type=layer_type,
                params=layer.get("params", {}),
                display_name=f"{node_id} ({layer_type})",
            )
            nodes.append(node)
            if prev_id is not None:
                edges.append(Edge(source=prev_id, target=node_id))
            prev_id = node_id

        return ModelGraph(nodes=nodes, edges=edges, metadata={"framework": "simple"})
