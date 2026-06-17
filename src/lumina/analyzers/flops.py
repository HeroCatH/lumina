from typing import Any, Dict

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class FlopAnalyzer(Analyzer):
    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        total = 0
        per_node = {}

        for node in graph.nodes:
            flops = self._estimate_node_flops(node)
            per_node[node.id] = flops
            total += flops

        return {
            "total_flops": total,
            "total_macs": total // 2,
            "per_node": per_node,
        }

    def _estimate_node_flops(self, node: Any) -> int:
        params = node.params
        layer_type = node.type

        if layer_type in ("Linear", "nn.Linear"):
            in_f = params.get("in_features", 0)
            out_f = params.get("out_features", 0)
            return 2 * in_f * out_f

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
            return 2 * in_ch * out_ch * k

        return 0
