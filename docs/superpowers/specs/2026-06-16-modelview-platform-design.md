# Lumina Platform Design Document

## 1. 目标与范围

Lumina 从一个"模型结构查看器"升级为一个**本地优先的端到端机器学习工作台**。它帮助用户管理从原始数据到模型训练、评估、推理的完整 ML 生命周期，同时保持对框架和依赖的松耦合。

### 核心原则

- **本地优先**：所有数据默认存储在用户本地，不强制上传云端。
- **框架无关**：不强制安装 PyTorch、MLX、TensorFlow 等框架，只使用用户环境中已存在的依赖。
- **快速查看 + 项目管理并存**：既可以一行代码临时查看，也可以创建项目长期管理。
- **可扩展**：Dataset、模型解析器、评估指标、可视化组件都通过 adapter/plugin 机制接入。
- **可复盘**：所有实验、训练日志、评估结果持久化，支持训练后回放。
- **训练不侵入代码**：Lumina 不定义训练方案（模型、优化器、损失函数等），只运行用户提供的训练脚本并记录指标。
- **CLI 优先**：提供完整命令行接口，方便脚本化、批量操作和测试运行。

### 支持范围

| 模块 | 覆盖内容 |
|------|----------|
| 数据 Data | 表格、图像目录、文本、Hugging Face datasets（可选 adapter） |
| 模型 Model | 结构可视化、参数量、FLOPs、形状、内存、配置导出、代码生成 |
| 训练 Train | 通用 Logger API、TensorBoard 日志读取、实时曲线、Checkpoint 管理 |
| 评估 Eval | 分类/回归指标、混淆矩阵、ROC/PR、残差图、指标对比 |
| 推理 Infer | 单条预测、批量推理、结果表格、错误案例分析 |
| 可解释性 XAI | 特征重要性、SHAP、注意力/Grad-CAM（可选 adapter） |

### 明确排除

- 分布式训练管理
- 模型版本控制（如 Git-LFS 集成，可后续扩展）
- 云端协作和多用户权限
- 自动超参搜索（AutoML）
- 模型部署 serving
- 训练方案设计 / 训练代码生成（Lumina 只运行用户脚本并记录指标）

---

## 2. 核心概念

### 2.1 项目 Project

项目是管理数据、模型、实验、评估、推理的容器。

```python
import lumina

project = lumina.open_project("my_project")  # 创建或打开
project.datasets.create(name="mnist", path="data/mnist")
project.models.register(name="lenet", path="models/lenet.pt", framework="pytorch")
exp = project.start_experiment(name="exp_001", model="lenet", dataset="mnist")
```

每个项目对应一个本地目录，包含：

- `lumina.db`：SQLite 元数据库
- `datasets/`：数据集文件或引用
- `models/`：模型文件
- `experiments/`：实验配置和摘要
- `checkpoints/`：训练 checkpoint
- `artifacts/`：评估报告、图表、推理结果

### 2.2 快速查看 Quick View

不创建项目，直接查看某个资源：

```python
lumina.view(model)
lumina.view_dataset("data/train.csv")
lumina.view_experiment("runs/exp_001")
lumina.view_logs("runs/exp_001")
```

快速查看也会把数据缓存到临时目录，但不长期保存。

### 2.3 实验 Experiment

实验是训练一次模型的完整记录，包含：

- 超参数
- 训练日志（每个 step/epoch 的 loss 和 metrics）
- Checkpoint 列表
- 关联的模型和数据集
- 评估结果引用

### 2.4 Dataset

Dataset 是统一的数据抽象，底层通过 adapter 支持不同格式：

```python
dataset = lumina.Dataset.from_csv("data/train.csv")
dataset = lumina.Dataset.from_image_folder("data/images", label_file="labels.csv")
dataset = lumina.Dataset.from_huggingface("mnist", split="train")  # 可选 adapter
```

Dataset 提供统一接口：

- `preview(n=10)`：查看前 N 条样本
- `statistics()`：统计信息（分布、缺失值、类别平衡）
- `schema()`：列/字段类型
- `split(train=0.8, val=0.1, test=0.1)`：划分数据集

---

## 3. 整体架构

### 3.1 后端架构

```
Python 包 lumina
├── core/               # 项目、配置、存储管理
├── storage/            # SQLite + 文件系统抽象
├── datasets/           # Dataset 抽象 + adapters
├── models/             # 模型解析 + analyzers
├── experiments/        # 实验记录 + logger
├── training/           # 训练日志读取 + 实时推送
├── evaluation/         # 评估指标 + 可视化数据生成
├── inference/          # 推理执行 + 结果管理
├── server/             # FastAPI + WebSocket/SSE
└── plugins/            # 第三方扩展点
```

### 3.2 前端架构

```
frontend/
├── App.tsx             # 路由 + 全局状态
├── panels/
│   ├── DataPanel.tsx
│   ├── ModelPanel.tsx
│   ├── TrainingPanel.tsx
│   ├── EvalPanel.tsx
│   ├── InferPanel.tsx
│   └── ProjectPanel.tsx
├── components/         # 可复用可视化组件
└── hooks/              # API 调用、WebSocket
```

### 3.3 数据流

1. 用户通过 Python API 创建项目或快速查看。
2. 后端把元数据写入 SQLite，大文件写入项目目录。
3. FastAPI 暴露 REST API 和 WebSocket 实时通道。
4. React 前端加载数据并渲染各个面板。
5. 训练时通过 Logger API 或 TensorBoard 读取实时更新前端。

---

## 4. 存储设计

### 4.1 文件系统布局

```
my_project/
├── lumina.db
├── config.yaml
├── datasets/
│   ├── mnist_train.parquet
│   └── mnist_val.parquet
├── models/
│   └── lenet_v1.pt
├── experiments/
│   └── exp_001.yaml
├── checkpoints/
│   └── exp_001/
│       ├── ckpt_0010.pt
│       └── ckpt_0100.pt
└── artifacts/
    ├── eval_001/
    │   ├── confusion_matrix.png
    │   └── metrics.json
    └── infer_001/
        └── predictions.csv
```

### 4.2 SQLite Schema

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE datasets (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    path TEXT,
    adapter_type TEXT NOT NULL,  -- csv, parquet, image_folder, huggingface
    schema_json TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    path TEXT,
    framework TEXT,
    config_json TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE experiments (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    model_id TEXT REFERENCES models(id),
    dataset_id TEXT REFERENCES datasets(id),
    hyperparams_json TEXT,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE training_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT REFERENCES experiments(id),
    step INTEGER,
    epoch INTEGER,
    metrics_json TEXT NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    experiment_id TEXT REFERENCES experiments(id),
    path TEXT NOT NULL,
    epoch INTEGER,
    step INTEGER,
    metrics_json TEXT,
    is_best BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evaluations (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    experiment_id TEXT REFERENCES experiments(id),
    model_id TEXT REFERENCES models(id),
    dataset_id TEXT REFERENCES datasets(id),
    metrics_json TEXT NOT NULL,
    artifact_paths_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inferences (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    model_id TEXT REFERENCES models(id),
    dataset_id TEXT REFERENCES datasets(id),
    output_path TEXT,
    metrics_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Python API 设计

### 5.1 项目管理

```python
import lumina

# 打开或创建项目
project = lumina.open_project("my_project", path="~/lumina_projects/my_project")

# 列出项目
lumina.list_projects()

# 删除项目
lumina.delete_project("my_project")
```

### 5.2 数据管理

```python
# 注册数据集
dataset = project.datasets.create(
    name="mnist_train",
    path="data/mnist_train.parquet",
    adapter="parquet"
)

# 查看数据
dataset.preview(10)
dataset.statistics()

# 划分
train, val, test = dataset.split(train=0.8, val=0.1, test=0.1)
```

### 5.3 模型管理

```python
# 注册模型
model = project.models.register(
    name="lenet",
    path="models/lenet.pt",
    framework="pytorch"
)

# 快速查看
lumina.view(model)
```

### 5.4 实验与训练

```python
# 启动实验
exp = project.start_experiment(
    name="exp_001",
    model="lenet",
    dataset="mnist_train",
    hyperparams={"lr": 0.001, "batch_size": 64}
)

# 记录日志
for epoch in range(100):
    loss = train_epoch()
    metrics = evaluate()
    exp.log(epoch=epoch, step=global_step, metrics={"loss": loss, **metrics})

# 保存 checkpoint
exp.save_checkpoint(path="checkpoints/exp_001/ckpt_0100.pt", epoch=100, metrics=metrics)

# 结束实验
exp.finish()
```

### 5.5 TensorBoard 读取

```python
# 读取 TensorBoard logs
lumina.view_logs("runs/exp_001")

# 导入到项目实验
project.import_tensorboard("runs/exp_001", experiment_name="exp_001")
```

### 5.6 评估

```python
eval = project.evaluate(
    model="lenet",
    dataset="mnist_val",
    metrics=["accuracy", "precision", "recall", "f1"],
    visualizations=["confusion_matrix", "roc"]
)
```

### 5.7 推理

```python
# 单条推理
result = project.infer(model="lenet", input={"image": "test/1.png"})

# 批量推理
project.infer_batch(
    model="lenet",
    dataset="mnist_test",
    output_path="artifacts/infer_001/predictions.csv"
)
```

---

## 6. CLI 设计

Lumina 提供统一的命令行入口 `lumina`（或 `mv`），覆盖项目创建、数据导入、模型查看、实验启动、评估推理、测试运行等常见操作。

### 6.1 全局选项

```bash
lumina --version
lumina --help
lumina --project PATH   # 指定当前项目目录
```

### 6.2 项目管理

```bash
# 创建项目
lumina project create my_project --path ~/lumina_projects/my_project

# 列出项目
lumina project list

# 打开项目并启动 UI
lumina project open my_project

# 删除项目
lumina project delete my_project
```

### 6.3 数据管理

```bash
# 导入数据集
lumina data add mnist_train data/mnist_train.parquet --adapter parquet

# 预览数据
lumina data preview mnist_train --n 10

# 查看统计
lumina data stats mnist_train

# 划分数据集
lumina data split mnist_train --train 0.8 --val 0.1 --test 0.1
```

### 6.4 模型管理

```bash
# 注册模型
lumina model add lenet models/lenet.pt --framework pytorch

# 查看模型结构（启动 UI）
lumina model view lenet

# 分析模型
lumina model analyze lenet

# 导出配置 / 生成代码
lumina model export lenet --format yaml
lumina model codegen lenet --output model.py
```

### 6.5 实验与训练

```bash
# 启动实验并打开训练面板
lumina experiment create exp_001 --model lenet --dataset mnist_train --lr 0.001

# 查看实验
lumina experiment list
lumina experiment view exp_001

# 导入 TensorBoard logs
lumina experiment import-tb runs/exp_001 --name exp_001
```

### 6.6 评估与推理

```bash
# 运行评估
lumina eval run exp_001 --dataset mnist_val --metrics accuracy,precision,recall

# 批量推理
lumina infer batch lenet --dataset mnist_test --output predictions.csv

# 单条推理
lumina infer single lenet --input test/1.png
```

### 6.7 启动 UI

```bash
# 默认打开当前项目或快速查看模式
lumina ui

# 指定端口
lumina ui --port 8080

# 快速查看模型文件
lumina ui --model models/lenet.pt

# 快速查看数据集
lumina ui --dataset data/train.csv

# 快速查看 TensorBoard logs
lumina ui --logs runs/exp_001
```

### 6.8 测试与检查

```bash
# 运行项目内所有测试
lumina test

# 检查环境依赖和 adapter 可用性
lumina doctor

# 验证项目配置
lumina project validate
```

### 6.9 实现说明

- CLI 基于 `typer` 或 `click` 构建，作为 `lumina` 包的 console script 注册到 `pyproject.toml`。
- CLI 调用与 Python API 相同的内部函数，避免逻辑重复。
- 所有耗时操作（如训练、评估、批量推理）提供 `--no-ui` 选项，适合 CI/脚本场景。

---

## 7. FastAPI 接口

### 6.1 项目

- `GET /api/projects`：列出项目
- `POST /api/projects`：创建项目
- `GET /api/projects/{id}`：项目详情
- `DELETE /api/projects/{id}`：删除项目

### 6.2 数据集

- `GET /api/projects/{id}/datasets`：列出数据集
- `POST /api/projects/{id}/datasets`：创建数据集
- `GET /api/datasets/{id}`：数据集详情
- `GET /api/datasets/{id}/preview?n=10`：预览数据
- `GET /api/datasets/{id}/statistics`：统计信息

### 6.3 模型

- `GET /api/projects/{id}/models`：列出模型
- `POST /api/projects/{id}/models`：注册模型
- `GET /api/models/{id}`：模型详情
- `GET /api/models/{id}/graph`：模型结构图
- `GET /api/models/{id}/stats`：模型分析统计

### 6.4 实验

- `GET /api/projects/{id}/experiments`：列出实验
- `POST /api/projects/{id}/experiments`：创建实验
- `GET /api/experiments/{id}`：实验详情
- `GET /api/experiments/{id}/logs`：训练日志
- `GET /api/experiments/{id}/checkpoints`：checkpoint 列表
- `POST /api/experiments/{id}/logs`：写入日志（用于快速查看模式）
- `WS /api/experiments/{id}/stream`：WebSocket 实时日志流

### 6.5 评估与推理

- `POST /api/evaluations`：执行评估
- `GET /api/evaluations/{id}`：评估结果
- `POST /api/inferences`：执行推理
- `GET /api/inferences/{id}`：推理结果

---

## 8. 前端面板设计

### 7.1 项目首页

- 项目概览卡片：数据集数、模型数、实验数、最近实验
- 快速入口：新建实验、查看数据、注册模型

### 7.2 数据面板

- 数据集列表
- 数据表格预览（分页、排序、筛选）
- 统计卡片：行数、列数、缺失值、类别分布
- 可视化：数值分布直方图、类别饼图、相关性热力图

### 7.3 模型面板

- 模型列表
- 结构可视化（保留现有 Cytoscape 图）
- 分析面板：参数量、FLOPs、形状、内存
- 配置导出 / 代码生成

### 7.4 训练面板

- 实验列表
- 训练曲线：loss、metrics 多轴图
- 实时模式：WebSocket 自动刷新
- 回放模式：加载历史实验
- Checkpoint 列表和对比
- 超参卡片

### 7.5 评估面板

- 指标表格
- 混淆矩阵
- ROC / PR 曲线
- 回归残差图
- 多实验指标对比

### 7.6 推理面板

- 单条输入表单或上传
- 预测结果展示
- 批量推理结果表格
- 错误案例分析

---

## 9. Adapter 架构

### 8.1 Dataset Adapter

```python
from lumina.datasets.adapter import DatasetAdapter

class CSVAdapter(DatasetAdapter):
    name = "csv"
    supported_extensions = [".csv"]

    def load(self, path: str) -> Any:
        import polars  # 可选依赖
        return polars.read_csv(path)

    def preview(self, n: int = 10) -> list[dict]:
        ...

    def statistics(self) -> dict:
        ...
```

内置 adapters：

- `csv`：CSV 文件
- `parquet`：Parquet 文件
- `image_folder`：图像目录 + 标签文件
- `text`：文本文件或目录
- `huggingface`：Hugging Face datasets（可选安装）
- `sqlite`：SQLite 表

### 8.2 Model Parser Adapter

已存在：simple、pytorch、mlx、keras、onnx、sklearn。未来通过 `lumina.plugins.register_parser()` 扩展。

### 8.3 Evaluation Metric Adapter

```python
lumina.evaluation.register_metric("my_metric", my_metric_fn)
```

### 8.4 Visualization Adapter

```python
lumina.visualization.register("shap", ShapVisualization)
```

---

## 10. 实时训练更新机制

### 训练边界说明

Lumina **不定义训练方案**，也不生成训练代码。训练方案（模型架构、优化器、损失函数、学习率策略等）完全由用户在自己的 `train.py` 中决定。

Lumina 在训练环节只负责三件事：

1. **启动/停止训练脚本**：用户指定训练脚本路径，Lumina 以子进程方式运行，并可随时停止。
2. **记录训练指标**：训练脚本通过 `lumina.log()` 主动上报，或写入 TensorBoard events 文件。
3. **展示训练曲线**：前端通过 REST/WebSocket 实时或回放展示 loss、metrics、checkpoint 等信息。

示例用户训练脚本：

```python
# train.py
import lumina

exp = lumina.start_experiment(project="my_project", name="exp_001")

for epoch in range(100):
    # 用户自己定义的训练逻辑
    loss = train_one_epoch(...)
    metrics = evaluate(...)
    exp.log(epoch=epoch, metrics={"loss": loss, **metrics})
```

启动方式：

```bash
lumina train run --script train.py --project my_project --name exp_001
```

### 10.1 Logger 写入

训练代码调用：

```python
exp.log(epoch=10, step=1000, metrics={"loss": 0.5, "acc": 0.9})
```

后端：

1. 写入 SQLite `training_logs`。
2. 发布到 WebSocket channel `/api/experiments/{id}/stream`。
3. 同时追加到本地 TensorBoard-compatible events 文件（可选）。

### 10.2 WebSocket 推送

前端连接 `WS /api/experiments/{id}/stream`，后端用 `Broadcast` 推送新日志。前端收到后更新曲线。

### 10.3 TensorBoard 读取

支持两种模式：

1. **文件监控**：轮询 `runs/` 目录下的 `events.out.tfevents.*` 文件，解析 scalar 后入库/推送。
2. **一次性导入**：读取 TensorBoard 日志并导入到项目实验。

使用 `tensorboard-backend` 或自研解析器（可选依赖）。

---

## 11. 安全与隐私

- 默认本地运行，不向外发送数据。
- 项目目录权限跟随操作系统。
- 未来如支持远程访问，需加身份验证和 HTTPS。

---

## 12. 性能考虑

- 大数据集预览限制默认 1000 行，避免前端卡死。
- 训练日志按实验分表或分区，避免单表过大。
- 图像数据集用缩略图缓存。
- WebSocket 推送做节流，避免高频训练日志刷屏。

---

## 13. 测试策略

- 单元测试：每个 adapter、parser、analyzer、metric。
- 集成测试：项目创建 → 数据集注册 → 实验 → 评估 → 推理 完整流程。
- 前端测试：面板渲染、图表交互、WebSocket mock。
- 性能测试：大数据集预览、大量训练日志查询。

---

## 14. 分阶段实现建议

| 阶段 | 目标 | 关键产出 |
|------|------|----------|
| Phase 1 | 项目与数据面板 | 项目创建、SQLite 存储、Dataset adapter、数据预览与统计 |
| Phase 2 | 模型面板增强 | FLOPs、形状、内存分析、配置导出、代码生成 |
| Phase 3 | 训练面板 | Logger API、TensorBoard 读取、实时曲线、checkpoint 管理 |
| Phase 4 | 评估面板 | 分类/回归指标、混淆矩阵、ROC/PR、多实验对比 |
| Phase 5 | 推理面板 | 单条/批量推理、结果展示、错误案例分析 |
| Phase 6 | 可解释性 | SHAP、特征重要性、Grad-CAM 等可选 adapter |
| Phase 7 | 插件系统 | 第三方 adapter、metric、visualization 注册机制 |

---

## 15. 与现有 MVP 的关系

当前 MVP 已实现：

- 模型结构可视化（simple/pytorch/mlx/keras/onnx/sklearn parsers）
- 参数分析器
- FastAPI + React 前端基础
- sklearn 决策树可视化

完整平台 spec 在此基础上扩展：

- 把 `lumina.view()` 升级为项目级 API 的入口之一。
- 保留现有 model parser 和 analyzer 架构。
- 新增 `core`、`storage`、`datasets`、`experiments`、`evaluation`、`inference` 模块。
- 前端从单页面扩展为多面板应用。
