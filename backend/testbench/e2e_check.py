#!/usr/bin/env python3
"""
End-to-end check: device (built-in simulator OR device_simulator.py over MQTT) -> backend -> SQLite -> REST.

  # variant 1: no broker, no device
  SIMULATE_DEVICES=true SIMULATE_INTERVAL_SEC=2 uvicorn app.main:app --port 8000
  python testbench/e2e_check.py --api http://localhost:8000 --devices sim-room-1,sim-room-2,sim-room-3

  # variant 2: via MQTT (broker + MQTT_URL=mqtt://localhost:1883 + `python testbench/device_simulator.py`)
  python testbench/e2e_check.py --api http://localhost:8000 --devices <id printed by the emulator>
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

FAILED = 0


def get(base: str, path: str):
    try:
        with urllib.request.urlopen(base + path, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except OSError as e:
        return 0, {"error": str(e)}


def check(cond: bool, name: str, detail: str = ""):
    global FAILED
    print(("✅ " if cond else "❌ ") + name + ("" if cond else f" — {detail}"), flush=True)
    FAILED += 0 if cond else 1
    return cond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--devices", default="sim-room-1,sim-room-2,sim-room-3")
    ap.add_argument("--wait", type=int, default=30, help="seconds to wait for first telemetry")
    a = ap.parse_args()
    base = a.api.rstrip("/")

    status, _ = get(base, "/health")
    if not check(status == 200, "backend is up", f"GET /health -> {status}"):
        sys.exit(1)

    for dev in [d.strip() for d in a.devices.split(",") if d.strip()]:
        print(f"\n== device {dev} ==")
        deadline, data = time.time() + a.wait, None
        while time.time() < deadline:
            status, body = get(base, f"/api/comfort/{dev}/sensors")
            if status == 200:
                data = body["data"]
                break
            time.sleep(1)
        if not check(data is not None, "telemetry reached DB and REST", f"no data within {a.wait}s"):
            continue
        r = data["latestReading"]
        check(all(k in r for k in ("temperature", "humidity", "gas", "light", "sound")), "all 5 sensors present")
        check(-10 < r["temperature"] < 50 and 0 <= r["humidity"] <= 100, "temperature/humidity are plausible", str(r))
        check(200 <= r["gas"] <= 10000 and 40 <= r["sound"] <= 120, "gas/sound converted from raw ADC", str(r))
        status, body = get(base, f"/api/comfort/{dev}")
        check(status == 200 and 0 <= body["data"]["comfortPercentage"] <= 100, "comfort percentage", str(body))
        status, body = get(base, f"/api/comfort/{dev}/recommendations")
        check(status == 200 and isinstance(body["data"]["recommendations"], list), "recommendations endpoint")

    print("\nRESULT:", "ALL PASSED" if not FAILED else f"{FAILED} FAILED")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
