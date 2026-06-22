import { useCallback, useEffect, useState } from 'react'
import { fetchCurrentProject } from './hooks/useApi'
import { CYBER, neonShadow } from './theme'
import DataPanel from './panels/DataPanel'
import EvaluatePanel from './panels/EvaluatePanel'
import ExperimentsPanel from './panels/ExperimentsPanel'
import ModelPanel from './panels/ModelPanel'
import OnboardingScreen from './panels/OnboardingScreen'

type Mode = 'project' | 'model' | 'experiments' | 'evaluations'

export default function App() {
  const [mode, setMode] = useState<Mode | null>(null)
  const [project, setProject] = useState<{ name: string; path: string } | null>(null)
  const [loading, setLoading] = useState(true)

  const loadProject = useCallback(() => {
    setLoading(true)
    fetchCurrentProject()
      .then((p) => {
        setProject(p)
        setMode((current) => current ?? 'project')
      })
      .catch((err) => {
        if (err.message !== 'No project loaded') {
          console.error('Unexpected error fetching project:', err)
        }
        setProject(null)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadProject()
  }, [loadProject])

  if (loading) {
    return (
      <div style={{ padding: 20, background: CYBER.bg, color: CYBER.text, fontFamily: CYBER.font }}>
        &gt; INITIALIZING...
      </div>
    )
  }

  if (!project) {
    return <OnboardingScreen onProjectLoaded={loadProject} />
  }

  if (mode === null) return <div style={{ padding: 20, background: CYBER.bg, color: CYBER.text }}>Loading...</div>

  const buttons: { label: string; target: Mode }[] =
    mode === 'project'
      ? [
          { label: 'Model View', target: 'model' },
          { label: 'Experiments', target: 'experiments' },
          { label: 'Evaluations', target: 'evaluations' },
        ]
      : mode === 'model'
      ? [
          { label: 'Data View', target: 'project' },
          { label: 'Experiments', target: 'experiments' },
          { label: 'Evaluations', target: 'evaluations' },
        ]
      : mode === 'experiments'
      ? [
          { label: 'Data View', target: 'project' },
          { label: 'Model View', target: 'model' },
          { label: 'Evaluations', target: 'evaluations' },
        ]
      : [
          { label: 'Data View', target: 'project' },
          { label: 'Model View', target: 'model' },
          { label: 'Experiments', target: 'experiments' },
        ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: CYBER.bg }}>
      <header
        style={{
          padding: '12px 20px',
          borderBottom: `1px solid ${CYBER.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: CYBER.panel,
          color: CYBER.text,
          fontFamily: CYBER.font,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 20, color: CYBER.green, textShadow: neonShadow(CYBER.green) }}>
            LUMINA
          </h1>
          {project && <div style={{ fontSize: 12, color: CYBER.muted }}>{project.name}</div>}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {buttons.map((b) => (
            <NavButton key={b.target} onClick={() => setMode(b.target)}>
              {b.label}
            </NavButton>
          ))}
        </div>
      </header>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {mode === 'project' ? (
          <DataPanel />
        ) : mode === 'experiments' ? (
          <ExperimentsPanel onEvaluate={() => setMode('evaluations')} />
        ) : mode === 'evaluations' ? (
          <EvaluatePanel />
        ) : (
          <ModelPanel />
        )}
      </div>
    </div>
  )
}

function NavButton({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
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
      {children}
    </button>
  )
}
