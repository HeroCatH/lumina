import { useEffect, useState } from 'react'
import { fetchDatasets, fetchDatasetPreview } from '../hooks/useApi'
import { DatasetInfo, DatasetPreview } from '../types'

export default function DataPanel() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    fetchDatasetPreview(selected).then(setPreview).catch((e) => setError(e.message))
  }, [selected])

  if (error) return <div style={{ padding: 20 }}>Error: {error}</div>

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: 260, borderRight: '1px solid #e0e0e0', padding: 12 }}>
        <h3>Datasets</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {datasets.map((ds) => (
            <li
              key={ds.id}
              onClick={() => setSelected(ds.name)}
              style={{
                padding: '8px',
                cursor: 'pointer',
                background: ds.name === selected ? '#e6f7ff' : 'transparent',
              }}
            >
              <div>{ds.name}</div>
              <div style={{ fontSize: 12, color: '#888' }}>{ds.adapter_type}</div>
            </li>
          ))}
        </ul>
      </div>
      <div style={{ flex: 1, padding: 12, overflow: 'auto' }}>
        {preview ? (
          <div>
            <h3>{selected}</h3>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
              <StatCard label="Rows" value={preview.statistics.row_count} />
              <StatCard label="Columns" value={preview.statistics.column_count} />
            </div>
            <h4>Preview</h4>
            <table style={{ borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {preview.statistics.columns.map((col) => (
                    <th key={col} style={{ border: '1px solid #ddd', padding: 6 }}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx}>
                    {preview.statistics.columns.map((col) => (
                      <td key={col} style={{ border: '1px solid #ddd', padding: 6 }}>{String(row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Select a dataset to preview.</p>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: '1px solid #e0e0e0', borderRadius: 6, padding: 12, minWidth: 100 }}>
      <div style={{ fontSize: 12, color: '#888' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 600 }}>{value}</div>
    </div>
  )
}
