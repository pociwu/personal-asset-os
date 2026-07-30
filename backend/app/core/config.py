from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PAOS_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Personal Asset OS"
    app_env: str = "development"
    log_level: str = "INFO"
    postgres_host: str = "postgres"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "personal_asset_os"
    postgres_user: str = "personal_asset_os"
    postgres_password: SecretStr | None = None
    redis_host: str = "redis"
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_password: SecretStr | None = None
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=30)


@lru_cache
def get_settings() -> Settings:
    return Settings()
