"""
main.py
-------
A REST API for storing and querying IoT sensor readings.

This plays the role of a proper backend/cloud ingestion service --
the kind of thing project 1's dashboard.py did in a very simplified
way (in-memory deque, no real database, no validation). This version
fixes those gaps: real persistence (SQLite), input validation
(Pydantic), and a queryable API (filter by device/time, get stats).

Run with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API documentation
that FastAPI generates automatically from this code.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import database

app = FastAPI(
    title="Sensor Data API",
    description="Stores and queries IoT sensor readings (temperature, humidity, motion).",
)


# --- Request/response schemas ------------------------------------------
# Pydantic models define exactly what shape of data is valid. FastAPI
# uses these to automatically validate incoming requests (rejecting
# anything that doesn't match, with a clear error) and to generate the
# interactive docs at /docs.

class ReadingIn(BaseModel):
    device_id: str = Field(..., min_length=1, examples=["sim-device-01"])
    temperature_c: float = Field(..., ge=-40, le=125, description="Celsius, sane sensor range")
    humidity_pct: float = Field(..., ge=0, le=100)
    motion_detected: bool = False
    timestamp: Optional[str] = None  # if omitted, server fills in "now"


class ReadingOut(BaseModel):
    id: int
    device_id: str
    timestamp: str
    temperature_c: float
    humidity_pct: float
    motion_detected: bool


@app.on_event("startup")
def on_startup():
    database.init_db()


# --- Routes --------------------------------------------------------------

@app.post("/readings", response_model=ReadingOut, status_code=201)
def create_reading(reading: ReadingIn):
    """Stores one new sensor reading."""
    timestamp = reading.timestamp or datetime.now(timezone.utc).isoformat()

    new_id = database.insert_reading(
        device_id=reading.device_id,
        timestamp=timestamp,
        temperature_c=reading.temperature_c,
        humidity_pct=reading.humidity_pct,
        motion_detected=reading.motion_detected,
    )

    stored = database.get_reading_by_id(new_id)
    return _row_to_reading_out(stored)


@app.get("/readings", response_model=list[ReadingOut])
def list_readings(
    device_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
):
    """
    Lists readings, newest first. All filters are optional query params,
    e.g.: GET /readings?device_id=sim-device-01&limit=10
    """
    rows = database.get_readings(device_id, start_time, end_time, limit)
    return [_row_to_reading_out(row) for row in rows]


@app.get("/readings/{reading_id}", response_model=ReadingOut)
def get_reading(reading_id: int):
    row = database.get_reading_by_id(reading_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Reading {reading_id} not found")
    return _row_to_reading_out(row)


@app.delete("/readings/{reading_id}", status_code=204)
def delete_reading(reading_id: int):
    deleted = database.delete_reading(reading_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Reading {reading_id} not found")
    return None


@app.get("/stats")
def stats(device_id: Optional[str] = None):
    """Returns count/avg/min/max temperature and humidity, and total motion events."""
    return database.get_stats(device_id)


def _row_to_reading_out(row: dict) -> ReadingOut:
    """Converts a raw DB row (dict) into the API's response schema."""
    return ReadingOut(
        id=row["id"],
        device_id=row["device_id"],
        timestamp=row["timestamp"],
        temperature_c=row["temperature_c"],
        humidity_pct=row["humidity_pct"],
        motion_detected=bool(row["motion_detected"]),
    )
