# ModelView

A Python library for visualizing model structures in the browser.

## Quick Start

```bash
# Install the package
uv pip install -e .

# Or with pip
pip install -e .
```

```python
import modelview
from modelview.parsers.simple import SimpleModel

model = SimpleModel([
    {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3}},
    {"type": "ReLU", "params": {}},
    {"type": "Linear", "params": {"in_features": 64, "out_features": 10}},
])

modelview.view(model, port=8080)
```

Then open http://localhost:8080 in your browser.

## Features

- **Layer tree** and **interactive node graph** in the browser
- **Parameter count** statistics per layer
- **Framework-agnostic** core: only the frameworks you have installed are used
- Optional parsers for PyTorch, MLX, TensorFlow/Keras, ONNX, scikit-learn, XGBoost, LightGBM

## Optional Framework Support

ModelView detects which ML frameworks are installed in your environment and uses them lazily:

```python
import torch
import modelview

model = torch.nn.Sequential(
    torch.nn.Linear(10, 20),
    torch.nn.ReLU(),
)
modelview.view(model)
```

If PyTorch is not installed, the PyTorch parser is simply not available.

## Development

```bash
uv pip install -e ".[dev]"
.venv/bin/pytest
```

## Roadmap

- [x] Browser-based model visualization
- [x] Parameter statistics
- [x] Optional dependency loading
- [ ] FLOPs / MACs analysis
- [ ] Input/output shape analysis
- [ ] Memory usage analysis
- [ ] Export model structure to YAML/JSON
- [ ] Generate PyTorch `nn.Module` code from config
