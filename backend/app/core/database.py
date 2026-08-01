from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.secrets import load_secret_file


def create_database_engine(settings: Settings) -> AsyncEngine:
    secret = load_secret_file(
        settings.postgres_password_file,
        name="postgres_password",
        required=settings.app_env.casefold() == "production",
    )
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=settings.postgres_user,
        password=secret.get_secret_value() if secret else None,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )
    return create_async_engine(url, pool_pre_ping=True)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session
