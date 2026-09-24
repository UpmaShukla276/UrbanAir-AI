from source_attribution import estimate_source_mix

WIND_MULTIPLIER_MIN = 0.3
WIND_MULTIPLIER_MAX = 3.0
SOURCE_KEYS = ["traffic", "industrial", "construction", "waste_burning", "background"]


def simulate_reduction(location, current_aqi, current_pm25, current_pm10, reductions, wind_multiplier=1.0):
    estimate = estimate_source_mix(location["zone_type"], current_pm25, current_pm10)
    mix = estimate.get("mix_percent", {})

    wind_multiplier = max(WIND_MULTIPLIER_MIN, min(WIND_MULTIPLIER_MAX, wind_multiplier))

    source_factor = 1.0
    applied = {}
    for key in SOURCE_KEYS:
        pct = max(0, min(100, reductions.get(key, 0) or 0))
        share = mix.get(key, 0)
        cut = (share / 100.0) * (pct / 100.0)
        source_factor *= (1 - cut)
        if pct > 0:
            applied[key] = {"reduction_percent": pct, "estimated_share_percent": share}

    overall_factor = source_factor / wind_multiplier

    def apply(pm):
        if pm is None:
            return None
        return round(pm * overall_factor, 1)

    new_pm25 = apply(current_pm25)
    new_pm10 = apply(current_pm10)

    simulated_aqi = round(current_aqi * overall_factor) if current_aqi is not None else None

    wind_note = (
        "no change to wind" if wind_multiplier == 1.0
        else f"wind scaled to {wind_multiplier}x current -- "
             f"{'more dispersion, lower concentration' if wind_multiplier > 1 else 'calmer air, higher concentration'}"
    )

    if applied:
        parts = [f"{k} down {v['reduction_percent']}% (est. {v['estimated_share_percent']}% share)" for k, v in applied.items()]
        source_note = "; ".join(parts)
    else:
        source_note = "no source reductions applied"

    return {
        "location": location,
        "parameters": {
            "reductions": {k: reductions.get(k, 0) or 0 for k in SOURCE_KEYS},
            "wind_multiplier": wind_multiplier,
        },
        "methodology": (
            "Current AQI is the live figure (same as Overview) -- not recalculated. "
            f"Simulated AQI scales that real number down using: {source_note}; {wind_note}. "
            "Not a validated atmospheric dispersion model (that requires tools like AERMOD/CALPUFF)."
        ),
        "current_pm25": current_pm25,
        "current_pm10": current_pm10,
        "simulated_pm25": new_pm25,
        "simulated_pm10": new_pm10,
        "current_estimated_aqi": current_aqi,
        "simulated_estimated_aqi": simulated_aqi,
        "estimated_aqi_change": (
            simulated_aqi - current_aqi if (current_aqi is not None and simulated_aqi is not None) else None
        ),
    }