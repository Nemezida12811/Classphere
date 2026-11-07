import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import HTTPException, status

log = logging.getLogger("api")


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


class ApiError(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)


def ok(data):
    """Standard success envelope used by the sensor/comfort endpoints."""
    return {"success": True, "data": data}


def iso(dt: datetime) -> str:
    """datetime -> 'YYYY-MM-DDTHH:MM:SS.mmmZ' (naive datetimes are treated as UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


@contextmanager
def failing_as(message: str, with_details: bool = False):
    """Let HTTP errors through; turn any other exception into a 500 with `message`."""
    try:
        yield
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("%s", message)
        raise ApiError(500, f"{message}: {exc}" if with_details else message)
