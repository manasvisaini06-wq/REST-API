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

## How this connects to Project 1

Project 1's `publisher.py` (the simulated device) could point at this
API instead of the dashboard's simple `/api/ingest` route -- change
one URL and one payload shape, and you'd have the simulated device
writing into a real, persistent, validated database instead of
disappearing memory. That's intentional: these two projects together
show the same IoT pipeline built two different ways, at two different
levels of "production-readiness."

## Design notes / talking points for interviews

- **Why FastAPI over Flask here?** FastAPI validates request data
  automatically using Pydantic models (`ReadingIn`), rejecting bad
  input (e.g. humidity over 100%) before your code even runs, and it
  auto-generates interactive API docs at `/docs` for free. Flask
  requires manual validation code for the same safety.
- **Why SQLite and not just a Python list/dict?** Data survives a
  server restart. A list in memory (like Project 1's deque) is wiped
  every time the process stops -- fine for a live demo, not fine for
  anything real.
- **Why parameterized queries (`?` placeholders) instead of building
  SQL strings directly?** Prevents SQL injection -- never insert raw
  user input directly into a query string. This is a real security
  practice, not just a style choice.
- **Why a separate `database.py` instead of putting SQL in `main.py`?**
  Separation of concerns: `main.py` (the API layer) doesn't need to
  know *how* data is stored, only that `database.py` can save/fetch
  it. This means swapping SQLite for Postgres later only touches
  `database.py`, not any route logic.
- **Why return 204 (no content) on delete, but 201 (created) on
  post?** These are standard REST/HTTP conventions: 201 signals a new
  resource was created (and returns it), 204 signals success with
  nothing to return (the resource is gone, there's nothing to show).
- **Known limitations / next steps:** no authentication (anyone can
  post/delete), no pagination beyond a simple `limit`, no rate
  limiting. Worth naming these unprompted in an interview -- it shows
  you know what "production-ready" would actually require beyond this.
