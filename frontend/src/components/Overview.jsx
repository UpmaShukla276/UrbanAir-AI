import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import { Badge, LoadingDots, ErrorNote } from '../ui'
import MapView from './MapView'

export default function Overview({ selectedId, onSelect }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await api.currentAll()
      setItems(data)
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
  if (!items) return <LoadingDots label="Loading live data for all 21 locations" />

  const selected = items.find((i) => i.location.id === selectedId)

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Live Overview</h2>
          <p className="section-note">Real-time AQI across 21 Delhi NCR monitoring points. Click a marker or card to see full detail in other tabs.</p>
        </div>
        <button className="pill-btn" onClick={async () => { await api.refresh(); load() }}>Refresh now</button>
      </div>

      <MapView items={items} selectedId={selectedId} onSelect={onSelect} />

      {selected && (
        <div className="panel" style={{ marginTop: 16 }}>
          <div className="location-card-top">
            <div>
              <div className="location-name">{selected.location.name}</div>
              <div className="zone-tag">{selected.location.zone_type.replace('_', ' ')}</div>
            </div>
            <Badge category={selected.band?.category} />
          </div>
          {selected.reading ? (
            <>
              <div className="aqi-number" style={{ marginTop: 8 }}>{selected.reading.aqi}</div>
              <p className="section-note" style={{ marginTop: 4 }}>{selected.band?.advisory}</p>
              {!selected.is_live && (
                <div className="stale-note">Showing last known reading -- {selected.data_age_minutes} min old.</div>
              )}
              {selected.data_note && <div className="station-note">{selected.data_note}</div>}
            </>
          ) : (
            <p className="section-note">No data fetched yet for this location.</p>
          )}
        </div>
      )}

      <div className="section-header" style={{ marginTop: 24 }}>
        <h2>All Locations</h2>
      </div>
      <div className="grid grid-cards">
        {items.map((item) => (
          <div
            key={item.location.id}
            className={`location-card ${item.location.id === selectedId ? 'selected' : ''}`}
            onClick={() => onSelect(item.location.id)}
          >
            <div className="location-card-top">
              <div>
                <div className="location-name">{item.location.name}</div>
                <div className="zone-tag">{item.location.zone_type.replace('_', ' ')}</div>
              </div>
              <Badge category={item.band?.category} />
            </div>
            <div className="aqi-number" style={{ marginTop: 8 }}>
              {item.reading ? item.reading.aqi : '--'}
            </div>
            {item.reading && !item.is_live && (
              <div className="stale-note">{item.data_age_minutes} min old</div>
            )}
          </div>
        ))}
      </div>
    </>
  )
}
