import { useEffect, useState } from 'react'
import { fetchDatasets, fetchDatasetPreview } from '../hooks/useApi'
import { cardStyle, CYBER, sectionTitle, tdStyle, thStyle } from '../theme'
import { DatasetInfo, DatasetPreview } from '../types'

export default function DataPanel() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDatasets()
      .then((data) => {
        setError(null)
        setDatasets(data)
      })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    setError(null)
    fetchDatasetPreview(selected)
      .then((data) => {
        setError(null)
        setPreview(data)
      })
      .catch((e) => setError(e.message))
  }, [selected])

  if (error) return <div style={{ padding: 20, background: CYBER.bg, color: CYBER.red }}>[ERR] {error}</div>

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        background: CYBER.bg,
        color: CYBER.text,
        fontFamily: CYBER.font,
      }}
    >
      <div
        style={{
          width: 260,
          borderRight: `1px solid ${CYBER.border}`,
          padding: 12,
          background: CYBER.panel,
          overflow: 'auto',
        }}
      >
        <div style={sectionTitle(CYBER.blue)}>Datasets</div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {datasets.map((ds) => (
            <li
              key={ds.id}
              onClick={() => setSelected(ds.name)}
              style={{
                padding: '8px',
                cursor: 'pointer',
                background: ds.name === selected ? `${CYBER.blue}22` : 'transparent',
                border: `1px solid ${ds.name === selected ? CYBER.blue : 'transparent'}`,
                borderRadius: 4,
                marginBottom: 6,
              }}
            >
              <div style={{ color: ds.name === selected ? CYBER.blue : CYBER.text }}>{ds.name}</div>
              <div style={{ fontSize: 12, color: CYBER.muted }}>{ds.adapter_type}</div>
            </li>
          ))}
        </ul>
      </div>
      <div style={{ flex: 1, padding: 16, overflow: 'auto' }}>
        {preview ? (
          <div>
            <div
              style={{
                fontSize: 18,
                color: CYBER.green,
                textShadow: `0 0 10px ${CYBER.green}55`,
                marginBottom: 12,
              }}
            >
              {selected}
            </div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
              <StatCard label="ROWS" value={preview.statistics.row_count} color={CYBER.blue} />
              <StatCard label="COLUMNS" value={preview.statistics.column_count} color={CYBER.pink} />
            </div>
            <div style={sectionTitle(CYBER.blue)}>Preview</div>
            <table style={{ borderCollapse: 'collapse', fontSize: 13, border: `1px solid ${CYBER.border}` }}>
              <thead style={{ background: CYBER.panel2 }}>
                <tr>
                  {preview.statistics.columns.map((col) => (
                    <th key={col} style={{ ...thStyle, border: `1px solid ${CYBER.border}` }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: `1px solid ${CYBER.border}` }}>
                    {preview.statistics.columns.map((col) => (
                      <td key={col} style={{ ...tdStyle, border: `1px solid ${CYBER.border}` }}>
                        {String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: CYBER.muted }}>Select a dataset to preview.</div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      style={{
        ...cardStyle,
        padding: 14,
        minWidth: 120,
        borderColor: `${color}55`,
        boxShadow: `0 0 12px ${color}22`,
      }}
    >
      <div style={{ fontSize: 10, color: CYBER.muted }}>{label}</div>
      <div style={{ fontSize: 24, color, textShadow: `0 0 10px ${color}55` }}>{value}</div>
    </div>
  )
}
