from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from modelview.graph import ModelGraph
from modelview.loaders import load_model


STATIC_DIR = Path(__file__).parent / "static"


def create_app(model: Any) -> FastAPI:
    graph = load_model(model)
    app = FastAPI(title="ModelView")

    @app.get("/api/graph")
    def get_graph() -> dict:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "params": n.params,
                    "display_name": n.display_name or n.id,
                }
                for n in graph.nodes
            ],
            "edges": [{"source": e.source, "target": e.target} for e in graph.edges],
            "metadata": graph.metadata,
        }

    @app.get("/api/stats")
    def get_stats() -> dict:
        from modelview.analyzers.params import ParamAnalyzer

        return ParamAnalyzer().analyze(graph)

    @app.get("/api/node/{node_id}")
    def get_node(node_id: str) -> dict:
        for n in graph.nodes:
            if n.id == node_id:
                return {
                    "id": n.id,
                    "type": n.type,
                    "params": n.params,
                    "display_name": n.display_name or n.id,
                }
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app
