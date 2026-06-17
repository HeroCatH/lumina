import { DatasetInfo, DatasetPreview } from '../types'

export async function fetchCurrentProject(): Promise<{ name: string; path: string }> {
  const res = await fetch('/api/projects/current')
  if (res.status === 404) throw new Error('No project loaded')
  if (!res.ok) throw new Error('Failed to fetch current project')
  return res.json()
}

export async function fetchDatasets(): Promise<DatasetInfo[]> {
  const res = await fetch('/api/datasets')
  if (!res.ok) throw new Error('Failed to fetch datasets')
  return res.json()
}

export async function fetchDatasetPreview(name: string, n: number = 50): Promise<DatasetPreview> {
  const res = await fetch(`/api/datasets/${name}/preview?n=${n}`)
  if (!res.ok) throw new Error(`Failed to fetch dataset ${name}`)
  return res.json()
}
