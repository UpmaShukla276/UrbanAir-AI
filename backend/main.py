"""
main.py -- UrbanAir AI backend

Runs a FastAPI server that:
1. On startup, fetches REAL live AQI + wind data for every monitored
   Delhi NCR location (WAQI for AQI/pollutants, OpenWeatherMap for wind)
   and stores it in a local SQLite database.
2. Repeats that fetch automatically every FETCH_INTERVAL_MINUTES, building
   a genuine 12-hour (and beyond) historical trend over real time.
3. Exposes REST endpoints for the frontend dashboard -- current data,
   trend, source attribution, GRAP stage, real pollutant-based forecast,
   and wind info -- for EVERY monitored location (all 21).

No fabricated numbers anywhere: if a live fetch fails, we do not invent
a value -- we keep serving the last known real reading flagged as
not-live, or return "unavailable" and say why.
"""

import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import database
from locations import LOCATIONS, get_location
from waqi_client import fetch_live_reading
from owm_client import fetch_wind, fetch_pollution_forecast
from aqi_formula import calculate_aqi, calculate_aqi_best_effort
from health_advisory import get_band
from grap import get_grap_stage
from source_attribution import estimate_source_mix
from wind_impact import get_downwind_locations, get_upwind_locations, haversine_km, wind_origin_summary
from enforcement import build_enforcement_list
from alerts import build_official_report, build_public_advisory_hinglish, send_email_alert
from grap_compliance import record_stage_if_changed, get_compliance_status
from whatif import simulate_reduction

load_dotenv()

FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "15"))

app = FastAPI(title="UrbanAir AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_background_task = None


async def fetch_all_locations_once():
    """One real fetch cycle across every monitored location: AQI (WAQI) + wind (OWM)."""
    results = {"fetched": [], "unavailable": []}
    for loc in LOCATIONS:
        live = fetch_live_reading(loc["lat"], loc["lon"])
        wind = fetch_wind(loc["lat"], loc["lon"])

        if live and (live.get("pm25") is not None or live.get("pm10") is not None):
            station_geo = live.get("station_geo") or [None, None]
            cpcb_result = calculate_aqi_best_effort({
                "pm10": live.get("pm10"),
                "pm2_5": live.get("pm25"),
                "no2": live.get("no2"),
                "so2": live.get("so2"),
                "o3": live.get("o3"),
                "co": live.get("co"),
            })
            database.insert_reading(
                location_id=loc["id"],
                aqi=live.get("aqi_waqi_reported"),
                pm25=live.get("pm25"),
                pm10=live.get("pm10"),
                wind_speed=(wind["speed_ms"] if wind else live.get("wind_speed")),
                wind_deg=(wind["deg"] if wind else None),
                station_name=live.get("station_name"),
                station_lat=station_geo[0] if len(station_geo) > 0 else None,
                station_lon=station_geo[1] if len(station_geo) > 1 else None,
                no2=live.get("no2"),
                so2=live.get("so2"),
                o3=live.get("o3"),
                co=live.get("co"),
                dominant_pollutant=cpcb_result.get("dominant_pollutant"),
                official_compliant=False,
                source="waqi_live",
            )
            results["fetched"].append(loc["id"])
        else:
            results["unavailable"].append(loc["id"])

    worst_aqi = None
    worst_location_name = None
    worst_location_id = None
    for loc in LOCATIONS:
        reading = database.get_latest_reading(loc["id"])
        if reading and reading["aqi"] is not None:
            if worst_aqi is None or reading["aqi"] > worst_aqi:
                worst_aqi = reading["aqi"]
                worst_location_name = loc["name"]
                worst_location_id = loc["id"]
    record_stage_if_changed(worst_aqi, worst_location_id, worst_location_name)

    return results


async def _background_fetch_loop():
    while True:
        try:
            await fetch_all_locations_once()
        except Exception as e:
            print(f"[fetch loop] error: {e}")
        await asyncio.sleep(FETCH_INTERVAL_MINUTES * 60)


@app.on_event("startup")
async def on_startup():
    database.init_db()
    if not os.getenv("WAQI_TOKEN"):
        print("WARNING: WAQI_TOKEN not set in .env -- live AQI fetch will not work until you add it.")
    if not os.getenv("OWM_API_KEY"):
        print("WARNING: OWM_API_KEY not set in .env -- wind + forecast will not work until you add it.")
    global _background_task
    _background_task = asyncio.create_task(_background_fetch_loop())


def _minutes_since(iso_timestamp: str) -> float:
    then = datetime.fromisoformat(iso_timestamp)
    now = datetime.now(timezone.utc)
    return (now - then).total_seconds() / 60


def _build_current_payload(loc: dict):
    reading = database.get_latest_reading(loc["id"])
    if not reading:
        return {
            "location": loc,
            "reading": None,
            "band": None,
            "is_live": False,
            "message": "No data fetched yet -- check WAQI_TOKEN / OWM_API_KEY in .env and server logs.",
        }
    age_minutes = _minutes_since(reading["fetched_at"])
    band = get_band(reading["aqi"])
    station_distance_km = None
    if reading.get("station_lat") is not None and reading.get("station_lon") is not None:
        station_distance_km = round(
            haversine_km(loc["lat"], loc["lon"], reading["station_lat"], reading["station_lon"]), 2
        )
    return {
        "location": loc,
        "reading": reading,
        "band": band,
        "is_live": age_minutes <= FETCH_INTERVAL_MINUTES * 1.5,
        "data_age_minutes": round(age_minutes, 1),
        "station_distance_km": station_distance_km,
        "data_note": (
            f"Live reading is from the real CPCB/monitoring station '{reading.get('station_name')}', "
            f"~{station_distance_km} km from this point -- the nearest real station to it."
            if station_distance_km is not None else None
        ),
        "aqi_methodology": "Live figure reported directly by WAQI's real-time monitoring network (aqicn.org), from the nearest official CPCB station.",
    }


@app.get("/")
def root():
    return {"status": "ok", "service": "UrbanAir AI Backend"}


@app.get("/api/locations")
def list_locations():
    """All 21 monitored Delhi NCR locations."""
    return LOCATIONS


@app.get("/api/current")
def current_all():
    """Live snapshot (AQI + wind) for all 21 monitored NCR locations."""
    return [_build_current_payload(loc) for loc in LOCATIONS]


@app.get("/api/current/{location_id}")
def current_one(location_id: str):
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")
    return _build_current_payload(loc)


@app.get("/api/trend/{location_id}")
def trend(location_id: str, hours: int = 12):
    """Real historical trend for one location, built from stored live readings."""
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")
    rows = database.get_trend(location_id, hours=hours)
    return {"location": loc, "hours": hours, "points": rows}


@app.get("/api/source-attribution/{location_id}")
def source_attribution(location_id: str):
    """Transparent rule-based estimate of pollution source mix for one location."""
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")
    reading = database.get_latest_reading(location_id)
    pm25 = reading["pm25"] if reading else None
    pm10 = reading["pm10"] if reading else None
    estimate = estimate_source_mix(loc["zone_type"], pm25, pm10)
    return {"location": loc, **estimate}


@app.get("/api/grap/{location_id}")
def grap_for_location(location_id: str):
    """Official CAQM GRAP stage + mandated actions for one location's current AQI."""
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")
    reading = database.get_latest_reading(location_id)
    aqi = reading["aqi"] if reading else None
    stage = get_grap_stage(aqi)
    return {"location": loc, "aqi": aqi, "grap": stage}


@app.get("/api/grap")
def grap_overall():
    """Worst-case GRAP stage across all monitored points -- how CAQM actually decides it."""
    worst_aqi = None
    worst_location_name = None
    for loc in LOCATIONS:
        reading = database.get_latest_reading(loc["id"])
        if reading and reading["aqi"] is not None:
            if worst_aqi is None or reading["aqi"] > worst_aqi:
                worst_aqi = reading["aqi"]
                worst_location_name = loc["name"]
    stage = get_grap_stage(worst_aqi)
    return {"ncr_worst_aqi": worst_aqi, "worst_location_name": worst_location_name, "grap": stage}


@app.get("/api/forecast/{location_id}")
def forecast(location_id: str):
    """
    Real pollutant forecast (OpenWeatherMap's own 4-day hourly model) run
    through the official CPCB formula to get a CPCB-comparable AQI
    forecast for THIS specific location. Works for any of the 21 points.
    """
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    raw_forecast = fetch_pollution_forecast(loc["lat"], loc["lon"])
    if raw_forecast is None:
        raise HTTPException(
            status_code=503,
            detail="Forecast unavailable -- check OWM_API_KEY in .env (new keys can take up to a couple of hours to activate).",
        )

    points = []
    for entry in raw_forecast:
        c = entry["components"]
        result = calculate_aqi({
            "pm10": c.get("pm10"),
            "pm2_5": c.get("pm2_5"),
            "no2": c.get("no2"),
            "so2": c.get("so2"),
            "nh3": c.get("nh3"),
            "o3": c.get("o3"),
            "co": c.get("co"),
        })
        points.append({
            "timestamp_unix": entry["timestamp_unix"],
            "timestamp_iso": datetime.fromtimestamp(entry["timestamp_unix"], tz=timezone.utc).isoformat(),
            "aqi": result.get("aqi"),
            "dominant_pollutant": result.get("dominant_pollutant"),
            "band": get_band(result.get("aqi")) if result.get("aqi") is not None else None,
        })

    def _closest_to(hours_ahead):
        target = datetime.now(timezone.utc).timestamp() + hours_ahead * 3600
        if not points:
            return None
        return min(points, key=lambda p: abs(p["timestamp_unix"] - target))

    return {
        "location": loc,
        "source": "OpenWeatherMap pollutant forecast -> official CPCB AQI formula",
        "hourly": points,
        "snapshot_24h": _closest_to(24),
        "snapshot_48h": _closest_to(48),
        "snapshot_72h": _closest_to(72),
    }


@app.get("/api/wind-impact/{location_id}")
def wind_impact(location_id: str):
    """
    Live wind for this location, described in plain language --
    where it's coming from and what that generally tends to mean.
    """
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    reading = database.get_latest_reading(location_id)
    if not reading or reading.get("wind_deg") is None:
        raise HTTPException(
            status_code=503,
            detail="No live wind direction available yet for this location -- check OWM_API_KEY and wait for the next fetch cycle.",
        )

    summary = wind_origin_summary(loc["name"], reading["wind_deg"], reading.get("wind_speed"))

    return {
        "location": loc,
        "wind_speed_ms": reading.get("wind_speed"),
        "wind_from_deg": reading.get("wind_deg"),
        "summary": summary,
    }


@app.post("/api/refresh")
async def manual_refresh():
    """Trigger an immediate real fetch cycle instead of waiting for the timer."""
    result = await fetch_all_locations_once()
    return result


@app.get("/api/enforcement")
def enforcement_list():
    """
    Ranked priority list across all 21 locations -- which one needs
    enforcement attention first, and what to do there.
    """
    current = [_build_current_payload(loc) for loc in LOCATIONS]
    return build_enforcement_list(current)


@app.get("/api/alert/{location_id}")
def alert_for_location(location_id: str):
    """Generates an official-style report and a Hinglish public advisory from real current data."""
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    reading = database.get_latest_reading(location_id)
    aqi = reading["aqi"] if reading else None
    band = get_band(aqi) if aqi is not None else None
    stage = get_grap_stage(aqi)
    pm25 = reading.get("pm25") if reading else None
    pm10 = reading.get("pm10") if reading else None
    source_estimate = estimate_source_mix(loc["zone_type"], pm25, pm10)

    return {
        "location": loc,
        "official_report": build_official_report(loc, aqi, band, stage, source_estimate),
        "public_advisory_hinglish": build_public_advisory_hinglish(loc, aqi, band),
    }


@app.post("/api/alert/{location_id}/send-email")
def send_alert_email(location_id: str, to_email: str):
    """
    Optional: actually emails the official report, ONLY if SMTP_HOST /
    SMTP_PORT / SMTP_USER / SMTP_PASSWORD are set in .env.
    """
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    reading = database.get_latest_reading(location_id)
    aqi = reading["aqi"] if reading else None
    band = get_band(aqi) if aqi is not None else None
    stage = get_grap_stage(aqi)
    pm25 = reading.get("pm25") if reading else None
    pm10 = reading.get("pm10") if reading else None
    source_estimate = estimate_source_mix(loc["zone_type"], pm25, pm10)
    report = build_official_report(loc, aqi, band, stage, source_estimate)

    success, message = send_email_alert(to_email, f"UrbanAir AI Alert -- {loc['name']}", report)
    return {"sent": success, "message": message}


@app.get("/api/grap-compliance")
def grap_compliance():
    """Real, time-tracked GRAP stage history and how long NCR has been in the current stage."""
    return get_compliance_status()


@app.get("/api/whatif/{location_id}")
def whatif(
    location_id: str,
    traffic_reduction: float = 0,
    industrial_reduction: float = 0,
    construction_reduction: float = 0,
    waste_burning_reduction: float = 0,
    background_reduction: float = 0,
    wind_multiplier: float = 1.0,
):
    """
    Transparent estimate with 6 independent sliders -- one per pollution
    source, plus wind.
    """
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location_id")

    reductions = {
        "traffic": traffic_reduction,
        "industrial": industrial_reduction,
        "construction": construction_reduction,
        "waste_burning": waste_burning_reduction,
        "background": background_reduction,
    }
    for key, val in reductions.items():
        if not (0 <= val <= 100):
            raise HTTPException(status_code=400, detail=f"{key}_reduction must be between 0 and 100")

    reading = database.get_latest_reading(location_id)
    if not reading:
        raise HTTPException(status_code=503, detail="No live reading yet for this location.")

    result = simulate_reduction(
        loc, reading.get("aqi"), reading.get("pm25"), reading.get("pm10"),
        reductions, wind_multiplier,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result