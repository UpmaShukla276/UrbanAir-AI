import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import { LoadingDots, ErrorNote } from '../ui'

export default function Enforcement({ onSelect }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const d = await api.enforcement()
      setItems(d)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (error) return <ErrorNote message={error} />
  if (!items) return <LoadingDots label="Ranking locations" />

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Enforcement Priority</h2>
          <p className="section-note">All 21 locations ranked by current AQI and GRAP stage, with the top estimated source driving each one.</p>
        </div>
      </div>

      <div className="panel" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Rank</th><th>Location</th><th>AQI</th><th>GRAP</th><th>Top source</th><th>Top action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.location.id} onClick={() => onSelect(it.location.id)} style={{ cursor: 'pointer' }}>
                <td className="mono-num">{it.rank}</td>
                <td>{it.location.name}</td>
                <td className="mono-num">{it.aqi ?? '--'}</td>
                <td>{it.grap_label}</td>
                <td>{it.top_estimated_source ? it.top_estimated_source.replace('_', ' ') : '--'}</td>
                <td style={{ maxWidth: 280, fontSize: 12.5, color: 'var(--ink-soft)' }}>
                  {it.recommended_actions[0]}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
