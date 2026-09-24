export const bandColor = (category) => {
  const map = {
    Good: 'var(--band-good)',
    Satisfactory: 'var(--band-satisfactory)',
    Moderate: 'var(--band-moderate)',
    Poor: 'var(--band-poor)',
    'Very Poor': 'var(--band-verypoor)',
    Severe: 'var(--band-severe)',
  }
  return map[category] || 'var(--ink-faint)'
}

export const sourceColor = (key) => {
  const map = {
    traffic: 'var(--src-traffic)',
    industrial: 'var(--src-industrial)',
    construction: 'var(--src-construction)',
    waste_burning: 'var(--src-waste)',
    background: 'var(--src-background)',
  }
  return map[key] || 'var(--ink-faint)'
}

export function Badge({ category }) {
  if (!category) return <span className="badge" style={{ background: 'var(--ink-faint)' }}>No data</span>
  return (
    <span className="badge" style={{ background: bandColor(category) }}>
      {category}
    </span>
  )
}

export function LoadingDots({ label = 'Loading' }) {
  return <div className="loading-dots">{label}...</div>
}

export function ErrorNote({ message }) {
  return <div className="error-note">{message}</div>
}

export function formatSourceLabel(key) {
  const map = {
    traffic: 'Traffic',
    industrial: 'Industrial',
    construction: 'Construction',
    waste_burning: 'Waste Burning',
    background: 'Background',
  }
  return map[key] || key
}
