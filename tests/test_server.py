from fastapi.testclient import TestClient
from lumina.parsers.simple import SimpleModel
from lumina.server import create_app


def test_get_graph():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    app = create_app(model)
    client = TestClient(app)
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert len(data["nodes"]) == 1


def test_get_stats():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    app = create_app(model)
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_params"] == 55
