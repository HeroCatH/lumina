from modelview.parsers.simple import SimpleModel, SimpleParser
from modelview.analyzers.params import ParamAnalyzer


def test_linear_params():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 20}},
    ])
    graph = SimpleParser().parse(model)
    stats = ParamAnalyzer().analyze(graph)
    assert stats["total_params"] == 220  # 10*20 weights + 20 biases


def test_conv2d_params():
    model = SimpleModel([
        {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3}},
    ])
    graph = SimpleParser().parse(model)
    stats = ParamAnalyzer().analyze(graph)
    assert stats["total_params"] == 1792  # 3*64*3*3 weights + 64 biases
