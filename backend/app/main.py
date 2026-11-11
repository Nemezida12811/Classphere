import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db import init_db
from app.errors import ok
from app.routers.auth import router as auth_router
from app.routers.comfort import router as comfort_router
from app.routers.frontend_auth import router as frontend_auth_router
from app.routers.frontend_locations import router as frontend_locations_router
from app.routers.locations import router as locations_router
from app.simulator import simulator
from app.telemetry import handle_message

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    if settings.SIMULATE_DEVICE:
        await simulator.start()  # fake devices, no MQTT broker / hardware needed
    if settings.mqtt_url:  # real devices via MQTT (optional)
        from app.mqtt_client import mqtt_client
        mqtt_client.initialize(asyncio.get_running_loop(), handle_message)
    yield
    # Shutdown
    await simulator.stop()
    if settings.mqtt_url:
        from app.mqtt_client import mqtt_client
        mqtt_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Smart School Environment system. Covers Authentication, Users, Locations, "
                "device telemetry and comfort.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS setup for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- error format ---
# The frontend (/api/auth, /api/locations, /api/comfort) expects {"success": false, "error": "<message>"}.
# /api/v1/* keeps FastAPI's default {"detail": ...}.
def _frontend_api(request: Request) -> bool:
    path = request.url.path
    return path.startswith("/api/") and not path.startswith(settings.API_V1_PREFIX + "/")


@app.exception_handler(StarletteHTTPException)
async def _http_error(request: Request, exc: StarletteHTTPException):
    if _frontend_api(request):
        return JSONResponse({"success": False, "error": str(exc.detail)}, status_code=exc.status_code,
                            headers=getattr(exc, "headers", None))
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    if _frontend_api(request):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", ()) if p not in ("body", "query", "path"))
        message = f"{field}: {first.get('msg', 'Invalid request')}" if field else first.get("msg", "Invalid request")
        return JSONResponse({"success": False, "error": message}, status_code=422)
    return await request_validation_exception_handler(request, exc)


# Register routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(locations_router, prefix=settings.API_V1_PREFIX)
app.include_router(frontend_auth_router)
app.include_router(frontend_locations_router)
app.include_router(comfort_router)


@app.get("/health", tags=["Health"])
def healthcheck():
    """Service health status check."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/api/simulator/devices", tags=["Simulator"])
def simulator_devices():
    """Ids of simulated devices (copy one into 'Add room' in the UI). Empty unless SIMULATE_DEVICE=true."""
    return ok({"enabled": settings.SIMULATE_DEVICE, "devices": simulator.describe()})


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
