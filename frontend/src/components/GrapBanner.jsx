import { useEffect, useState } from 'react'
import { api } from '../api'
import { bandColor } from '../ui'

const STAGE_DOT_COLOR = {
  0: 'var(--band-good)',
  1: 'var(--band-poor)',
  2: 'var(--band-verypoor)',
  3: 'var(--band-severe)',
  4: 'var(--band-severe)',
}

export default function GrapBanner() {
  const [data, setData] = useState(null)

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const d = await api.grapOverall()
        if (mounted) setData(d)
      } catch (e) {
        // Banner fails quietly -- individual panels show their own errors.
      }
    }
    load()
    const t = setInterval(load, 60000)
    return () => { mounted = false; clearInterval(t) }
  }, [])

  if (!data) return null

  return (
    <div className="grap-banner">
      <span className="grap-dot" style={{ background: STAGE_DOT_COLOR[data.grap.stage] }} />
      <strong>NCR-wide: {data.grap.label}</strong>
      <span style={{ color: 'var(--ink-soft)' }}>
        Worst live AQI right now: {data.ncr_worst_aqi ?? 'no data yet'}
      </span>
    </div>
  )
}
