from lumina.analyzers.shapes import ShapeAnalyzer
from lumina.graph import ModelGraph, Node, Edge


def test_linear_chain_shapes():
    graph = ModelGraph(nodes=[
        Node(id="linear1", type="Linear", params={"in_features": 10, "out_features": 20}),
        Node(id="relu", type="ReLU"),
        Node(id="linear2", type="Linear", params={"in_features": 20, "out_features": 5}),
    ], edges=[
        Edge(source="linear1", target="relu"),
        Edge(source="relu", target="linear2"),
    ])
    stats = ShapeAnalyzer(input_shape=[1, 10]).analyze(graph)
    assert stats["input_shape"] == [1, 10]
    assert stats["per_node"]["linear1"]["output_shape"] == [1, 20]
    assert stats["per_node"]["linear2"]["output_shape"] == [1, 5]


def test_conv2d_shape():
    graph = ModelGraph(nodes=[
        Node(id="conv", type="Conv2d", params={
            "in_channels": 3,
            "out_channels": 64,
            "kernel_size": 3,
            "stride": 1,
            "padding": 1,
        }),
    ])
    stats = ShapeAnalyzer(input_shape=[1, 3, 32, 32]).analyze(graph)
    assert stats["per_node"]["conv"]["output_shape"] == [1, 64, 32, 32]


def test_flatten_shape():
    graph = ModelGraph(nodes=[
        Node(id="flatten", type="Flatten"),
    ])
    stats = ShapeAnalyzer(input_shape=[1, 3, 4, 4]).analyze(graph)
    assert stats["per_node"]["flatten"]["output_shape"] == [1, 48]
