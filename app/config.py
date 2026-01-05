from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    environment: str = "production"
    log_level: str = "INFO"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    otel_service_name: str = "fnol-observability-api"
    otel_exporter_endpoint: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
