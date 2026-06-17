from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from lumina.experiments.service import ExperimentService

if TYPE_CHECKING:
    from lumina.core.project import Project


class Run:
    def __init__(self, run_id: str, project: Optional[Project], service: ExperimentService):
        self.id = run_id
        self._project = project
        self._service = service

    @classmethod
    def start(cls, project: Project, name: Optional[str] = None) -> "Run":
        service = project.experiments
        run_id = str(uuid.uuid4())
        service.runs.create(
            run_id=run_id,
            project_id=project.id,
            name=name or run_id[:8],
            status="running",
            source="sdk",
        )
        return cls(run_id=run_id, project=project, service=service)

    def log(self, name: str, value: float, step: int) -> None:
        self._service.metrics.create(run_id=self.id, step=step, name=name, value=value)

    def save_checkpoint(self, source_path: str, step: int) -> Path:
        if self._project is None:
            raise RuntimeError("save_checkpoint requires a project-bound run")
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Checkpoint source not found: {source_path}")
        dest_dir = self._service.checkpoint_dir(self.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"step_{step}{src.suffix}"
        shutil.copy2(src, dest)
        rel_path = dest.relative_to(self._project.path)
        self._service.checkpoints.create(run_id=self.id, step=step, path=str(rel_path))
        return dest

    def finish(self) -> None:
        self._service.runs.update_status(self.id, "finished")
