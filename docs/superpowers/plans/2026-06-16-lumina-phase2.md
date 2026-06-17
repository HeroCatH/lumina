# Lumina Phase 2: Model Analysis Panel Enhancement

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the model panel with FLOPs/MACs, input/output shape, and memory usage analysis for neural network layers.

**Architecture:** Add three new analyzer classes (`FlopAnalyzer`, `ShapeAnalyzer`, `MemoryAnalyzer`) alongside the existing `ParamAnalyzer`. The analyzers operate on the unified `ModelGraph` and return JSON-friendly statistics. FastAPI aggregates them into a single `/api/models/{id}/stats` endpoint (and keeps backward-compatible `/api/stats` for quick model view). The frontend ModelPanel displays per-layer analysis tables and aggregated totals.

**Tech Stack:** Python 3.12, FastAPI, React, TypeScript.

---

## File Structure

```
src/lumina/
├── analyzers/
│   ├── __init__.py
│   ├── base.py
│   ├── params.py          # existing
│   ├── flops.py           # new
│   ├── shapes.py          # new
│   └── memory.py          # new
├── core/
│   └── model_manager.py   # optional: register models in projects
└── server.py              # extend model stats endpoint

frontend/src/
├── panels/
│   └── ModelPanel.tsx     # enhance with analysis tabs/tables
└── types.ts               # add analysis types

tests/
├── test_flop_analyzer.py
├── test_shape_analyzer.py
├── test_memory_analyzer.py
└── test_model_stats.py
```

---

## Task 1: FLOPs/MACs Analyzer

**Files:**
- Create: `src/lumina/analyzers/flops.py`
- Modify: `src/lumina/analyzers/__init__.py`
- Create: `tests/test_flop_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_flop_analyzer.py
from lumina.analyzers.flops import FlopAnalyzer
from lumina.graph import ModelGraph, Node


def test_linear_flops():
    graph = ModelGraph(nodes=[
        Node(id="linear", type="Linear", params={"in_features": 10, "out_features": 20}),
    ])
    stats = FlopAnalyzer().analyze(graph)
    # FLOPs for Linear: 2 * in * out (MAC counted as 2 FLOPs)
    assert stats["total_flops"] == 2 * 10 * 20
    assert stats["per_node"]["linear"] == 2 * 10 * 20


def test_conv2d_flops():
    graph = ModelGraph(nodes=[
        Node(id="conv", type="Conv2d", params={
            "in_channels": 3,
            "out_channels": 64,
            "kernel_size": 3,
            "stride": 1,
            "padding": 0,
        }),
    ])
    stats = FlopAnalyzer().analyze(graph)
    # Approximate: 2 * k^2 * Cin * Cout (ignoring output spatial dims in MVP)
    assert stats["total_flops"] == 2 * 3 * 3 * 3 * 64
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_flop_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/analyzers/flops.py`**

```python
from typing import Any, Dict

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class FlopAnalyzer(Analyzer):
    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        total = 0
        per_node = {}

        for node in graph.nodes:
            flops = self._estimate_node_flops(node)
            per_node[node.id] = flops
            total += flops

        return {
            "total_flops": total,
            "total_macs": total // 2,
            "per_node": per_node,
        }

    def _estimate_node_flops(self, node: Any) -> int:
        params = node.params
        layer_type = node.type

        if layer_type in ("Linear", "nn.Linear"):
            in_f = params.get("in_features", 0)
            out_f = params.get("out_features", 0)
            return 2 * in_f * out_f

        if layer_type in ("Conv2d", "nn.Conv2d"):
            in_ch = params.get("in_channels", 0)
            out_ch = params.get("out_channels", 0)
            kernel = params.get("kernel_size", 1)
            if isinstance(kernel, (tuple, list)):
                k = 1
                for dim in kernel:
                    k *= dim
            else:
                k = kernel * kernel
            return 2 * in_ch * out_ch * k

        return 0
```

- [ ] **Step 4: Modify `src/lumina/analyzers/__init__.py`**

```python
from lumina.analyzers.base import Analyzer
from lumina.analyzers.flops import FlopAnalyzer
from lumina.analyzers.memory import MemoryAnalyzer
from lumina.analyzers.params import ParamAnalyzer
from lumina.analyzers.shapes import ShapeAnalyzer

__all__ = ["Analyzer", "ParamAnalyzer", "FlopAnalyzer", "ShapeAnalyzer", "MemoryAnalyzer"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_flop_analyzer.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/lumina/analyzers/flops.py tests/test_flop_analyzer.py
git commit -m "feat: add FLOPs/MACs analyzer"
```

---

## Task 2: Input/Output Shape Analyzer

**Files:**
- Create: `src/lumina/analyzers/shapes.py`
- Create: `tests/test_shape_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_shape_analyzer.py
from lumina.analyzers.shapes import ShapeAnalyzer
from lumina.graph import ModelGraph, Node, Edge


def test_linear_chain_shapes():
    graph = ModelGraph(nodes=[
        Node(id="linear1", type="Linear", params={"in_features": 10, "out_features": 20}),
        Node(id="relu", type="ReLU"),
        Node(id="linear2", type="Linear", params={"in_features": 20, "out_features": 5}),
    ], edges=[
        Edge(source="linear1", target="relu"),
        Edge(source="relu", target="linear2"),
    ])
    stats = ShapeAnalyzer(input_shape=[1, 10]).analyze(graph)
    assert stats["input_shape"] == [1, 10]
    assert stats["per_node"]["linear1"]["output_shape"] == [1, 20]
    assert stats["per_node"]["linear2"]["output_shape"] == [1, 5]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_shape_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/analyzers/shapes.py`**

```python
from typing import Any, Dict, List

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class ShapeAnalyzer(Analyzer):
    def __init__(self, input_shape: List[int]):
        self.input_shape = input_shape

    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        per_node = {}
        current_shape = list(self.input_shape)

        # Build adjacency for edge-based traversal; fall back to node order
        node_order = [n.id for n in graph.nodes]

        for node in graph.nodes:
            out_shape = self._estimate_output_shape(node, current_shape)
            per_node[node.id] = {
                "input_shape": list(current_shape),
                "output_shape": list(out_shape),
            }
            current_shape = out_shape

        return {
            "input_shape": list(self.input_shape),
            "output_shape": list(current_shape),
            "per_node": per_node,
        }

    def _estimate_output_shape(self, node: Any, input_shape: List[int]) -> List[int]:
        layer_type = node.type
        params = node.params

        if layer_type in ("Linear", "nn.Linear"):
            out_features = params.get("out_features", input_shape[-1])
            return input_shape[:-1] + [out_features]

        if layer_type in ("Conv2d", "nn.Conv2d"):
            h, w = input_shape[-2], input_shape[-1]
            kernel = params.get("kernel_size", 1)
            stride = params.get("stride", 1)
            padding = params.get("padding", 0)
            out_ch = params.get("out_channels", input_shape[-3])

            if isinstance(kernel, (tuple, list)):
                k_h, k_w = kernel[0], kernel[1]
            else:
                k_h = k_w = kernel
            if isinstance(stride, (tuple, list)):
                s_h, s_w = stride[0], stride[1]
            else:
                s_h = s_w = stride
            if isinstance(padding, (tuple, list)):
                p_h, p_w = padding[0], padding[1]
            else:
                p_h = p_w = padding

            out_h = (h + 2 * p_h - k_h) // s_h + 1
            out_w = (w + 2 * p_w - k_w) // s_w + 1
            return list(input_shape[:-3]) + [out_ch, out_h, out_w]

        if layer_type in ("Flatten", "nn.Flatten"):
            total = 1
            for dim in input_shape[1:]:
                total *= dim
            return [input_shape[0], total]

        # Default: shape passes through
        return input_shape
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_shape_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/analyzers/shapes.py tests/test_shape_analyzer.py
git commit -m "feat: add input/output shape analyzer"
```

---

## Task 3: Memory Analyzer

**Files:**
- Create: `src/lumina/analyzers/memory.py`
- Create: `tests/test_memory_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory_analyzer.py
from lumina.analyzers.memory import MemoryAnalyzer
from lumina.graph import ModelGraph, Node


def test_linear_memory():
    graph = ModelGraph(nodes=[
        Node(id="linear", type="Linear", params={"in_features": 10, "out_features": 20}),
    ])
    stats = MemoryAnalyzer().analyze(graph)
    # Params: 10*20 weights + 20 biases = 220 floats, 4 bytes each
    assert stats["param_bytes"] == 220 * 4
    assert stats["per_node"]["linear"]["param_bytes"] == 220 * 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_memory_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Write `src/lumina/analyzers/memory.py`**

```python
from typing import Any, Dict

from lumina.analyzers.base import Analyzer
from lumina.graph import ModelGraph


class MemoryAnalyzer(Analyzer):
    BYTES_PER_PARAM = 4  # float32

    def analyze(self, graph: ModelGraph, **kwargs: Any) -> Dict[str, Any]:
        total = 0
        per_node = {}

        for node in graph.nodes:
            bytes_used = self._estimate_node_memory(node)
            per_node[node.id] = {"param_bytes": bytes_used}
            total += bytes_used

        return {
            "param_bytes": total,
            "param_megabytes": round(total / (1024 * 1024), 4),
            "per_node": per_node,
        }

    def _estimate_node_memory(self, node: Any) -> int:
        params = node.params
        layer_type = node.type

        if layer_type in ("Linear", "nn.Linear"):
            in_f = params.get("in_features", 0)
            out_f = params.get("out_features", 0)
            bias = params.get("bias", True)
            total = in_f * out_f
            if bias:
                total += out_f
            return total * self.BYTES_PER_PARAM

        if layer_type in ("Conv2d", "nn.Conv2d"):
            in_ch = params.get("in_channels", 0)
            out_ch = params.get("out_channels", 0)
            kernel = params.get("kernel_size", 1)
            if isinstance(kernel, (tuple, list)):
                k = 1
                for dim in kernel:
                    k *= dim
            else:
                k = kernel * kernel
            bias = params.get("bias", True)
            total = in_ch * out_ch * k
            if bias:
                total += out_ch
            return total * self.BYTES_PER_PARAM

        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_memory_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/analyzers/memory.py tests/test_memory_analyzer.py
git commit -m "feat: add memory usage analyzer"
```

---

## Task 4: Analyzer Aggregation and Model Stats Endpoint

**Files:**
- Create: `src/lumina/analyzers/aggregate.py`
- Modify: `src/lumina/server.py`
- Modify: `src/lumina/api.py`
- Create: `tests/test_model_stats.py`

- [ ] **Step 1: Update existing test expectations**

The existing `tests/test_server.py::test_get_stats` currently asserts `data["total_params"] == 55`. Since `/api/stats` will now return aggregated analysis, update it:

```python
# tests/test_server.py
def test_get_stats():
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
    )
    app = create_app(model=model)
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "params" in data
    assert data["params"]["total_params"] == 55
    assert "flops" in data
    assert "memory" in data
```

- [ ] **Step 2: Write the new aggregated stats test**

```python
# tests/test_model_stats.py
from pathlib import Path
from fastapi.testclient import TestClient
from lumina.parsers.simple import SimpleModel
from lumina.server import create_app


def test_model_stats_endpoint():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
        {"type": "ReLU", "params": {}},
    ])
    app = create_app(model=model)
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "params" in data
    assert "flops" in data
    assert "memory" in data


def test_model_stats_with_input_shape():
    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    app = create_app(model=model)
    client = TestClient(app)
    response = client.get("/api/stats?input_shape=1,10")
    assert response.status_code == 200
    data = response.json()
    assert "shapes" in data
    assert data["shapes"]["output_shape"] == [1, 5]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_model_stats.py::test_model_stats_endpoint -v`
Expected: FAIL

- [ ] **Step 4: Write `src/lumina/analyzers/aggregate.py`**

```python
from typing import Any, Dict, List, Optional

from lumina.analyzers.flops import FlopAnalyzer
from lumina.analyzers.memory import MemoryAnalyzer
from lumina.analyzers.params import ParamAnalyzer
from lumina.analyzers.shapes import ShapeAnalyzer
from lumina.graph import ModelGraph


def aggregate_analysis(
    graph: ModelGraph,
    input_shape: Optional[List[int]] = None,
) -> Dict[str, Any]:
    result = {
        "params": ParamAnalyzer().analyze(graph),
        "flops": FlopAnalyzer().analyze(graph),
        "memory": MemoryAnalyzer().analyze(graph),
    }
    if input_shape is not None:
        result["shapes"] = ShapeAnalyzer(input_shape).analyze(graph)
    return result
```

- [ ] **Step 5: Modify `src/lumina/server.py`**

Update the existing `/api/stats` endpoint to return aggregated stats:

```python
from lumina.analyzers.aggregate import aggregate_analysis

@app.get("/api/stats")
def get_stats(input_shape: Optional[str] = None) -> dict:
    shape = None
    if input_shape:
        shape = [int(x) for x in input_shape.split(",")]
    return aggregate_analysis(graph, input_shape=shape)
```

- [ ] **Step 6: Modify `src/lumina/api.py`** (optional: expose analyze helper)

```python
from lumina.analyzers.aggregate import aggregate_analysis


def analyze(model: Any, input_shape: Optional[List[int]] = None) -> Dict[str, Any]:
    from lumina.loaders import load_model

    graph = load_model(model)
    return aggregate_analysis(graph, input_shape=input_shape)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_model_stats.py tests/test_server.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/lumina/analyzers/aggregate.py src/lumina/server.py src/lumina/api.py tests/test_model_stats.py
git commit -m "feat: aggregate model analysis stats and expose via API"
```

---

## Task 5: Frontend ModelPanel Analysis View

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/panels/ModelPanel.tsx`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add analysis types**

Modify `frontend/src/types.ts`:

```typescript
export interface ModelStats {
  params: {
    total_params: number
    trainable_params: number
    per_node: Record<string, number>
  }
  flops: {
    total_flops: number
    total_macs: number
    per_node: Record<string, number>
  }
  memory: {
    param_bytes: number
    param_megabytes: number
    per_node: Record<string, { param_bytes: number }>
  }
  shapes?: {
    input_shape: number[]
    output_shape: number[]
    per_node: Record<string, { input_shape: number[]; output_shape: number[] }>
  }
}
```

- [ ] **Step 2: Update `frontend/src/api.ts`**

```typescript
import { ModelGraph, Stats, ModelStats } from './types'

export async function fetchStats(inputShape?: number[]): Promise<ModelStats> {
  const query = inputShape ? `?input_shape=${inputShape.join(',')}` : ''
  const res = await fetch(`/api/stats${query}`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}
```

- [ ] **Step 3: Modify `frontend/src/panels/ModelPanel.tsx`**

Add an "Analysis" section/table below the graph. Show:
- Total params, FLOPs, MACs, memory
- Per-node table: type, params, FLOPs, memory, input/output shapes
- Optional input shape form to trigger shape analysis

Keep the existing layer tree, node graph, and detail panel layout.

- [ ] **Step 4: Build frontend**

Run:
```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/panels/ModelPanel.tsx frontend/src/api.ts frontend/src/types.ts frontend/src/App.tsx src/lumina/static
git commit -m "feat: display model analysis in ModelPanel"
```

---

## Task 6: CLI `lumina model analyze`

**Files:**
- Modify: `src/lumina/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
def test_cli_model_analyze(capsys, tmp_path):
    from lumina.parsers.simple import SimpleModel

    model = SimpleModel([
        {"type": "Linear", "params": {"in_features": 10, "out_features": 5}},
    ])
    import pickle
    model_path = tmp_path / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # This test verifies the command parses and runs; actual analyze may need pickle support
    code = main(["model", "analyze", "--model", str(model_path), "--input-shape", "1,10"])
    assert code == 0
    captured = capsys.readouterr()
    assert "params" in captured.out or "FLOPs" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py::test_cli_model_analyze -v`
Expected: FAIL

- [ ] **Step 3: Add CLI command**

In `src/lumina/cli.py`, add:

```python
model_parser = subparsers.add_parser("model", help="Model management")
model_sub = model_parser.add_subparsers(dest="model_command")
analyze_parser = model_sub.add_parser("analyze", help="Analyze a model file")
analyze_parser.add_argument("--model", required=True, help="Path to model file")
analyze_parser.add_argument("--input-shape", help="Input shape as comma-separated ints")
```

Handle:

```python
elif args.command == "model" and args.model_command == "analyze":
    return _handle_model_analyze(args)
```

```python
def _handle_model_analyze(args: argparse.Namespace) -> int:
    import pickle
    from lumina.api import analyze

    with open(args.model, "rb") as f:
        model = pickle.load(f)

    input_shape = None
    if args.input_shape:
        input_shape = [int(x) for x in args.input_shape.split(",")]

    stats = analyze(model, input_shape=input_shape)
    print(f"Params: {stats['params']['total_params']}")
    print(f"FLOPs: {stats['flops']['total_flops']}")
    print(f"MACs: {stats['flops']['total_macs']}")
    print(f"Memory: {stats['memory']['param_megabytes']} MB")
    if "shapes" in stats:
        print(f"Output shape: {stats['shapes']['output_shape']}")
    return 0
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lumina/cli.py tests/test_cli.py
git commit -m "feat: add lumina model analyze CLI command"
```

---

## Task 7: README Update and Final Verification

**Files:**
- Modify: `README.md`
- Create: `examples/model_analysis.py`

- [ ] **Step 1: Update README**

Add to README under model section:

```markdown
## Model Analysis

Lumina can analyze your model's parameters, FLOPs/MACs, memory footprint, and layer shapes.

```python
import lumina
from lumina.parsers.simple import SimpleModel

model = SimpleModel([
    {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3}},
    {"type": "ReLU", "params": {}},
    {"type": "Linear", "params": {"in_features": 64, "out_features": 10}},
])

stats = lumina.analyze(model, input_shape=[1, 3, 32, 32])
print(stats)
```

Or via CLI:

```bash
lumina model analyze --model path/to/model.pkl --input-shape 1,3,32,32
```
```

- [ ] **Step 2: Create `examples/model_analysis.py`**

```python
import lumina
from lumina.parsers.simple import SimpleModel

model = SimpleModel([
    {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3, "padding": 1}},
    {"type": "ReLU", "params": {}},
    {"type": "Flatten", "params": {}},
    {"type": "Linear", "params": {"in_features": 64 * 32 * 32, "out_features": 10}},
])

stats = lumina.analyze(model, input_shape=[1, 3, 32, 32])
print("Params:", stats["params"]["total_params"])
print("FLOPs:", stats["flops"]["total_flops"])
print("Memory (MB):", stats["memory"]["param_megabytes"])
print("Output shape:", stats["shapes"]["output_shape"])
```

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add README.md examples/model_analysis.py
git commit -m "docs: add model analysis examples and README section"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| FLOPs / MACs analysis | Task 1 |
| Input/output shape analysis | Task 2 |
| Memory usage analysis | Task 3 |
| Analyzer aggregation | Task 4 |
| Frontend model analysis display | Task 5 |
| CLI model analyze | Task 6 |
| Documentation | Task 7 |

---

## Phase 2 Completion Criteria

- [ ] `FlopAnalyzer` estimates FLOPs/MACs for Linear and Conv2d
- [ ] `ShapeAnalyzer` computes per-layer shapes given an input shape
- [ ] `MemoryAnalyzer` estimates parameter memory
- [ ] `/api/stats` returns aggregated analysis
- [ ] Frontend ModelPanel shows analysis tables
- [ ] CLI `lumina model analyze` works
- [ ] All tests pass
