from lumina.analyzers.memory import MemoryAnalyzer
from lumina.graph import ModelGraph, Node


def test_linear_memory():
    graph = ModelGraph(nodes=[
        Node(id="linear", type="Linear", params={"in_features": 10, "out_features": 20}),
    ])
    stats = MemoryAnalyzer().analyze(graph)
    assert stats["param_bytes"] == 220 * 4
    assert stats["per_node"]["linear"]["param_bytes"] == 220 * 4


def test_conv2d_memory():
    graph = ModelGraph(nodes=[
        Node(id="conv", type="Conv2d", params={
            "in_channels": 3,
            "out_channels": 64,
            "kernel_size": 3,
        }),
    ])
    stats = MemoryAnalyzer().analyze(graph)
    # 3*64*3*3 weights + 64 biases = 1792 params, 4 bytes each
    assert stats["param_bytes"] == 1792 * 4
