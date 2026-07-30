from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["backend"]


@router.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    """Report process liveness without checking external dependencies."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="ok", service="backend")
