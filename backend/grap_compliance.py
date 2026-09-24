"""
grap_compliance.py
Tracks, using REAL data over REAL time (starting from whenever this
server first runs), how long Delhi NCR has actually stayed in each
GRAP stage, and logs every real transition. This is not backfilled or
simulated -- the log starts empty and grows only as genuine stage
changes are observed.
"""

from datetime import datetime, timezone

import database
from grap import get_grap_stage


def record_stage_if_changed(ncr_worst_aqi):
    """Call this after every real fetch cycle. Logs a new row only when
    the stage actually changes from the last logged one."""
    new_stage = get_grap_stage(ncr_worst_aqi)
    last = database.get_latest_grap_log()

    if last is None or last["stage"] != new_stage["stage"]:
        database.insert_grap_log(new_stage["stage"], new_stage["label"], ncr_worst_aqi)


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
        "in_this_stage_since": last["started_at"],
        "duration_hours": duration_hours,
        "history": database.get_grap_log_history(),
    }
