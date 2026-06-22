import mimetypes
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lumina.analyzers.aggregate import aggregate_analysis
from lumina.core.project import Project
from lumina.core.project_manager import ProjectManager
from lumina.datasets.dataset import Dataset
from lumina.loaders import load_model


STATIC_DIR = Path(__file__).parent / "static"


class CreateEvaluationRequest(BaseModel):
    run_id: str
    predictions_path: str
    dataset_id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    task_type: Optional[Literal["classification", "regression"]] = Field(None)


class CreateProjectRequest(BaseModel):
    name: str
    path: Optional[str] = Field(None)


def _current_project(request: Request) -> Project:
    project = request.app.state.project
    if project is None:
        raise HTTPException(status_code=404, detail="No project loaded")
    return project


def create_app(model: Optional[Any] = None, project: Optional[Project] = None) -> FastAPI:
    app = FastAPI(title="Lumina")
    app.state.project = project

    @app.get("/api/projects")
    def list_projects() -> list[dict]:
        with ProjectManager() as manager:
            return manager.list()

    @app.post("/api/projects", status_code=201)
    def create_project(payload: CreateProjectRequest) -> dict:
        with ProjectManager() as manager:
            new_project = manager.create(payload.name, Path(payload.path) if payload.path else None)
            app.state.project = new_project
            return {"id": new_project.id, "name": new_project.name, "path": str(new_project.path)}

    @app.post("/api/projects/{name}/open")
    def open_project(name: str) -> dict:
        with ProjectManager() as manager:
            opened = manager.open(name)
            app.state.project = opened
            return {"id": opened.id, "name": opened.name, "path": str(opened.path)}

    @app.get("/api/projects/current")
    def get_current_project(request: Request) -> dict:
        proj = _current_project(request)
        return {"name": proj.name, "path": str(proj.path)}

    @app.get("/api/datasets")
    def list_datasets(request: Request) -> list[dict]:
        proj = _current_project(request)
        return proj.datasets.list_by_project(proj.id)

    @app.get("/api/datasets/{name}/preview")
    def preview_dataset(name: str, request: Request, n: int = Query(10, ge=1)) -> dict:
        proj = _current_project(request)
        record = proj.datasets.get_by_name(proj.id, name)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Dataset {name} not found")
        ds = Dataset(name=record["name"], path=Path(record["path"]), adapter_type=record["adapter_type"])
        return {"rows": ds.preview(n), "schema": ds.schema(), "statistics": ds.statistics()}

    @app.get("/api/runs")
    def list_runs(request: Request) -> list[dict]:
        proj = _current_project(request)
        return proj.experiments.runs.list_by_project(proj.id)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str, request: Request) -> dict:
        proj = _current_project(request)
        run = proj.experiments.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.get("/api/metrics")
    def list_metrics(request: Request, run_id: str, name: Optional[str] = None) -> list[dict]:
        proj = _current_project(request)
        if proj.experiments.runs.get(run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return proj.experiments.metrics.list_by_run(run_id, name=name)

    @app.get("/api/checkpoints")
    def list_checkpoints(request: Request, run_id: str) -> list[dict]:
        proj = _current_project(request)
        if proj.experiments.runs.get(run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return proj.experiments.checkpoints.list_by_run(run_id)

    @app.get("/api/checkpoints/{checkpoint_id}/download")
    def download_checkpoint(checkpoint_id: int, request: Request):
        proj = _current_project(request)
        row = proj.experiments.get_checkpoint(checkpoint_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        file_path = proj.path / row["path"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Checkpoint file missing")
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
        )

    @app.get("/api/evaluations")
    def list_evaluations(request: Request, run_id: Optional[str] = Query(None)) -> list[dict]:
        proj = _current_project(request)
        if run_id is not None and proj.experiments.runs.get(run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        if run_id is not None:
            return proj.experiments.evaluations.list_by_run(run_id)
        return proj.experiments.evaluations.list_by_project(proj.id)

    @app.post("/api/evaluations", status_code=201)
    def create_evaluation(request: Request, payload: CreateEvaluationRequest = Body(...)) -> dict:
        proj = _current_project(request)
        try:
            evaluation = proj.experiments.evaluations.create(
                run_id=payload.run_id,
                predictions_path=payload.predictions_path,
                dataset_id=payload.dataset_id,
                name=payload.name,
                task_type=payload.task_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return evaluation

    @app.get("/api/evaluations/{evaluation_id}")
    def get_evaluation(evaluation_id: str, request: Request, include_predictions: bool = Query(False)) -> dict:
        proj = _current_project(request)
        evaluation = proj.experiments.evaluations.get(evaluation_id, include_predictions=include_predictions)
        if evaluation is None:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        return evaluation

    @app.delete("/api/evaluations/{evaluation_id}")
    def delete_evaluation(evaluation_id: str, request: Request) -> dict:
        proj = _current_project(request)
        if proj.experiments.evaluations.get(evaluation_id) is None:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        proj.experiments.evaluations.delete(evaluation_id)
        return {"deleted": True}

    @app.post("/api/projects/{project_id}/logs")
    def register_log_dir(project_id: str, request: Request, log_dir: str, name: Optional[str] = None) -> dict:
        proj = _current_project(request)
        if project_id != proj.id:
            raise HTTPException(status_code=404, detail="Project not found")
        try:
            return proj.experiments.register_log_dir(Path(log_dir), name=name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/projects/current/logs/sync")
    def sync_current_log_dir(request: Request, run_id: str) -> dict:
        proj = _current_project(request)
        run = proj.experiments.runs.get(run_id)
        if run is None or run["log_dir"] is None:
            raise HTTPException(status_code=400, detail="Run has no log directory")
        count = proj.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
        return {"synced": count}

    @app.post("/api/projects/{project_id}/logs/sync")
    def sync_log_dir(project_id: str, request: Request, run_id: str) -> dict:
        proj = _current_project(request)
        if project_id != proj.id:
            raise HTTPException(status_code=404, detail="Project not found")
        run = proj.experiments.runs.get(run_id)
        if run is None or run["log_dir"] is None:
            raise HTTPException(status_code=400, detail="Run has no log directory")
        count = proj.experiments.sync_log_dir(Path(run["log_dir"]), run_id)
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
