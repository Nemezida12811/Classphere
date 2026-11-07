# Backend (Python / FastAPI)

Core of the **Smart School Environment** system: user authentication, location management,
sensor telemetry (MQTT) and room comfort analysis.

## Tech stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Auth**: JWT (JSON Web Tokens) + Bcrypt
- **Database**: SQLite (default for local development) or PostgreSQL (Docker)
- **Messaging**: MQTT via paho-mqtt (optional)
- **AI tips**: OpenAI API (optional, with a rule-based fallback)

---

## Quick start (local)

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (copy the example):
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The server is available at `http://localhost:8000`.
Interactive Swagger docs: `http://localhost:8000/docs`.

---

## Running without a physical device (simulator)

The backend ships with a built-in device simulator, so the whole project can be run and tested
without hardware and without an MQTT broker.

Set this in `.env`:
```env
SIMULATE_DEVICES=true
SIMULATE_DEVICE_IDS=sim-room-1,sim-room-2,sim-room-3
SIMULATE_INTERVAL_SEC=5
```

The simulator creates fake devices (scenarios: `comfortable`, `stuffy`, `school-day`) that produce
payloads in the same format as the firmware. They go through the same pipeline as real MQTT data:
parsing → unit conversion → SQLite → REST. Try it:

```bash
curl http://localhost:8000/api/comfort/sim-room-1/sensors
curl http://localhost:8000/api/comfort/sim-room-2
curl http://localhost:8000/api/comfort/sim-room-2/recommendations
```

To run through a real MQTT broker instead, see [`testbench/README.md`](testbench/README.md).

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./school_env.db` | SQLite or PostgreSQL connection string |
| `SECRET_KEY` | *(dev value)* | JWT signing key — change in production |
| `MQTT_URL` | *(empty)* | e.g. `mqtt://localhost:1883`; empty disables MQTT |
| `SIMULATE_DEVICES` | `false` | Enable the built-in device simulator |
| `SIMULATE_DEVICE_IDS` | `sim-room-1,sim-room-2,sim-room-3` | Simulated device ids |
| `SIMULATE_INTERVAL_SEC` | `5` | Simulator measurement interval |
| `OPENAI_API_KEY` | *(empty)* | Enables AI recommendations; without it, rule-based tips are returned |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used for recommendations |

See `.env.example` for the full list.

---

## Running with Docker Compose

```bash
docker compose up --build
```

---

## Running tests

```bash
pip install -r requirements-test.txt
pytest
```

Tests use a temporary SQLite database — no MQTT broker, device or external services are required.

---

## API endpoints

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — register a new user
- `POST /api/v1/auth/login` — log in and receive a JWT
- `GET /api/v1/auth/me` — current authenticated user

### Locations (`/api/v1/locations`)
- `GET /api/v1/locations/` — list all locations
- `POST /api/v1/locations/` — create a location (token required)
- `GET /api/v1/locations/{id}` — get a location by ID
- `PUT /api/v1/locations/{id}` — update a location (token required)
- `DELETE /api/v1/locations/{id}` — delete a location (token required)

### Sensors and comfort (`/api/comfort`)
- `GET /api/comfort/{device_id}/sensors` — latest sensor readings of a device
- `GET /api/comfort/{device_id}` — comfort percentage (0–100) based on the latest readings
- `GET /api/comfort/{device_id}/recommendations` — comfort improvement tips (AI or rule-based)

Responses of these endpoints use the envelope `{"success": true, "data": ...}`.

### Service
- `GET /health` — health check
