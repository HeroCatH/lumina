import importlib
from typing import Any

from modelview.graph import ModelGraph
from modelview.parsers.simple import SimpleModel, SimpleParser


# Map: module name substring -> (parser module path, parser class name)
_FRAMEWORKS = [
    ("mlx", "modelview.parsers.mlx", "MlxParser"),
    ("torch", "modelview.parsers.pytorch", "PytorchParser"),
    ("tensorflow", "modelview.parsers.keras", "KerasParser"),
    ("keras", "modelview.parsers.keras", "KerasParser"),
    ("onnx", "modelview.parsers.onnx", "OnnxParser"),
    ("sklearn", "modelview.parsers.sklearn", "SklearnParser"),
]


def load_model(model: Any) -> ModelGraph:
    """Dispatch model to the appropriate parser based on its type.

    Framework-specific dependencies are imported lazily so that users only
    need to install the frameworks they actually use.
    """
    if isinstance(model, (SimpleModel, list, dict)):
        return SimpleParser().parse(model)

    module_name = type(model).__module__
    for substring, parser_module, parser_class in _FRAMEWORKS:
        if substring in module_name:
            parser_cls = _import_parser(parser_module, parser_class)
            return parser_cls().parse(model)

    raise ValueError(f"Unsupported model type: {type(model)} (module: {module_name})")


def _import_parser(module_path: str, class_name: str) -> Any:
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(
            f"Parser module {module_path} could not be imported. "
            f"Make sure the corresponding framework is installed."
        ) from exc
    return getattr(module, class_name)
