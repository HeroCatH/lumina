import { useEffect, useState } from 'react'
import { fetchGraph, fetchStats } from './api'
import { ModelGraph, Stats } from './types'
import LayerTree from './components/LayerTree'
import NodeGraph from './components/NodeGraph'
import DetailPanel from './components/DetailPanel'

export default function App() {
  const [graph, setGraph] = useState<ModelGraph | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchGraph(), fetchStats()])
      .then(([g, s]) => {
        setGraph(g)
        setStats(s)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>
  if (!graph) return <div style={{ padding: 20 }}>Loading...</div>

  const selectedNode = graph.nodes.find((n) => n.id === selectedId) || null

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: 280, borderRight: '1px solid #e0e0e0' }}>
        <LayerTree nodes={graph.nodes} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1 }}>
          <NodeGraph
            nodes={graph.nodes}
            edges={graph.edges}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
      </div>
      <div style={{ width: 320, borderLeft: '1px solid #e0e0e0' }}>
        <DetailPanel node={selectedNode} stats={stats} />
      </div>
    </div>
  )
}
