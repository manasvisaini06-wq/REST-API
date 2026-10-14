# Sensor Data REST API

A REST API for storing and querying IoT sensor readings, built with
FastAPI + SQLite. This is the "real backend" version of what Project
1's dashboard did in a very simplified way -- proper persistence,
input validation, and a queryable interface instead of an in-memory
list that disappears on restart.

## What it does

- **POST /readings** -- store a new sensor reading
- **GET /readings** -- list readings, filterable by `device_id`,
  `start_time`, `end_time`, and `limit`
- **GET /readings/{id}** -- fetch a single reading by its id
- **DELETE /readings/{id}** -- delete a reading
- **GET /stats** -- count, average/min/max temperature, average
  humidity, and total motion events (optionally filtered by device)

## How to run it

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Start the server:
   ```
   uvicorn main:app --reload
   ```
3. Open **http://127.0.0.1:8000/docs** in your browser -- FastAPI
   auto-generates interactive documentation where you can try every
   endpoint directly from the browser, no need to write curl commands
   to test it manually.

### Example requests (if you want to use curl instead of /docs)

```bash
# Create a reading
curl -X POST http://127.0.0.1:8000/readings \
  -H "Content-Type: application/json" \
  -d '{"device_id":"sim-device-01","temperature_c":28.5,"humidity_pct":60,"motion_detected":true}'

# List readings for one device
curl http://127.0.0.1:8000/readings?device_id=sim-device-01

# Get stats
curl http://127.0.0.1:8000/stats
```
