"""
database.py
Very small SQLite wrapper. No ORM, no external DB server needed --
this creates a single file `urbanair.db` next to this script.
Every row here is a REAL reading fetched from WAQI at the time it was stored.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "urbanair.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS aqi_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id TEXT NOT NULL,
            aqi INTEGER,
            pm25 REAL,
            pm10 REAL,
            wind_speed REAL,
            wind_deg REAL,
            station_name TEXT,
            station_lat REAL,
            station_lon REAL,
            no2 REAL,
            so2 REAL,
            o3 REAL,
            co REAL,
            dominant_pollutant TEXT,
            official_compliant INTEGER,
            source TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
        """
    )
    existing_cols = [row["name"] for row in conn.execute("PRAGMA table_info(aqi_readings)")]
    for col, coltype in [
        ("wind_deg", "REAL"), ("station_name", "TEXT"), ("station_lat", "REAL"),
        ("station_lon", "REAL"), ("no2", "REAL"), ("so2", "REAL"), ("o3", "REAL"),
        ("co", "REAL"), ("dominant_pollutant", "TEXT"), ("official_compliant", "INTEGER"),
    ]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE aqi_readings ADD COLUMN {col} {coltype}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_location_time ON aqi_readings (location_id, fetched_at)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS grap_stage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage INTEGER NOT NULL,
            label TEXT NOT NULL,
            ncr_worst_aqi INTEGER,
            started_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_latest_grap_log():
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM grap_stage_log ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_grap_log(stage: int, label: str, ncr_worst_aqi):
    conn = get_connection()
    conn.execute(
        "INSERT INTO grap_stage_log (stage, label, ncr_worst_aqi, started_at) VALUES (?, ?, ?, ?)",
        (stage, label, ncr_worst_aqi, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_grap_log_history(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM grap_stage_log ORDER BY started_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_reading(location_id: str, aqi, pm25, pm10, wind_speed, wind_deg, station_name, station_lat, station_lon,
                    no2, so2, o3, co, dominant_pollutant, official_compliant, source: str):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO aqi_readings (
            location_id, aqi, pm25, pm10, wind_speed, wind_deg, station_name, station_lat, station_lon,
            no2, so2, o3, co, dominant_pollutant, official_compliant, source, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            location_id, aqi, pm25, pm10, wind_speed, wind_deg, station_name, station_lat, station_lon,
            no2, so2, o3, co, dominant_pollutant, (1 if official_compliant else 0),
            source, datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO aqi_readings (location_id, aqi, pm25, pm10, wind_speed, wind_deg, station_name, station_lat, station_lon, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            location_id,
            aqi,
            pm25,
            pm10,
            wind_speed,
            wind_deg,
            station_name,
            station_lat,
            station_lon,
            source,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_latest_reading(location_id: str):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM aqi_readings
        WHERE location_id = ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (location_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_trend(location_id: str, hours: int = 12):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT aqi, pm25, pm10, fetched_at FROM aqi_readings
        WHERE location_id = ? AND fetched_at >= ?
        ORDER BY fetched_at ASC
        """,
        (location_id, since),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
