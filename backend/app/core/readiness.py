import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings
from app.core.secrets import load_secret_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReadinessResult:
    postgres: bool
    redis: bool

    @property
    def ready(self) -> bool:
        return self.postgres and self.redis


class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessResult: ...

    async def close(self) -> None: ...


class ExternalServicesReadinessProbe:
    """Probe runtime dependencies without exposing connection error details."""

    def __init__(self, settings: Settings) -> None:
        secrets_required = settings.app_env.casefold() == "production"
        postgres_secret = load_secret_file(
            settings.postgres_password_file,
            name="postgres_password",
            required=secrets_required,
        )
        redis_secret = load_secret_file(
            settings.redis_password_file,
            name="redis_password",
            required=secrets_required,
        )
        postgres_password = (
            postgres_secret.get_secret_value() if postgres_secret else None
        )
        redis_password = redis_secret.get_secret_value() if redis_secret else None
        postgres_url = URL.create(
            drivername="postgresql+asyncpg",
            username=settings.postgres_user,
            password=postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
        )
        self._postgres: AsyncEngine = create_async_engine(postgres_url)
        self._redis: Redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=redis_password,
            decode_responses=True,
        )
        self._timeout_seconds = settings.readiness_timeout_seconds

    async def check(self) -> ReadinessResult:
        postgres_ok, redis_ok = await asyncio.gather(
            self._check_postgres(),
            self._check_redis(),
        )
        return ReadinessResult(postgres=postgres_ok, redis=redis_ok)

    async def close(self) -> None:
        await asyncio.gather(
            self._postgres.dispose(),
            self._redis.aclose(),
        )

    async def _check_postgres(self) -> bool:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with self._postgres.connect() as connection:
                    await connection.execute(text("SELECT 1"))
            return True
        except Exception as error:
            logger.warning(
                "readiness_dependency_unavailable",
                extra={
                    "dependency": "postgres",
                    "error_type": type(error).__name__,
                },
            )
            return False

    async def _check_redis(self) -> bool:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return bool(await self._redis.ping())
        except Exception as error:
            logger.warning(
                "readiness_dependency_unavailable",
                extra={
                    "dependency": "redis",
                    "error_type": type(error).__name__,
                },
            )
            return False
