import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn

from lumina.analyzers.aggregate import aggregate_analysis
from lumina.core.project import Project
from lumina.core.project_manager import ProjectManager
from lumina.experiments.run import Run
from lumina.loaders import load_model
from lumina.server import create_app


def analyze(model: Any, input_shape: Optional[List[int]] = None) -> Dict[str, Any]:
    graph = load_model(model)
    return aggregate_analysis(graph, input_shape=input_shape)


def view(model: Any, port: int = 8080, open_browser: bool = True) -> None:
    app = create_app(model)
    if open_browser:
        url = f"http://localhost:{port}"
        webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def view_project(project: Project, port: int = 8080, open_browser: bool = True) -> None:
    app = create_app(project=project)
    if open_browser:
        webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def export_config(model: Any, path: str) -> None:
    raise NotImplementedError("export_config is planned for a later iteration")


def generate_code(path: str) -> str:
    raise NotImplementedError("generate_code is planned for a later iteration")


def open_project(name: str, root: Optional[str] = None) -> Project:
    """Open an existing project. The caller is responsible for closing the returned Project."""
    with ProjectManager(root=Path(root) if root else None) as manager:
        return manager.open(name)


def create_project(name: str, root: Optional[str] = None) -> Project:
    """Create a new project under the given root directory. The caller is responsible for closing the returned Project."""
    with ProjectManager(root=Path(root) if root else None) as manager:
        return manager.create(name)


def list_projects(root: Optional[str] = None) -> list[dict]:
    """List projects under the given root directory."""
    with ProjectManager(root=Path(root) if root else None) as manager:
        return manager.list()


def start_run(project: Project, name: Optional[str] = None) -> Run:
    """Start a new experiment run bound to the given project."""
    return Run.start(project=project, name=name)
