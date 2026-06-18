import { useEffect, useMemo, useState } from 'react'
import { fetchDatasets } from '../hooks/useApi'
import {
  createEvaluation,
  deleteEvaluation,
  fetchEvaluations,
  fetchEvaluation,
  fetchRuns,
  parseMetrics,
} from '../api'
import {
  ClassificationMetrics,
  CreateEvaluationBody,
  DatasetInfo,
  Evaluation,
  MetricsJson,
  Prediction,
  RegressionMetrics,
  Run,
} from '../types'

const C = {
  bg: '#050505',
  panel: '#0a0a0a',
  panel2: '#111111',
  border: '#222222',
  green: '#00ff41',
  pink: '#ff00ff',
  blue: '#00ccff',
  red: '#ff3333',
  text: '#e0e0e0',
  muted: '#888888',
  font: "'JetBrains Mono', 'Fira Code', monospace",
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function isClassification(m: MetricsJson): m is ClassificationMetrics {
  return 'accuracy' in m && 'confusion_matrix' in m
}

export default function EvaluatePanel() {
  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null)
  const [detail, setDetail] = useState<(Evaluation & { predictions?: Prediction[] }) | null>(null)
  const [metrics, setMetrics] = useState<MetricsJson | null>(null)
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [predictionsPath, setPredictionsPath] = useState('')
  const [evalName, setEvalName] = useState('')
  const [taskType, setTaskType] = useState<'auto' | 'classification' | 'regression'>('auto')
  const [datasetId, setDatasetId] = useState('')

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchRuns(), fetchDatasets()])
      .then(([r, d]) => {
        setRuns(r)
        setDatasets(d)
        if (r.length > 0) setSelectedRunId(r[0].id)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedRunId) {
      setEvaluations([])
      return
    }
    setError(null)
    setLoading(true)
    fetchEvaluations(selectedRunId)
      .then((es) => {
        setEvaluations(es)
        if (es.length > 0 && !es.find((e) => e.id === selectedEvalId)) {
          setSelectedEvalId(es[0].id)
        } else if (es.length === 0) {
          setSelectedEvalId(null)
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedRunId])

  useEffect(() => {
    if (!selectedEvalId) {
      setDetail(null)
      setMetrics(null)
      return
    }
    setError(null)
    setLoading(true)
    fetchEvaluation(selectedEvalId, true)
      .then((ev) => {
        setDetail(ev)
        setMetrics(parseMetrics(ev.metrics))
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedEvalId])

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId) || null,
    [runs, selectedRunId]
  )

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRunId || !predictionsPath.trim()) return
    const body: CreateEvaluationBody = {
      run_id: selectedRunId,
      predictions_path: predictionsPath.trim(),
      name: evalName.trim() || undefined,
      task_type: taskType === 'auto' ? undefined : taskType,
      dataset_id: datasetId || null,
    }
    setLoading(true)
    setError(null)
    try {
      const created = await createEvaluation(body)
      setPredictionsPath('')
      setEvalName('')
      setTaskType('auto')
      setDatasetId('')
      const updated = await fetchEvaluations(selectedRunId)
      setEvaluations(updated)
      setSelectedEvalId(created.id)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedEvalId) return
    if (!confirm('Delete this evaluation?')) return
    setLoading(true)
    setError(null)
    try {
      await deleteEvaluation(selectedEvalId)
      setSelectedEvalId(null)
      if (selectedRunId) {
        const updated = await fetchEvaluations(selectedRunId)
        setEvaluations(updated)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        height: '100%',
        background: C.bg,
        color: C.text,
        fontFamily: C.font,
      }}
    >
      <aside
        style={{
          width: 280,
          borderRight: `1px solid ${C.border}`,
          background: C.panel,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto',
        }}
      >
        <div style={{ padding: 16, borderBottom: `1px solid ${C.border}` }}>
          <div style={{ color: C.green, fontSize: 12, marginBottom: 6, textTransform: 'uppercase' }}>
            Run Target
          </div>
          <select
            value={selectedRunId ?? ''}
            onChange={(e) => setSelectedRunId(e.target.value || null)}
            style={{
              width: '100%',
              background: C.panel2,
              color: C.text,
              border: `1px solid ${C.border}`,
              borderRadius: 4,
              padding: '8px 10px',
              fontFamily: C.font,
              outline: 'none',
            }}
          >
            {runs.length === 0 && <option value="">No runs</option>}
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          {selectedRun && (
            <div style={{ marginTop: 8, fontSize: 11, color: C.muted }}>
              {selectedRun.status} • {selectedRun.source}
            </div>
          )}
        </div>

        <div style={{ padding: 16, borderBottom: `1px solid ${C.border}` }}>
          <div
            style={{ color: C.blue, fontSize: 12, marginBottom: 10, textTransform: 'uppercase' }}
          >
            New Evaluation
          </div>
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input
              placeholder="predictions path"
              value={predictionsPath}
              onChange={(e) => setPredictionsPath(e.target.value)}
              required
              style={inputStyle}
            />
            <input
              placeholder="name (optional)"
              value={evalName}
              onChange={(e) => setEvalName(e.target.value)}
              style={inputStyle}
            />
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value as typeof taskType)}
              style={inputStyle}
            >
              <option value="auto">auto</option>
              <option value="classification">classification</option>
              <option value="regression">regression</option>
            </select>
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              style={inputStyle}
            >
              <option value="">no dataset</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!selectedRunId || loading}
              style={{
                background: 'transparent',
                color: C.green,
                border: `1px solid ${C.green}`,
                borderRadius: 4,
                padding: '8px 12px',
                fontFamily: C.font,
                cursor: 'pointer',
                boxShadow: `0 0 8px ${C.green}33`,
              }}
            >
              CREATE EVAL
            </button>
          </form>
        </div>

        <div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
          <div style={{ color: C.pink, fontSize: 12, marginBottom: 10, textTransform: 'uppercase' }}>
            Evaluations
          </div>
          {evaluations.length === 0 && (
            <div style={{ color: C.muted, fontSize: 12 }}>No evaluations found.</div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {evaluations.map((ev) => {
              const primary = primaryMetric(ev)
              const active = ev.id === selectedEvalId
              return (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEvalId(ev.id)}
                  style={{
                    padding: 10,
                    borderRadius: 4,
                    border: `1px solid ${active ? C.green : C.border}`,
                    background: active ? `${C.green}11` : C.panel2,
                    cursor: 'pointer',
                    boxShadow: active ? `0 0 12px ${C.green}33` : 'none',
                  }}
                >
                  <div style={{ fontWeight: 'bold', fontSize: 13, color: active ? C.green : C.text }}>
                    {ev.name || ev.id.slice(0, 8)}
                  </div>
                  <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>
                    {ev.task_type} • {primary}
                  </div>
                  <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>{fmtDate(ev.created_at)}</div>
                </div>
              )
            })}
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, overflow: 'auto', padding: 24 }}>
        {loading && (
          <div
            style={{
              color: C.blue,
              fontSize: 14,
              textShadow: `0 0 8px ${C.blue}`,
              marginBottom: 12,
            }}
          >
            &gt; LOADING NEURAL telemetry...
          </div>
        )}
        {error && (
          <div
            style={{
              color: C.red,
              border: `1px solid ${C.red}`,
              padding: 10,
              borderRadius: 4,
              marginBottom: 12,
              background: `${C.red}11`,
            }}
          >
            [ERR] {error}
          </div>
        )}

        {!detail && !loading && (
          <div style={{ color: C.muted }}>
            Select or create an evaluation to inspect predictions and metrics.
          </div>
        )}

        {detail && metrics && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div
              style={{
                background: C.panel,
                border: `1px solid ${C.border}`,
                borderRadius: 6,
                padding: 16,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: 18, color: C.green, textShadow: `0 0 10px ${C.green}55` }}>
                  {detail.name || `Evaluation ${detail.id.slice(0, 8)}`}
                </div>
                <div style={{ fontSize: 12, color: C.muted, marginTop: 6 }}>
                  {detail.task_type} • {fmtDate(detail.created_at)} • {detail.predictions_path}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: C.muted }}>PRIMARY METRIC</div>
                  <div style={{ fontSize: 20, color: C.blue, textShadow: `0 0 10px ${C.blue}55` }}>
                    {isClassification(metrics)
                      ? metrics.accuracy.toFixed(4)
                      : (metrics as RegressionMetrics).mae.toFixed(4)}
                  </div>
                  <div style={{ fontSize: 10, color: C.muted }}>
                    {isClassification(metrics) ? 'accuracy' : 'mae'}
                  </div>
                </div>
                <button
                  onClick={handleDelete}
                  style={{
                    background: 'transparent',
                    color: C.red,
                    border: `1px solid ${C.red}`,
                    borderRadius: 4,
                    padding: '8px 14px',
                    fontFamily: C.font,
                    cursor: 'pointer',
                  }}
                >
                  DELETE
                </button>
              </div>
            </div>

            {isClassification(metrics) ? (
              <ClassificationDetail metrics={metrics} predictions={detail.predictions || []} />
            ) : (
              <RegressionDetail metrics={metrics as RegressionMetrics} predictions={detail.predictions || []} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function ClassificationDetail({
  metrics,
  predictions,
}: {
  metrics: ClassificationMetrics
  predictions: Prediction[]
}) {
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <MetricCard label="ACCURACY" value={metrics.accuracy} color={C.green} />
        <MetricCard label="PRECISION" value={metrics.precision} color={C.blue} />
        <MetricCard label="RECALL" value={metrics.recall} color={C.pink} />
        <MetricCard label="F1" value={metrics.f1} color={C.green} />
      </div>

      <div
        style={{
          background: C.panel,
          border: `1px solid ${C.border}`,
          borderRadius: 6,
          padding: 16,
        }}
      >
        <div style={{ color: C.pink, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
          Confusion Matrix
        </div>
        <ConfusionMatrix matrix={metrics.confusion_matrix} />
      </div>

      <div
        style={{
          background: C.panel,
          border: `1px solid ${C.border}`,
          borderRadius: 6,
          padding: 16,
        }}
      >
        <div style={{ color: C.blue, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
          Per-Class Metrics
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              <th style={thStyle}>Class</th>
              <th style={thStyle}>Precision</th>
              <th style={thStyle}>Recall</th>
              <th style={thStyle}>F1</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.per_class).map(([cls, vals]) => (
              <tr key={cls} style={{ borderBottom: `1px solid ${C.border}` }}>
                <td style={tdStyle}>{cls}</td>
                <td style={tdStyle}>{vals.precision.toFixed(4)}</td>
                <td style={tdStyle}>{vals.recall.toFixed(4)}</td>
                <td style={tdStyle}>{vals.f1.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <PredictionsTable predictions={predictions} />
    </>
  )
}

function RegressionDetail({
  metrics,
  predictions,
}: {
  metrics: RegressionMetrics
  predictions: Prediction[]
}) {
  const numeric = useMemo(
    () =>
      predictions
        .map((p) => ({ trueV: parseFloat(p.true_value), predV: parseFloat(p.pred_value) }))
        .filter((p) => !isNaN(p.trueV) && !isNaN(p.predV)),
    [predictions]
  )

  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <MetricCard label="MAE" value={metrics.mae} color={C.green} />
        <MetricCard label="RMSE" value={metrics.rmse} color={C.blue} />
        <MetricCard label="R²" value={metrics.r2 === null ? 'N/A' : metrics.r2} color={C.pink} />
      </div>

      {numeric.length > 0 && (
        <div
          style={{
            background: C.panel,
            border: `1px solid ${C.border}`,
            borderRadius: 6,
            padding: 16,
          }}
        >
          <div style={{ color: C.blue, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
            Predictions vs Truth
          </div>
          <RegressionScatter data={numeric} />
        </div>
      )}

      <PredictionsTable predictions={predictions} />
    </>
  )
}

function MetricCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  const display = typeof value === 'number' ? value.toFixed(4) : value
  return (
    <div
      style={{
        background: C.panel,
        border: `1px solid ${color}55`,
        borderRadius: 6,
        padding: 14,
        boxShadow: `0 0 12px ${color}22`,
      }}
    >
      <div style={{ fontSize: 10, color: C.muted }}>{label}</div>
      <div style={{ fontSize: 22, color, textShadow: `0 0 10px ${color}55`, marginTop: 4 }}>{display}</div>
    </div>
  )
}

function ConfusionMatrix({ matrix }: { matrix: ClassificationMetrics['confusion_matrix'] }) {
  const rows = useMemo(() => Object.keys(matrix), [matrix])
  const cols = useMemo(
    () => Array.from(new Set(rows.flatMap((r) => Object.keys(matrix[r] || {})))),
    [matrix, rows]
  )
  const allLabels = useMemo(
    () => Array.from(new Set([...rows, ...cols])).sort(),
    [rows, cols]
  )
  const maxVal = useMemo(
    () =>
      Math.max(
        1,
        ...allLabels.flatMap((r) => allLabels.map((c) => matrix[r]?.[c] || 0))
      ),
    [matrix, allLabels]
  )

  const cellSize = 56

  return (
    <div style={{ overflow: 'auto' }}>
      <div style={{ display: 'flex' }}>
        <div style={{ width: cellSize }} />
        {allLabels.map((c) => (
          <div
            key={c}
            style={{
              width: cellSize,
              textAlign: 'center',
              fontSize: 10,
              color: C.blue,
              paddingBottom: 6,
            }}
          >
            {c}
          </div>
        ))}
      </div>
      {allLabels.map((r) => (
        <div key={r} style={{ display: 'flex' }}>
          <div
            style={{
              width: cellSize,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingRight: 8,
              fontSize: 10,
              color: C.blue,
            }}
          >
            {r}
          </div>
          {allLabels.map((c) => {
            const val = matrix[r]?.[c] || 0
            const isDiag = r === c
            const alpha = Math.min(1, (val / maxVal) * 0.85 + (val > 0 ? 0.15 : 0))
            const glowColor = isDiag ? C.green : C.pink
            return (
              <div
                key={`${r}-${c}`}
                style={{
                  width: cellSize,
                  height: cellSize,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `1px solid ${C.border}`,
                  backgroundColor: val > 0 ? `${glowColor}${Math.round(alpha * 255).toString(16).padStart(2, '0')}` : C.panel2,
                  color: '#fff',
                  fontSize: 12,
                  textShadow: val > 0 ? `0 0 6px ${glowColor}` : 'none',
                  boxShadow: val > 0 && isDiag ? `inset 0 0 10px ${C.green}44` : 'none',
                }}
              >
                {val}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

function RegressionScatter({ data }: { data: { trueV: number; predV: number }[] }) {
  const values = data.flatMap((d) => [d.trueV, d.predV])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 320
  const height = 240
  const pad = 24
  const scale = (v: number) => pad + ((v - min) / range) * (Math.min(width, height) - pad * 2)

  return (
    <svg width={width} height={height} style={{ background: C.panel2, border: `1px solid ${C.border}` }}>
      <line
        x1={pad}
        y1={height - pad}
        x2={width - pad}
        y2={pad}
        stroke={C.muted}
        strokeDasharray="4 4"
      />
      {data.map((d, i) => (
        <circle
          key={i}
          cx={scale(d.trueV)}
          cy={height - scale(d.predV)}
          r={3}
          fill={C.blue}
          opacity={0.8}
        />
      ))}
      <text x={pad} y={height - 6} fill={C.muted} fontSize={10}>
        {min.toFixed(2)}
      </text>
      <text x={width - pad - 40} y={pad - 6} fill={C.muted} fontSize={10}>
        {max.toFixed(2)}
      </text>
    </svg>
  )
}

function PredictionsTable({ predictions }: { predictions: Prediction[] }) {
  return (
    <div
      style={{
        background: C.panel,
        border: `1px solid ${C.border}`,
        borderRadius: 6,
        padding: 16,
      }}
    >
      <div style={{ color: C.green, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
        Predictions ({predictions.length})
      </div>
      <div style={{ maxHeight: 320, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead style={{ position: 'sticky', top: 0, background: C.panel }}>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              <th style={thStyle}>Sample</th>
              <th style={thStyle}>True</th>
              <th style={thStyle}>Predicted</th>
              <th style={thStyle}>Confidence</th>
              <th style={thStyle}>Correct</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((p) => {
              const correct = p.is_correct === 1
              return (
                <tr
                  key={p.id}
                  style={{
                    borderBottom: `1px solid ${C.border}`,
                    background: correct ? `${C.green}0d` : `${C.pink}0d`,
                  }}
                >
                  <td style={tdStyle}>{p.sample_id}</td>
                  <td style={tdStyle}>{p.true_value}</td>
                  <td style={tdStyle}>{p.pred_value}</td>
                  <td style={tdStyle}>
                    {p.confidence === null ? '—' : p.confidence.toFixed(4)}
                  </td>
                  <td style={{ ...tdStyle, color: correct ? C.green : C.pink }}>
                    {correct ? 'YES' : 'NO'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function primaryMetric(ev: Evaluation): string {
  const m = parseMetrics(ev.metrics)
  if (!m) return '—'
  if (isClassification(m)) return `acc ${m.accuracy.toFixed(4)}`
  return `mae ${m.mae.toFixed(4)}`
}

const inputStyle: React.CSSProperties = {
  background: C.panel2,
  color: C.text,
  border: `1px solid ${C.border}`,
  borderRadius: 4,
  padding: '8px 10px',
  fontFamily: C.font,
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
}

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '8px 10px',
  color: C.muted,
  fontWeight: 'normal',
  textTransform: 'uppercase',
  fontSize: 10,
}

const tdStyle: React.CSSProperties = {
  padding: '8px 10px',
}
