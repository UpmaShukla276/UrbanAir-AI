import { useEffect, useState, useCallback } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { LoadingDots, ErrorNote, Badge } from '../ui'

export default function Forecast({ locationId, locationName }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!locationId) return
    setLoading(true)
    try {
      const d = await api.forecast(locationId)
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [locationId])

  useEffect(() => { load() }, [load])

  const chartData = (data?.hourly || []).map((p) => ({
    time: new Date(p.timestamp_iso).toLocaleString([], { weekday: 'short', hour: '2-digit' }),
    aqi: p.aqi,
  }))

  return (
    <>
      <div className="section-header">
        <div>
          <h2>4-Day Forecast -- {locationName}</h2>
          <p className="section-note">
            Real pollutant forecast from OpenWeatherMap, converted through the official CPCB AQI formula.
          </p>
        </div>
      </div>

      {loading && <LoadingDots label="Fetching forecast" />}
      {error && (
        <div className="hint-banner">
          {error}. New OpenWeatherMap keys can take up to a couple of hours to activate -- try again later.
        </div>
      )}

      {data && (
        <>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 16 }}>
            {[
              { label: 'In 24 hours', snap: data.snapshot_24h },
              { label: 'In 48 hours', snap: data.snapshot_48h },
              { label: 'In 72 hours', snap: data.snapshot_72h },
            ].map(({ label, snap }) => (
              <div className="panel" key={label}>
                <div className="zone-tag">{label}</div>
                <div className="aqi-number" style={{ marginTop: 6 }}>{snap?.aqi ?? '--'}</div>
                <Badge category={snap?.band?.category} />
              </div>
            ))}
          </div>

          <div className="panel">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="var(--ink-soft)" fontSize={10} interval={5} />
                <YAxis stroke="var(--ink-soft)" fontSize={11} />
                <Tooltip contentStyle={{ fontFamily: 'var(--font-body)', fontSize: 12, borderRadius: 8 }} />
                <Area type="monotone" dataKey="aqi" stroke="var(--accent-deep)" fill="url(#aqiGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </>
  )
}
