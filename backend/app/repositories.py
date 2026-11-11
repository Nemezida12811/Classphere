from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import User, Location
from app.schemas import UserCreate, LocationCreate, LocationUpdate
from app.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user


class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, location_id: int) -> Optional[Location]:
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_by_name(self, name: str) -> Optional[Location]:
        return self.db.query(Location).filter(Location.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Location]:
        return self.db.query(Location).offset(skip).limit(limit).all()

    def create(self, loc_in: LocationCreate) -> Location:
        db_location = Location(
            name=loc_in.name,
            building=loc_in.building,
            floor=loc_in.floor,
            description=loc_in.description,
            is_active=True,
        )
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def update(self, location_id: int, loc_in: LocationUpdate) -> Optional[Location]:
        db_location = self.get_by_id(location_id)
        if not db_location:
            return None

        update_data = loc_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_location, key, value)

        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def delete(self, location_id: int) -> bool:
        db_location = self.get_by_id(location_id)
        if not db_location:
            return False
        self.db.delete(db_location)
        self.db.commit()
        return True


# ==================== SENSOR READINGS / DEVICES ====================
from datetime import timezone  # noqa: E402
from app.db import Device, SensorReading  # noqa: E402

UNIT_DEFAULTS = {"temperature": "°C", "humidity": "%", "gas": "ppm", "light": "lx", "sound": "dB"}


class SensorReadings:
    """Telemetry storage. All methods take an explicit Session (works for requests, MQTT and the simulator)."""

    @staticmethod
    def save(db: Session, device_id: str, t: dict) -> None:
        ts = t["timestamp"]
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        db.add(SensorReading(
            device_id=device_id,
            temperature=t["temperature"], humidity=t["humidity"], gas=t["gas"],
            light=t["light"], sound=t["sound"],
            units=t.get("units"), timestamp=ts,
        ))
        db.commit()

    @staticmethod
    def exists(db: Session, device_id: str) -> bool:
        return db.query(SensorReading.id).filter(SensorReading.device_id == device_id).first() is not None

    @staticmethod
    def find_latest(db: Session, device_id: str) -> Optional[dict]:
        row = (
            db.query(SensorReading)
            .filter(SensorReading.device_id == device_id)
            .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
            .first()
        )
        if not row:
            return None
        device = db.query(Device).filter(Device.id == device_id).first()
        units = {**UNIT_DEFAULTS, **{k: v for k, v in (row.units or {}).items() if v}}
        return {
            "temperature": row.temperature, "humidity": row.humidity, "gas": row.gas,
            "light": row.light, "sound": row.sound, "units": units, "timestamp": row.timestamp,
            "name": (device.name if device else None) or "",
            "hidden": bool(device.hidden) if device else False,
        }

    @staticmethod
    def prune(db: Session, device_id: str, keep: int = 500) -> None:
        """Keep only the newest `keep` readings of the device (the simulator writes continuously)."""
        ids = (
            db.query(SensorReading.id)
            .filter(SensorReading.device_id == device_id)
            .order_by(SensorReading.id.desc())
            .offset(keep).limit(1).first()
        )
        if ids:
            db.query(SensorReading).filter(
                SensorReading.device_id == device_id, SensorReading.id <= ids[0]
            ).delete(synchronize_session=False)
            db.commit()
