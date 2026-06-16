import { ModelGraph, Stats } from './types'

export async function fetchGraph(): Promise<ModelGraph> {
  const res = await fetch('/api/graph')
  if (!res.ok) throw new Error('Failed to fetch graph')
  return res.json()
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch('/api/stats')
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}
