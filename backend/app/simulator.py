"""Built-in device simulator: replaces the physical Inspector-comforT device (Pico W) for local runs.

It builds payloads exactly like the firmware does (ISO timestamp, RAW 16-bit ADC values for
gas/sound/light) and feeds them into the same pipeline as MQTT (app.telemetry.handle_message),
so no MQTT broker and no hardware are required. Enable with SIMULATE_DEVICE=true.
Device ids are stable between runs and match testbench/device_simulator.py (room-0, room-1, ...).
"""
import asyncio
import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone

from .config import settings
from .db import SessionLocal
from .repositories import SensorReadings
from .telemetry import handle_message

log = logging.getLogger("simulator")

RAW_MAX = 65535
UNITS = {"temperature": "°C", "humidity": "%", "gas": "ppm", "light": "lx", "sound": "dB"}
SCENARIOS = ["school-day", "comfortable", "stuffy"]  # assigned to devices in this order (cycled)


def device_id_for(index: int, prefix: str = "room") -> str:
    return f"com-{hashlib.sha1(f'{prefix}-{index}'.encode()).hexdigest()[:16]}-fort"


def _school_people(h: float) -> float:
    lessons = [(8.0, 8.75), (8.92, 9.67), (9.83, 10.58), (10.92, 11.67), (11.83, 12.58), (12.75, 13.5)]
    if any(a <= h < b for a, b in lessons):
        return 24
    return 3 if 8.0 <= h < 13.6 else 0


def _people(scenario: str, hour: float) -> float:
    if scenario == "school-day":
        return _school_people(hour)
    return {"comfortable": 6, "stuffy": 25}[scenario]


class Room:
    """Tiny physical model: CO2 grows with people and decays with ventilation."""

    def __init__(self, index: int, scenario: str):
        self.index, self.scenario, self.id = index, scenario, device_id_for(index)
        self.co2, self.temp, self.hum = 450.0, 21.0, 45.0
        self.people = 0.0

    def step(self, hour: float, dt_min: float) -> None:
        self.people = _people(self.scenario, hour)
        vent = {"school-day": 0.02, "comfortable": 0.05, "stuffy": 0.004}[self.scenario]
        if self.scenario == "school-day" and self.people <= 3:
            vent += 0.06  # windows open during breaks
        self.co2 += (self.people * 1.2 - (self.co2 - 420) * vent) * dt_min
        target_t = {"school-day": 20.5, "comfortable": 22.0, "stuffy": 26.5}[self.scenario] + self.people * 0.03
        self.temp += (target_t - self.temp) * min(1.0, 0.05 * dt_min)
        target_h = {"school-day": 42, "comfortable": 45, "stuffy": 62}[self.scenario]
        self.hum += (target_h - self.hum) * min(1.0, 0.03 * dt_min)

    def physical(self) -> dict:
        light = {"school-day": 450, "comfortable": 650, "stuffy": 350}[self.scenario]
        return {
            "temperature": round(self.temp + random.uniform(-0.3, 0.3)),
            "humidity": round(self.hum + random.uniform(-1, 1)),
            "gas": max(200, self.co2 + random.uniform(-15, 15)),
            "light": max(0.1, light + random.uniform(-25, 25)),
            "sound": min(120, max(40, 38 + self.people * 1.1 + random.uniform(-2, 2))),
        }


def build_payload(values: dict, now: datetime | None = None) -> dict:
    """Physical values -> firmware payload (inverse of telemetry.convert_units)."""
    now = now or datetime.now(timezone.utc)
    raw = {
        "temperature": values["temperature"],
        "humidity": values["humidity"],
        "gas": round((values["gas"] - 200) / (10000 - 200) * RAW_MAX),
        "sound": round((values["sound"] - 40) / (120 - 40) * RAW_MAX),
        "light": round((values["light"] - 0.1) / (100000 - 0.1) * RAW_MAX),
    }
    return {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sensors": {k: {"value": v, "units": UNITS[k]} for k, v in raw.items()},
    }


class Simulator:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.rooms: list[Room] = []
        self.hour = 8.0  # simulated clock; starts at the first lesson
        self._task: asyncio.Task | None = None
        self._ticks = 0

    def configure(self, devices: int) -> None:
        self.rooms = [Room(i, SCENARIOS[i % len(SCENARIOS)]) for i in range(max(1, devices))]

    async def tick(self, dt_min: float) -> None:
        """One measurement from every simulated device."""
        self.hour = (self.hour + dt_min / 60) % 24
        for room in self.rooms:
            room.step(self.hour, dt_min)
            payload = build_payload(room.physical())
            await handle_message(f"iot/device/{room.id}/telemetry", json.dumps(payload).encode(), self.session_factory)
        self._ticks += 1
        if self._ticks % 50 == 0:
            with self.session_factory() as db:
                for room in self.rooms:
                    SensorReadings.prune(db, room.id)

    async def _run(self) -> None:
        interval, speed = settings.SIM_INTERVAL_SECONDS, settings.SIM_SPEED
        while True:
            await asyncio.sleep(interval)
            try:
                await self.tick(interval * speed / 60)
            except Exception:
                log.exception("simulator tick failed")

    async def start(self) -> None:
        self.configure(settings.SIM_DEVICES)
        await self.tick(1.0)  # first readings immediately, so rooms can be added right after startup
        for r in self.rooms:
            log.warning("🤖 Simulated device %s (%s)", r.id, r.scenario)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def describe(self) -> list[dict]:
        return [{"id": r.id, "scenario": r.scenario} for r in self.rooms]


simulator = Simulator()
