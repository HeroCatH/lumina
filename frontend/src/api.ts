import { ModelGraph, ModelStats } from './types'

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
