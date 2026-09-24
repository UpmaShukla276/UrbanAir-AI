"""
aqi_formula.py

The REAL, official Indian CPCB National Air Quality Index formula (2014).
Source: CPCB "National Air Quality Index" report + CPCB breakpoint table.

This is a deterministic piecewise-linear formula, not a machine-learning
model -- the same formula CPCB itself uses to turn raw pollutant
concentrations into the single AQI number:

    Ip = ((IHi - ILo) / (BPHi - BPLo)) * (Cp - BPLo) + ILo

Units expected by this module (24-hour averages, 8-hour for O3/CO):
  pm10, pm2_5, no2, so2, nh3, o3  -> micrograms per cubic metre (ug/m3)
  co                              -> milligrams per cubic metre (mg/m3)
"""

BREAKPOINTS = {
    "pm10": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (431, 500, 401, 500),
    ],
    "pm2_5": [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, 380, 401, 500),
    ],
    "no2": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 180, 101, 200),
        (181, 280, 201, 300),
        (281, 400, 301, 400),
        (401, 500, 401, 500),
    ],
    "so2": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 380, 101, 200),
        (381, 800, 201, 300),
        (801, 1600, 301, 400),
        (1601, 2100, 401, 500),
    ],
    "nh3": [
        (0, 200, 0, 50),
        (201, 400, 51, 100),
        (401, 800, 101, 200),
        (801, 1200, 201, 300),
        (1201, 1800, 301, 400),
        (1801, 2400, 401, 500),
    ],
    "o3": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 168, 101, 200),
        (169, 208, 201, 300),
        (209, 748, 301, 400),
        (749, 900, 401, 500),
    ],
    "co": [
        (0, 1.0, 0, 50),
        (1.1, 2.0, 51, 100),
        (2.1, 10, 101, 200),
        (10.1, 17, 201, 300),
        (17.1, 34, 301, 400),
        (34.1, 50, 401, 500),
    ],
}


def sub_index(pollutant: str, concentration):
    if concentration is None:
        return None
    table = BREAKPOINTS.get(pollutant)
    if not table:
        return None
    if concentration < 0:
        return None

    for bp_lo, bp_hi, i_lo, i_hi in table:
        if bp_lo <= concentration <= bp_hi:
            return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo, 1)

    top_bp_hi = table[-1][1]
    if concentration > top_bp_hi:
        return 500.0
    return None


def calculate_aqi(pollutants_ugm3: dict):
    sub_indices = {}

    for pollutant in ("pm10", "pm2_5", "no2", "so2", "nh3", "o3"):
        val = pollutants_ugm3.get(pollutant)
        idx = sub_index(pollutant, val)
        if idx is not None:
            sub_indices[pollutant] = idx

    co_ugm3 = pollutants_ugm3.get("co")
    if co_ugm3 is not None:
        co_mgm3 = co_ugm3 / 1000.0
        idx = sub_index("co", co_mgm3)
        if idx is not None:
            sub_indices["co"] = idx

    has_pm = "pm10" in sub_indices or "pm2_5" in sub_indices
    if len(sub_indices) < 3 or not has_pm:
        return {
            "aqi": None,
            "sub_indices": sub_indices,
            "reason": "CPCB requires at least 3 pollutants, including PM10 or PM2.5, to compute a composite AQI.",
        }

    dominant = max(sub_indices, key=sub_indices.get)
    return {
        "aqi": round(sub_indices[dominant]),
        "dominant_pollutant": dominant,
        "sub_indices": sub_indices,
    }


def calculate_aqi_best_effort(pollutants_ugm3: dict):
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