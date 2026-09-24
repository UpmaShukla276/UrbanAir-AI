"""
grap_compliance.py
Tracks, using REAL data over REAL time, how long Delhi NCR has stayed
in each GRAP stage, and which location triggered it.
"""

from datetime import datetime, timezone

import database
from grap import get_grap_stage


def record_stage_if_changed(ncr_worst_aqi, worst_location_id=None, worst_location_name=None):
    new_stage = get_grap_stage(ncr_worst_aqi)
    last = database.get_latest_grap_log()

    if last is None or last["stage"] != new_stage["stage"]:
        database.insert_grap_log(new_stage["stage"], new_stage["label"], ncr_worst_aqi, worst_location_id, worst_location_name)


def get_compliance_status():
    last = database.get_latest_grap_log()
    if not last:
        return {
            "current_stage": None,
            "message": "No GRAP stage recorded yet -- waiting for the first live fetch cycle.",
            "history": [],
        }

    started = datetime.fromisoformat(last["started_at"])
    duration_hours = round((datetime.now(timezone.utc) - started).total_seconds() / 3600, 2)

    return {
        "current_stage": last["stage"],
        "current_label": last["label"],
        "ncr_worst_aqi_at_entry": last["ncr_worst_aqi"],
        "worst_location_name": last.get("worst_location_name"),
        "in_this_stage_since": last["started_at"],
        "duration_hours": duration_hours,
        "history": database.get_grap_log_history(),
    }