# API Reference

Base URL (local): `http://127.0.0.1:8000`
Base URL (deployed): `[https://urban-air-ai-kappa.vercel.app/]`

All responses are JSON. `location_id` values come from `GET /api/locations` (e.g. `anand_vihar`).

---

### `GET /`
Health check. Returns `{"status": "ok", "service": "UrbanAir AI Backend"}`.

### `GET /api/locations`
All 21 monitored Delhi NCR locations, with `id`, `name`, `lat`, `lon`, and `zone_type`.

### `GET /api/current`
Live snapshot (reading + AQI band + live/stale flag) for all 21 locations at once. Used to populate the map and overview panel.

### `GET /api/current/{location_id}`
Same as above, for a single location. Includes `data_age_minutes`, `is_live`, distance to the real station used, and a human-readable `data_note`.

### `GET /api/trend/{location_id}?hours=12`
Historical trend for one location, built from real stored readings (not interpolated). `hours` is optional, default `12`.

### `GET /api/source-attribution/{location_id}`
Rule-based estimate of pollution source mix (traffic / industrial / construction / waste-burning / background) for one location. Always returned tagged as an estimate — see `docs/METHODOLOGY.md`.

### `GET /api/grap/{location_id}`
Current GRAP stage + mandated actions, based on this location's current AQI.

### `GET /api/grap`
Current GRAP stage for the **worst** AQI across all 21 locations, plus which location that is — mirrors how CAQM actually calls a region-wide stage.

### `GET /api/forecast/{location_id}`
OpenWeatherMap's 4-day hourly pollutant forecast, converted to CPCB-comparable AQI. Returns the full hourly series plus `snapshot_24h`, `snapshot_48h`, `snapshot_72h`. Returns `503` if `OWM_API_KEY` isn't set or the forecast API is unavailable.

### `GET /api/wind-impact/{location_id}`
Live wind speed/direction for one location, with a plain-language summary of where it's coming from. Returns `503` if no live wind reading is available yet.

### `POST /api/refresh`
Triggers an immediate fetch cycle for all 21 locations instead of waiting for the next scheduled one. ⚠️ Not authenticated — each call makes ~42 external API requests (21 locations × WAQI + OWM).

### `GET /api/enforcement`
All 21 locations ranked by which needs enforcement attention first, with reasoning.

### `GET /api/alert/{location_id}`
Auto-generated official-style report and a Hinglish public advisory, from real current data for one location.

### `POST /api/alert/{location_id}/send-email?to_email=someone@example.com`
Emails the official report for one location. Only works if `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` are set in `backend/.env`; otherwise returns `sent: false` with an explanatory message.

### `GET /api/grap-compliance`
Time-tracked GRAP stage history — how long NCR has been in the current stage, and past transitions.

### `GET /api/whatif/{location_id}`
Estimated AQI impact of hypothetical reductions. Query parameters (all optional, `0`–`100`, default `0` except where noted):

| Param | Meaning |
|---|---|
| `traffic_reduction` | % reduction in traffic-source pollution |
| `industrial_reduction` | % reduction in industrial-source pollution |
| `construction_reduction` | % reduction in construction-source pollution |
| `waste_burning_reduction` | % reduction in waste-burning-source pollution |
| `background_reduction` | % reduction in background pollution |
| `wind_multiplier` | multiplier on current wind speed (default `1.0`) |

Returns `503` if no live reading exists yet for the location, `400` if any reduction value is outside 0–100.

---

## Error format

Failed requests return a standard FastAPI error body:

```json
{ "detail": "Unknown location_id" }
```

with an appropriate HTTP status code (`404`, `400`, `503`).
