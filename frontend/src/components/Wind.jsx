import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import { LoadingDots, ErrorNote } from '../ui'

function Compass({ fromDeg }) {
  const toDeg = fromDeg != null ? (fromDeg + 180) % 360 : null
  return (
    <svg viewBox="0 0 200 200" width="180" height="180">
      <circle cx="100" cy="100" r="92" fill="var(--bg-inset)" stroke="var(--line)" strokeWidth="2" />
      {['N', 'E', 'S', 'W'].map((label, i) => {
        const angle = i * 90
        const rad = (angle - 90) * (Math.PI / 180)
        const x = 100 + 76 * Math.cos(rad)
        const y = 100 + 76 * Math.sin(rad)
        return (
          <text key={label} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="12" fill="var(--ink-soft)">
            {label}
          </text>
        )
      })}
      {toDeg != null && (
        <g transform={`rotate(${toDeg}, 100, 100)`}>
          <line x1="100" y1="100" x2="100" y2="35" stroke="var(--accent-deep)" strokeWidth="4" strokeLinecap="round" />
          <polygon points="100,22 90,45 110,45" fill="var(--accent-deep)" />
        </g>
      )}
      <circle cx="100" cy="100" r="5" fill="var(--ink)" />
    </svg>
  )
}

export default function Wind({ locationId, locationName }) {
  const [current, setCurrent] = useState(null)
  const [impact, setImpact] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!locationId) return
    try {
      const [cur, imp] = await Promise.all([
        api.currentOne(locationId),
        api.windImpact(locationId).catch((e) => ({ error: e.message })),
      ])
      setCurrent(cur)
      setImpact(imp)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [locationId])

  useEffect(() => {
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [load])

  if (error) return <ErrorNote message={error} />
  if (!current) return <LoadingDots label="Loading wind data" />

  const reading = current.reading

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Wind -- {locationName}</h2>
          <p className="section-note">Live wind from OpenWeatherMap, in plain language.</p>
        </div>
      </div>

      <div className="panel" style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
        <Compass fromDeg={reading?.wind_deg} />
        <div style={{ maxWidth: 480 }}>
          {impact?.error ? (
            <div className="hint-banner">{impact.error}</div>
          ) : impact?.summary ? (
            <p style={{ fontSize: 15, lineHeight: 1.7 }}>{impact.summary}</p>
          ) : (
            <div className="zone-tag">No live wind data yet</div>
          )}
        </div>
      </div>
    </>
  )
}