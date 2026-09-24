import { useEffect, useState, useCallback } from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { LoadingDots, ErrorNote, sourceColor, formatSourceLabel } from '../ui'

export default function SourceMix({ locationId, locationName }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!locationId) return
    try {
      const d = await api.sourceAttribution(locationId)
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [locationId])

  useEffect(() => { load() }, [load])

  if (error) return <ErrorNote message={error} />
  if (!data) return <LoadingDots label="Estimating source mix" />

  const pieData = Object.entries(data.mix_percent || {}).map(([key, value]) => ({
    name: formatSourceLabel(key),
    key,
    value,
  }))

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Estimated Pollution Sources -- {locationName}</h2>
          <p className="section-note">{data.methodology}</p>
        </div>
      </div>

      <div className="two-col">
        <div className="panel">
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={110}
                label={({ value }) => `${value}%`}
              >
                {pieData.map((entry) => (
                  <Cell key={entry.key} fill={sourceColor(entry.key)} stroke="var(--bg-panel)" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ fontFamily: 'var(--font-body)', fontSize: 12, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h3 style={{ fontSize: 15 }}>How this estimate was built</h3>
          <ul style={{ paddingLeft: 18, margin: 0, fontSize: 13, color: 'var(--ink-soft)' }}>
            {(data.reasoning || []).map((r, i) => <li key={i} style={{ marginBottom: 6 }}>{r}</li>)}
          </ul>
          <div className="hint-banner" style={{ marginTop: 14 }}>
            No sensor anywhere directly measures "% from traffic vs industry." This is a transparent,
            documented rule-based estimate -- not a lab measurement.
          </div>
        </div>
      </div>
    </>
  )
}
