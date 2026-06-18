import {
  ModelGraph,
  ModelStats,
  Run,
  Metric,
  Checkpoint,
  Evaluation,
  Prediction,
  CreateEvaluationBody,
} from './types'

async function apiError(res: Response, fallback: string): Promise<Error> {
  try {
    const body = await res.json()
    return new Error(body.detail || fallback)
  } catch {
    return new Error(fallback)
  }
}

export async function fetchGraph(): Promise<ModelGraph> {
  const res = await fetch('/api/graph')
  if (!res.ok) throw new Error('Failed to fetch graph')
  return res.json()
}

export async function fetchStats(inputShape?: number[]): Promise<ModelStats> {
  const query = inputShape ? `?input_shape=${inputShape.join(',')}` : ''
  const res = await fetch(`/api/stats${query}`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}

export async function fetchRuns(): Promise<Run[]> {
  const res = await fetch('/api/runs')
  if (!res.ok) throw new Error('Failed to fetch runs')
  return res.json()
}

export async function fetchMetrics(runId: string, name?: string): Promise<Metric[]> {
  const params = new URLSearchParams({ run_id: runId })
  if (name) params.append('name', name)
  const res = await fetch(`/api/metrics?${params.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

export async function fetchCheckpoints(runId: string): Promise<Checkpoint[]> {
  const res = await fetch(`/api/checkpoints?run_id=${runId}`)
  if (!res.ok) throw new Error('Failed to fetch checkpoints')
  return res.json()
}

export async function syncLogs(runId: string): Promise<{ synced: number }> {
  const res = await fetch(`/api/projects/current/logs/sync?run_id=${runId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to sync logs')
  return res.json()
}

export async function fetchEvaluations(runId?: string): Promise<Evaluation[]> {
  const params = new URLSearchParams()
  if (runId) params.append('run_id', runId)
  const query = params.toString()
  const res = await fetch(`/api/evaluations${query ? `?${query}` : ''}`)
  if (!res.ok) throw new Error('Failed to fetch evaluations')
  return res.json()
}

export async function fetchEvaluation(
  id: string,
  includePredictions: boolean = false,
): Promise<Evaluation & { predictions?: Prediction[] }> {
  const query = includePredictions ? '?include_predictions=true' : ''
  const res = await fetch(`/api/evaluations/${id}${query}`)
  if (!res.ok) throw new Error('Failed to fetch evaluation')
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
