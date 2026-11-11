"""Locations / rooms (devices) in the format used by frontend/client (/api/locations/...).
The classic REST endpoints under /api/v1/locations stay untouched."""
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import Device, Location, LocationMember, User, get_db
from app.errors import ConflictException, EntityNotFoundException, ForbiddenException, iso, ok
from app.repositories import SensorReadings
from app.security import get_current_user

router = APIRouter(prefix="/api/locations", tags=["Locations (frontend API)"])


class LocationIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TargetUserIn(BaseModel):
    targetUserId: str


class DeviceIn(BaseModel):
    deviceId: str = Field(..., min_length=1, max_length=64)
    name: Optional[str] = Field(None, max_length=100)


def _serialize(db: Session, loc: Location) -> dict:
    members = [m.user_id for m in db.query(LocationMember).filter(LocationMember.location_id == loc.id)]
    user_ids = list(dict.fromkeys(([loc.admin_id] if loc.admin_id else []) + members))
    devices = [d.id for d in db.query(Device).filter(Device.location_id == loc.id).order_by(Device.created_at)]
    return {
        "id": str(loc.id),
        "name": loc.name,
        "adminId": str(loc.admin_id) if loc.admin_id else "",
        "userIds": [str(i) for i in user_ids],
        "deviceIds": devices,
        "createdAt": iso(loc.created_at),
    }


def _get_location(db: Session, location_id: int) -> Location:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise EntityNotFoundException("Location not found")
    return loc


def _get_admin_location(db: Session, location_id: int, user: User) -> Location:
    loc = _get_location(db, location_id)
    if loc.admin_id != user.id:
        raise ForbiddenException("Only the location admin can do this")
    return loc


def _get_device(db: Session, loc: Location, device_id: str) -> Device:
    dev = db.query(Device).filter(Device.id == device_id, Device.location_id == loc.id).first()
    if not dev:
        raise EntityNotFoundException("Device not found in this location")
    return dev


@router.get("")
def list_locations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    created = db.query(Location).filter(Location.admin_id == user.id).order_by(Location.id).all()
    joined_ids = [m.location_id for m in db.query(LocationMember).filter(LocationMember.user_id == user.id)]
    joined = (
        db.query(Location).filter(Location.id.in_(joined_ids), Location.admin_id != user.id).order_by(Location.id).all()
        if joined_ids else []
    )
    return ok({"created": [_serialize(db, l) for l in created], "joined": [_serialize(db, l) for l in joined]})


@router.post("", status_code=status.HTTP_201_CREATED)
def create_location(body: LocationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise ConflictException("Location name must not be empty")
    if db.query(Location).filter(Location.name == name).first():
        raise ConflictException(f"Location '{name}' already exists")
    loc = Location(name=name, building="Main", floor=1, is_active=True, admin_id=user.id)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return ok({"id": str(loc.id), "name": loc.name, "adminId": str(user.id)})


@router.get("/{location_id}")
def get_location(location_id: int, db: Session = Depends(get_db)):
    # Public on purpose: the frontend shows a location to visitors who are not logged in.
    return ok(_serialize(db, _get_location(db, location_id)))


@router.patch("/{location_id}")
def rename_location(location_id: int, body: LocationIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    loc = _get_admin_location(db, location_id, user)
    name = body.name.strip()
    clash = db.query(Location).filter(Location.name == name, Location.id != loc.id).first()
    if clash or not name:
        raise ConflictException(f"Location '{name}' already exists" if clash else "Location name must not be empty")
    loc.name = name
    db.commit()
    return ok({"message": "Location updated", "name": loc.name})


@router.delete("/{location_id}")
def delete_location(location_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loc = _get_admin_location(db, location_id, user)
    db.query(LocationMember).filter(LocationMember.location_id == loc.id).delete(synchronize_session=False)
    db.query(Device).filter(Device.location_id == loc.id).delete(synchronize_session=False)
    db.delete(loc)
    db.commit()
    return ok({"message": "Location deleted"})


# ---------------- users ----------------
@router.post("/{location_id}/users")
def add_user(location_id: int, body: TargetUserIn, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """Join a location yourself (the frontend 'join by id' flow) or, as admin, add another user."""
    loc = _get_location(db, location_id)
    if not body.targetUserId.isdigit():
        raise EntityNotFoundException("User not found")
    target_id = int(body.targetUserId)
    if target_id != user.id and loc.admin_id != user.id:
        raise ForbiddenException("Only the location admin can add other users")
    if not db.query(User.id).filter(User.id == target_id).first():
        raise EntityNotFoundException("User not found")
    already = target_id == loc.admin_id or db.query(LocationMember).filter(
        LocationMember.location_id == loc.id, LocationMember.user_id == target_id).first()
    if not already:
        db.add(LocationMember(location_id=loc.id, user_id=target_id))
        db.commit()
    return ok({"message": "User already has access" if already else "User added to location"})


@router.delete("/{location_id}/users/{target_user_id}")
def remove_user(location_id: int, target_user_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    loc = _get_location(db, location_id)
    if target_user_id != user.id and loc.admin_id != user.id:
        raise ForbiddenException("Only the location admin can remove other users")
    if target_user_id == loc.admin_id:
        raise ConflictException("The location admin cannot be removed")
    member = db.query(LocationMember).filter(
        LocationMember.location_id == loc.id, LocationMember.user_id == target_user_id).first()
    if not member:
        raise EntityNotFoundException("User is not a member of this location")
    db.delete(member)
    db.commit()
    return ok({"message": "User removed from location"})


# ---------------- devices (rooms) ----------------
@router.post("/{location_id}/devices", status_code=status.HTTP_201_CREATED)
def add_device(location_id: int, body: DeviceIn, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    loc = _get_admin_location(db, location_id, user)
    device_id = body.deviceId.strip()
    if not SensorReadings.exists(db, device_id):
        raise EntityNotFoundException("Device not found: no telemetry received from it yet")
    dev = db.query(Device).filter(Device.id == device_id).first()
    if dev and dev.location_id is not None:
        raise ConflictException(
            "Device is already added to this location" if dev.location_id == loc.id
            else "Device is already added to another location")
    name = (body.name or "").strip() or None
    if dev:
        dev.location_id, dev.name = loc.id, name
    else:
        db.add(Device(id=device_id, name=name, location_id=loc.id))
    db.commit()
    return ok({"message": "Device added to location"})


@router.patch("/{location_id}/devices/{device_id}/hide")
def hide_device(location_id: int, device_id: str, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    dev = _get_device(db, _get_admin_location(db, location_id, user), device_id)
    dev.hidden = True
    db.commit()
    return ok({"message": "Device hidden"})


@router.patch("/{location_id}/devices/{device_id}/show")
def show_device(location_id: int, device_id: str, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    dev = _get_device(db, _get_admin_location(db, location_id, user), device_id)
    dev.hidden = False
    db.commit()
    return ok({"message": "Device is visible again"})


@router.delete("/{location_id}/devices/{device_id}")
def remove_device(location_id: int, device_id: str, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    dev = _get_device(db, _get_admin_location(db, location_id, user), device_id)
    db.delete(dev)
    db.commit()
    return ok({"message": "Device removed from location"})
