from modelview.parsers.simple import SimpleModel, SimpleParser


def test_parse_simple_model():
    model = SimpleModel([
        {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64}},
        {"type": "ReLU", "params": {}},
        {"type": "Linear", "params": {"in_features": 64, "out_features": 10}},
    ])
    graph = SimpleParser().parse(model)
    assert len(graph.nodes) == 3
    assert graph.nodes[0].type == "Conv2d"
    assert graph.nodes[2].type == "Linear"
    assert len(graph.edges) == 2
    assert graph.edges[0].source == "0"
    assert graph.edges[0].target == "1"
