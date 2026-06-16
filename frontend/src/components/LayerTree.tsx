import { GraphNode } from '../types'

interface LayerTreeProps {
  nodes: GraphNode[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function LayerTree({ nodes, selectedId, onSelect }: LayerTreeProps) {
  return (
    <div style={{ padding: 12, overflow: 'auto', height: '100%' }}>
      <h3>Layers</h3>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {nodes.map((node) => (
          <li
            key={node.id}
            onClick={() => onSelect(node.id)}
            style={{
              padding: '6px 8px',
              cursor: 'pointer',
              background: node.id === selectedId ? '#e6f7ff' : 'transparent',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <div style={{ fontWeight: 500 }}>{node.display_name}</div>
            <div style={{ fontSize: 12, color: '#888' }}>{node.type}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
