import pytest

sklearn = pytest.importorskip("sklearn")

from sklearn.tree import DecisionTreeClassifier
from modelview.parsers.sklearn import SklearnParser


def test_parse_decision_tree():
    X = [[0], [1], [2], [3]]
    y = [0, 0, 1, 1]
    model = DecisionTreeClassifier(max_depth=2, random_state=42)
    model.fit(X, y)

    graph = SklearnParser().parse(model)
    assert len(graph.nodes) > 0
    assert graph.metadata["framework"] == "sklearn"
    # Root should be a Decision node
    assert graph.nodes[0].type == "Decision"
    # Leaf nodes should exist
    assert any(n.type == "Leaf" for n in graph.nodes)
