import { useState, useMemo, useRef, useEffect } from 'react'
import {
  Map, TrendingUp, PieChart, CloudSun, Wind, ShieldAlert,
  Megaphone, ClipboardList, FlaskConical,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview & Map', icon: Map },
  { id: 'trend', label: '12h Trend', icon: TrendingUp },
  { id: 'source', label: 'Source Mix', icon: PieChart },
  { id: 'forecast', label: 'Forecast', icon: CloudSun },
  { id: 'wind', label: 'Wind & Impact', icon: Wind },
  { id: 'enforcement', label: 'Enforcement', icon: ShieldAlert },
  { id: 'alerts', label: 'Alerts', icon: Megaphone },
  { id: 'compliance', label: 'GRAP Compliance', icon: ClipboardList },
  { id: 'whatif', label: 'What-If Simulator', icon: FlaskConical },
]

export default function Sidebar({ locations, selectedId, onSelectLocation, activeTab, onSelectTab }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const boxRef = useRef(null)

  const filtered = useMemo(() => {
    if (!query.trim()) return locations
    const q = query.toLowerCase()
    return locations.filter((l) => l.name.toLowerCase().includes(q))
  }, [query, locations])

  useEffect(() => {
    function onClickOutside(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const selectedLocation = locations.find((l) => l.id === selectedId)

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">UrbanAir AI</span>
        <span className="brand-sub">Delhi NCR</span>
      </div>

      <div className="search-box" ref={boxRef}>
        <input
          className="search-input"
          placeholder="Search a location..."
          value={open ? query : (selectedLocation ? selectedLocation.name : query)}
          onFocus={() => { setOpen(true); setQuery('') }}
          onChange={(e) => setQuery(e.target.value)}
        />
        {open && (
          <div className="search-dropdown">
            {filtered.length === 0 && (
              <div className="search-dropdown-item" style={{ color: '#8A8271' }}>No match</div>
            )}
            {filtered.map((loc) => (
              <div
                key={loc.id}
                className={`search-dropdown-item ${loc.id === selectedId ? 'active' : ''}`}
                onClick={() => { onSelectLocation(loc.id); setOpen(false); setQuery('') }}
              >
                <span>{loc.name}</span>
                <span style={{ color: '#8A8271', fontSize: 11 }}>{loc.zone_type.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="location-select-label">Or pick from all 21 locations:</div>
      <select
        value={selectedId || ''}
        onChange={(e) => onSelectLocation(e.target.value)}
        style={{ width: '100%', background: '#35332C', color: '#EFE9DB', border: '1px solid #4A473D' }}
      >
        {locations.map((loc) => (
          <option key={loc.id} value={loc.id}>{loc.name}</option>
        ))}
      </select>

      <nav className="nav-list">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${activeTab === id ? 'active' : ''}`}
            onClick={() => onSelectTab(id)}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        Live data: WAQI + OpenWeatherMap.<br />
        CPCB &amp; CAQM official standards.
      </div>
    </aside>
  )
}
