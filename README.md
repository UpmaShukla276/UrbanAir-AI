# UrbanAir AI

**Live air quality, GRAP tracking and enforcement decision-support for Delhi NCR.**

[Live demo](https://urban-air-ai-kappa.vercel.app/) · [Demo video]([DEMO_VIDEO_URL]) · [API reference](docs/API.md) · [How the numbers are made](docs/METHODOLOGY.md)

![UrbanAir AI dashboard](docs/screenshots/overview.png)


---

## Why we built this

Every winter, Delhi NCR's air turns into a daily headline. The AQI number is easy to find. What's harder is answering the questions that come right after it: *Which area needs attention first? What is the government plan actually asking for at this level? Where is the smoke likely coming from? What should an ordinary person do today?*

A lot of AQI apps stop at showing the number. UrbanAir AI tries to go one step further and serve two kinds of people at once:

- **Officials and enforcement teams**, who need to decide where to send inspectors and which GRAP actions apply.
- **Citizens**, who would rather read a plain advisory in Hinglish than a bulletin.

It watches 21 locations across Delhi, Noida, Gurugram, Ghaziabad and Faridabad, refreshes them on a schedule, and builds its own history as it runs.

## What you can do with it

The dashboard has nine views, all driven by the location you pick in the sidebar (or by clicking a marker on the map).

| View | What it shows |
|---|---|
| **Overview & Map** | Live AQI for all 21 locations on an OpenStreetMap map, coloured by CPCB category, with data freshness and the distance to the real station behind each reading |
| **12h Trend** | The reading history for a location, built from the data the server has actually collected |
| **Source Mix** | An *estimated* split of pollution sources (traffic, industry, construction, waste burning, background), clearly labelled as an estimate |
| **Forecast** | A 24 / 48 / 72-hour AQI outlook for the selected location |
| **Wind & Impact** | Live wind speed and direction, explained in plain language (where the air is coming from and what that usually means) |
| **Enforcement** | All 21 locations ranked by urgency, with recommended actions for each |
| **Alerts** | An official-style report plus a Hinglish public advisory, with optional email sending |
| **GRAP Compliance** | The current GRAP stage for NCR, how long it has been in that stage, and the history of stage changes |
| **What-If Simulator** | Sliders for cutting each pollution source and changing wind, to see the rough effect on AQI |

A GRAP banner at the top of every view shows the current NCR-wide stage.

## A note on honesty

The most important rule in this codebase is that **it never invents a number.** If a live fetch fails, we keep serving the last real reading and flag it as not live, or we say the data is unavailable. Nothing is filled in with a guess.

Different numbers in the app have different levels of certainty, and we label them that way:

| Kind | Examples | Where it comes from |
|---|---|---|
| **Measured** | AQI, PM2.5, PM10, wind speed and direction | Real monitoring stations (via WAQI) and OpenWeatherMap |
| **Computed with an official formula** | Forecast AQI, health category, GRAP stage | The CPCB AQI formula and published CPCB/CAQM tables |
| **Estimated** | Source mix, what-if results, enforcement priorities | Documented rule-based logic, always tagged as estimates |

Details for every one of these are in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Tech stack

- **Backend:** Python, FastAPI, SQLite, `requests`, `python-dotenv`
- **Frontend:** React 18, Vite, Leaflet / react-leaflet, Recharts, lucide-react
- **Data:** [WAQI](https://aqicn.org/api/) for live air quality, [OpenWeatherMap](https://openweathermap.org/api) for wind and pollutant forecasts, OpenStreetMap for map tiles

## How it works, briefly

1. When the backend starts, it creates the SQLite database and launches a background loop.
2. Every `FETCH_INTERVAL_MINUTES` (default 15), the loop fetches live AQI from WAQI and wind from OpenWeatherMap for every location, and stores each real reading.
3. After each cycle it looks at the worst AQI across all locations and records a new entry whenever the NCR-wide GRAP stage changes.
4. The React dashboard calls the REST API and renders everything from what is stored, so the trend and compliance views get richer the longer the server runs.

A diagram and a fuller walkthrough are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run it locally

You'll need Python 3.10+ and Node.js 18+, plus two free API keys:

- a **WAQI token** from <https://aqicn.org/data-platform/token/>
- an **OpenWeatherMap API key** from <https://openweathermap.org/api> (newly created keys can take a while to activate, so if the forecast shows an error right after signing up, give it a bit)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then open .env and paste your two keys
uvicorn main:app --reload
```

The API is now at <http://127.0.0.1:8000>. FastAPI also serves interactive docs at `/docs`. The first data appears after the first fetch cycle finishes, which takes a few seconds. You can also trigger it yourself with `POST /api/refresh`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env            # only needed if your backend isn't on 127.0.0.1:8000
npm run dev
```

Open <http://localhost:5173>.

## Configuration

Backend settings live in `backend/.env` (see `backend/.env.example`):

| Variable | Required | Purpose |
|---|---|---|
| `WAQI_TOKEN` | Yes | Live AQI and pollutant data |
| `OWM_API_KEY` | Yes | Wind data and the pollutant forecast |
| `FETCH_INTERVAL_MINUTES` | No (default `15`) | How often the background fetch runs |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | No | Only needed if you want the Alerts view to send real emails |

Frontend setting, in `frontend/.env`:

| Variable | Required | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | No (default `http://127.0.0.1:8000`) | URL of the backend the dashboard talks to |

> **Quota heads-up:** at the default 15-minute interval, the server makes 21 WAQI and 21 OpenWeatherMap calls per cycle, which is roughly 2,000 OpenWeatherMap calls a day. If you're on a free tier and hit limits, raise `FETCH_INTERVAL_MINUTES`.

## Deployment notes

The backend is deployed on [BACKEND_HOST] and the frontend on [FRONTEND_HOST]. If you deploy your own copy, three things are worth knowing:

- `VITE_API_BASE_URL` is read **at build time** by Vite, so set it in your frontend host's environment settings *before* building, and rebuild if the backend URL changes.
- Set `WAQI_TOKEN` and `OWM_API_KEY` as environment variables on the backend host. Never commit a real `.env`.
- The database is a single SQLite file (`backend/urbanair.db`). On hosts with an ephemeral filesystem it is wiped on every redeploy or restart, which resets the trend and GRAP history. Attach a persistent disk, or move to a hosted database, if you want history to survive.

## Project structure

```
UrbanAir-AI/
├── backend/
│   ├── main.py                # FastAPI app, background fetch loop, all endpoints
│   ├── waqi_client.py         # Live AQI + pollutants from WAQI
│   ├── owm_client.py          # Wind + pollutant forecast from OpenWeatherMap
│   ├── aqi_formula.py         # Official CPCB AQI formula
│   ├── health_advisory.py     # CPCB categories and health advisories
│   ├── grap.py                # GRAP stages and actions
│   ├── grap_compliance.py     # Stage-change tracking over time
│   ├── source_attribution.py  # Rule-based pollution source estimate
│   ├── wind_impact.py         # Wind direction maths and plain-language summary
│   ├── whatif.py              # What-if simulator
│   ├── enforcement.py         # Location priority ranking
│   ├── alerts.py              # Official report, Hinglish advisory, email
│   ├── locations.py           # The 21 monitored locations
│   ├── database.py            # SQLite access
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Layout and tab routing
│   │   ├── api.js             # API client
│   │   ├── ui.jsx             # Shared UI pieces
│   │   └── components/        # One component per dashboard view
│   ├── package.json
│   └── vite.config.js
└── docs/                      # Architecture, methodology, and API documentation
```

## Known limitations

We would rather you hear these from us:

- **Stations, not street corners.** Each location is matched to the nearest real station, which can be several kilometres away. The dashboard shows that distance. Two nearby locations can end up reading the same station.
- **Source mix is an estimate.** No agency measures "how much of this air came from traffic". Our split is a documented rule-based assumption adjusted by the PM2.5/PM10 ratio and the season, and it is labelled as an estimate everywhere it appears.
- **The What-If simulator is a simple proportional model.** It is useful for "which lever matters more", not a validated dispersion model.
- **Wind info is directional and general**, not a traced pollution path.
- **History starts when the server starts.** The trend only covers what the server has collected itself, and on ephemeral hosting it resets on redeploy.
- **No authentication yet.** The API is open (CORS allows all origins), including `POST /api/refresh` (the dashboard's "Refresh now" button), which triggers a full fetch cycle. That's fine for a demo but should be locked down for real use.
- **GRAP thresholds should be re-checked.** The stage ranges in `backend/grap.py` reflect the plan as we encoded it. CAQM revises GRAP from time to time, so verify against the latest official notification before relying on it operationally.

## Data sources and credits

- Air quality data: [World Air Quality Index Project (WAQI)](https://aqicn.org/), sourced from official monitoring stations
- Wind and pollutant forecasts: [OpenWeatherMap](https://openweathermap.org/)
- Map tiles: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
- AQI categories and formula: Central Pollution Control Board (CPCB), National Air Quality Index
- Graded Response Action Plan: Commission for Air Quality Management (CAQM)

## License

Released under the [MIT License](LICENSE).
