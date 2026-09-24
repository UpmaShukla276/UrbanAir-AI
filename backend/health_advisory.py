"""
health_advisory.py
Official CPCB (Central Pollution Control Board) National AQI categories
and the health-advisory text published for each band. These breakpoints
are the real government standard -- not an estimate.
"""

CPCB_BANDS = [
    {"min": 0, "max": 50, "category": "Good", "color": "#4CAF50",
     "advisory": "Minimal impact. Safe for outdoor activities for everyone."},
    {"min": 51, "max": 100, "category": "Satisfactory", "color": "#8BC34A",
     "advisory": "Minor breathing discomfort to sensitive people (asthma, elderly, children)."},
    {"min": 101, "max": 200, "category": "Moderate", "color": "#FFC107",
     "advisory": "Breathing discomfort to people with lung disease, children, and older adults. Reduce prolonged outdoor exertion."},
    {"min": 201, "max": 300, "category": "Poor", "color": "#FF9800",
     "advisory": "Breathing discomfort to most people on prolonged exposure. Sensitive groups should avoid outdoor activity."},
    {"min": 301, "max": 400, "category": "Very Poor", "color": "#F44336",
     "advisory": "Respiratory illness on prolonged exposure. Avoid outdoor physical activity, especially children and elderly."},
    {"min": 401, "max": 500, "category": "Severe", "color": "#7E0023",
     "advisory": "Affects healthy people and seriously impacts those with existing diseases. Avoid all outdoor physical activity."},
]


def get_band(aqi):
    if aqi is None:
        return None
    for band in CPCB_BANDS:
        if band["min"] <= aqi <= band["max"]:
            return band
    # AQI above 500 -- still Severe band, cap display at 500+
    if aqi > 500:
        return CPCB_BANDS[-1]
    return None
