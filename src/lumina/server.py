from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from lumina.analyzers.aggregate import aggregate_analysis
from lumina.core.project import Project
from lumina.datasets.dataset import Dataset
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
    def preview_dataset(name: str, n: int = Query(10, ge=1)) -> dict:
        if project is None:
            raise HTTPException(status_code=404, detail="No project loaded")
        record = project.datasets.get_by_name(project.id, name)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Dataset {name} not found")
        ds = Dataset(name=record["name"], path=Path(record["path"]), adapter_type=record["adapter_type"])
        return {"rows": ds.preview(n), "schema": ds.schema(), "statistics": ds.statistics()}

    if project is not None:
        @app.get("/api/runs")
        def list_runs() -> list[dict]:
            return project.experiments.runs.list_by_project(project.id)

        @app.get("/api/runs/{run_id}")
        def get_run(run_id: str) -> dict:
            run = project.experiments.runs.get(run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="Run not found")
            return run

        @app.get("/api/metrics")
        def list_metrics(run_id: str, name: Optional[str] = None) -> list[dict]:
            return project.experiments.metrics.list_by_run(run_id, name=name)

        @app.get("/api/checkpoints")
        def list_checkpoints(run_id: str) -> list[dict]:
            return project.experiments.checkpoints.list_by_run(run_id)

        @app.get("/api/checkpoints/{checkpoint_id}/download")
        def download_checkpoint(checkpoint_id: int):
            import mimetypes
            row = project.experiments.get_checkpoint(checkpoint_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Checkpoint not found")
            file_path = project.path / row["path"]
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Checkpoint file missing")
            from fastapi.responses import FileResponse
            return FileResponse(
                path=str(file_path),
                filename=file_path.name,
                media_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
            )

        @app.post("/api/projects/{project_id}/logs")
        def register_log_dir(project_id: str, log_dir: str, name: Optional[str] = None) -> dict:
            if project_id != project.id:
                raise HTTPException(status_code=404, detail="Project not found")
            return project.experiments.register_log_dir(Path(log_dir), name=name)

        @app.post("/api/projects/{project_id}/logs/sync")
        def sync_log_dir(project_id: str, run_id: str) -> dict:
            if project_id != project.id:
                raise HTTPException(status_code=404, detail="Project not found")
            run = project.experiments.runs.get(run_id)
            if run is None or run["log_dir"] is None:
                raise HTTPException(status_code=400, detail="Run has no log directory")
            count = project.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
            return {"synced": count}

        @app.post("/api/projects/current/logs/sync")
        def sync_current_log_dir(run_id: str) -> dict:
            if project is None:
                raise HTTPException(status_code=404, detail="No project loaded")
            run = project.experiments.runs.get(run_id)
            if run is None or run["log_dir"] is None:
                raise HTTPException(status_code=400, detail="Run has no log directory")
            count = project.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
            return {"synced": count}

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
        def get_stats(input_shape: Optional[str] = None) -> dict:
            shape = None
            if input_shape:
                shape = [int(x) for x in input_shape.split(",")]
            return aggregate_analysis(graph, input_shape=shape)

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
