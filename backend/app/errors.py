from fastapi import HTTPException, status


class EntityNotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ---- helpers for the frontend-facing API (/api/auth, /api/locations, /api/comfort) ----
from datetime import datetime, timezone  # noqa: E402


def iso(dt: datetime | None) -> str | None:
    """ISO-8601 UTC string with 'Z'. Naive datetimes are treated as UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def ok(data):
    """Envelope expected by frontend/client/src/newRestApiService.tsx (it reads `json.data`)."""
    return {"success": True, "data": data}
