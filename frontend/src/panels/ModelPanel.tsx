import { useEffect, useState } from 'react'
import { fetchGraph, fetchStats } from '../api'
import { CYBER, inputStyle, tdStyle, thStyle } from '../theme'
import { ModelGraph, ModelStats } from '../types'
import LayerTree from '../components/LayerTree'
import NodeGraph from '../components/NodeGraph'
import DetailPanel from '../components/DetailPanel'

export default function ModelPanel() {
  const [graph, setGraph] = useState<ModelGraph | null>(null)
  const [stats, setStats] = useState<ModelStats | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [shapeText, setShapeText] = useState<string>('1,3,32,32')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchGraph()
      .then((g) => setGraph(g))
      .catch((e) => setError(e.message))
    fetchStats()
      .then((s) => setStats(s))
      .catch((e) => setError(e.message))
  }, [])

  const handleAnalyzeShape = () => {
    const inputShape = shapeText
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s !== '')
      .map((s) => Number(s))
    if (inputShape.some((n) => Number.isNaN(n))) {
      setError('Invalid input shape')
      return
    }
    setError(null)
    fetchStats(inputShape)
      .then((s) => setStats(s))
      .catch((e) => setError(e.message))
  }

  if (error) return <div style={{ padding: 20, background: CYBER.bg, color: CYBER.red }}>[ERR] {error}</div>
  if (!graph) return <div style={{ padding: 20, background: CYBER.bg, color: CYBER.text }}>Loading...</div>

  const selectedNode = graph.nodes.find((n) => n.id === selectedId) || null

  const rows = graph.nodes.map((node) => ({
    id: node.id,
    type: node.type,
    params: stats?.params.per_node[node.id] ?? 0,
    flops: stats?.flops.per_node[node.id] ?? 0,
    memory: stats?.memory.per_node[node.id]?.param_bytes ?? 0,
    inputShape: stats?.shapes?.per_node[node.id]?.input_shape,
    outputShape: stats?.shapes?.per_node[node.id]?.output_shape,
  }))

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <div style={{ width: 280, borderRight: `1px solid ${CYBER.border}`, background: CYBER.panel }}>
        <LayerTree nodes={graph.nodes} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {stats && (
          <div style={{ padding: 12, borderBottom: `1px solid ${CYBER.border}`, background: CYBER.panel }}>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
              {[
                { label: 'PARAMS', value: stats.params.total_params.toLocaleString(), color: CYBER.green },
                { label: 'FLOPs', value: stats.flops.total_flops.toLocaleString(), color: CYBER.blue },
                { label: 'MACs', value: stats.flops.total_macs.toLocaleString(), color: CYBER.pink },
                { label: 'MEMORY', value: `${stats.memory.param_megabytes.toFixed(2)} MB`, color: CYBER.yellow },
              ].map((item) => (
                <span key={item.label} style={{ color: item.color }}>
                  {item.label}: {item.value}
                </span>
              ))}
              {stats.shapes && (
                <span style={{ color: CYBER.muted }}>OUT: [{stats.shapes.output_shape.join(', ')}]</span>
              )}
            </div>
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={shapeText}
                onChange={(e) => setShapeText(e.target.value)}
                placeholder="1,3,32,32"
                style={{ ...inputStyle, width: 'auto' }}
              />
              <button
                onClick={handleAnalyzeShape}
                style={{
                  background: 'transparent',
                  color: CYBER.blue,
                  border: `1px solid ${CYBER.blue}`,
                  borderRadius: 4,
                  padding: '6px 12px',
                  fontFamily: CYBER.font,
                  cursor: 'pointer',
                  boxShadow: `0 0 8px ${CYBER.blue}33`,
                }}
              >
                ANALYZE SHAPE
              </button>
            </div>
          </div>
        )}
        <div style={{ flex: 1, minHeight: 0 }}>
          <NodeGraph
            nodes={graph.nodes}
            edges={graph.edges}
            metadata={graph.metadata}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
        <div style={{ maxHeight: '40%', borderTop: `1px solid ${CYBER.border}`, overflow: 'auto', background: CYBER.panel }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead style={{ position: 'sticky', top: 0, background: CYBER.panel2 }}>
              <tr>
                {['Node', 'Type', 'Params', 'FLOPs', 'Memory', 'Input Shape', 'Output Shape'].map((h) => (
                  <th key={h} style={thStyle}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelectedId(row.id)}
                  style={{
                    background: selectedId === row.id ? `${CYBER.blue}22` : 'transparent',
                    cursor: 'pointer',
                    borderBottom: `1px solid ${CYBER.border}`,
                  }}
                >
                  <td style={{ ...tdStyle, color: selectedId === row.id ? CYBER.blue : CYBER.text }}>{row.id}</td>
                  <td style={tdStyle}>{row.type}</td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.params)}</td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.flops)}</td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{String(row.memory)}</td>
                  <td style={tdStyle}>{row.inputShape ? `[${row.inputShape.join(', ')}]` : '-'}</td>
                  <td style={tdStyle}>{row.outputShape ? `[${row.outputShape.join(', ')}]` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div style={{ width: 320, borderLeft: `1px solid ${CYBER.border}`, background: CYBER.panel }}>
        <DetailPanel node={selectedNode} stats={stats} />
      </div>
    </div>
  )
}
