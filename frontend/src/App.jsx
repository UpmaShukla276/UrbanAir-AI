import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import GrapBanner from './components/GrapBanner'
import Overview from './components/Overview'
import Trend from './components/Trend'
import SourceMix from './components/SourceMix'
import Forecast from './components/Forecast'
import Wind from './components/Wind'
import Enforcement from './components/Enforcement'
import Alerts from './components/Alerts'
import Compliance from './components/Compliance'
import WhatIf from './components/WhatIf'
import { api } from './api'
import { LoadingDots, ErrorNote } from './ui'

export default function App() {
  const [locations, setLocations] = useState(null)
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    api.locations()
      .then((locs) => {
        setLocations(locs)
        if (locs.length > 0) setSelectedId(locs[0].id)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div style={{ padding: 40 }}>
        <h2>UrbanAir AI</h2>
        <ErrorNote message={`Could not reach the backend: ${error}. Is it running at http://127.0.0.1:8000 ?`} />
      </div>
    )
  }

  if (!locations) {
    return (
      <div style={{ padding: 40 }}>
        <LoadingDots label="Connecting to backend" />
      </div>
    )
  }

  const selectedLocation = locations.find((l) => l.id === selectedId)
  const locationName = selectedLocation ? selectedLocation.name : ''

  function renderTab() {
    switch (activeTab) {
      case 'overview':
        return <Overview selectedId={selectedId} onSelect={setSelectedId} />
      case 'trend':
        return <Trend locationId={selectedId} locationName={locationName} />
      case 'source':
        return <SourceMix locationId={selectedId} locationName={locationName} />
      case 'forecast':
        return <Forecast locationId={selectedId} locationName={locationName} />
      case 'wind':
        return <Wind locationId={selectedId} locationName={locationName} />
      case 'enforcement':
        return <Enforcement onSelect={(id) => { setSelectedId(id); setActiveTab('overview') }} />
      case 'alerts':
        return <Alerts locationId={selectedId} locationName={locationName} />
      case 'compliance':
        return <Compliance />
      case 'whatif':
        return <WhatIf locationId={selectedId} locationName={locationName} />
      default:
        return null
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        locations={locations}
        selectedId={selectedId}
        onSelectLocation={setSelectedId}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />
      <div className="main-area">
        <GrapBanner />
        <div className="main-content">
          {renderTab()}
        </div>
      </div>
    </div>
  )
}
