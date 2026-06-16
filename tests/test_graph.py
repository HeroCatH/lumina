from modelview.graph import ModelGraph, Node, Edge


def test_model_graph_creation():
    node = Node(id="conv1", type="Conv2d", params={"in_channels": 3, "out_channels": 64})
    graph = ModelGraph(nodes=[node], edges=[])
    assert graph.nodes[0].id == "conv1"
    assert graph.nodes[0].type == "Conv2d"
