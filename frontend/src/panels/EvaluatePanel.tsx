import { useEffect, useMemo, useState } from 'react'
import { fetchDatasets } from '../hooks/useApi'
import {
  createEvaluation,
  createDeployment,
  deleteDeployment,
  deleteEvaluation,
  fetchDeployments,
  fetchEvaluations,
  fetchEvaluation,
  fetchRuns,
  parseMetrics,
} from '../api'
import EmptyState from '../components/EmptyState'
import { CYBER, inputStyle, tdStyle, thStyle } from '../theme'
import {
  ClassificationMetrics,
  CreateEvaluationBody,
  DatasetInfo,
  Deployment,
  Evaluation,
  MetricsJson,
  Prediction,
  RegressionMetrics,
  Run,
} from '../types'

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
  const [filterDatasetId, setFilterDatasetId] = useState('')

  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [deployTarget, setDeployTarget] = useState('')
  const [deployConfig, setDeployConfig] = useState('')

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
    fetchEvaluations(selectedRunId, filterDatasetId || undefined)
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
  }, [selectedRunId, filterDatasetId])

  useEffect(() => {
    if (!selectedEvalId) {
      setDetail(null)
      setMetrics(null)
      setDeployments([])
      return
    }
    setError(null)
    setLoading(true)
    Promise.all([fetchEvaluation(selectedEvalId, true), fetchDeployments(undefined, selectedEvalId)])
      .then(([ev, deps]) => {
        setDetail(ev)
        setMetrics(parseMetrics(ev.metrics))
        setDeployments(deps)
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
      const updated = await fetchEvaluations(selectedRunId, filterDatasetId || undefined)
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
        const updated = await fetchEvaluations(selectedRunId, filterDatasetId || undefined)
        setEvaluations(updated)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateDeployment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedEvalId || !deployTarget.trim()) return
    let config: Record<string, any> | null = null
    if (deployConfig.trim()) {
      try {
        config = JSON.parse(deployConfig.trim())
      } catch {
        setError('Deployment config must be valid JSON')
        return
      }
    }
    setLoading(true)
    setError(null)
    try {
      await createDeployment({
        target: deployTarget.trim(),
        evaluation_id: selectedEvalId,
        config,
      })
      setDeployTarget('')
      setDeployConfig('')
      const updated = await fetchDeployments(undefined, selectedEvalId)
      setDeployments(updated)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteDeployment = async (id: string) => {
    if (!confirm('Delete this deployment?')) return
    setLoading(true)
    setError(null)
    try {
      await deleteDeployment(id)
      if (selectedEvalId) {
        const updated = await fetchDeployments(undefined, selectedEvalId)
        setDeployments(updated)
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
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <aside
        style={{
          width: 280,
          borderRight: `1px solid ${CYBER.border}`,
          background: CYBER.panel,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto',
        }}
      >
        <div style={{ padding: 16, borderBottom: `1px solid ${CYBER.border}` }}>
          <div style={{ color: CYBER.green, fontSize: 12, marginBottom: 6, textTransform: 'uppercase' }}>
            Run Target
          </div>
          <select
            value={selectedRunId ?? ''}
            onChange={(e) => setSelectedRunId(e.target.value || null)}
            style={{
              width: '100%',
              background: CYBER.panel2,
              color: CYBER.text,
              border: `1px solid ${CYBER.border}`,
              borderRadius: 4,
              padding: '8px 10px',
              fontFamily: CYBER.font,
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
            <div style={{ marginTop: 8, fontSize: 11, color: CYBER.muted }}>
              {selectedRun.status} • {selectedRun.source}
            </div>
          )}
          {runs.length === 0 && (
            <EmptyState style={{ marginTop: 12 }}>Create a run first.</EmptyState>
          )}
        </div>

        <div style={{ padding: 16, borderBottom: `1px solid ${CYBER.border}` }}>
          <div style={{ color: CYBER.pink, fontSize: 12, marginBottom: 10, textTransform: 'uppercase' }}>
            Filter by Dataset
          </div>
          <select
            value={filterDatasetId}
            onChange={(e) => setFilterDatasetId(e.target.value)}
            style={inputStyle}
          >
            <option value="">all datasets</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ padding: 16, borderBottom: `1px solid ${CYBER.border}` }}>
          <div
            style={{ color: CYBER.blue, fontSize: 12, marginBottom: 10, textTransform: 'uppercase' }}
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
                color: CYBER.green,
                border: `1px solid ${CYBER.green}`,
                borderRadius: 4,
                padding: '8px 12px',
                fontFamily: CYBER.font,
                cursor: 'pointer',
                boxShadow: `0 0 8px ${CYBER.green}33`,
              }}
            >
              CREATE EVAL
            </button>
          </form>
        </div>

        <div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
          <div style={{ color: CYBER.pink, fontSize: 12, marginBottom: 10, textTransform: 'uppercase' }}>
            Evaluations
          </div>
          {evaluations.length === 0 && (
            <EmptyState style={{ padding: 12, fontSize: 12 }}>No evaluations found.</EmptyState>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {evaluations.map((ev) => {
              const primary = primaryMetric(ev)
              const active = ev.id === selectedEvalId
              const dsName = ev.dataset_id ? datasets.find((d) => d.id === ev.dataset_id)?.name : null
              return (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEvalId(ev.id)}
                  style={{
                    padding: 10,
                    borderRadius: 4,
                    border: `1px solid ${active ? CYBER.green : CYBER.border}`,
                    background: active ? `${CYBER.green}11` : CYBER.panel2,
                    cursor: 'pointer',
                    boxShadow: active ? `0 0 12px ${CYBER.green}33` : 'none',
                  }}
                >
                  <div style={{ fontWeight: 'bold', fontSize: 13, color: active ? CYBER.green : CYBER.text }}>
                    {ev.name || ev.id.slice(0, 8)}
                  </div>
                  <div style={{ fontSize: 11, color: CYBER.muted, marginTop: 4 }}>
                    {ev.task_type} • {primary}
                    {dsName ? ` • ds:${dsName}` : ''}
                  </div>
                  <div style={{ fontSize: 10, color: CYBER.muted, marginTop: 4 }}>{fmtDate(ev.created_at)}</div>
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
              color: CYBER.blue,
              fontSize: 14,
              textShadow: `0 0 8px ${CYBER.blue}`,
              marginBottom: 12,
            }}
          >
            &gt; LOADING NEURAL telemetry...
          </div>
        )}
        {error && (
          <div
            style={{
              color: CYBER.red,
              border: `1px solid ${CYBER.red}`,
              padding: 10,
              borderRadius: 4,
              marginBottom: 12,
              background: `${CYBER.red}11`,
            }}
          >
            [ERR] {error}
          </div>
        )}

        {!detail && !loading && (
          <EmptyState>Select or create an evaluation to inspect predictions and metrics.</EmptyState>
        )}

        {detail && metrics && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div
              style={{
                background: CYBER.panel,
                border: `1px solid ${CYBER.border}`,
                borderRadius: 6,
                padding: 16,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: 18, color: CYBER.green, textShadow: `0 0 10px ${CYBER.green}55` }}>
                  {detail.name || `Evaluation ${detail.id.slice(0, 8)}`}
                </div>
                <div style={{ fontSize: 12, color: CYBER.muted, marginTop: 6 }}>
                  {detail.task_type} • {fmtDate(detail.created_at)} • {detail.predictions_path}
                  {detail.dataset_id
                    ? ` • dataset: ${datasets.find((d) => d.id === detail.dataset_id)?.name || detail.dataset_id.slice(0, 8)}`
                    : ''}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: CYBER.muted }}>PRIMARY METRIC</div>
                  <div style={{ fontSize: 20, color: CYBER.blue, textShadow: `0 0 10px ${CYBER.blue}55` }}>
                    {isClassification(metrics)
                      ? metrics.accuracy.toFixed(4)
                      : (metrics as RegressionMetrics).mae.toFixed(4)}
                  </div>
                  <div style={{ fontSize: 10, color: CYBER.muted }}>
                    {isClassification(metrics) ? 'accuracy' : 'mae'}
                  </div>
                </div>
                <button
                  onClick={handleDelete}
                  style={{
                    background: 'transparent',
                    color: CYBER.red,
                    border: `1px solid ${CYBER.red}`,
                    borderRadius: 4,
                    padding: '8px 14px',
                    fontFamily: CYBER.font,
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

            <DeploymentSection
              deployments={deployments}
              target={deployTarget}
              config={deployConfig}
              onTargetChange={setDeployTarget}
              onConfigChange={setDeployConfig}
              onCreate={handleCreateDeployment}
              onDelete={handleDeleteDeployment}
            />
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
        <MetricCard label="ACCURACY" value={metrics.accuracy} color={CYBER.green} />
        <MetricCard label="PRECISION" value={metrics.precision} color={CYBER.blue} />
        <MetricCard label="RECALL" value={metrics.recall} color={CYBER.pink} />
        <MetricCard label="F1" value={metrics.f1} color={CYBER.green} />
      </div>

      <div
        style={{
          background: CYBER.panel,
          border: `1px solid ${CYBER.border}`,
          borderRadius: 6,
          padding: 16,
        }}
      >
        <div style={{ color: CYBER.pink, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
          Confusion Matrix
        </div>
        <ConfusionMatrix matrix={metrics.confusion_matrix} />
      </div>

      <div
        style={{
          background: CYBER.panel,
          border: `1px solid ${CYBER.border}`,
          borderRadius: 6,
          padding: 16,
        }}
      >
        <div style={{ color: CYBER.blue, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
          Per-Class Metrics
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${CYBER.border}` }}>
              <th style={thStyle}>Class</th>
              <th style={thStyle}>Precision</th>
              <th style={thStyle}>Recall</th>
              <th style={thStyle}>F1</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.per_class).map(([cls, vals]) => (
              <tr key={cls} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
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
        <MetricCard label="MAE" value={metrics.mae} color={CYBER.green} />
        <MetricCard label="RMSE" value={metrics.rmse} color={CYBER.blue} />
        <MetricCard label="R²" value={metrics.r2 === null ? 'N/A' : metrics.r2} color={CYBER.pink} />
      </div>

      {numeric.length > 0 && (
        <div
          style={{
            background: CYBER.panel,
            border: `1px solid ${CYBER.border}`,
            borderRadius: 6,
            padding: 16,
          }}
        >
          <div style={{ color: CYBER.blue, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
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
        background: CYBER.panel,
        border: `1px solid ${color}55`,
        borderRadius: 6,
        padding: 14,
        boxShadow: `0 0 12px ${color}22`,
      }}
    >
      <div style={{ fontSize: 10, color: CYBER.muted }}>{label}</div>
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
              color: CYBER.blue,
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
              color: CYBER.blue,
            }}
          >
            {r}
          </div>
          {allLabels.map((c) => {
            const val = matrix[r]?.[c] || 0
            const isDiag = r === c
            const alpha = Math.min(1, (val / maxVal) * 0.85 + (val > 0 ? 0.15 : 0))
            const glowColor = isDiag ? CYBER.green : CYBER.pink
            return (
              <div
                key={`${r}-${c}`}
                style={{
                  width: cellSize,
                  height: cellSize,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `1px solid ${CYBER.border}`,
                  backgroundColor: val > 0 ? `${glowColor}${Math.round(alpha * 255).toString(16).padStart(2, '0')}` : CYBER.panel2,
                  color: '#fff',
                  fontSize: 12,
                  textShadow: val > 0 ? `0 0 6px ${glowColor}` : 'none',
                  boxShadow: val > 0 && isDiag ? `inset 0 0 10px ${CYBER.green}44` : 'none',
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
    <svg width={width} height={height} style={{ background: CYBER.panel2, border: `1px solid ${CYBER.border}` }}>
      <line
        x1={pad}
        y1={height - pad}
        x2={width - pad}
        y2={pad}
        stroke={CYBER.muted}
        strokeDasharray="4 4"
      />
      {data.map((d, i) => (
        <circle
          key={i}
          cx={scale(d.trueV)}
          cy={height - scale(d.predV)}
          r={3}
          fill={CYBER.blue}
          opacity={0.8}
        />
      ))}
      <text x={pad} y={height - 6} fill={CYBER.muted} fontSize={10}>
        {min.toFixed(2)}
      </text>
      <text x={width - pad - 40} y={pad - 6} fill={CYBER.muted} fontSize={10}>
        {max.toFixed(2)}
      </text>
    </svg>
  )
}

function PredictionsTable({ predictions }: { predictions: Prediction[] }) {
  return (
    <div
      style={{
        background: CYBER.panel,
        border: `1px solid ${CYBER.border}`,
        borderRadius: 6,
        padding: 16,
      }}
    >
      <div style={{ color: CYBER.green, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
        Predictions ({predictions.length})
      </div>
      <div style={{ maxHeight: 320, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead style={{ position: 'sticky', top: 0, background: CYBER.panel }}>
            <tr style={{ borderBottom: `1px solid ${CYBER.border}` }}>
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
                    borderBottom: `1px solid ${CYBER.border}`,
                    background: correct ? `${CYBER.green}0d` : `${CYBER.pink}0d`,
                  }}
                >
                  <td style={tdStyle}>{p.sample_id}</td>
                  <td style={tdStyle}>{p.true_value}</td>
                  <td style={tdStyle}>{p.pred_value}</td>
                  <td style={tdStyle}>
                    {p.confidence === null ? '—' : p.confidence.toFixed(4)}
                  </td>
                  <td style={{ ...tdStyle, color: correct ? CYBER.green : CYBER.pink }}>
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

function DeploymentSection({
  deployments,
  target,
  config,
  onTargetChange,
  onConfigChange,
  onCreate,
  onDelete,
}: {
  deployments: Deployment[]
  target: string
  config: string
  onTargetChange: (v: string) => void
  onConfigChange: (v: string) => void
  onCreate: (e: React.FormEvent) => void
  onDelete: (id: string) => void
}) {
  return (
    <div
      style={{
        background: CYBER.panel,
        border: `1px solid ${CYBER.border}`,
        borderRadius: 6,
        padding: 16,
      }}
    >
      <div style={{ color: CYBER.pink, fontSize: 12, marginBottom: 12, textTransform: 'uppercase' }}>
        Deployments
      </div>
      <form onSubmit={onCreate} style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          placeholder="target (e.g. local, cloud)"
          value={target}
          onChange={(e) => onTargetChange(e.target.value)}
          required
          style={{ ...inputStyle, flex: 1, minWidth: 180 }}
        />
        <input
          placeholder='config JSON (optional)'
          value={config}
          onChange={(e) => onConfigChange(e.target.value)}
          style={{ ...inputStyle, flex: 2, minWidth: 240 }}
        />
        <button
          type="submit"
          style={{
            background: 'transparent',
            color: CYBER.pink,
            border: `1px solid ${CYBER.pink}`,
            borderRadius: 4,
            padding: '8px 14px',
            fontFamily: CYBER.font,
            cursor: 'pointer',
            boxShadow: `0 0 8px ${CYBER.pink}33`,
          }}
        >
          DEPLOY
        </button>
      </form>
      {deployments.length === 0 ? (
        <EmptyState style={{ padding: 12, fontSize: 12 }}>No deployments yet.</EmptyState>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${CYBER.border}` }}>
              <th style={thStyle}>Target</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Config</th>
              <th style={thStyle}>Created</th>
              <th style={thStyle} />
            </tr>
          </thead>
          <tbody>
            {deployments.map((d) => (
              <tr key={d.id} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
                <td style={tdStyle}>{d.target}</td>
                <td style={tdStyle}>{d.status}</td>
                <td style={tdStyle}>{d.config ? d.config : '—'}</td>
                <td style={tdStyle}>{fmtDate(d.created_at)}</td>
                <td style={tdStyle}>
                  <button
                    onClick={() => onDelete(d.id)}
                    style={{
                      background: 'transparent',
                      color: CYBER.red,
                      border: `1px solid ${CYBER.red}`,
                      borderRadius: 4,
                      padding: '4px 10px',
                      fontFamily: CYBER.font,
                      cursor: 'pointer',
                    }}
                  >
                    DELETE
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function primaryMetric(ev: Evaluation): string {
  const m = parseMetrics(ev.metrics)
  if (!m) return '—'
  if (isClassification(m)) return `acc ${m.accuracy.toFixed(4)}`
  return `mae ${m.mae.toFixed(4)}`
}


