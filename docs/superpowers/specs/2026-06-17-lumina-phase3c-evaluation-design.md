# Lumina Phase 3-C 设计文档：评估与数据集联动

## 背景与目标

Phase 3-A 已经实现了训练/实验追踪。Phase 3-C 的目标是让 Lumina 能够评估模型在数据集上的表现：计算指标、可视化 confusion matrix、检查错误样本，并与项目里的数据集关联起来。

## 范围

### 在范围内

1. **Predictions CSV 读取**：用户把评估结果写成 CSV，Lumina 读取并计算指标。
2. **自动任务类型推断**：根据 CSV 内容判断是分类还是回归。
3. **指标计算**：
   - 分类：accuracy、precision、recall、F1、confusion matrix。
   - 回归：MAE、RMSE、R²、residual plot 数据。
4. **数据库存储**：evaluations 和 predictions 表。
5. **API/CLI**：创建/列出 evaluation。
6. **浏览器面板**：Evaluate Panel（赛博朋克风格），展示指标、confusion matrix、错误样本。

### 不在范围内

- SDK 上报 predictions（Phase 3-C 以 CSV 为主，SDK 作为后续增强）。
- 自动运行用户评估脚本。
- 分布式评估。

## 总体架构

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐      ┌─────────────────┐
│ Predictions CSV │ ───> │ EvaluationLoader │ ───> │   SQLite    │ ───> │  EvaluatePanel  │
│ (id/true/pred)  │      │ (detect / calc)  │      │ evaluations │      │ (metrics + viz) │
└─────────────────┘      └──────────────────┘      │ predictions │      └─────────────────┘
                                                   └─────────────┘
```

### 关键设计决策

- **CSV 格式约定**：必须包含 `id`、`true`、`pred` 列；分类任务可选 `confidence`。
- **任务类型自动推断**：`true`/`pred` 列离散值多则分类，连续值则回归。
- **与 Dataset 关联**：通过 dataset name 关联项目里的 dataset。
- **与 Run 关联**：每个 evaluation 绑定到一个 run。

## CSV 格式

```csv
id,true,pred,confidence
0,cat,cat,0.95
1,dog,cat,0.62
2,dog,dog,0.88
```

## 数据模型

### `evaluations`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | evaluation 唯一标识 |
| run_id | TEXT FK | 关联 runs |
| dataset_id | TEXT FK | 关联 datasets（存 datasets.id；CLI/API 中用户传 dataset name，内部查找） |
| name | TEXT | 用户可读名称 |
| task_type | TEXT | `classification` / `regression` |
| predictions_path | TEXT | predictions CSV 相对项目根的路径 |
| metrics | TEXT | JSON blob，存储指标 |
| created_at | TIMESTAMP | |

### `predictions`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| evaluation_id | TEXT FK | |
| sample_id | TEXT | 样本 id |
| true_value | TEXT | 真实值 |
| pred_value | TEXT | 预测值 |
| confidence | REAL | 可选 |
| is_correct | INTEGER | 是否正确 |

## 任务类型推断

1. 读取 CSV 的 `true` 和 `pred` 列。
2. 如果两列都是数值且唯一值数量 <= 20，或两列是字符串/布尔值，视为分类。
3. 否则视为回归。
4. 用户可通过 `--task-type` 强制覆盖。

## API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/evaluations | 创建 evaluation |
| GET | /api/evaluations | 列出 evaluations |
| GET | /api/evaluations/{id} | 详情 + metrics |
| GET | /api/evaluations/{id}/predictions | predictions 列表 |

## CLI

```bash
lumina project eval create \
  --project my_project \
  --run run-001 \
  --dataset test.csv \
  --predictions predictions.csv \
  --name "baseline on test"

lumina project eval list --project my_project
```

## UI 设计

Evaluate Panel 采用**赛博朋克风格**：

- 纯黑背景 + 霓虹绿/粉/蓝高亮。
- 等宽字体、大写标签、斜切角卡片。
- 顶部深色头部显示 run/dataset/task 信息 + `+ NEW_EVAL` 按钮。
- 四格指标卡，每张卡片右上角有对应颜色的细线装饰。
- 主内容区左右分栏：分类任务左侧显示 confusion matrix（霓虹色块 + 发光效果），回归任务左侧显示 residual plot；右侧显示错误样本列表（粉色左边框 + 半透明背景）。

## 错误处理

- CSV 缺少必须列时返回清晰错误。
- predictions 文件不存在时返回 400 / CLI 非零退出。
- dataset 不存在时仍保存 evaluation，但 UI 无法展示原始输入。
- 任务类型推断歧义时支持 `--task-type` 强制指定。

## 测试策略

- **单元测试**：任务类型推断、分类指标、回归指标、CSV loader 错误。
- **API 测试**：创建/列出/详情/预测列表。
- **CLI 测试**：eval create/list。
- **隔离**：使用 `LUMINA_PROJECTS_ROOT` 临时目录。

## 与后续阶段的衔接

- **Phase 3-A**：Evaluate Panel 选择 run 时直接读取 Phase 3-A 的 runs 列表。
- **Phase 3-D**：在错误样本上点击可跳转到 Interpret Panel，查看该样本的可解释性分析。
