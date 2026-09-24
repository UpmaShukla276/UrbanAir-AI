# Methodology

This document explains where every number in the dashboard comes from, and — just as importantly — which numbers are real measurements versus documented estimates.

## 1. AQI — official CPCB formula

`backend/aqi_formula.py` implements India's real National Air Quality Index formula (CPCB, 2014): a deterministic, piecewise-linear sub-index calculation, not a machine-learning model.

For each pollutant `p`:

```
Ip = ((IHi - ILo) / (BPHi - BPLo)) * (Cp - BPLo) + ILo
```

where `Cp` is the measured concentration, `BPLo`/`BPHi` are the breakpoint concentrations bracketing it, and `ILo`/`IHi` are the corresponding index values from CPCB's official breakpoint table. The overall AQI is the **maximum** sub-index across all available pollutants — CPCB's own "worst pollutant governs" rule — and that pollutant is reported as the `dominant_pollutant`.

Two entry points are exposed:
- `calculate_aqi` — expects a full pollutant set (used for the OpenWeatherMap-based forecast).
- `calculate_aqi_best_effort` — computes the best possible result from whatever subset of pollutants WAQI actually returned for a given live reading, since real-world stations don't always report every pollutant.

Units: PM10, PM2.5, NO2, SO2, NH3, O3 in µg/m³ (24-hour averages, 8-hour for O3/CO where applicable); CO in mg/m³ — matching CPCB's own units.

## 2. GRAP stages — official CAQM policy

`backend/grap.py` maps the current AQI to the Commission for Air Quality Management's Graded Response Action Plan:

| Stage | Label | AQI range | Example mandated actions |
|---|---|---|---|
| 0 | None | 0–200 | — |
| I | Poor | 201–300 | Mechanized road sweeping, water sprinkling, strict action on open waste burning |
| II | Very Poor | 301–400 | Intensify public transport, raise parking fees, ban non-essential diesel gensets |
| III | Severe | 401–450 | Ban construction/demolition (except essential), stop stone crushers/hot-mix plants, restrict BS-III petrol / BS-IV diesel private vehicles in Delhi |
| IV | Severe+ | 451+ | Ban truck entry (except essential goods), halt all construction/demolition, consider odd-even rationing and online schooling |

These are the real, currently operating stage thresholds and actions — not invented. `GET /api/grap` reports the stage for the **worst** location across the whole monitored NCR area, which mirrors how CAQM actually calls a stage in practice. `grap_compliance.py` tracks how long the region has stayed in its current stage.

## 3. Source attribution — a transparent estimate, not a measurement

**This is the one number in the dashboard that is not a direct measurement, and the API always labels it as an estimate.**

No agency — not CPCB, not SAFAR, not CAQM — has a sensor that measures what fraction of today's pollution at a specific point came from traffic vs. industry vs. construction vs. waste burning vs. background sources. That ground truth doesn't exist at the point level. What official bodies actually use instead is documented rule-based reasoning combined with known emission-inventory shares — and that's exactly what `backend/source_attribution.py` does:

1. Each monitored location has a `zone_type` (traffic-heavy, industrial, residential, green zone, or mixed) — our own classification, not a measured value.
2. Each zone type has a base source-mix assumption, broadly consistent with CPCB/TERI emission-inventory studies for Delhi NCR (e.g. a traffic-heavy zone is assumed ~55% traffic, 10% industrial, 10% construction, 5% waste burning, 20% background).
3. That base mix is adjusted using the current PM2.5/PM10 ratio and time of day as documented signals.

Every weight is a stated assumption, openly documented in the code, and the API response is always tagged `"estimated"`.

## 4. Forecast

`GET /api/forecast/{location_id}` uses OpenWeatherMap's own 4-day hourly pollutant forecast, then runs each hourly pollutant set back through the same official CPCB formula from section 1 — so the forecast AQI is directly comparable to the live AQI, rather than being a separately-modeled number. 24h/48h/72h snapshots are picked from the closest available forecast point.

## 5. What-if simulator

`backend/whatif.py` takes the current reading and six independent inputs — reduction percentages for traffic, industrial, construction, waste-burning, and background sources, plus a wind-speed multiplier — and estimates the resulting AQI by scaling the source-attribution mix from section 3. Like source attribution, this is a transparent, documented estimate meant to communicate direction and rough magnitude of impact, not a precise physical air-dispersion model.

## 6. Wind

`backend/wind_impact.py` uses live wind speed/direction from OpenWeatherMap and haversine distance to describe, in plain language, where the wind at a location is coming from. The module also includes `get_downwind_locations` and `get_upwind_locations` helpers for identifying which monitored points are up/downwind of a given one — these are implemented and imported in `main.py` but not yet wired to a live API endpoint.

## Summary: what's measured vs. estimated

| Data | Type |
|---|---|
| AQI, pollutant concentrations | Real, live (WAQI) |
| Wind speed/direction | Real, live (OpenWeatherMap) |
| AQI formula result | Deterministic official CPCB calculation |
| GRAP stage | Deterministic official CAQM mapping |
| Pollutant forecast | Real OWM model output, through the CPCB formula |
| Source-mix % | Documented rule-based **estimate** |
| What-if results | Documented rule-based **estimate** |
