import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers.auth import router as auth_router
from app.routers.locations import router as locations_router
from app.routers.comfort import router as comfort_router
from app import simulator
from app.mqtt_client import mqtt_client
from app.telemetry import handle_message

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    # MQTT is optional: without MQTT_URL the backend runs with REST (+ simulator) only
    mqtt_client.initialize(asyncio.get_running_loop(), handle_message)
    sim_task = simulator.start()  # no-op unless SIMULATE_DEVICES=true
    yield
    if sim_task:
        sim_task.cancel()
    mqtt_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Smart School Environment system. Covers Authentication, Users, and Locations.",
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

# Register routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(locations_router, prefix=settings.API_V1_PREFIX)
app.include_router(comfort_router)  # /api/comfort/...


@app.get("/health", tags=["Health"])
def healthcheck():
    """Service health status check."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
