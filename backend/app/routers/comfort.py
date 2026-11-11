from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import comfort
from ..db import get_db
from ..errors import EntityNotFoundException, iso, ok
from ..repositories import SensorReadings

# Public (the frontend may call it without a token). `{device_id}` is the device/room id.
router = APIRouter(prefix="/api/comfort", tags=["Comfort (frontend API)"])


@router.get("/{device_id}")
def get_comfort_level(device_id: str, db: Session = Depends(get_db)):
    latest = SensorReadings.find_latest(db, device_id)
    if not latest:
        raise EntityNotFoundException("No sensor data found")
    return ok({
        "audienceId": device_id,
        "comfortPercentage": comfort.calculate_manual_comfort(latest),
        "timestamp": iso(latest["timestamp"]),
    })


@router.get("/{device_id}/recommendations")
def get_recommendations(device_id: str, db: Session = Depends(get_db)):
    latest = SensorReadings.find_latest(db, device_id)
    if not latest:
        raise EntityNotFoundException("No recommendations found")
    return ok({
        "audienceId": device_id,
        "recommendations": comfort.generate_tips(latest),
        "generatedAt": iso(datetime.now(timezone.utc)),
    })


@router.get("/{device_id}/sensors")
def get_sensor_data(device_id: str, db: Session = Depends(get_db)):
    latest = SensorReadings.find_latest(db, device_id)
    if not latest:
        raise EntityNotFoundException("No sensor data found for this device")
    return ok({
        "deviceId": device_id,
        "name": latest["name"],
        "hidden": latest["hidden"],
        "latestReading": {k: latest[k] for k in ("temperature", "humidity", "gas", "light", "sound", "units")},
        "timestamp": iso(latest["timestamp"]),
    })
