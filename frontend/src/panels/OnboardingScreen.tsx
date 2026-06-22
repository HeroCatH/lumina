import { useEffect, useState } from 'react'
import { createProject, fetchProjects, openProject } from '../api'
import { CYBER, inputStyle, sectionTitle } from '../theme'
import { ProjectInfo } from '../types'

export default function OnboardingScreen({ onProjectLoaded }: { onProjectLoaded: () => void }) {
  const [projects, setProjects] = useState<ProjectInfo[]>([])
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]))
  }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setLoading(true)
    setError(null)
    try {
      await createProject(newName.trim())
      setNewName('')
      onProjectLoaded()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleOpen = async (name: string) => {
    setLoading(true)
    setError(null)
    try {
      await openProject(name)
      onProjectLoaded()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <div
        style={{
          width: 520,
          background: CYBER.panel,
          border: `1px solid ${CYBER.border}`,
          borderRadius: 8,
          padding: 32,
          boxShadow: `0 0 24px ${CYBER.green}22`,
        }}
      >
        <div
          style={{
            fontSize: 28,
            color: CYBER.green,
            textShadow: `0 0 16px ${CYBER.green}66`,
            marginBottom: 8,
            textTransform: 'uppercase',
          }}
        >
          LUMINA
        </div>
        <div style={{ color: CYBER.muted, marginBottom: 24 }}>No project loaded. Initialize a workspace to begin.</div>

        <div style={sectionTitle(CYBER.blue)}>Create New Project</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          <input
            placeholder="project name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            style={{ ...inputStyle, flex: 1 }}
          />
          <button
            onClick={handleCreate}
            disabled={loading || !newName.trim()}
            style={{
              background: 'transparent',
              color: CYBER.green,
              border: `1px solid ${CYBER.green}`,
              borderRadius: 4,
              padding: '8px 16px',
              fontFamily: CYBER.font,
              cursor: 'pointer',
              boxShadow: `0 0 8px ${CYBER.green}33`,
              opacity: loading || !newName.trim() ? 0.5 : 1,
            }}
          >
            CREATE
          </button>
        </div>

        {projects.length > 0 && (
          <>
            <div style={sectionTitle(CYBER.pink)}>Open Existing Project</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
              {projects.map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleOpen(p.name)}
                  style={{
                    padding: 10,
                    borderRadius: 4,
                    border: `1px solid ${CYBER.border}`,
                    background: CYBER.panel2,
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ color: CYBER.blue }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: CYBER.muted }}>{p.path}</div>
                </div>
              ))}
            </div>
          </>
        )}

        {error && (
          <div
            style={{
              color: CYBER.red,
              border: `1px solid ${CYBER.red}`,
              padding: 10,
              borderRadius: 4,
              background: `${CYBER.red}11`,
            }}
          >
            [ERR] {error}
          </div>
        )}

        <div style={{ marginTop: 24, fontSize: 11, color: CYBER.muted, lineHeight: 1.6 }}>
          CLI alternative:
          <br />
          <code style={{ color: CYBER.green }}>lumina project create &lt;name&gt;</code>
          <br />
          <code style={{ color: CYBER.green }}>lumina project open &lt;name&gt;</code>
        </div>
      </div>
    </div>
  )
}
