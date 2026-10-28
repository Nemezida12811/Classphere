from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db import get_db, User
from app.errors import ConflictException, EntityNotFoundException
from app.repositories import LocationRepository
from app.schemas import LocationCreate, LocationResponse, LocationUpdate
from app.security import get_current_user

router = APIRouter(prefix="/locations", tags=["Locations & Rooms"])


@router.get("/", response_model=List[LocationResponse])
def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve all school locations / rooms."""
    repo = LocationRepository(db)
    return repo.get_all(skip=skip, limit=limit)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    loc_in: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new location / room (requires authentication)."""
    repo = LocationRepository(db)

    if repo.get_by_name(loc_in.name):
        raise ConflictException(detail=f"Location '{loc_in.name}' already exists")

    return repo.create(loc_in)


@router.get("/{location_id}", response_model=LocationResponse)
def get_location_by_id(location_id: int, db: Session = Depends(get_db)):
    """Get location details by ID."""
    repo = LocationRepository(db)
    location = repo.get_by_id(location_id)
    if not location:
        raise EntityNotFoundException(detail=f"Location with id {location_id} not found")
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    loc_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update location details (requires authentication)."""
    repo = LocationRepository(db)
    updated = repo.update(location_id, loc_in)
    if not updated:
        raise EntityNotFoundException(detail=f"Location with id {location_id} not found")
    return updated


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a location by ID (requires authentication)."""
    repo = LocationRepository(db)
    deleted = repo.delete(location_id)
    if not deleted:
        raise EntityNotFoundException(detail=f"Location with id {location_id} not found")
    return None
