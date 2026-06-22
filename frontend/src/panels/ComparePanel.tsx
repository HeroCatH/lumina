import { useEffect, useMemo, useState } from 'react'
import { fetchEvaluations, fetchEvaluation, fetchMetrics, fetchRuns } from '../api'
import { CYBER, sectionTitle, tdStyle, thStyle } from '../theme'
import { Evaluation, Metric, Run } from '../types'

const COMPARE_COLORS = [CYBER.green, CYBER.blue, CYBER.pink, CYBER.yellow, CYBER.red]

export default function ComparePanel() {
  const [runs, setRuns] = useState<Run[]>([])
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [selectedRunIds, setSelectedRunIds] = useState<Set<string>>(new Set())
  const [selectedEvalIds, setSelectedEvalIds] = useState<Set<string>>(new Set())
  const [runMetrics, setRunMetrics] = useState<Record<string, Metric[]>>({})
  const [evalDetails, setEvalDetails] = useState<Record<string, Evaluation>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchRuns(), fetchEvaluations()])
      .then(([r, e]) => {
        setRuns(r)
        setEvaluations(e)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedRunIds.size === 0) {
      setRunMetrics({})
      return
    }
    setLoading(true)
    setError(null)
    Promise.all(
      Array.from(selectedRunIds).map((runId) => fetchMetrics(runId).then((m) => ({ runId, metrics: m })))
    )
      .then((results) => {
        const map: Record<string, Metric[]> = {}
        results.forEach(({ runId, metrics }) => {
          map[runId] = metrics
        })
        setRunMetrics(map)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedRunIds])

  useEffect(() => {
    if (selectedEvalIds.size === 0) {
      setEvalDetails({})
      return
    }
    setLoading(true)
    setError(null)
    Promise.all(
      Array.from(selectedEvalIds).map((id) => fetchEvaluation(id).then((e) => ({ id, eval: e })))
    )
      .then((results) => {
        const map: Record<string, Evaluation> = {}
        results.forEach(({ id, eval: e }) => {
          map[id] = e
        })
        setEvalDetails(map)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedEvalIds])

  const toggleRun = (id: string) => {
    setSelectedRunIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleEval = (id: string) => {
    setSelectedEvalIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const metricNames = useMemo(() => {
    const names = new Set<string>()
    Object.values(runMetrics).forEach((ms) => ms.forEach((m) => names.add(m.name)))
    return Array.from(names)
  }, [runMetrics])

  return (
    <div
      style={{
        display: 'flex',
        height: '100%',
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
        overflow: 'hidden',
      }}
    >
      <aside
        style={{
          width: 260,
          borderRight: `1px solid ${CYBER.border}`,
          padding: 16,
          background: CYBER.panel,
          overflow: 'auto',
        }}
      >
        <div style={sectionTitle(CYBER.green)}>Compare Runs</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 24 }}>
          {runs.map((run, idx) => (
            <SelectableRow
              key={run.id}
              label={run.name}
              color={COMPARE_COLORS[idx % COMPARE_COLORS.length]}
              selected={selectedRunIds.has(run.id)}
              onClick={() => toggleRun(run.id)}
            />
          ))}
          {runs.length === 0 && <div style={{ color: CYBER.muted, fontSize: 12 }}>No runs available.</div>}
        </div>

        <div style={sectionTitle(CYBER.pink)}>Compare Evaluations</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {evaluations.map((ev, idx) => (
            <SelectableRow
              key={ev.id}
              label={ev.name || ev.id.slice(0, 8)}
              color={COMPARE_COLORS[idx % COMPARE_COLORS.length]}
              selected={selectedEvalIds.has(ev.id)}
              onClick={() => toggleEval(ev.id)}
            />
          ))}
          {evaluations.length === 0 && (
            <div style={{ color: CYBER.muted, fontSize: 12 }}>No evaluations available.</div>
          )}
        </div>
      </aside>

      <main style={{ flex: 1, padding: 24, overflow: 'auto' }}>
        {loading && <div style={{ color: CYBER.blue }}>&gt; LOADING comparison data...</div>}
        {error && <div style={{ color: CYBER.red }}>[ERR] {error}</div>}

        {selectedRunIds.size > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={sectionTitle(CYBER.blue)}>Run Metric Curves</div>
            {metricNames.map((name) => (
              <div key={name} style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: CYBER.blue, marginBottom: 6 }}>{name}</div>
                <ComparisonCurve
                  metricName={name}
                  runs={runs.filter((r) => selectedRunIds.has(r.id))}
                  runMetrics={runMetrics}
                />
              </div>
            ))}
            {metricNames.length === 0 && (
              <div style={{ color: CYBER.muted }}>No metrics found for selected runs.</div>
            )}
          </div>
        )}

        {selectedEvalIds.size > 0 && (
          <div>
            <div style={sectionTitle(CYBER.pink)}>Evaluation Metrics</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24, border: `1px solid ${CYBER.border}` }}>
              <thead style={{ background: CYBER.panel2 }}>
                <tr>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>Evaluation</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>Type</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>Accuracy</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>Precision</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>Recall</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>F1</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>MAE</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>RMSE</th>
                  <th style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>R²</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(selectedEvalIds).map((id) => {
                  const ev = evalDetails[id]
                  if (!ev) return null
                  const metrics = JSON.parse(ev.metrics)
                  const isCls = 'accuracy' in metrics
                  return (
                    <tr key={id} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {ev.name || ev.id.slice(0, 8)}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>{ev.task_type}</td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {isCls ? metrics.accuracy.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {isCls ? metrics.precision.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {isCls ? metrics.recall.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {isCls ? metrics.f1.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {!isCls ? metrics.mae.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {!isCls ? metrics.rmse.toFixed(4) : '—'}
                      </td>
                      <td style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {!isCls ? (metrics.r2 === null ? 'N/A' : metrics.r2.toFixed(4)) : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {selectedRunIds.size === 0 && selectedEvalIds.size === 0 && !loading && (
          <div style={{ color: CYBER.muted }}>Select runs or evaluations from the sidebar to compare.</div>
        )}
      </main>
    </div>
  )
}

function SelectableRow({
  label,
  color,
  selected,
  onClick,
}: {
  label: string
  color: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '6px 8px',
        borderRadius: 4,
        border: `1px solid ${selected ? color : CYBER.border}`,
        background: selected ? `${color}22` : CYBER.panel2,
        color: selected ? color : CYBER.text,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        fontSize: 12,
      }}
    >
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: 2,
          background: selected ? color : 'transparent',
          border: `1px solid ${color}`,
        }}
      />
      {label}
    </div>
  )
}

function ComparisonCurve({
  metricName,
  runs,
  runMetrics,
}: {
  metricName: string
  runs: Run[]
  runMetrics: Record<string, Metric[]>
}) {
  const width = 560
  const height = 120
  const pad = 20

  const series = runs
    .map((run) => ({
      run,
      points: (runMetrics[run.id] || [])
        .filter((m) => m.name === metricName)
        .sort((a, b) => a.step - b.step),
    }))
    .filter((s) => s.points.length > 0)

  const allValues = series.flatMap((s) => s.points.map((p) => p.value))
  if (allValues.length === 0) return null
  const min = Math.min(...allValues)
  const max = Math.max(...allValues)
  const range = max - min || 1

  return (
    <svg
      width={width}
      height={height}
      style={{ background: CYBER.panel2, border: `1px solid ${CYBER.border}` }}
    >
      {series.map((s, idx) => {
        const color = COMPARE_COLORS[idx % COMPARE_COLORS.length]
        const points = s.points.map((p, i) => {
          const x = pad + (i / (s.points.length - 1 || 1)) * (width - pad * 2)
          const y = height - pad - ((p.value - min) / range) * (height - pad * 2)
          return `${x},${y}`
        })
        return (
          <g key={s.run.id}>
            <polyline fill="none" stroke={color} strokeWidth={2} points={points.join(' ')} />
            <text x={width - 100} y={pad + idx * 14 + 10} fill={color} fontSize={10}>
              {s.run.name}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
