from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.request_context import install_request_context


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    application = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
    )
    install_request_context(application)
    application.include_router(health_router, prefix="/api/v1")
    return application


app = create_app()
