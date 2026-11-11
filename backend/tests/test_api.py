"""Tests of the frontend-facing API (/api/auth, /api/locations, /api/comfort), telemetry and the simulator.
Runs on a temporary SQLite database: no MongoDB, MQTT broker or hardware needed."""
import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.comfort import calculate_manual_comfort, generate_tips
from app.db import Base, get_db
from app.main import app
from app.simulator import Simulator, device_id_for
from app.telemetry import handle_message, parse_telemetry, parse_timestamp


@pytest.fixture()
def env(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'api.db').as_posix()}", connect_args={"check_same_thread": False})
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), factory  # without `with` -> lifespan (simulator/MQTT) does not start
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


def register(c, name, email):
    r = c.post("/api/auth/register", json={"username": name, "email": email, "password": "secret1"})
    assert r.status_code == 201, r.text
    return r.json()["data"]


def telemetry(factory, device_id, raw=32768, ts=1765978387):
    payload = {"timestamp": ts, "sensors": {
        "temperature": {"value": 22, "units": "C"}, "humidity": {"value": 45, "units": "%"},
        "gas": {"value": raw, "units": "ppm"}, "light": {"value": raw, "units": "lx"},
        "sound": {"value": raw, "units": "dB"}}}
    asyncio.run(handle_message(f"iot/device/{device_id}/telemetry", json.dumps(payload).encode(), factory))


def test_auth(env):
    c, _ = env
    assert c.post("/api/auth/register", json={"email": "a@b.sk"}).status_code == 422
    assert c.post("/api/auth/register", json={"username": "user", "email": "bad", "password": "123456"}).status_code == 422
    d = register(c, "roma", "roma@x.sk")
    assert d["token"] and d["user"]["username"] == "roma"
    assert c.post("/api/auth/register", json={"username": "other", "email": "ROMA@x.sk", "password": "123456"}).status_code == 409
    assert c.post("/api/auth/login", json={"email": "roma@x.sk", "password": "wrong!!"}).status_code == 401
    login = c.post("/api/auth/login", json={"email": "Roma@X.sk", "password": "secret1"}).json()["data"]
    assert login["user"]["id"] == d["user"]["id"] and login["user"]["createdAt"].endswith("Z")
    me = c.get("/api/auth/me", headers=hdr(login["token"])).json()["data"]
    assert me["username"] == "roma" and me["ownedLocationIds"] == []
    r = c.get("/api/auth/me")
    assert r.status_code == 401 and isinstance(r.json()["error"], str)  # frontend reads `error` as a string
    assert c.get("/api/auth/me", headers=hdr("garbage")).status_code == 401


def test_v1_api_keeps_default_error_format(env):
    c, _ = env
    r = c.post("/api/v1/auth/register", json={"username": "u"})
    assert r.status_code == 422 and "detail" in r.json()


def test_locations_and_devices(env):
    c, factory = env
    admin, other = register(c, "admin", "a@x.sk"), register(c, "other", "o@x.sk")
    A, O = hdr(admin["token"]), hdr(other["token"])

    lid = c.post("/api/locations", json={"name": "Lab"}, headers=A).json()["data"]["id"]
    assert c.post("/api/locations", json={"name": "Lab"}, headers=O).status_code == 409
    lst = c.get("/api/locations", headers=A).json()["data"]
    assert [l["id"] for l in lst["created"]] == [lid] and lst["joined"] == []

    assert c.patch(f"/api/locations/{lid}", json={"name": "X"}, headers=O).status_code == 403
    assert c.patch(f"/api/locations/{lid}", json={"name": "Lab2"}, headers=A).json()["data"]["name"] == "Lab2"
    assert c.get("/api/locations/9999").status_code == 404
    assert c.get(f"/api/locations/{lid}").json()["data"]["name"] == "Lab2"  # public

    assert c.post(f"/api/locations/{lid}/devices", json={"deviceId": "dev1"}, headers=A).status_code == 404  # no telemetry yet
    telemetry(factory, "dev1")
    assert c.post(f"/api/locations/{lid}/devices", json={"deviceId": "dev1", "name": "Room 1"}, headers=A).status_code == 201
    assert c.post(f"/api/locations/{lid}/devices", json={"deviceId": "dev1"}, headers=A).status_code == 409
    assert c.get(f"/api/locations/{lid}").json()["data"]["deviceIds"] == ["dev1"]

    s = c.get("/api/comfort/dev1/sensors").json()["data"]
    assert s["name"] == "Room 1" and s["hidden"] is False
    assert s["latestReading"]["gas"] == 5100 and s["latestReading"]["sound"] == 80
    assert s["timestamp"] == "2025-12-17T13:33:07.000Z"
    assert c.get("/api/comfort/dev1").json()["data"]["comfortPercentage"] == 45
    recs = c.get("/api/comfort/dev1/recommendations").json()["data"]
    assert recs["recommendations"] and {"id", "priority", "type", "message", "reason"} <= recs["recommendations"][0].keys()
    assert c.get("/api/comfort/missing").status_code == 404
    assert c.get("/api/comfort/missing/recommendations").status_code == 404

    assert c.patch(f"/api/locations/{lid}/devices/dev1/hide", headers=A).status_code == 200
    assert c.get("/api/comfort/dev1/sensors").json()["data"]["hidden"] is True
    assert c.patch(f"/api/locations/{lid}/devices/dev1/show", headers=A).status_code == 200

    # join by id (self) and admin adding a user
    assert c.post(f"/api/locations/{lid}/users", json={"targetUserId": other["user"]["id"]}, headers=O).status_code == 200
    assert len(c.get("/api/locations", headers=O).json()["data"]["joined"]) == 1
    assert c.post(f"/api/locations/{lid}/users", json={"targetUserId": admin["user"]["id"]}, headers=O).status_code == 403
    assert c.delete(f"/api/locations/{lid}/users/{admin['user']['id']}", headers=A).status_code == 409
    assert c.delete(f"/api/locations/{lid}/users/{other['user']['id']}", headers=A).status_code == 200
    assert c.delete(f"/api/locations/{lid}/devices/dev1", headers=O).status_code == 403
    assert c.delete(f"/api/locations/{lid}/devices/dev1", headers=A).status_code == 200
    assert c.delete(f"/api/locations/{lid}", headers=A).status_code == 200
    assert c.get("/api/auth/me", headers=A).json()["data"]["ownedLocationIds"] == []


def test_simulator_feeds_the_same_pipeline(env):
    c, factory = env
    sim = Simulator(session_factory=factory)
    sim.configure(3)
    for _ in range(5):
        asyncio.run(sim.tick(1.5))
    ids = [r["id"] for r in sim.describe()]
    assert ids[0] == device_id_for(0) and len(set(ids)) == 3
    for dev in ids:
        s = c.get(f"/api/comfort/{dev}/sensors").json()["data"]["latestReading"]
        assert 200 <= s["gas"] <= 10000 and 40 <= s["sound"] <= 120 and s["units"]["gas"] == "ppm"
        assert 0 <= c.get(f"/api/comfort/{dev}").json()["data"]["comfortPercentage"] <= 100
    # a simulated device can be added to a location like a real one
    admin = register(c, "adm", "adm@x.sk")
    lid = c.post("/api/locations", json={"name": "Sim"}, headers=hdr(admin["token"])).json()["data"]["id"]
    assert c.post(f"/api/locations/{lid}/devices", json={"deviceId": ids[0]}, headers=hdr(admin["token"])).status_code == 201


def test_telemetry_helpers():
    t = parse_telemetry({"sensors": {"temperature": {"value": "abc", "units": "C"}}})
    assert t["temperature"] != t["temperature"]  # NaN
    ok_ = {"temperature": 22, "humidity": 45, "gas": 600, "light": 500, "sound": 30}
    assert calculate_manual_comfort(ok_) == 100 and generate_tips(ok_) == []
    assert calculate_manual_comfort({**ok_, "temperature": 27}) == 88
    tips = generate_tips({**ok_, "gas": 2000, "temperature": 27})
    assert tips[0]["type"] == "gas" and tips[0]["priority"] == "high" and [t["id"] for t in tips] == [1, 2]


def test_timestamp_formats():
    assert parse_timestamp(1765978387) == 1765978387000          # epoch, seconds
    assert parse_timestamp("1765978387") == 1765978387000
    assert parse_timestamp("2025-12-17T13:33:07Z") == 1765978387000   # ISO — firmware format
    assert parse_timestamp(1765978387000) == 1765978387000       # milliseconds
    assert abs(parse_timestamp(None) - time.time() * 1000) < 2000
    assert abs(parse_timestamp("garbage") - time.time() * 1000) < 2000
