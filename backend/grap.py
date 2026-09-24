"""
grap.py
Official CAQM (Commission for Air Quality Management) Graded Response
Action Plan for Delhi-NCR. These stages and their trigger AQI ranges
are the real, currently operating government policy -- not invented.
"""

GRAP_STAGES = [
    {
        "stage": 0,
        "label": "None",
        "min": 0,
        "max": 200,
        "actions": [],
    },
    {
        "stage": 1,
        "label": "Stage I - Poor",
        "min": 201,
        "max": 300,
        "actions": [
            "Mechanized sweeping and water sprinkling on roads",
            "Strict action against open burning of waste",
            "Ensure PUC compliance for all vehicles",
            "Dust mitigation at construction sites",
        ],
    },
    {
        "stage": 2,
        "label": "Stage II - Very Poor",
        "min": 301,
        "max": 400,
        "actions": [
            "Intensify public transport frequency (bus/metro)",
            "Increase parking fees to discourage private vehicle use",
            "Ban on diesel generator sets (non-essential)",
            "Enhanced road sweeping and water sprinkling",
        ],
    },
    {
        "stage": 3,
        "label": "Stage III - Severe",
        "min": 401,
        "max": 450,
        "actions": [
            "Ban on construction and demolition activities (except essential)",
            "Stop stone crushers and hot-mix plants",
            "Ban entry of BS-III petrol / BS-IV diesel private vehicles in Delhi",
            "Consider closing primary schools",
        ],
    },
    {
        "stage": 4,
        "label": "Stage IV - Severe+",
        "min": 451,
        "max": 999,
        "actions": [
            "Ban entry of trucks into Delhi (except essential goods)",
            "Halt all construction and demolition activity",
            "State governments may consider odd-even vehicle rationing",
            "Consider shifting schools to online mode",
        ],
    },
]


def get_grap_stage(aqi):
    if aqi is None:
        return GRAP_STAGES[0]
    for stage in GRAP_STAGES:
        if stage["min"] <= aqi <= stage["max"]:
            return stage
    return GRAP_STAGES[-1]
