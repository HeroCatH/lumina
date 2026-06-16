import pytest

from lumina.loaders import load_model
from lumina.parsers.simple import SimpleModel


def test_load_simple_model():
    model = SimpleModel([
        {"type": "Conv2d", "params": {"in_channels": 3}},
        {"type": "Linear", "params": {"out_features": 10}},
    ])
    graph = load_model(model)
    assert len(graph.nodes) == 2
    assert graph.metadata["framework"] == "simple"


def test_load_unsupported_type():
    with pytest.raises(ValueError):
        load_model(object())
