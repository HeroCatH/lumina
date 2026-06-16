from typing import Any, Dict

from modelview.graph import ModelGraph
from modelview.analyzers.base import Analyzer


class ParamAnalyzer(Analyzer):
    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        total = 0
        trainable = 0
        per_node: Dict[str, int] = {}

        for node in graph.nodes:
            node_total = self._estimate_node_params(node)
            per_node[node.id] = node_total
            total += node_total
            trainable += node_total

        return {
            "total_params": total,
            "trainable_params": trainable,
            "per_node": per_node,
        }

    def _estimate_node_params(self, node: Any) -> int:
        """Best-effort parameter count from node.params.

        Works for simple descriptions and common layer types.
        """
        params = node.params
        layer_type = node.type

        if layer_type in ("Linear", "nn.Linear"):
            in_f = params.get("in_features", params.get("in_channels", 0))
            out_f = params.get("out_features", params.get("out_channels", 0))
            bias = params.get("bias", True)
            total = in_f * out_f
            if bias:
                total += out_f
            return total

        if layer_type in ("Conv2d", "nn.Conv2d"):
            in_ch = params.get("in_channels", 0)
            out_ch = params.get("out_channels", 0)
            kernel = params.get("kernel_size", 1)
            if isinstance(kernel, (tuple, list)):
                k = 1
                for dim in kernel:
                    k *= dim
            else:
                k = kernel * kernel
            bias = params.get("bias", True)
            total = in_ch * out_ch * k
            if bias:
                total += out_ch
            return total

        return 0
