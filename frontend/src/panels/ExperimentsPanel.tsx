import { useEffect, useMemo, useState } from 'react'
import { fetchCheckpoints, fetchMetrics, fetchRuns, syncLogs } from '../api'
import { Checkpoint, Metric, Run } from '../types'

export default function ExperimentsPanel() {
  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [metricName, setMetricName] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId) || null,
    [runs, selectedRunId]
  )

  useEffect(() => {
    fetchRuns()
      .then((rs) => {
        setRuns(rs)
        setSelectedRunId((current) => (current === null && rs.length > 0 ? rs[0].id : current))
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedRunId) return
    setLoading(true)
    setError(null)
    let stale = false
    Promise.all([
      fetchMetrics(selectedRunId, metricName || undefined),
      fetchCheckpoints(selectedRunId),
    ])
      .then(([m, c]) => {
        if (stale) return
        setMetrics(m)
        setCheckpoints(c)
      })
      .catch((err) => {
        if (stale) return
        setError(err.message)
      })
      .finally(() => {
        if (!stale) setLoading(false)
      })
    return () => {
      stale = true
    }
  }, [selectedRunId, metricName])

  const metricNames = useMemo(
    () => Array.from(new Set(metrics.map((m) => m.name))),
    [metrics]
  )

  const handleSync = async () => {
    if (!selectedRunId) return
    const runId = selectedRunId
    const filter = metricName || undefined
    const isStale = () => runId !== selectedRunId || filter !== (metricName || undefined)
    setLoading(true)
    setError(null)
    try {
      await syncLogs(runId)
      const [updatedMetrics, updatedCheckpoints] = await Promise.all([
        fetchMetrics(runId, filter),
        fetchCheckpoints(runId),
      ])
      if (!isStale()) {
        setMetrics(updatedMetrics)
        setCheckpoints(updatedCheckpoints)
      }
    } catch (err: any) {
      if (!isStale()) {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 240, borderRight: '1px solid #e0e0e0', padding: 12, overflow: 'auto' }}>
        <h3>Runs</h3>
        {runs.map((run) => (
          <div
            key={run.id}
            onClick={() => setSelectedRunId(run.id)}
            style={{
              padding: 8,
              marginBottom: 6,
              borderRadius: 4,
              cursor: 'pointer',
              background: run.id === selectedRunId ? '#dbeafe' : '#f3f4f6',
            }}
          >
            <div style={{ fontWeight: 'bold', fontSize: 13 }}>{run.name}</div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>
              {run.status} • {run.source}
            </div>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={handleSync}>Sync logs</button>
          <select value={metricName} onChange={(e) => setMetricName(e.target.value)}>
            <option value="">All metrics</option>
            {metricNames.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          {selectedRun && <span style={{ fontSize: 12, color: '#6b7280' }}>{selectedRun.name}</span>}
        </div>
        {loading && <div style={{ fontSize: 12, color: '#6b7280' }}>Loading...</div>}
        {error && <div style={{ fontSize: 12, color: '#ef4444' }}>{error}</div>}
        <MetricCurve metrics={metrics} />
        <CheckpointList checkpoints={checkpoints} />
      </div>
    </div>
  )
}

function MetricCurve({ metrics }: { metrics: Metric[] }) {
  const byName = useMemo(() => {
    const grouped: Record<string, Metric[]> = {}
    metrics.forEach((m) => {
      if (!grouped[m.name]) grouped[m.name] = []
      grouped[m.name].push(m)
    })
    return grouped
  }, [metrics])

  return (
    <div style={{ flex: 1, border: '1px solid #e0e0e0', borderRadius: 6, padding: 12 }}>
      <h4 style={{ margin: '0 0 12px' }}>Metrics</h4>
      {Object.entries(byName).map(([name, values]) => (
        <div key={name} style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 'bold', marginBottom: 4 }}>{name}</div>
          <SimpleLine data={values} />
        </div>
      ))}
    </div>
  )
}

function SimpleLine({ data }: { data: Metric[] }) {
  if (data.length === 0) return null
  const sorted = [...data].sort((a, b) => a.step - b.step)
  const values = sorted.map((d) => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 400
  const height = 80
  const points = sorted.map((d, i) => {
    const x = (i / (sorted.length - 1 || 1)) * width
    const y = height - ((d.value - min) / range) * height
    return `${x},${y}`
  })

  return (
    <svg width={width} height={height} style={{ background: '#f9fafb' }}>
      <polyline fill="none" stroke="#3b82f6" strokeWidth={2} points={points.join(' ')} />
    </svg>
  )
}

function CheckpointList({ checkpoints }: { checkpoints: Checkpoint[] }) {
  return (
    <div style={{ height: 160, border: '1px solid #e0e0e0', borderRadius: 6, padding: 12, overflow: 'auto' }}>
      <h4 style={{ margin: '0 0 12px' }}>Checkpoints</h4>
      <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '1px solid #e0e0e0' }}>
            <th>Step</th>
            <th>Path</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {checkpoints.map((ckpt) => (
            <tr key={ckpt.id}>
              <td>{ckpt.step}</td>
              <td>{ckpt.path}</td>
              <td>
                <a href={`/api/checkpoints/${ckpt.id}/download`} download>
                  Download
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
