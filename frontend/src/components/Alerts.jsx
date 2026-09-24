import { useEffect, useState, useCallback } from 'react'
import { api } from '../api'
import { LoadingDots, ErrorNote } from '../ui'

export default function Alerts({ locationId, locationName }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [email, setEmail] = useState('')
  const [sendStatus, setSendStatus] = useState(null)
  const [sending, setSending] = useState(false)

  const load = useCallback(async () => {
    if (!locationId) return
    try {
      const d = await api.alert(locationId)
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [locationId])

  useEffect(() => { load(); setSendStatus(null) }, [load])

  async function handleSend() {
    if (!email) return
    setSending(true)
    setSendStatus(null)
    try {
      const res = await api.sendAlertEmail(locationId, email)
      setSendStatus(res)
    } catch (e) {
      setSendStatus({ sent: false, message: e.message })
    } finally {
      setSending(false)
    }
  }

  if (error) return <ErrorNote message={error} />
  if (!data) return <LoadingDots label="Building alert" />

  return (
    <>
      <div className="section-header">
        <div>
          <h2>Alerts -- {locationName}</h2>
          <p className="section-note">Generated from the current real reading. Email sending needs SMTP settings in the backend .env.</p>
        </div>
      </div>

      <div className="two-col">
        <div className="panel">
          <h3 style={{ fontSize: 15 }}>Official Report</h3>
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--ink)' }}>
            {data.official_report}
          </pre>
        </div>
        <div className="panel">
          <h3 style={{ fontSize: 15 }}>Public Advisory (Hinglish)</h3>
          <p style={{ fontSize: 13.5 }}>{data.public_advisory_hinglish}</p>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ fontSize: 15 }}>Send Official Report by Email</h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label className="field-label">Recipient email</label>
            <input type="email" placeholder="official@example.gov.in" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: 260 }} />
          </div>
          <button className="pill-btn primary" onClick={handleSend} disabled={sending || !email}>
            {sending ? 'Sending...' : 'Send'}
          </button>
        </div>
        {sendStatus && (
          <div className={sendStatus.sent ? 'hint-banner' : 'error-note'} style={{ marginTop: 12 }}>
            {sendStatus.message}
          </div>
        )}
      </div>
    </>
  )
}
