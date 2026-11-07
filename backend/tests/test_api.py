"""Telemetry -> SQLite -> comfort/sensors REST (no MongoDB, no MQTT broker, no device needed)."""
import asyncio
import json
import os
import time

import pytest

from app import comfort, simulator
from app.comfort import calculate_manual_comfort, rule_based_tips
from app.telemetry import convert_units, handle_message, parse_telemetry, parse_timestamp


def telemetry(device_id, raw=32768, ts=1765978387):
    payload = {"timestamp": ts, "sensors": {
        "temperature": {"value": 22, "units": "C"}, "humidity": {"value": 45, "units": "%"},
        "gas": {"value": raw, "units": "ppm"}, "light": {"value": raw, "units": "lx"},
        "sound": {"value": raw, "units": "dB"}}}
    asyncio.run(handle_message(f"iot/device/{device_id}/telemetry", json.dumps(payload).encode()))


def test_sensors_and_comfort(client):
    assert client.get("/api/comfort/dev1/sensors").status_code == 404
    telemetry("dev1")
    s = client.get("/api/comfort/dev1/sensors").json()["data"]
    assert s["deviceId"] == "dev1"
    assert s["latestReading"]["gas"] == 5100 and s["latestReading"]["sound"] == 80
    assert s["timestamp"] == "2025-12-17T13:33:07.000Z"
    assert client.get("/api/comfort/dev1").json()["data"]["comfortPercentage"] == 45
    assert client.get("/api/comfort/missing").status_code == 404


def test_latest_reading_wins(client):
    telemetry("dev2", raw=0, ts=1765978000)
    telemetry("dev2", raw=65535, ts=1765978387)
    assert client.get("/api/comfort/dev2/sensors").json()["data"]["latestReading"]["gas"] == 10000


def test_invalid_payload_ignored(client):
    asyncio.run(handle_message("iot/device/bad/telemetry", b"not json"))
    asyncio.run(handle_message("iot/device/bad/telemetry", b'{"sensors": {}}'))
    assert client.get("/api/comfort/bad/sensors").status_code == 404


def test_recommendations_rule_based_without_key(client, monkeypatch):
    monkeypatch.setattr(comfort.settings, "openai_api_key", "")
    telemetry("dev-9", raw=65535)  # very high gas/light/sound
    r = client.get("/api/comfort/dev-9/recommendations")
    assert r.status_code == 200
    tips = r.json()["data"]["recommendations"]
    assert tips and {t["type"] for t in tips} <= {"temperature", "humidity", "gas", "light", "sound"}
    assert client.get("/api/comfort/missing/recommendations").status_code == 404


def _fake_ai(create):
    ns = lambda **kw: type("N", (), kw)  # noqa: E731
    return ns(chat=ns(completions=ns(create=staticmethod(create))))


def test_recommendations_openai_success(client, monkeypatch):
    monkeypatch.setattr(comfort.settings, "openai_api_key", "test")
    telemetry("dev-8")

    async def create(**kwargs):
        tips = [{"priority": "high", "type": "gas", "message": "Open a window", "reason": "CO2 is high"}]
        msg = type("M", (), {"content": json.dumps({"recommendations": tips})})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})

    monkeypatch.setattr(comfort, "_get_ai", lambda: _fake_ai(create))
    r = client.get("/api/comfort/dev-8/recommendations")
    assert r.json()["data"]["recommendations"][0]["message"] == "Open a window"


def test_recommendations_openai_failure_gives_empty_list(client, monkeypatch):
    monkeypatch.setattr(comfort.settings, "openai_api_key", "test")
    telemetry("dev-7")

    async def boom(**kwargs): raise RuntimeError("no key")

    monkeypatch.setattr(comfort, "_get_ai", lambda: _fake_ai(boom))
    r = client.get("/api/comfort/dev-7/recommendations")
    assert r.status_code == 200 and r.json()["data"]["recommendations"] == []


def test_simulator_feeds_pipeline(client):
    """Simulated device payloads go through the same pipeline as real MQTT data."""
    import random
    for scenario in ("comfortable", "stuffy", "school-day"):
        payload = simulator.make_payload(scenario, 30.0, random.Random(1))
        asyncio.run(handle_message(f"iot/device/sim-{scenario}/telemetry", json.dumps(payload).encode()))
    ok_ = client.get("/api/comfort/sim-comfortable").json()["data"]["comfortPercentage"]
    bad = client.get("/api/comfort/sim-stuffy").json()["data"]["comfortPercentage"]
    assert ok_ > bad
    r = client.get("/api/comfort/sim-comfortable/sensors").json()["data"]["latestReading"]
    assert 400 <= r["gas"] <= 800 and 20 <= r["temperature"] <= 24


def test_simulator_disabled_by_default():
    assert simulator.start() is None


def test_telemetry_helpers():
    t = parse_telemetry({"sensors": {"temperature": {"value": "abc", "units": "C"}}})
    assert t["temperature"] != t["temperature"]  # NaN
    assert calculate_manual_comfort({"temperature": 22, "humidity": 45, "gas": 600, "light": 500, "sound": 30}) == 100
    assert calculate_manual_comfort({"temperature": 27, "humidity": 45, "gas": 600, "light": 500, "sound": 30}) == 88
    assert rule_based_tips({"temperature": 22, "humidity": 45, "gas": 600, "light": 500, "sound": 30}) == []


def test_timestamp_formats():
    assert parse_timestamp(1765978387) == 1765978387000          # epoch, seconds
    assert parse_timestamp("1765978387") == 1765978387000
    assert parse_timestamp("2025-12-17T13:33:07Z") == 1765978387000   # ISO - firmware format
    assert parse_timestamp(1765978387000) == 1765978387000       # milliseconds
    assert abs(parse_timestamp(None) - time.time() * 1000) < 2000
    assert abs(parse_timestamp("garbage") - time.time() * 1000) < 2000


def test_openai_api_connection():
    """Checks real connection to OpenAI API (skipped without OPENAI_API_KEY)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is not configured")
    model = os.getenv("OPENAI_MODEL")
    if not model:
        pytest.fail("OPENAI_MODEL is not configured")
    from openai import OpenAI
    with OpenAI(api_key=api_key) as c:
        r = c.chat.completions.create(model=model, messages=[
            {"role": "user", "content": "Reply with exactly: OpenAI API works!"}], max_completion_tokens=30)
    assert r.choices[0].message.content.strip() == "OpenAI API works!"
