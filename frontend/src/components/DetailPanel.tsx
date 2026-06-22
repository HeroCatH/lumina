import { CYBER, sectionTitle } from '../theme'
import { GraphNode, ModelStats } from '../types'

interface DetailPanelProps {
  node: GraphNode | null
  stats: ModelStats | null
}

export default function DetailPanel({ node, stats }: DetailPanelProps) {
  return (
    <div
      style={{
        padding: 12,
        overflow: 'auto',
        height: '100%',
        background: CYBER.panel,
        color: CYBER.text,
        fontFamily: CYBER.font,
        borderLeft: `1px solid ${CYBER.border}`,
      }}
    >
      <div style={sectionTitle(CYBER.blue)}>Details</div>
      {node ? (
        <div>
          <p>
            <span style={{ color: CYBER.muted }}>ID:</span> {node.id}
          </p>
          <p>
            <span style={{ color: CYBER.muted }}>Type:</span> {node.type}
          </p>
          <p>
            <span style={{ color: CYBER.muted }}>Params:</span>
          </p>
          <pre
            style={{
              fontSize: 12,
              background: CYBER.panel2,
              padding: 8,
              border: `1px solid ${CYBER.border}`,
              overflow: 'auto',
            }}
          >
            {JSON.stringify(node.params, null, 2)}
          </pre>
        </div>
      ) : (
        <p style={{ color: CYBER.muted }}>Select a layer to see details.</p>
      )}

      <div style={sectionTitle(CYBER.green)}>Stats</div>
      {stats ? (
        <div>
          <p>
            <span style={{ color: CYBER.muted }}>Total params:</span> {stats.params.total_params}
          </p>
          <p>
            <span style={{ color: CYBER.muted }}>Trainable params:</span>{' '}
            {stats.params.trainable_params}
          </p>
        </div>
      ) : (
        <p style={{ color: CYBER.muted }}>Loading stats...</p>
      )}
    </div>
  )
}
