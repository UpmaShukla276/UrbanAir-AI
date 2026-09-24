import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import { bandColor } from '../ui'

function FlyToSelected({ items, selectedId }) {
  const map = useMap()
  useEffect(() => {
    const item = items.find((i) => i.location.id === selectedId)
    if (item) {
      map.flyTo([item.location.lat, item.location.lon], 12, { duration: 0.6 })
    }
  }, [selectedId])
  return null
}

export default function MapView({ items, selectedId, onSelect }) {
  const center = [28.62, 77.21]

  return (
    <div className="map-wrap">
      <MapContainer center={center} zoom={10} style={{ height: '100%', width: '100%' }} scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FlyToSelected items={items} selectedId={selectedId} />
        {items.map((item) => {
          const { location, reading, band, is_live } = item
          const color = band ? bandColor(band.category) : 'var(--ink-faint)'
          const isSelected = location.id === selectedId
          return (
            <CircleMarker
              key={location.id}
              center={[location.lat, location.lon]}
              radius={isSelected ? 12 : 8}
              pathOptions={{
                color: isSelected ? 'var(--ink)' : '#ffffff',
                weight: isSelected ? 2 : 1.5,
                fillColor: color,
                fillOpacity: 0.9,
              }}
              eventHandlers={{ click: () => onSelect(location.id) }}
            >
              <Popup>
                <strong>{location.name}</strong><br />
                {reading ? (
                  <>
                    AQI: {reading.aqi} ({band?.category})<br />
                    {is_live ? 'Live' : 'Last known reading'}
                  </>
                ) : (
                  'No data yet'
                )}
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}
