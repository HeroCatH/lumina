import { useEffect, useState } from 'react'
import { fetchCurrentProject } from './hooks/useApi'
import DataPanel from './panels/DataPanel'
import ExperimentsPanel from './panels/ExperimentsPanel'
import ModelPanel from './panels/ModelPanel'

export default function App() {
  const [mode, setMode] = useState<'project' | 'model' | 'experiments' | null>(null)
  const [project, setProject] = useState<{ name: string; path: string } | null>(null)

  useEffect(() => {
    fetchCurrentProject()
      .then((p) => {
        setProject(p)
        setMode('project')
      })
      .catch(() => {
        // No project loaded; assume model-only quick view mode
        setMode('model')
      })
  }, [])

  if (mode === null) return <div style={{ padding: 20 }}>Loading...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ padding: '12px 20px', borderBottom: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 20 }}>Lumina</h1>
          {project && <div style={{ fontSize: 12, color: '#666' }}>{project.name}</div>}
        </div>
        {mode === 'project' && (
          <>
            <button onClick={() => setMode('model')}>Model View</button>
            <button onClick={() => setMode('experiments')}>Experiments</button>
          </>
        )}
        {mode === 'model' && (
          <>
            <button onClick={() => setMode('project')}>Data View</button>
            <button onClick={() => setMode('experiments')}>Experiments</button>
          </>
        )}
        {mode === 'experiments' && (
          <>
            <button onClick={() => setMode('project')}>Data View</button>
            <button onClick={() => setMode('model')}>Model View</button>
          </>
        )}
      </header>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {mode === 'project' ? <DataPanel /> : mode === 'experiments' ? <ExperimentsPanel /> : <ModelPanel />}
      </div>
    </div>
  )
}
