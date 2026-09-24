"""
waqi_client.py
Fetches REAL live air quality data from the WAQI (World Air Quality Index)
public API: https://aqicn.org/api/

We query by geographic coordinates (geo:lat;lon) so it always finds the
nearest real official monitoring station to that point, rather than
depending on guessing exact station names.
"""

import os
import requests

WAQI_BASE_URL = "https://api.waqi.info"


def fetch_live_reading(lat: float, lon: float):
    """
    Returns a dict: {aqi, pm25, pm10, wind_speed, station_name, measured_at}
    or None if the live call failed / no token configured.
    Never fabricates a value -- if WAQI has no data, we return None and the
    caller must mark the reading as 'unavailable' rather than invent a number.
    """
    token = os.getenv("WAQI_TOKEN")
    if not token:
        return None

    url = f"{WAQI_BASE_URL}/feed/geo:{lat};{lon}/"
    try:
        resp = requests.get(url, params={"token": token}, timeout=6)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException:
        return None

    if payload.get("status") != "ok":
        return None

    data = payload.get("data", {})
    iaqi = data.get("iaqi", {})

    def _v(key):
        entry = iaqi.get(key)
        return entry.get("v") if entry else None

    return {
        "aqi_waqi_reported": data.get("aqi"),
        "pm25": _v("pm25"),
        "pm10": _v("pm10"),
        "no2": _v("no2"),
        "so2": _v("so2"),
        "o3": _v("o3"),
        "co": _v("co"),
        "wind_speed": _v("w"),
        "station_name": (data.get("city") or {}).get("name"),
        "station_geo": (data.get("city") or {}).get("geo"),
        "measured_at": (data.get("time") or {}).get("s"),
    }


def calculate_aqi_best_effort(pollutants_ugm3: dict):
    """
    Same CPCB formula, but does NOT enforce CPCB's minimum-3-pollutants
    rule -- used for the headline AQI shown across the app so it reads
    consistently even when WAQI only exposes PM2.5/PM10 for a station.
    """
    strict = calculate_aqi(pollutants_ugm3)
    if strict.get("aqi") is not None:
        strict["official_compliant"] = True
        return strict

    sub_indices = strict.get("sub_indices", {})
    if not sub_indices:
        return {"aqi": None, "sub_indices": {}, "official_compliant": False,
                "reason": "No pollutant concentrations available."}

    dominant = max(sub_indices, key=sub_indices.get)
    return {
        "aqi": round(sub_indices[dominant]),
        "dominant_pollutant": dominant,
        "sub_indices": sub_indices,
        "official_compliant": False,
        "reason": strict.get("reason"),
    }
