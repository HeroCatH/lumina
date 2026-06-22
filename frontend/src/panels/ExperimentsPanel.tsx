import { useEffect, useMemo, useState } from 'react'
import { fetchCheckpoints, fetchMetrics, fetchRuns, syncLogs } from '../api'
import EmptyState from '../components/EmptyState'
import TrainingPanel from '../components/TrainingPanel'
import { cardStyle, CYBER, sectionTitle, tdStyle, thStyle } from '../theme'
import { Checkpoint, Metric, Run } from '../types'

export default function ExperimentsPanel({ onEvaluate }: { onEvaluate?: () => void }) {
  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [metricName, setMetricName] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'metrics' | 'checkpoints' | 'trainings'>('metrics')
  const [inFlight, setInFlight] = useState(0)
  const loading = inFlight > 0
  const [error, setError] = useState<string | null>(null)

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId) || null,
    [runs, selectedRunId]
  )

  useEffect(() => {
    setInFlight((n) => n + 1)
    fetchRuns()
      .then((rs) => {
        setRuns(rs)
        setSelectedRunId((current) => (current === null && rs.length > 0 ? rs[0].id : current))
      })
      .catch((err) => setError(err.message))
      .finally(() => {
        setInFlight((n) => Math.max(0, n - 1))
      })
  }, [])

  useEffect(() => {
    if (!selectedRunId) return
    setError(null)
    setInFlight((n) => n + 1)
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
        setInFlight((n) => Math.max(0, n - 1))
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
    setError(null)
    setInFlight((n) => n + 1)
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
      setInFlight((n) => Math.max(0, n - 1))
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        height: '100%',
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <div
        style={{
          width: 240,
          borderRight: `1px solid ${CYBER.border}`,
          padding: 12,
          overflow: 'auto',
          background: CYBER.panel,
        }}
      >
        <div style={sectionTitle(CYBER.green)}>Runs</div>
        {runs.length === 0 && <EmptyState>No runs found.</EmptyState>}
        {runs.map((run) => (
          <div
            key={run.id}
            onClick={() => setSelectedRunId(run.id)}
            style={{
              padding: 8,
              marginBottom: 6,
              borderRadius: 4,
              cursor: 'pointer',
              background: run.id === selectedRunId ? `${CYBER.green}22` : CYBER.panel2,
              border: `1px solid ${run.id === selectedRunId ? CYBER.green : CYBER.border}`,
              boxShadow: run.id === selectedRunId ? `0 0 10px ${CYBER.green}33` : 'none',
            }}
          >
            <div
              style={{
                fontWeight: 'bold',
                fontSize: 13,
                color: run.id === selectedRunId ? CYBER.green : CYBER.text,
              }}
            >
              {run.name}
            </div>
            <div style={{ fontSize: 11, color: CYBER.muted }}>
              {run.status} • {run.source}
            </div>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            onClick={handleSync}
            style={{
              background: 'transparent',
              color: CYBER.green,
              border: `1px solid ${CYBER.green}`,
              borderRadius: 4,
              padding: '6px 12px',
              fontFamily: CYBER.font,
              cursor: 'pointer',
              boxShadow: `0 0 8px ${CYBER.green}33`,
            }}
          >
            SYNC LOGS
          </button>
          {onEvaluate && (
            <button
              onClick={onEvaluate}
              style={{
                background: 'transparent',
                color: CYBER.pink,
                border: `1px solid ${CYBER.pink}`,
                borderRadius: 4,
                padding: '6px 12px',
                fontFamily: CYBER.font,
                cursor: 'pointer',
                boxShadow: `0 0 8px ${CYBER.pink}33`,
              }}
            >
              EVALUATE
            </button>
          )}
          <select
            value={metricName}
            onChange={(e) => setMetricName(e.target.value)}
            style={{
              background: CYBER.panel2,
              color: CYBER.text,
              border: `1px solid ${CYBER.border}`,
              borderRadius: 4,
              padding: '6px 8px',
              fontFamily: CYBER.font,
            }}
          >
            <option value="">All metrics</option>
            {metricNames.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          {selectedRun && <span style={{ fontSize: 12, color: CYBER.muted }}>{selectedRun.name}</span>}
        </div>
        {loading && <div style={{ fontSize: 12, color: CYBER.blue }}>&gt; LOADING telemetry...</div>}
        {error && <div style={{ fontSize: 12, color: CYBER.red }}>[ERR] {error}</div>}

        <div style={{ display: 'flex', gap: 8, borderBottom: `1px solid ${CYBER.border}`, paddingBottom: 8 }}>
          {[
            { key: 'metrics', label: 'Metrics' },
            { key: 'checkpoints', label: 'Checkpoints' },
            { key: 'trainings', label: 'Trainings' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as typeof activeTab)}
              style={{
                background: activeTab === tab.key ? `${CYBER.blue}22` : 'transparent',
                color: activeTab === tab.key ? CYBER.blue : CYBER.muted,
                border: `1px solid ${activeTab === tab.key ? CYBER.blue : CYBER.border}`,
                borderRadius: 4,
                padding: '6px 12px',
                fontFamily: CYBER.font,
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'metrics' && <MetricCurve metrics={metrics} />}
        {activeTab === 'checkpoints' && <CheckpointList checkpoints={checkpoints} />}
        {activeTab === 'trainings' && selectedRunId && <TrainingPanel runId={selectedRunId} />}
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
    <div style={{ flex: 1, ...cardStyle, padding: 12 }}>
      <div style={sectionTitle(CYBER.blue)}>Metrics</div>
      {Object.entries(byName).map(([name, values]) => (
        <div key={name} style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 'bold', marginBottom: 4, color: CYBER.blue }}>{name}</div>
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
    <svg width={width} height={height} style={{ background: CYBER.panel2, border: `1px solid ${CYBER.border}` }}>
      <polyline fill="none" stroke={CYBER.blue} strokeWidth={2} points={points.join(' ')} />
    </svg>
  )
}

function CheckpointList({ checkpoints }: { checkpoints: Checkpoint[] }) {
  return (
    <div style={{ height: 160, ...cardStyle, padding: 12, overflow: 'auto' }}>
      <div style={sectionTitle(CYBER.pink)}>Checkpoints</div>
      <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: `1px solid ${CYBER.border}` }}>
            <th style={thStyle}>Step</th>
            <th style={thStyle}>Path</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {checkpoints.map((ckpt) => (
            <tr key={ckpt.id} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
              <td style={tdStyle}>{ckpt.step}</td>
              <td style={tdStyle}>{ckpt.path}</td>
              <td style={tdStyle}>
                <a href={`/api/checkpoints/${ckpt.id}/download`} download style={{ color: CYBER.blue }}>
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
