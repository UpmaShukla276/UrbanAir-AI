"""
enforcement.py
Ranks all monitored locations by how urgently they need enforcement
action right now, using REAL live AQI + REAL GRAP rules + the
transparent source-attribution estimate. This is decision-support
logic (documented rules), not a black-box score.
"""

from grap import get_grap_stage
from source_attribution import estimate_source_mix


def _priority_score(aqi):
    """Higher AQI = higher priority. Simple, transparent, matches GRAP philosophy."""
    if aqi is None:
        return -1
    return aqi


def build_enforcement_list(locations_with_readings):
    """
    locations_with_readings: list of dicts like the /api/current items
    (each has 'location' and 'reading').
    Returns a ranked list (highest priority first) with recommended actions.
    """
    ranked = []
    for item in locations_with_readings:
        loc = item["location"]
        reading = item.get("reading")
        aqi = reading["aqi"] if reading else None
        stage = get_grap_stage(aqi)
        pm25 = reading.get("pm25") if reading else None
        pm10 = reading.get("pm10") if reading else None
        source = estimate_source_mix(loc["zone_type"], pm25, pm10)

        # The single biggest contributing source drives the top recommended action.
        top_source = None
        if source.get("mix_percent"):
            top_source = max(source["mix_percent"], key=source["mix_percent"].get)

        recommended_actions = list(stage["actions"])  # official GRAP actions for this AQI
        if top_source == "construction":
            recommended_actions.insert(0, "Priority inspection: construction/demolition dust control at this site")
        elif top_source == "traffic":
            recommended_actions.insert(0, "Priority: traffic diversion / PUC enforcement drive at this location")
        elif top_source == "industrial":
            recommended_actions.insert(0, "Priority inspection: industrial emission compliance check")
        elif top_source == "waste_burning":
            recommended_actions.insert(0, "Priority: anti-open-burning patrol at this location")

        ranked.append({
            "location": loc,
            "aqi": aqi,
            "grap_stage": stage["stage"],
            "grap_label": stage["label"],
            "top_estimated_source": top_source,
            "priority_score": _priority_score(aqi),
            "recommended_actions": recommended_actions,
            "is_live": item.get("is_live", False),
        })

    ranked.sort(key=lambda r: r["priority_score"], reverse=True)
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i
    return ranked
