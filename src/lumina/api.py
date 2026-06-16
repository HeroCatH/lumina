import webbrowser
from typing import Any

import uvicorn

from lumina.server import create_app


def view(model: Any, port: int = 8080, open_browser: bool = True) -> None:
    app = create_app(model)
    if open_browser:
        url = f"http://localhost:{port}"
        webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def export_config(model: Any, path: str) -> None:
    raise NotImplementedError("export_config is planned for a later iteration")


def generate_code(path: str) -> str:
    raise NotImplementedError("generate_code is planned for a later iteration")
