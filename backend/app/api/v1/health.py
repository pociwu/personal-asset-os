from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from app.core.readiness import ReadinessProbe

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["backend"]


class DependencyStatus(BaseModel):
    postgres: Literal["ok", "unavailable"]
    redis: Literal["ok", "unavailable"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: DependencyStatus


@router.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    """Report process liveness without checking external dependencies."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="ok", service="backend")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(request: Request, response: Response) -> ReadinessResponse:
    """Report dependency readiness without returning internal error details."""
    probe: ReadinessProbe = request.app.state.readiness_probe
    result = await probe.check()
    response.headers["Cache-Control"] = "no-store"
    if not result.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if result.ready else "not_ready",
        dependencies=DependencyStatus(
            postgres="ok" if result.postgres else "unavailable",
            redis="ok" if result.redis else "unavailable",
        ),
    )
