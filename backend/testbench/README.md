# Test bench: running without a real device (SQLite, no MongoDB)

## Option 1 — built-in simulator (no broker, no device)
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env            # contains SIMULATE_DEVICES=true
uvicorn app.main:app --reload --port 8000
```
The backend creates virtual devices `sim-room-1..3` (scenarios `comfortable`, `stuffy`, `school-day`)
and feeds their data through the same pipeline as real MQTT messages:
parsing → unit conversion → SQLite.

Verify:
```bash
curl localhost:8000/api/comfort/sim-room-1/sensors
curl localhost:8000/api/comfort/sim-room-2
curl localhost:8000/api/comfort/sim-room-2/recommendations
python testbench/e2e_check.py --api http://localhost:8000
```
Tuning: `SIMULATE_DEVICE_IDS` and `SIMULATE_INTERVAL_SEC` in `.env`.

## Option 2 — over MQTT (`device_simulator.py` emulator)
```bash
docker run -d -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf
MQTT_URL=mqtt://localhost:1883 SIMULATE_DEVICES=false uvicorn app.main:app --port 8000
pip install -r testbench/requirements.txt
python testbench/device_simulator.py --broker localhost:1883 --speed 30 --interval-ms 3000
python testbench/e2e_check.py --api http://localhost:8000 --devices <id printed by the emulator>
```
Everything in Docker: `docker compose -f testbench/docker-compose.dev.yml up --build`.

Emulator console commands: `status`, `scenario stuffy 0`, `offline on|off`, `bad`, `burst 20`, `quit`.

## Notes
- AI recommendations need `OPENAI_API_KEY`; without it, simple rule-based tips are returned.
- Telemetry topic: `iot/device/<id>/telemetry`. The current firmware (`device/`) publishes to
  `<department>/<room>/Sensor/<id>/data` with a different payload — this still has to be aligned.
