from lumina.analyzers.flops import FlopAnalyzer
from lumina.graph import ModelGraph, Node


def test_linear_flops():
    graph = ModelGraph(nodes=[
        Node(id="linear", type="Linear", params={"in_features": 10, "out_features": 20}),
    ])
    stats = FlopAnalyzer().analyze(graph)
    assert stats["total_flops"] == 2 * 10 * 20
    assert stats["per_node"]["linear"] == 2 * 10 * 20


def test_conv2d_flops():
    graph = ModelGraph(nodes=[
        Node(id="conv", type="Conv2d", params={
            "in_channels": 3,
            "out_channels": 64,
            "kernel_size": 3,
            "stride": 1,
            "padding": 0,
        }),
    ])
    stats = FlopAnalyzer().analyze(graph)
    assert stats["total_flops"] == 2 * 3 * 3 * 3 * 64
