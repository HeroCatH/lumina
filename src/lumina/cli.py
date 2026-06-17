import argparse
from pathlib import Path
import sys
from typing import List

from lumina.api import view
from lumina.parsers.simple import SimpleModel


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lumina", description="Lumina ML Workbench")
    subparsers = parser.add_subparsers(dest="command")

    # lumina start
    start_parser = subparsers.add_parser("start", help="Start the Lumina UI")
    start_parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    start_parser.add_argument("--model", type=str, help="Path to a model file to view")
    start_parser.add_argument("--dataset", type=str, help="Path to a dataset to view")
    start_parser.add_argument("--logs", type=str, help="Path to TensorBoard logs to view")
    start_parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    # lumina project
    project_parser = subparsers.add_parser("project", help="Project management")
    project_sub = project_parser.add_subparsers(dest="project_command")
    create_parser = project_sub.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--path", help="Project directory path")
    list_parser = project_sub.add_parser("list", help="List projects")
    open_parser = project_sub.add_parser("open", help="Open a project in the UI")
    open_parser.add_argument("name", help="Project name")
    open_parser.add_argument("--port", type=int, default=8080, help="Port to run the UI on")

    # lumina data
    data_parser = subparsers.add_parser("data", help="Dataset management")
    data_sub = data_parser.add_subparsers(dest="data_command")
    add_data_parser = data_sub.add_parser("add", help="Add a dataset to a project")
    add_data_parser.add_argument("name", help="Dataset name")
    add_data_parser.add_argument("path", help="Path to dataset file")
    add_data_parser.add_argument("--adapter", help="Adapter type (auto-detect if omitted)")
    add_data_parser.add_argument("--project", required=True, help="Project name")

    # lumina version
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args(argv)

    if args.command == "start":
        return _handle_start(args)
    elif args.command == "project" and args.project_command == "create":
        return _handle_project_create(args)
    elif args.command == "project" and args.project_command == "list":
        return _handle_project_list()
    elif args.command == "project" and args.project_command == "open":
        return _handle_project_open(args)
    elif args.command == "data" and args.data_command == "add":
        return _handle_data_add(args)
    elif args.command == "version":
        print("lumina 0.1.0")
        return 0
    else:
        parser.print_help()
        return 1


def _handle_start(args: argparse.Namespace) -> int:
    # Quick view fallback: if no model/dataset/logs provided, use a demo simple model.
    if args.model:
        raise NotImplementedError("Loading model from CLI path is not yet implemented")
    if args.dataset:
        raise NotImplementedError("Loading dataset from CLI path is not yet implemented")
    if args.logs:
        raise NotImplementedError("Loading logs from CLI path is not yet implemented")

    demo_model = SimpleModel([
        {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3}},
        {"type": "ReLU", "params": {}},
        {"type": "Linear", "params": {"in_features": 64, "out_features": 10}},
    ])
    view(demo_model, port=args.port, open_browser=not args.no_browser)
    return 0


def _handle_project_create(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    path = Path(args.path) if args.path else None
    project = manager.create(args.name, path)
    print(f"Created project: {project.name} at {project.path}")
    return 0


def _handle_project_list() -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    for project in manager.list():
        print(f"{project['name']}\t{project['path']}")
    return 0


def _handle_project_open(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager
    from lumina.api import view_project

    manager = ProjectManager()
    project = manager.open(args.name)
    view_project(project, port=args.port)
    return 0


def _handle_data_add(args: argparse.Namespace) -> int:
    from lumina.core.project_manager import ProjectManager

    manager = ProjectManager()
    project = manager.open(args.project)
    dataset = project.register_dataset(args.name, args.path, args.adapter)
    print(f"Added dataset: {dataset.name} ({dataset.adapter_type})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
