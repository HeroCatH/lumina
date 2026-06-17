from typing import Any, Dict, List

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class ShapeAnalyzer(Analyzer):
    def __init__(self, input_shape: List[int]):
        self.input_shape = input_shape

    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        per_node = {}
        current_shape = list(self.input_shape)

        for node in graph.nodes:
            out_shape = self._estimate_output_shape(node, current_shape)
            per_node[node.id] = {
                "input_shape": list(current_shape),
                "output_shape": list(out_shape),
            }
            current_shape = out_shape

        return {
            "input_shape": list(self.input_shape),
            "output_shape": list(current_shape),
            "per_node": per_node,
        }

    def _estimate_output_shape(self, node: Any, input_shape: List[int]) -> List[int]:
        layer_type = node.type
        params = node.params

        if layer_type in ("Linear", "nn.Linear"):
            out_features = params.get("out_features", input_shape[-1])
            return input_shape[:-1] + [out_features]

        if layer_type in ("Conv2d", "nn.Conv2d"):
            h, w = input_shape[-2], input_shape[-1]
            kernel = params.get("kernel_size", 1)
            stride = params.get("stride", 1)
            padding = params.get("padding", 0)
            out_ch = params.get("out_channels", input_shape[-3])

            if isinstance(kernel, (tuple, list)):
                k_h, k_w = kernel[0], kernel[1]
            else:
                k_h = k_w = kernel
            if isinstance(stride, (tuple, list)):
                s_h, s_w = stride[0], stride[1]
            else:
                s_h = s_w = stride
            if isinstance(padding, (tuple, list)):
                p_h, p_w = padding[0], padding[1]
            else:
                p_h = p_w = padding

            out_h = (h + 2 * p_h - k_h) // s_h + 1
            out_w = (w + 2 * p_w - k_w) // s_w + 1
            return list(input_shape[:-3]) + [out_ch, out_h, out_w]

        if layer_type in ("Flatten", "nn.Flatten"):
            total = 1
            for dim in input_shape[1:]:
                total *= dim
            return [input_shape[0], total]

        # Default: shape passes through
        return input_shape
