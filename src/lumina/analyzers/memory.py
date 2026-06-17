from typing import Any, Dict

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class MemoryAnalyzer(Analyzer):
    BYTES_PER_PARAM = 4  # float32

    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        total = 0
        per_node = {}

        for node in graph.nodes:
            bytes_used = self._estimate_node_memory(node)
            per_node[node.id] = {"param_bytes": bytes_used}
            total += bytes_used

        return {
            "param_bytes": total,
            "param_megabytes": round(total / (1024 * 1024), 4),
            "per_node": per_node,
        }

    def _estimate_node_memory(self, node: Any) -> int:
        params = node.params
        layer_type = node.type

        if layer_type in ("Linear", "nn.Linear"):
            in_f = params.get("in_features", 0)
            out_f = params.get("out_features", 0)
            bias = params.get("bias", True)
            total = in_f * out_f
            if bias:
                total += out_f
            return total * self.BYTES_PER_PARAM

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
            return total * self.BYTES_PER_PARAM

        return 0
