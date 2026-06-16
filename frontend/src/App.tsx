import { useEffect, useState } from 'react'
import { fetchGraph } from './api'
import { ModelGraph } from './types'

export default function App() {
  const [graph, setGraph] = useState<ModelGraph | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchGraph()
      .then(setGraph)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>
  if (!graph) return <div style={{ padding: 20 }}>Loading...</div>

  return (
    <div style={{ padding: 20 }}>
      <h1>ModelView</h1>
      <p>Loaded {graph.nodes.length} nodes and {graph.edges.length} edges.</p>
    </div>
  )
}
