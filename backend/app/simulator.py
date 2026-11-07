"""Built-in device simulator.

Lets you run the whole backend without a physical device and without an MQTT broker.
Fake devices produce payloads in the same format as the firmware (raw 16-bit ADC values
for gas/sound/light, ISO timestamp) and feed them into the normal telemetry pipeline
(`telemetry.handle_message`), so parsing, unit conversion, DB storage and the comfort
endpoints are exercised exactly as with real MQTT data.

Enable with SIMULATE_DEVICES=true (see .env.example).
"""
import asyncio
import json
import logging
import math
import random
from datetime import datetime, timezone

from .config import settings
from .telemetry import handle_message

log = logging.getLogger("simulator")

# scenario -> (temperature C, humidity %, CO2 ppm, light lx, noise dB)
_SCENARIOS = {
    "comfortable": (22.0, 45.0, 600.0, 500.0, 35.0),
    "stuffy": (26.5, 65.0, 1600.0, 250.0, 55.0),
    "school-day": (21.0, 40.0, 900.0, 600.0, 45.0),
}


def _raw(value: float, lo: float, hi: float) -> int:
    """Inverse of telemetry.convert_units: physical value -> raw 16-bit ADC value."""
    return int(max(0.0, min(1.0, (value - lo) / (hi - lo))) * 65535)


def make_payload(scenario: str, t: float, rng: random.Random) -> dict:
    temp, hum, co2, lux, db = _SCENARIOS[scenario]
    if scenario == "school-day":  # CO2 rises during a "lesson" and drops at the "break" (saw-tooth)
        co2 += 700 * math.sin(math.pi * ((t / 60.0) % 1.0))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "timestamp": now,
        "sensors": {
            "temperature": {"value": round(temp + rng.uniform(-0.5, 0.5), 1), "units": "C"},
            "humidity": {"value": round(hum + rng.uniform(-3, 3), 1), "units": "%"},
            "gas": {"value": _raw(co2 + rng.uniform(-50, 50), 200, 10000), "units": "ppm"},
            "light": {"value": _raw(lux + rng.uniform(-40, 40), 0.1, 100000), "units": "lx"},
            "sound": {"value": _raw(db + rng.uniform(-3, 3), 40, 120), "units": "dB"},
        },
    }


async def _run(device_ids: list[str], interval: float) -> None:
    rng = random.Random(42)
    scenarios = list(_SCENARIOS)
    assigned = {d: scenarios[i % len(scenarios)] for i, d in enumerate(device_ids)}
    log.info("🤖 Simulator started: %s every %.1fs", assigned, interval)
    t = 0.0
    while True:
        for device_id, scenario in assigned.items():
            payload = make_payload(scenario, t, rng)
            await handle_message(f"iot/device/{device_id}/telemetry", json.dumps(payload).encode())
        await asyncio.sleep(interval)
        t += interval


def start() -> asyncio.Task | None:
    """Start the simulator as a background task (call from a running event loop)."""
    if not settings.simulate_devices:
        return None
    ids = [d.strip() for d in settings.simulate_device_ids.split(",") if d.strip()]
    if not ids:
        return None
    return asyncio.create_task(_run(ids, max(0.5, settings.simulate_interval_sec)))
