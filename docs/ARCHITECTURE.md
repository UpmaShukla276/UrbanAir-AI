# Architecture

## Overview

UrbanAir AI has two parts: a FastAPI backend that continuously pulls real air-quality and weather data, stores it, and derives everything else from it; and a React + Vite dashboard that reads that data over a REST API.

```
   WAQI (aqicn.org)         OpenWeatherMap
   live AQI + pollutants     wind + 4-day pollutant forecast
          |                          |
          v                          v
   waqi_client.py             owm_client.py
          |                          |
          +------------+-------------+
                       |
                       v
         fetch_all_locations_once()   <-- runs on startup, then every
              (main.py)                   FETCH_INTERVAL_MINUTES
                       |
                       v
                database.py  (SQLite: urbanair.db)
                       |
        +-----------+--+-----------+--------------------+
        v           v              v                    v
   aqi_formula.py  grap.py   source_attribution.py  wind_impact.py
   (CPCB formula)  (CAQM     (rule-based estimate,   (haversine,
                    stage)    tagged "estimated")     plain-language
                                                       wind summary)
        |           |              |                    |
        +-----+-----+------+-------+--------------------+
                    |
                    v
              FastAPI endpoints (main.py)
                    |
                    v
         React dashboard (frontend/src)
         Leaflet map + Recharts + component panels
```

## Backend flow

1. **On startup** (`main.py` → `on_startup`), the app initializes the SQLite database and kicks off a background asyncio loop.
2. **Every fetch cycle** (`fetch_all_locations_once`), for each of the 21 monitored locations in `locations.py`:
   - `waqi_client.fetch_live_reading` gets the live AQI, pollutant concentrations, and station metadata from WAQI.
   - `owm_client.fetch_wind` gets live wind speed/direction from OpenWeatherMap.
   - `aqi_formula.calculate_aqi_best_effort` recomputes a CPCB-comparable AQI from whichever pollutants are actually present.
   - The combined reading is written to SQLite via `database.insert_reading`.
   - If a location's fetch fails, it's recorded as unavailable rather than backfilled with a guessed value — the API later reports the last known reading, flagged as not live.
3. **After each cycle**, the worst AQI across all locations is used to update the GRAP stage history (`grap_compliance.record_stage_if_changed`).
4. **On each API request**, endpoints read from SQLite and layer on derived logic (AQI band, GRAP stage, source-mix estimate, distance to the real station, forecast, etc.) rather than storing pre-computed derived fields — so the derived logic always reflects the current code, not a stale snapshot.

## Frontend flow

- `frontend/src/api.js` is the single point of contact with the backend — every dashboard panel calls through it, and it reads `VITE_API_BASE_URL` so the same build works against local or deployed backends.
- `App.jsx` composes the panels: `MapView` (Leaflet), `Overview`, `Trend` and `Forecast` (Recharts), `GrapBanner`, `SourceMix`, `Wind`, `Enforcement`, `Compliance`, `Alerts`, and `WhatIf`.
- Each panel is responsible for its own data fetch + loading/error state, keeping panels independent of one another.

## Data honesty by design

Two things run through the whole system on purpose:
- **No invented numbers.** A failed live fetch results in "last known reading, flagged not-live" or an explicit "unavailable" — never a fabricated value.
- **Estimates are labeled as estimates.** Source attribution is a transparent, documented rule-based calculation (see `docs/METHODOLOGY.md`), and the API always returns it tagged as an estimate rather than presenting it as measured fact.
