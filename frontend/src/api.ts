import { ModelGraph, ModelStats, Run, Metric, Checkpoint } from './types'

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
