from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# SQLite needs connect_args for multithreading
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="student", nullable=False)  # student, teacher, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "Room 204", "Physics Lab"
    building = Column(String(50), nullable=False, default="Main")
    floor = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Owner of the location (set by the /api/locations endpoints used by the frontend)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)


class LocationMember(Base):
    """Users who joined a location (besides its admin)."""
    __tablename__ = "location_members"

    location_id = Column(Integer, ForeignKey("locations.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)


class Device(Base):
    """A room/device attached to a location. `id` is the device id from telemetry (com-<hex>-fort)."""
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=True)
    hidden = Column(Boolean, default=False, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SensorReading(Base):
    """One telemetry measurement (already converted to physical units). `timestamp` is naive UTC."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    gas = Column(Float, nullable=False)
    light = Column(Float, nullable=False)
    sound = Column(Float, nullable=False)
    units = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
