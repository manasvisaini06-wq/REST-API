"""
database.py
-----------
Handles all direct interaction with the SQLite database. Kept separate
from main.py so the API layer (routes, validation) doesn't need to know
anything about SQL -- it just calls these functions.

SQLite is used here because it needs zero setup (no separate server to
install/run, just a single file on disk) which makes it ideal for a
learning project. A real production system handling many devices and
high write volume would typically use a proper time-series database
(InfluxDB, TimescaleDB) or at least Postgres/MySQL -- but the query
patterns and API design shown here would look almost identical either
way. Swapping the database later mainly means changing this file, not
the API routes in main.py.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "sensor_data.db"


def init_db():
    """Creates the readings table if it doesn't already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                motion_detected INTEGER NOT NULL
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    """
    Provides a database connection as a context manager, so callers can
    write `with get_connection() as conn:` and the connection is always
    closed afterward, even if an error occurs inside the `with` block.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    try:
        yield conn
    finally:
        conn.close()


def insert_reading(device_id, timestamp, temperature_c, humidity_pct, motion_detected):
    """Inserts one reading and returns its new row id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO readings (device_id, timestamp, temperature_c, humidity_pct, motion_detected)
            VALUES (?, ?, ?, ?, ?)
            """,
            (device_id, timestamp, temperature_c, humidity_pct, int(motion_detected)),
        )
        conn.commit()
        return cursor.lastrowid


def get_readings(device_id=None, start_time=None, end_time=None, limit=100):
    """
    Fetches readings, optionally filtered by device and/or time range.
    Parameterized queries (the '?' placeholders) are used throughout to
    prevent SQL injection -- never build a query by directly inserting
    user input into a string.
    """
    query = "SELECT * FROM readings WHERE 1=1"
    params = []

    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_reading_by_id(reading_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM readings WHERE id = ?", (reading_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_reading(reading_id):
    """Returns True if a row was deleted, False if no matching id existed."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM readings WHERE id = ?", (reading_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_stats(device_id=None):
    """Returns count/avg/min/max temperature and humidity, optionally per device."""
    query = """
        SELECT
            COUNT(*) as count,
            AVG(temperature_c) as avg_temp,
            MIN(temperature_c) as min_temp,
            MAX(temperature_c) as max_temp,
            AVG(humidity_pct) as avg_humidity,
            SUM(motion_detected) as motion_events
        FROM readings
    """
    params = []
    if device_id:
        query += " WHERE device_id = ?"
        params.append(device_id)

    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row)
