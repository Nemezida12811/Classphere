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

4. Запустити сервер розробки (порт **3001** — його очікує frontend):
   ```bash
   python -m app            # або: uvicorn app.main:app --reload --port 3001
   ```

Сервер буде доступний за адресою: `http://localhost:3001`
Автоматична Swagger документація: `http://localhost:3001/docs`

> Якщо база `school_env.db` лишилась від старої версії — видаліть її: у таблицю `locations` додано колонку `admin_id`, а `create_all` існуючі таблиці не змінює.

---

## Запуск без фізичного пристрою (backend + frontend)

У `.env` має бути `SIMULATE_DEVICE=true` (є в `.env.example`). Тоді backend сам генерує телеметрію
3 кімнат (`school-day`, `comfortable`, `stuffy`) у тому ж форматі, що й прошивка (ISO-час, сирі 16-бітні
значення АЦП), і пропускає її через той самий конвеєр, що й MQTT — **MQTT-брокер не потрібен**.

```bash
# термінал 1
cd backend && python -m app
# термінал 2
cd frontend/client && npm install && npm run dev
```
1. Список id симульованих пристроїв: `GET http://localhost:3001/api/simulator/devices`
   (також друкується в консолі backend; id стабільні: `com-0a6085b9ed2396e6-fort`, …).
2. У frontend: зареєструйтесь → створіть локацію → «Add room» → вставте id пристрою.
3. Швидкість моделі: `SIM_INTERVAL_SECONDS` (період вимірювань) і `SIM_SPEED` (1 с реального часу = N с моделі).

Справжні пристрої через MQTT: задайте `MQTT_URL=mqtt://host:1883` (залежність `paho-mqtt`).

Рекомендації в `/api/comfort/{id}/recommendations` формуються правилами (без OpenAI).

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
Backend буде на `http://localhost:3001` (симулятор увімкнено у `docker-compose.yml`).

---

## Running tests

### Для frontend (`/api/...`, відповіді `{"success": true, "data": ...}`, помилки `{"success": false, "error": "..."}`)
- `POST /api/auth/register`, `POST /api/auth/login` (JSON `{email, password}`), `POST /api/auth/logout`, `GET /api/auth/me`
- `GET|POST /api/locations`, `GET|PATCH|DELETE /api/locations/{id}`
- `POST /api/locations/{id}/users`, `DELETE /api/locations/{id}/users/{userId}`
- `POST /api/locations/{id}/devices`, `PATCH .../devices/{deviceId}/hide|show`, `DELETE .../devices/{deviceId}`
- `GET /api/comfort/{deviceId}`, `/api/comfort/{deviceId}/recommendations`, `/api/comfort/{deviceId}/sensors`
- `GET /api/simulator/devices`

### Класичний REST (`/api/v1`)

### Автентифікація (`/api/v1/auth`)
- `POST /api/v1/auth/register` — реєстрація нового користувача
- `POST /api/v1/auth/login` — вхід та отримання JWT токена
- `GET /api/v1/auth/me` — інформація про поточного авторизованого користувача

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
