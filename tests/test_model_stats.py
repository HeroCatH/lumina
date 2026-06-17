from pathlib import Path
from fastapi.testclient import TestClient
from lumina.parsers.simple import SimpleModel
from lumina.server import create_app


def test_model_stats_endpoint():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
        {"type": "ReLU", "params": {}},
    ])
    app = create_app(model=model)
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "params" in data
    assert "flops" in data
    assert "memory" in data


def test_model_stats_with_input_shape():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    app = create_app(model=model)
    client = TestClient(app)
    response = client.get("/api/stats?input_shape=1,10")
    assert response.status_code == 200
    data = response.json()
    assert "shapes" in data
    assert data["shapes"]["output_shape"] == [1, 5]
