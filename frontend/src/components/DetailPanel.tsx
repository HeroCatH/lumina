import { GraphNode, Stats } from '../types'

interface DetailPanelProps {
  node: GraphNode | null
  stats: Stats | null
}

export default function DetailPanel({ node, stats }: DetailPanelProps) {
  return (
    <div style={{ padding: 12, overflow: 'auto', height: '100%' }}>
      <h3>Details</h3>
      {node ? (
        <div>
          <p><strong>ID:</strong> {node.id}</p>
          <p><strong>Type:</strong> {node.type}</p>
          <p><strong>Params:</strong></p>
          <pre style={{ fontSize: 12, background: '#f5f5f5', padding: 8 }}>
            {JSON.stringify(node.params, null, 2)}
          </pre>
        </div>
      ) : (
        <p>Select a layer to see details.</p>
      )}

      <h3>Stats</h3>
      {stats ? (
        <div>
          <p><strong>Total params:</strong> {stats.total_params}</p>
          <p><strong>Trainable params:</strong> {stats.trainable_params}</p>
        </div>
      ) : (
        <p>Loading stats...</p>
      )}
    </div>
  )
}
