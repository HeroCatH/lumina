export interface GraphNode {
  id: string
  type: string
  params: Record<string, any>
  display_name: string
}

export interface GraphEdge {
  source: string
  target: string
}

export interface ModelGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: Record<string, any>
}

export interface Stats {
  total_params: number
  trainable_params: number
  per_node: Record<string, number>
}

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

export interface DatasetInfo {
  id: string
  name: string
  adapter_type: string
  row_count?: number
}

export interface DatasetPreview {
  rows: Record<string, any>[]
  schema: Record<string, string>
  statistics: {
    row_count: number
    column_count: number
    columns: string[]
    column_types: Record<string, string>
    missing_counts: Record<string, number>
    numeric_summary: Record<string, any>[]
  }
}

export interface Run {
  id: string
  project_id?: string
  name: string
  status: string
  source: string
  log_dir?: string
  created_at: string
  updated_at: string
}

export interface Metric {
  id: number
  run_id: string
  step: number
  name: string
  value: number
  timestamp: string
}

export interface Checkpoint {
  id: number
  run_id: string
  step: number
  path: string
  created_at: string
}

export interface ClassificationMetrics {
  accuracy: number
  precision: number
  recall: number
  f1: number
  per_class: Record<string, { precision: number; recall: number; f1: number }>
  confusion_matrix: Record<string, Record<string, number>>
}

export interface RegressionMetrics {
  mae: number
  rmse: number
  r2: number | null
}

export type MetricsJson = ClassificationMetrics | RegressionMetrics

export interface Prediction {
  id: number
  evaluation_id: string
  sample_id: string
  true_value: string
  pred_value: string
  confidence: number | null
  is_correct: number
}

export interface Evaluation {
  id: string
  run_id: string
  dataset_id?: string | null
  name?: string | null
  task_type: 'classification' | 'regression'
  predictions_path: string
  metrics: string
  created_at: string
}

export interface CreateEvaluationBody {
  run_id: string
  predictions_path: string
  dataset_id?: string | null
  name?: string | null
  task_type?: 'classification' | 'regression' | null
}
