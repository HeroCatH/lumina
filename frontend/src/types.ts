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
