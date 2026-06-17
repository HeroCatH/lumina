# Lumina Phase 3-A 设计文档：实验追踪

## 背景与目标

Phase 2 完成后，Lumina 已经具备模型结构可视化、参数/FLOPs/内存/形状分析能力。Phase 3 的野心是让 Lumina 不止分析模型，而是覆盖完整的 ML 实验流：

- **Phase 3-A**：训练/实验追踪
- **Phase 3-C**：评估与数据集联动
- **Phase 3-D**：可解释性可视化

本文档聚焦 **Phase 3-A**。目标是让用户能在 Lumina 中查看训练过程：metric 曲线、run 列表、checkpoint 管理。Lumina **不定义训练逻辑**，只负责记录、同步、可视化用户已有训练脚本产生的数据。

## 范围

### 在范围内

1. **SDK 方式记录**：用户在训练脚本里通过 `lumina.start_run()` / `run.log()` / `run.save_checkpoint()` 写入项目数据库。
2. **文件方式同步**：用户在项目里注册外部日志目录，Lumina 通过适配器解析 `tfevents`、`.jsonl`、`.csv` 并同步到数据库。
3. **Checkpoint 管理**：Lumina 接管 checkpoint 文件，自动按 run/step 存放到项目 `checkpoints/` 下。
4. **浏览器面板**：新增 Experiments Panel，展示 run 列表、metric 曲线、checkpoint 列表。
5. **CLI**：`lumina project logs add/sync`、`lumina project runs list`。

### 不在范围内

- 生成训练代码或训练方案。
- 分布式训练协调。
- 模型版本控制（如 MLflow 的模型注册表）。

## 总体架构

```
┌─────────────────────┐      SDK      ┌─────────────┐
│ User Training Script│ ─────────────> │ Lumina SDK  │
│  lumina.start_run() │               │             │
│  run.log()          │               │ writes to   │
│  run.save_checkpoint│               │ SQLite DB   │
└─────────────────────┘               └──────┬──────┘
                                             │
┌─────────────────────┐      sync           │
│ External Log Dir    │ ────────────────────┤
│ tfevents/jsonl/csv  │    Log Adapters     │
└─────────────────────┘                     │
                                             ▼
                                      ┌─────────────┐
                                      │ SQLite      │
                                      │ runs        │
                                      │ metrics     │
                                      │ checkpoints │
                                      └──────┬──────┘
                                             │
                                             │ API
                                             ▼
                                      ┌─────────────┐
                                      │ FastAPI     │
                                      │ /api/runs   │
                                      │ /api/metrics│
                                      │ /api/checkp.│
                                      └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │ Experiments │
                                      │ Panel (UI)  │
                                      └─────────────┘
```

### 关键设计决策

- **统一数据库**：无论 SDK 还是文件日志，最终都落到 SQLite，UI 只查一种 schema。
- **Run 标识**：SDK 自动创建 `run_id`；文件日志按目录名 + 文件 `mtime` 生成 `run_id`，避免重复导入。
- **Checkpoint 路径**：`projects/<project>/checkpoints/<run_id>/step_<step>.pt`，数据库只存相对路径。
- **Checkpoint 必须关联项目**：`run.save_checkpoint()` 要求 run 已绑定 project；未绑定时抛出清晰错误，引导用户先打开项目。
- **可选依赖**：TensorBoard 解析依赖 `tensorboard` 包，未安装时优雅降级。

## 数据模型

### `runs`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | run 唯一标识 |
| project_id | TEXT | 所属项目（可空，用于独立日志目录） |
| name | TEXT | 用户可读名称 |
| status | TEXT | `running` / `finished` / `failed` |
| source | TEXT | `sdk` / `tfevents` / `jsonl` / `csv` |
| log_dir | TEXT | 外部日志目录路径 |
| created_at | TEXT | ISO 时间 |
| updated_at | TEXT | ISO 时间 |

### `metrics`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| run_id | TEXT | FK -> runs |
| step | INTEGER | 训练步数 |
| name | TEXT | metric 名，如 `loss` |
| value | REAL | metric 值 |
| timestamp | TEXT | ISO 时间 |

### `checkpoints`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| run_id | TEXT | FK -> runs |
| step | INTEGER | 训练步数 |
| path | TEXT | 相对项目根目录的路径 |
| created_at | TEXT | ISO 时间 |

## Python SDK

```python
import lumina

# 绑定到项目（可选）
project = lumina.open_project("my_project")

# 自动创建 run
run = lumina.start_run(project=project, name="lr=0.001")

# 记录 metric
run.log("loss", 0.42, step=100)
run.log("accuracy", 0.87, step=100)

# 保存 checkpoint（必须关联 project）
run.save_checkpoint("/path/to/model.pt", step=100)

# 结束 run
run.finish()
```

## API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/runs` | 列出 runs，支持 `project_id` 过滤 |
| GET | `/api/runs/<run_id>` | 单个 run 详情 |
| GET | `/api/metrics` | 查询 metrics，参数 `run_id`、`name`（可选） |
| GET | `/api/checkpoints` | 列出 checkpoints，参数 `run_id` |
| GET | `/api/checkpoints/<id>/download` | 下载某个 checkpoint 文件 |
| POST | `/api/projects/<project_id>/logs/sync` | 手动触发外部日志目录同步 |
| POST | `/api/projects/<project_id>/logs` | 注册外部日志目录 |

## CLI

```bash
# 注册外部日志目录
lumina project logs add ./logs --project my_project

# 手动触发同步
lumina project logs sync --project my_project

# 列出 runs
lumina project runs list --project my_project
```

## UI 设计

新增 **Experiments Panel**，布局如下：

- **左侧**：Run 列表，显示名称、状态、时间。点击切换当前 run。
- **右上**：工具栏，Refresh / Sync logs / metric 选择器 / auto-refresh 间隔。
- **右中**：Metric 曲线区，按 metric 名绘制 step/value 折线图，支持多选对比。
- **右下**：Checkpoint 列表，展示 step、路径、创建时间，支持下载/复制路径。

## 错误处理

- **可选依赖缺失**：未安装 `tensorboard` 时，tfevents 适配器不可用但其他功能正常；UI 提示用户安装。
- **日志目录被删除**：外部日志目录消失后，数据库中已有 metrics 保留，仅停止同步。
- **重复导入**：Log Adapter 用文件 `mtime` + 路径 hash 做去重，避免同一文件反复插入。
- **并发写入**：SQLite 单文件写锁；SDK 使用短事务，失败时重试一次。
- **Checkpoint 文件缺失**：数据库记录存在但文件被删时，UI 标记为“文件不可用”，不影响列表加载。

## 测试策略

- **单元测试**：
  - `Run` 创建、`log()` 写入、`finish()` 更新状态。
  - JSONL/CSV adapter 解析。
  - Checkpoint 保存路径和元数据记录。
- **API 测试**：
  - `/api/runs`、`/api/metrics?run_id=...`、`/api/checkpoints` 返回正确。
  - 外部日志目录注册和同步端点。
- **CLI 测试**：
  - `lumina project logs add/sync`、`lumina project runs list`。
- **隔离**：继续使用 `LUMINA_PROJECTS_ROOT` 临时目录，避免污染真实项目。

## 与后续阶段的衔接

- **Phase 3-C（评估）**：选中某个 run 的 checkpoint 后，可以直接跳转到 Evaluate Panel，用项目里的数据集跑推理并算指标。
- **Phase 3-D（可解释性）**：选中 checkpoint 和输入样本后，跳转到 Interpret Panel，展示激活图/attention 等。
