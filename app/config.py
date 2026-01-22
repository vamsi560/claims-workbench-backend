from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import Field
import os


class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    environment: str = "production"
    log_level: str = "INFO"
    frontend_url: str = Field(default="https://yellow-dune-0859cda0f.4.azurestaticapps.net", alias="FRONTEND_URL")

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url, "http://localhost:5173", "http://localhost:3000"]

    otel_service_name: str = "fnol-observability-api"
    otel_exporter_endpoint: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        allow_population_by_field_name = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
