# Lumina API & CLI 使用说明

Lumina 启动后会暴露一个本地 FastAPI 服务（默认 `http://localhost:8080`），同时提供 `lumina` 命令行工具。下面是当前可用接口与命令的说明。

---

## 目录

- [启动服务](#启动服务)
- [通用约定](#通用约定)
- [项目 API](#项目-api)
- [数据集 API](#数据集-api)
- [实验 / Run API](#实验--run-api)
- [指标 API](#指标-api)
- [Checkpoint API](#checkpoint-api)
- [评估 API](#评估-api)
- [CLI 命令](#cli-命令)

---

## 启动服务

```bash
# 方式 1：打开已有项目
lumina project open <project-name> --port 8080

# 方式 2：空启动（仅模型演示）
lumina start --port 8080
```

服务启动后，浏览器会自动打开 `http://localhost:8080`。

---

## 通用约定

- 所有接口以 `/api` 为前缀。
- 若当前未加载项目，大部分接口返回 `404`，响应体为 `{"detail": "No project loaded"}`。
- 查询参数使用 `URLSearchParams` 风格。
- 创建类接口返回 `201 Created`，删除类接口返回 `200 OK`。

---

## 项目 API

### 获取当前项目

```http
GET /api/projects/current
```

响应：

```json
{
  "name": "demo",
  "path": "/Users/hehang/lumina_projects/demo"
}
```

---

## 数据集 API

### 列出数据集

```http
GET /api/datasets
```

响应：

```json
[
  {
    "id": "...",
    "project_id": "...",
    "name": "mnist",
    "path": "...",
    "adapter_type": "csv",
    "created_at": "..."
  }
]
```

### 预览数据集

```http
GET /api/datasets/{name}/preview?n=50
```

响应包含 `rows`、`schema`、`statistics`。

---

## 实验 / Run API

### 列出 Run

```http
GET /api/runs
```

### 获取单个 Run

```http
GET /api/runs/{run_id}
```

### 注册外部日志目录

```http
POST /api/projects/{project_id}/logs?log_dir=/path/to/logs&name=my-run
```

### 同步日志

```http
POST /api/projects/current/logs/sync?run_id={run_id}
```

---

## 指标 API

### 列出指标

```http
GET /api/metrics?run_id={run_id}&name=loss
```

`name` 可选，用于按指标名过滤。

---

## Checkpoint API

### 列出 Checkpoint

```http
GET /api/checkpoints?run_id={run_id}
```

### 下载 Checkpoint

```http
GET /api/checkpoints/{checkpoint_id}/download
```

---

## 评估 API

评估用于记录模型在测试集上的预测结果及指标。 predictions CSV 必须包含 `id`、`true`、`pred` 三列，可选 `confidence` 列。

### 列出评估

```http
GET /api/evaluations
GET /api/evaluations?run_id={run_id}
```

响应：

```json
[
  {
    "id": "27c997c3-...",
    "run_id": "run-demo-1",
    "dataset_id": null,
    "name": "demo-eval",
    "task_type": "classification",
    "predictions_path": "/Users/.../evaluations/27c997c3-.../sample_predictions.csv",
    "metrics": "{\"accuracy\":0.6,...}",
    "created_at": "..."
  }
]
```

### 创建评估

```http
POST /api/evaluations
Content-Type: application/json
```

请求体：

```json
{
  "run_id": "run-demo-1",
  "predictions_path": "/path/to/predictions.csv",
  "dataset_id": "optional-dataset-id",
  "name": "my-eval",
  "task_type": "classification"
}
```

- `task_type` 可省略或传 `"auto"`，后端会根据数据自动推断 `classification` / `regression`。
- `dataset_id` 和 `name` 可选。
- 文件会被复制到项目目录 `evaluations/{evaluation_id}/{原文件名}` 中归档。

### 获取评估详情

```http
GET /api/evaluations/{evaluation_id}
GET /api/evaluations/{evaluation_id}?include_predictions=true
```

带 `include_predictions=true` 时会在响应中附加 `predictions` 数组：

```json
{
  "id": "...",
  "metrics": "...",
  "predictions": [
    {
      "id": 1,
      "evaluation_id": "...",
      "sample_id": "0",
      "true_value": "cat",
      "pred_value": "cat",
      "confidence": 0.95,
      "is_correct": 1
    }
  ]
}
```

### 删除评估

```http
DELETE /api/evaluations/{evaluation_id}
```

响应：

```json
{ "deleted": true }
```

---

## CLI 命令

### 项目管理

```bash
lumina project create <name> [--path <dir>]
lumina project list
lumina project open <name> [--port 8080]
```

### 数据集

```bash
lumina data add <name> <path> --project <project-name> [--adapter csv]
```

### 实验日志

```bash
lumina project logs add <log-dir> --project <project-name> [--name <run-name>]
lumina project logs sync --project <project-name> --run-id <run-id>
```

### Run

```bash
lumina project runs list --project <project-name>
```

### 评估

```bash
# 创建评估
lumina project eval create <predictions-path> \
  --project <project-name> \
  --run-id <run-id> \
  [--dataset-id <dataset-id>] \
  [--name <name>] \
  [--task-type classification|regression]

# 列评估
lumina project eval list --project <project-name> [--run-id <run-id>]
```

示例：

```bash
cat > /tmp/pred.csv <<EOF
id,true,pred,confidence
0,cat,cat,0.95
1,dog,cat,0.55
2,bird,bird,0.92
EOF

lumina project eval create /tmp/pred.csv \
  --project demo \
  --run-id run-demo-1 \
  --name my-eval
```

---

## predictions CSV 格式

| 列名 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 样本标识 |
| `true` | 是 | 真实标签/值 |
| `pred` | 是 | 模型预测 |
| `confidence` | 否 | 置信度，非法值会被忽略为 `null` |

任务类型推断规则：
- 若任意值包含小数点 → 回归。
- 若所有值都是整数且唯一值 ≤ 20 → 分类。
- 否则 → 回归。
- 可用 `task_type` 参数强制覆盖。

---

## Python SDK 快速示例

```python
from lumina.core.project_manager import ProjectManager

with ProjectManager() as manager:
    project = manager.open("demo")

    run = project.experiments.runs.create(
        run_id="run-2",
        project_id=project.id,
        name="run-2",
        source="sdk",
    )

    evaluation = project.experiments.evaluations.create(
        run_id=run["id"],
        predictions_path="/path/to/pred.csv",
        name="sdk-eval",
    )
    print(evaluation["id"], evaluation["task_type"])
```
