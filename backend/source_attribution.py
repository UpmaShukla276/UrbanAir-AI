"""
source_attribution.py

IMPORTANT (read this before trusting the numbers):
No agency in the world -- not CPCB, not SAFAR, not CAQM -- has a real
sensor that measures "how much of today's pollution came from traffic
vs industry vs construction" at a specific point. That ground truth
does not exist. What official bodies use instead is documented,
rule-based reasoning combined with known emission-inventory shares.

This module is exactly that: a transparent, documented estimate.
Every weight below is a stated assumption, not a measurement.
The API always returns this data tagged as "estimated" -- never
present it to an official as a measured fact.
"""

from datetime import datetime, timezone

# Base assumption: typical pollution-source mix by zone type.
# (Broadly consistent with CPCB/TERI emission-inventory studies for Delhi NCR,
# used here as a starting assumption -- not a live measurement.)
ZONE_BASE_MIX = {
    "traffic_heavy": {"traffic": 55, "industrial": 10, "construction": 10, "waste_burning": 5, "background": 20},
    "industrial":    {"traffic": 20, "industrial": 45, "construction": 10, "waste_burning": 5, "background": 20},
    "residential":   {"traffic": 30, "industrial": 10, "construction": 15, "waste_burning": 10, "background": 35},
    "green_zone":    {"traffic": 20, "industrial": 5,  "construction": 5,  "waste_burning": 5,  "background": 65},
    "mixed":         {"traffic": 30, "industrial": 20, "construction": 15, "waste_burning": 10, "background": 25},
}


def estimate_source_mix(zone_type: str, pm25, pm10):
    """
    Adjusts the zone's base assumption slightly using the live PM2.5/PM10
    ratio (a real, documented atmospheric-science signal):
    - PM10 >> PM2.5 usually points to coarse dust (construction/road dust)
    - PM2.5 dominant usually points to combustion sources (traffic/burning)
    Returns percentages that always sum to 100, plus the reasoning used.
    """
    mix = dict(ZONE_BASE_MIX.get(zone_type, ZONE_BASE_MIX["mixed"]))
    reasoning = [f"Base assumption for zone type '{zone_type}'."]

    if pm25 is not None and pm10 is not None and pm10 > 0:
        ratio = pm25 / pm10
        if ratio < 0.4:
            # coarse-dominant -> shift weight toward construction/dust
            shift = 8
            mix["construction"] += shift
            mix["traffic"] = max(5, mix["traffic"] - shift)
            reasoning.append("PM2.5/PM10 ratio is low -> coarse dust signal, shifted weight toward construction/road dust.")
        elif ratio > 0.75:
            shift = 6
            mix["traffic"] += shift
            mix["construction"] = max(5, mix["construction"] - shift)
            reasoning.append("PM2.5/PM10 ratio is high -> fine combustion particles, shifted weight toward traffic/burning.")

    # Seasonal stubble-burning heuristic (Oct-Jan, well-documented seasonal pattern in NCR)
    month = datetime.now(timezone.utc).month
    if month in (10, 11, 12, 1):
        add = 10
        mix["waste_burning"] += add
        mix["background"] = max(5, mix["background"] - add)
        reasoning.append("Oct-Jan stubble-burning season -> added weight to waste_burning.")

    total = sum(mix.values())
    normalized = {k: round(v * 100 / total, 1) for k, v in mix.items()}

    return {
        "estimated": True,
        "methodology": "Rule-based assumption, not a direct measurement. See reasoning.",
        "reasoning": reasoning,
        "mix_percent": normalized,
    }
