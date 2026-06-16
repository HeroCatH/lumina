from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from lumina.core.project import Project
from lumina.loaders import load_model


STATIC_DIR = Path(__file__).parent / "static"


def create_app(model: Optional[Any] = None, project: Optional[Project] = None) -> FastAPI:
    app = FastAPI(title="Lumina")

    @app.get("/api/projects/current")
    def get_current_project() -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        return {"name": project.name, "path": str(project.path)}

    @app.get("/api/datasets")
    def list_datasets() -> list[dict]:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        return project.datasets.list_by_project(project.id)

    @app.get("/api/datasets/{name}/preview")
    def preview_dataset(name: str, n: int = 10) -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        record = project.datasets.get_by_name(project.id, name)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Dataset {name} not found")
        from lumina.datasets.dataset import Dataset

        ds = Dataset(name=record["name"], path=Path(record["path"]), adapter_type=record["adapter_type"])
        return {"rows": ds.preview(n), "schema": ds.schema(), "statistics": ds.statistics()}

    # Existing model endpoints kept for backward compatibility
    if model is not None:
        graph = load_model(model)

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
            from lumina.analyzers.params import ParamAnalyzer

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
