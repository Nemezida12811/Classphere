import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart School Environment API"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_change_me_in_production_1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database: SQLite by default for easy local dev; Postgres in prod/docker
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./school_env.db")

    # Server (used by `python -m app`)
    HOST: str = "127.0.0.1"
    PORT: int = 3001  # the frontend (frontend/client) calls http://localhost:3001

    # Built-in device simulator: generates telemetry in-process, no MQTT broker / hardware needed
    SIMULATE_DEVICE: bool = False
    SIM_DEVICES: int = 3
    SIM_INTERVAL_SECONDS: float = 3.0
    SIM_SPEED: float = 30.0  # 1 real second == SIM_SPEED simulated seconds

    # Optional MQTT (real devices). Empty -> MQTT is disabled.
    mqtt_url: str = ""
    mqtt_client_id: str = "school-env-backend"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
