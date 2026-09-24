import { useState } from 'react'
import { api } from '../api'
import { ErrorNote } from '../ui'

const SLIDERS = [
  { key: 'traffic_reduction', label: 'Traffic reduction' },
  { key: 'industrial_reduction', label: 'Industrial reduction' },
  { key: 'construction_reduction', label: 'Construction reduction' },
  { key: 'waste_burning_reduction', label: 'Waste burning reduction' },
  { key: 'background_reduction', label: 'Background reduction' },
]

export default function WhatIf({ locationId, locationName }) {
  const [values, setValues] = useState({
    traffic_reduction: 0,
    industrial_reduction: 0,
    construction_reduction: 0,
    waste_burning_reduction: 0,
    background_reduction: 0,
    wind_multiplier: 1.0,
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  function setValue(key, val) {
    setValues((v) => ({ ...v, [key]: val }))
  }

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const d = await api.whatIf(locationId, values)
      setResult(d)
    } catch (e) {
      setError(e.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="section-header">
        <div>
          <h2>What-If Simulator -- {locationName}</h2>
          <p className="section-note">A transparent, disclosed estimate -- not a validated dispersion model. Current AQI is always the live figure from Overview.</p>
        </div>
      </div>

      <div className="panel">
        <div className="grid" style={{ gridTemplateColumns: '1fr', gap: 18 }}>
          {SLIDERS.map(({ key, label }) => (
            <div key={key}>
              <label className="field-label">{label}: {values[key]}%</label>
              <input
                type="range" min="0" max="100" value={values[key]}
                onChange={(e) => setValue(key, Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>
          ))}

          <div>
            <label className="field-label">
              Wind condition: {values.wind_multiplier}x current speed
              {' '}({values.wind_multiplier < 1 ? 'calmer' : values.wind_multiplier > 1 ? 'windier' : 'unchanged'})
            </label>
            <input
              type="range" min="0.3" max="3" step="0.1" value={values.wind_multiplier}
              onChange={(e) => setValue('wind_multiplier', Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <button className="pill-btn primary" onClick={run} disabled={loading} style={{ marginTop: 18 }}>
          {loading ? 'Calculating...' : 'Run simulation'}
        </button>
      </div>

      {error && <ErrorNote message={error} />}

      {result && (
        <div className="panel">
          <div className="grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', marginBottom: 14 }}>
            <div>
              <div className="zone-tag">Current AQI (live, same as Overview)</div>
              <div className="aqi-number">{result.current_estimated_aqi ?? '--'}</div>
            </div>
            <div>
              <div className="zone-tag">Simulated AQI</div>
              <div className="aqi-number" style={{ color: 'var(--accent-deep)' }}>{result.simulated_estimated_aqi ?? '--'}</div>
            </div>
            <div>
              <div className="zone-tag">Change</div>
              <div className="aqi-number">{result.estimated_aqi_change ?? '--'}</div>
            </div>
          </div>
          <p className="section-note">{result.methodology}</p>
          <div className="station-note">
            PM2.5: {result.current_pm25} &rarr; {result.simulated_pm25} | PM10: {result.current_pm10} &rarr; {result.simulated_pm10}
          </div>
        </div>
      )}
    </>
  )
}