import {
  ModelGraph,
  ModelStats,
  Run,
  Metric,
  Checkpoint,
  Evaluation,
  Prediction,
  CreateEvaluationBody,
  MetricsJson,
} from './types'

async function apiError(res: Response, fallback: string): Promise<Error> {
  try {
    const body = await res.json()
    const detail = body.detail
    if (typeof detail === 'string') return new Error(detail)
    if (Array.isArray(detail)) return new Error(detail.map((d: any) => d.msg || JSON.stringify(d)).join('; '))
    if (detail) return new Error(JSON.stringify(detail))
    return new Error(fallback)
  } catch {
    return new Error(fallback)
  }
}

function buildUrl(path: string, params?: URLSearchParams): string {
  if (!params || params.toString() === '') return path
  return `${path}?${params.toString()}`
}

export function parseMetrics(metricsJson: string): MetricsJson | null {
  try {
    const parsed = JSON.parse(metricsJson)
    if (parsed && typeof parsed === 'object') {
      return parsed as MetricsJson
    }
  } catch {
    // ignore
  }
  return null
}

export async function fetchGraph(): Promise<ModelGraph> {
  const res = await fetch('/api/graph')
  if (!res.ok) throw await apiError(res, 'Failed to fetch graph')
  return res.json()
}

export async function fetchStats(inputShape?: number[]): Promise<ModelStats> {
  const params = new URLSearchParams()
  if (inputShape) params.append('input_shape', inputShape.join(','))
  const res = await fetch(buildUrl('/api/stats', params))
  if (!res.ok) throw await apiError(res, 'Failed to fetch stats')
  return res.json()
}

export async function fetchRuns(): Promise<Run[]> {
  const res = await fetch('/api/runs')
  if (!res.ok) throw await apiError(res, 'Failed to fetch runs')
  return res.json()
}

export async function fetchMetrics(runId: string, name?: string): Promise<Metric[]> {
  const params = new URLSearchParams({ run_id: runId })
  if (name) params.append('name', name)
  const res = await fetch(`/api/metrics?${params.toString()}`)
  if (!res.ok) throw await apiError(res, 'Failed to fetch metrics')
  return res.json()
}

export async function fetchCheckpoints(runId: string): Promise<Checkpoint[]> {
  const params = new URLSearchParams({ run_id: runId })
  const res = await fetch(`/api/checkpoints?${params.toString()}`)
  if (!res.ok) throw await apiError(res, 'Failed to fetch checkpoints')
  return res.json()
}

export async function syncLogs(runId: string): Promise<{ synced: number }> {
  const params = new URLSearchParams({ run_id: runId })
  const res = await fetch(`/api/projects/current/logs/sync?${params.toString()}`, { method: 'POST' })
  if (!res.ok) throw await apiError(res, 'Failed to sync logs')
  return res.json()
}

export async function fetchEvaluations(runId?: string): Promise<Evaluation[]> {
  const params = new URLSearchParams()
  if (runId) params.append('run_id', runId)
  const res = await fetch(buildUrl('/api/evaluations', params))
  if (!res.ok) throw await apiError(res, 'Failed to fetch evaluations')
  return res.json()
}

export async function fetchEvaluation(
  id: string,
  includePredictions: boolean = false,
): Promise<Evaluation & { predictions?: Prediction[] }> {
  const params = new URLSearchParams()
  if (includePredictions) params.append('include_predictions', 'true')
  const res = await fetch(buildUrl(`/api/evaluations/${id}`, params))
  if (!res.ok) throw await apiError(res, 'Failed to fetch evaluation')
  return res.json()
}

export async function createEvaluation(body: CreateEvaluationBody): Promise<Evaluation> {
  const res = await fetch('/api/evaluations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw await apiError(res, 'Failed to create evaluation')
  return res.json()
}

export async function deleteEvaluation(id: string): Promise<{ deleted: boolean }> {
  const res = await fetch(`/api/evaluations/${id}`, { method: 'DELETE' })
  if (!res.ok) throw await apiError(res, 'Failed to delete evaluation')
  return res.json()
}
