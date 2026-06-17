import { useEffect, useState } from 'react'
import { fetchGraph, fetchStats } from '../api'
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

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>
  if (!graph) return <div style={{ padding: 20 }}>Loading...</div>

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
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: 280, borderRight: '1px solid #e0e0e0' }}>
        <LayerTree nodes={graph.nodes} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {stats && (
          <div style={{ padding: 12, borderBottom: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <span><strong>Params:</strong> {stats.params.total_params.toLocaleString()}</span>
              <span><strong>FLOPs:</strong> {stats.flops.total_flops.toLocaleString()}</span>
              <span><strong>MACs:</strong> {stats.flops.total_macs.toLocaleString()}</span>
              <span><strong>Memory:</strong> {stats.memory.param_megabytes.toFixed(2)} MB</span>
              {stats.shapes && (
                <span><strong>Output Shape:</strong> [{stats.shapes.output_shape.join(', ')}]</span>
              )}
            </div>
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={shapeText}
                onChange={(e) => setShapeText(e.target.value)}
                placeholder="1,3,32,32"
                style={{ padding: '4px 8px' }}
              />
              <button onClick={handleAnalyzeShape} style={{ padding: '4px 12px' }}>
                Analyze shape
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
        <div style={{ maxHeight: '40%', borderTop: '1px solid #e0e0e0', overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead style={{ position: 'sticky', top: 0, background: '#fafafa' }}>
              <tr>
                <th style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Node</th>
                <th style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Type</th>
                <th style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Params</th>
                <th style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #e0e0e0' }}>FLOPs</th>
                <th style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Memory</th>
                <th style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Input Shape</th>
                <th style={{ textAlign: 'left', padding: 8, borderBottom: '1px solid #e0e0e0' }}>Output Shape</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelectedId(row.id)}
                  style={{
                    background: selectedId === row.id ? '#e3f2fd' : 'transparent',
                    cursor: 'pointer',
                  }}
                >
                  <td style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>{row.id}</td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>{row.type}</td>
                  <td style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                    {String(row.params)}
                  </td>
                  <td style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                    {String(row.flops)}
                  </td>
                  <td style={{ textAlign: 'right', padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                    {String(row.memory)}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                    {row.inputShape ? `[${row.inputShape.join(', ')}]` : '-'}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                    {row.outputShape ? `[${row.outputShape.join(', ')}]` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div style={{ width: 320, borderLeft: '1px solid #e0e0e0' }}>
        <DetailPanel node={selectedNode} stats={stats} />
      </div>
    </div>
  )
}
