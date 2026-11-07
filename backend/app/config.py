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

    # MQTT (empty -> MQTT is disabled; the backend then works with REST + simulator only)
    mqtt_url: str = ""
    mqtt_client_id: str = "smart-school-backend"

    # Built-in device simulator: lets you run the whole project without a physical device
    simulate_devices: bool = False
    simulate_device_ids: str = "sim-room-1,sim-room-2,sim-room-3"
    simulate_interval_sec: float = 5.0

    # AI recommendations (optional; without a key a simple rule-based fallback is used)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
