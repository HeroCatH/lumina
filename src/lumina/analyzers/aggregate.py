from typing import Any, Dict, List, Optional

from lumina.analyzers.flops import FlopAnalyzer
from lumina.analyzers.memory import MemoryAnalyzer
from lumina.analyzers.params import ParamAnalyzer
from lumina.analyzers.shapes import ShapeAnalyzer
from lumina.graph import ModelGraph


def aggregate_analysis(
    graph: ModelGraph,
    input_shape: Optional[List[int]] = None,
) -> Dict[str, Any]:
    result = {
        "params": ParamAnalyzer().analyze(graph),
        "flops": FlopAnalyzer().analyze(graph),
        "memory": MemoryAnalyzer().analyze(graph),
    }
    if input_shape is not None:
        result["shapes"] = ShapeAnalyzer(input_shape).analyze(graph)
    return result
