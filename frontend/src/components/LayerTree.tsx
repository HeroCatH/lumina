import { CYBER, sectionTitle } from '../theme'
import { GraphNode } from '../types'

interface LayerTreeProps {
  nodes: GraphNode[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function LayerTree({ nodes, selectedId, onSelect }: LayerTreeProps) {
  return (
    <div
      style={{
        padding: 12,
        overflow: 'auto',
        height: '100%',
        background: CYBER.panel,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <div style={sectionTitle(CYBER.blue)}>Layers</div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {nodes.map((node) => (
          <li
            key={node.id}
            onClick={() => onSelect(node.id)}
            style={{
              padding: '6px 8px',
              cursor: 'pointer',
              background: node.id === selectedId ? `${CYBER.blue}22` : 'transparent',
              borderBottom: `1px solid ${CYBER.border}`,
              color: node.id === selectedId ? CYBER.blue : CYBER.text,
            }}
          >
            <div style={{ fontWeight: 500 }}>{node.display_name}</div>
            <div style={{ fontSize: 12, color: CYBER.muted }}>{node.type}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
