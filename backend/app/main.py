from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.assets_income import router as assets_income_router
from app.api.v1.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.database import create_database_engine
from app.core.logging import configure_logging
from app.core.readiness import ExternalServicesReadinessProbe, ReadinessProbe
from app.core.request_context import install_request_context


def create_app(
    settings: Settings | None = None,
    readiness_probe: ReadinessProbe | None = None,
) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    active_probe = readiness_probe or ExternalServicesReadinessProbe(active_settings)
    database_engine = create_database_engine(active_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await database_engine.dispose()
        await active_probe.close()

    application = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.readiness_probe = active_probe
    application.state.session_factory = async_sessionmaker(
        database_engine, class_=AsyncSession, expire_on_commit=False
    )
    install_request_context(application)
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(assets_income_router, prefix="/api/v1")
    return application


app = create_app()
