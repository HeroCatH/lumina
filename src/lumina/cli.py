import argparse
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

    # lumina version
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args(argv)

    if args.command == "start":
        return _handle_start(args)
    elif args.command == "project" and args.project_command == "create":
        return _handle_project_create(args)
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
    raise NotImplementedError("Project creation from CLI is planned for Phase 1")


if __name__ == "__main__":
    sys.exit(main())
