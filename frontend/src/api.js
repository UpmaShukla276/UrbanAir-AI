const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function getJSON(path) {
  const res = await fetch(`${BASE_URL}${path}`)
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = (data && data.detail) || `Request failed (${res.status})`
    throw new Error(detail)
  }
  return data
}

async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = (data && data.detail) || `Request failed (${res.status})`
    throw new Error(detail)
  }
  return data
}

export const api = {
  locations: () => getJSON('/api/locations'),
  currentAll: () => getJSON('/api/current'),
  currentOne: (id) => getJSON(`/api/current/${id}`),
  trend: (id, hours = 12) => getJSON(`/api/trend/${id}?hours=${hours}`),
  sourceAttribution: (id) => getJSON(`/api/source-attribution/${id}`),
  grapOverall: () => getJSON('/api/grap'),
  grapForLocation: (id) => getJSON(`/api/grap/${id}`),
  forecast: (id) => getJSON(`/api/forecast/${id}`),
  windImpact: (id) => getJSON(`/api/wind-impact/${id}`),
  enforcement: () => getJSON('/api/enforcement'),
  alert: (id) => getJSON(`/api/alert/${id}`),
  sendAlertEmail: (id, toEmail) => postJSON(`/api/alert/${id}/send-email?to_email=${encodeURIComponent(toEmail)}`),
  grapCompliance: () => getJSON('/api/grap-compliance'),
  whatIf: (id, params) => {
    const q = new URLSearchParams(params).toString()
    return getJSON(`/api/whatif/${id}?${q}`)
  },
  refresh: () => postJSON('/api/refresh'),
}