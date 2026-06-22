import { useEffect, useState } from 'react'
import { createTraining, deleteTraining, fetchTrainings, startTraining, stopTraining } from '../api'
import EmptyState from './EmptyState'
import { CYBER, inputStyle, tdStyle, thStyle } from '../theme'
import { Training } from '../types'

interface TrainingPanelProps {
  runId: string
}

export default function TrainingPanel({ runId }: TrainingPanelProps) {
  const [trainings, setTrainings] = useState<Training[]>([])
  const [command, setCommand] = useState('')
  const [name, setName] = useState('')
  const [configText, setConfigText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await fetchTrainings(runId)
      setTrainings(data)
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 3000)
    return () => clearInterval(interval)
  }, [runId])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!command.trim()) return
    let config = null
    if (configText.trim()) {
      try {
        config = JSON.parse(configText.trim())
      } catch {
        setError('Config must be valid JSON')
        return
      }
    }
    setLoading(true)
    setError(null)
    try {
      await createTraining({ run_id: runId, command: command.trim(), name: name.trim() || null, config })
      setCommand('')
      setName('')
      setConfigText('')
      await load()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async (id: string) => {
    try {
      await startTraining(id)
      await load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleStop = async (id: string) => {
    try {
      await stopTraining(id)
      await load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this training task?')) return
    try {
      await deleteTraining(id)
      await load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const statusColor: Record<string, string> = {
    pending: CYBER.muted,
    running: CYBER.green,
    stopped: CYBER.blue,
    failed: CYBER.red,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          placeholder="training command"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          style={{ ...inputStyle, flex: 1 }}
        />
        <input
          placeholder="name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ ...inputStyle, width: 160 }}
        />
        <input
          placeholder='config JSON (optional)'
          value={configText}
          onChange={(e) => setConfigText(e.target.value)}
          style={{ ...inputStyle, width: 200 }}
        />
        <button
          onClick={handleCreate}
          disabled={!command.trim() || loading}
          style={{
            background: 'transparent',
            color: CYBER.green,
            border: `1px solid ${CYBER.green}`,
            borderRadius: 4,
            padding: '8px 14px',
            fontFamily: CYBER.font,
            cursor: 'pointer',
            boxShadow: `0 0 8px ${CYBER.green}33`,
            opacity: !command.trim() || loading ? 0.5 : 1,
          }}
        >
          CREATE
        </button>
      </div>

      {error && <div style={{ color: CYBER.red }}>[ERR] {error}</div>}
      {loading && <div style={{ color: CYBER.blue }}>&gt; SYNCING...</div>}

      {trainings.length === 0 ? (
        <EmptyState>No training tasks for this run.</EmptyState>
      ) : (
        <div style={{ flex: 1, overflow: 'auto', border: `1px solid ${CYBER.border}`, borderRadius: 6 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead style={{ position: 'sticky', top: 0, background: CYBER.panel2 }}>
              <tr style={{ borderBottom: `1px solid ${CYBER.border}` }}>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>PID</th>
                <th style={thStyle}>Command</th>
                <th style={thStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {trainings.map((t) => (
                <tr key={t.id} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
                  <td style={tdStyle}>{t.name || t.id.slice(0, 8)}</td>
                  <td style={{ ...tdStyle, color: statusColor[t.status] || CYBER.text }}>{t.status}</td>
                  <td style={tdStyle}>{t.pid ?? '—'}</td>
                  <td style={tdStyle}>
                    <code style={{ color: CYBER.muted }}>{t.command}</code>
                  </td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {t.status !== 'running' && (
                        <button
                          onClick={() => handleStart(t.id)}
                          style={{
                            background: 'transparent',
                            color: CYBER.green,
                            border: `1px solid ${CYBER.green}`,
                            borderRadius: 4,
                            padding: '4px 8px',
                            fontFamily: CYBER.font,
                            cursor: 'pointer',
                            fontSize: 11,
                          }}
                        >
                          START
                        </button>
                      )}
                      {t.status === 'running' && (
                        <button
                          onClick={() => handleStop(t.id)}
                          style={{
                            background: 'transparent',
                            color: CYBER.blue,
                            border: `1px solid ${CYBER.blue}`,
                            borderRadius: 4,
                            padding: '4px 8px',
                            fontFamily: CYBER.font,
                            cursor: 'pointer',
                            fontSize: 11,
                          }}
                        >
                          STOP
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(t.id)}
                        style={{
                          background: 'transparent',
                          color: CYBER.red,
                          border: `1px solid ${CYBER.red}`,
                          borderRadius: 4,
                          padding: '4px 8px',
                          fontFamily: CYBER.font,
                          cursor: 'pointer',
                          fontSize: 11,
                        }}
                      >
                        DELETE
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
