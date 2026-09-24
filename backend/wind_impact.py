"""
wind_impact.py

Answers: "this location's air is moving in direction X -- which other
monitored locations are downwind of it, and might see this pollution
arrive in the next couple of hours?"

This is real physics-based direction math (bearing + haversine distance)
applied to REAL live wind readings -- not a fabricated number. But be
honest about its limits: it does NOT model wind speed decay, mixing
height, or atmospheric stability. It's a directional estimate, the same
kind of simplification the project's own documentation calls out for
its What-If tool: useful for "which direction should we worry about,"
not a certified dispersion model (that needs tools like AERMOD/CALPUFF).
"""

import math

from locations import LOCATIONS, get_location

# How far downwind we consider "possibly affected soon" -- pollution
# transport beyond this in a couple of hours is unlikely at typical
# urban wind speeds. Adjustable, clearly a chosen assumption.
MAX_IMPACT_RADIUS_KM = 25
# How wide a cone around the exact downwind bearing counts as "downwind"
# (wind direction wobbles, it's never a perfect straight line).
BEARING_TOLERANCE_DEG = 40


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Compass bearing (0-360, 0=North) from point 1 TO point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def _angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def get_downwind_locations(source_location_id: str, wind_from_deg: float, wind_speed_ms: float):
    """
    wind_from_deg follows meteorological convention: the direction the
    wind is blowing FROM (this is what OpenWeatherMap and WAQI both
    report). Pollution travels TOWARD the opposite direction.
    """
    source = get_location(source_location_id)
    if not source or wind_from_deg is None:
        return []

    downwind_bearing = (wind_from_deg + 180) % 360
    results = []

    for loc in LOCATIONS:
        if loc["id"] == source_location_id:
            continue
        distance = haversine_km(source["lat"], source["lon"], loc["lat"], loc["lon"])
        if distance > MAX_IMPACT_RADIUS_KM:
            continue
        bearing_to_loc = bearing_deg(source["lat"], source["lon"], loc["lat"], loc["lon"])
        angle_off = _angle_diff(bearing_to_loc, downwind_bearing)
        is_downwind = angle_off <= BEARING_TOLERANCE_DEG

        eta_hours = None
        if is_downwind and wind_speed_ms and wind_speed_ms > 0:
            eta_hours = round((distance * 1000) / (wind_speed_ms * 3600), 1)

        results.append({
            "location": loc,
            "distance_km": round(distance, 1),
            "bearing_from_source_deg": round(bearing_to_loc, 1),
            "is_downwind": is_downwind,
            "estimated_arrival_hours": eta_hours,
        })

    results.sort(key=lambda r: (not r["is_downwind"], r["distance_km"]))
    return results


def get_upwind_locations(target_location_id: str, wind_from_deg: float, wind_speed_ms: float):
    """
    The reverse question: given THIS location's live wind, which other
    monitored locations sit upwind of it -- i.e. in the direction the
    wind is blowing FROM -- and so might currently be contributing to
    this location's pollution via wind transport?
    """
    target = get_location(target_location_id)
    if not target or wind_from_deg is None:
        return []

    results = []
    for loc in LOCATIONS:
        if loc["id"] == target_location_id:
            continue
        distance = haversine_km(target["lat"], target["lon"], loc["lat"], loc["lon"])
        if distance > MAX_IMPACT_RADIUS_KM:
            continue
        bearing_to_loc = bearing_deg(target["lat"], target["lon"], loc["lat"], loc["lon"])
        angle_off = _angle_diff(bearing_to_loc, wind_from_deg)
        is_upwind = angle_off <= BEARING_TOLERANCE_DEG

        travel_hours = None
        if is_upwind and wind_speed_ms and wind_speed_ms > 0:
            travel_hours = round((distance * 1000) / (wind_speed_ms * 3600), 1)

        results.append({
            "location": loc,
            "distance_km": round(distance, 1),
            "bearing_from_target_deg": round(bearing_to_loc, 1),
            "is_upwind": is_upwind,
            "estimated_travel_hours": travel_hours,
        })

    results.sort(key=lambda r: (not r["is_upwind"], r["distance_km"]))
    return results


_COMPASS_POINTS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

_REGION_NOTES = {
    "N": "the Himalayan foothills (Himachal/Uttarakhand) side -- usually cooler, cleaner air.",
    "NE": "the Uttarakhand/Nepal hills side -- typically cooler and relatively clean.",
    "E": "the western Uttar Pradesh plains -- can pick up pollution from that industrial belt.",
    "SE": "the eastern UP/Bihar side -- during the monsoon this direction often carries moist air.",
    "S": "the Haryana/southern side -- generally dry air.",
    "SW": "the Rajasthan/Gujarat side -- during the monsoon (Jun-Sep) this is the moisture-bearing direction from the Arabian Sea.",
    "W": "the Rajasthan/Thar Desert side -- often dry and dust-laden, which can push PM10 higher.",
    "NW": "the Punjab/Haryana/Rajasthan side -- often dry and dusty, and in Oct-Jan this is the direction stubble-burning smoke typically arrives from.",
}


def compass_direction(deg: float) -> str:
    idx = round(deg / 22.5) % 16
    return _COMPASS_POINTS[idx]


def wind_origin_summary(location_name: str, wind_from_deg: float, wind_speed_ms: float):
    if wind_from_deg is None:
        return None

    direction = compass_direction(wind_from_deg)
    coarse_map = {"N": "N", "NNE": "N", "NE": "NE", "ENE": "E", "E": "E", "ESE": "E",
                  "SE": "SE", "SSE": "S", "S": "S", "SSW": "S", "SW": "SW", "WSW": "W",
                  "W": "W", "WNW": "NW", "NW": "NW", "NNW": "N"}
    coarse = coarse_map.get(direction, direction)
    region_note = _REGION_NOTES.get(coarse, "a nearby direction.")

    speed_word = "gently" if wind_speed_ms and wind_speed_ms < 2 else "moderately" if wind_speed_ms and wind_speed_ms < 5 else "strongly"

    return (
        f"Right now, wind is blowing into {location_name} from {region_note} "
        f"It's moving {speed_word} ({wind_speed_ms} m/s if available). "
        f"This is a general seasonal/regional pattern, not an exact traced path."
    )