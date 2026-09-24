import { useEffect, useState, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { LoadingDots, ErrorNote } from '../ui'

export default function Trend({ locationId, locationName }) {
  const [hours, setHours] = useState(12)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!locationId) return
    try {
      const d = await api.trend(locationId, hours)
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [locationId, hours])

  useEffect(() => {
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [load])

  const chartData = (data?.points || []).map((p) => ({
    time: new Date(p.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    aqi: p.aqi,
    pm25: p.pm25,
    pm10: p.pm10,
  }))

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Historical Trend -- {locationName}</h2>
          <p className="section-note">Built from real readings stored since this server started running. Not backfilled.</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {[6, 12, 24, 48].map((h) => (
            <button
              key={h}
              className={`pill-btn ${hours === h ? 'primary' : ''}`}
              onClick={() => setHours(h)}
            >
              {h}h
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorNote message={error} />}
      {!data && !error && <LoadingDots label="Loading trend" />}

      {data && (
        chartData.length === 0 ? (
          <div className="hint-banner">
            No history yet for this window. Since we never backfill fake data, the trend fills in as the
            server keeps running (a new real point every ~15 minutes).
          </div>
        ) : (
          <div className="panel">
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="var(--ink-soft)" fontSize={11} />
                <YAxis stroke="var(--ink-soft)" fontSize={11} />
                <Tooltip contentStyle={{ fontFamily: 'var(--font-body)', fontSize: 12, borderRadius: 8 }} />
                <Line type="monotone" dataKey="aqi" stroke="var(--accent-deep)" strokeWidth={2} dot={false} name="AQI" />
                <Line type="monotone" dataKey="pm25" stroke="var(--src-traffic)" strokeWidth={1.5} dot={false} name="PM2.5" />
                <Line type="monotone" dataKey="pm10" stroke="var(--src-background)" strokeWidth={1.5} dot={false} name="PM10" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      )}
    </>
  )
}
