import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import { LoadingDots, ErrorNote } from '../ui'

export default function Compliance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const d = await api.grapCompliance()
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [load])

  if (error) return <ErrorNote message={error} />
  if (!data) return <LoadingDots label="Loading GRAP compliance status" />

  if (!data.current_stage && data.current_stage !== 0) {
    return <div className="hint-banner">{data.message}</div>
  }

  return (
    <>
      <div className="section-header">
        <div>
          <h2>GRAP Compliance Tracking</h2>
          <p className="section-note">Real, time-tracked stage history for Delhi NCR -- starts logging from when this server first ran.</p>
        </div>
      </div>

      <div className="panel">
        <div className="zone-tag">Currently in</div>
        <div className="aqi-number" style={{ fontSize: 26, marginTop: 4 }}>{data.current_label}</div>
        <p className="section-note" style={{ marginTop: 6 }}>
          Since {new Date(data.in_this_stage_since).toLocaleString()} -- {data.duration_hours} hours so far.
          NCR worst AQI when this stage began: {data.ncr_worst_aqi_at_entry ?? 'N/A'}.
        </p>
      </div>

      <div className="panel">
        <h3 style={{ fontSize: 15 }}>Stage transition history</h3>
        {data.history.length <= 1 ? (
          <p className="section-note">No stage changes recorded yet -- history builds as the real AQI actually moves between GRAP stages.</p>
        ) : (
          <table className="table">
            <thead><tr><th>Stage</th><th>Started</th><th>NCR worst AQI</th></tr></thead>
            <tbody>
              {data.history.map((h) => (
                <tr key={h.id}>
                  <td>{h.label}</td>
                  <td>{new Date(h.started_at).toLocaleString()}</td>
                  <td className="mono-num">{h.ncr_worst_aqi ?? '--'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
