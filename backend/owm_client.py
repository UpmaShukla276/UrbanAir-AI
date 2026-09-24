"""
owm_client.py
Fetches REAL data from OpenWeatherMap:
  - fetch_wind(): live wind speed + direction (for the wind indicator)
  - fetch_pollution_forecast(): OWM's own 4-day hourly pollutant forecast
    (a real forecasting product, not something we invent). We then run
    those forecasted concentrations through the official CPCB formula
    (see aqi_formula.py) to get a CPCB-comparable forecasted AQI.

Never fabricates a value: any failure returns None and the caller must
handle that honestly (e.g. "forecast unavailable") rather than guessing.
"""

import os
import requests

BASE_URL = "https://api.openweathermap.org/data/2.5"


def _get_api_key():
    return os.getenv("OWM_API_KEY")


def fetch_wind(lat: float, lon: float):
    """Returns {'speed_ms': float, 'deg': float} or None."""
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/weather",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None

    wind = data.get("wind", {})
    if "speed" not in wind:
        return None
    return {"speed_ms": wind.get("speed"), "deg": wind.get("deg")}


def fetch_pollution_forecast(lat: float, lon: float):
    """
    Returns a list of {timestamp_unix, components: {...ug/m3...}} for the
    next 4 days (hourly), straight from OpenWeatherMap, or None on failure.
    """
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/air_pollution/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key},
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None

    entries = data.get("list", [])
    return [
        {"timestamp_unix": e["dt"], "components": e["components"]}
        for e in entries
        if "dt" in e and "components" in e
    ]
