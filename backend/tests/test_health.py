from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_health_reports_backend_liveness() -> None:
    async with _client() as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend"}
    assert response.headers["cache-control"] == "no-store"
    UUID(response.headers["x-request-id"])


@pytest.mark.anyio
async def test_health_preserves_a_valid_caller_request_id() -> None:
    async with _client() as client:
        response = await client.get(
            "/api/v1/health",
            headers={"X-Request-ID": "phase0-smoke-001"},
        )

    assert response.headers["x-request-id"] == "phase0-smoke-001"


@pytest.mark.anyio
async def test_health_replaces_an_invalid_caller_request_id() -> None:
    async with _client() as client:
        response = await client.get(
            "/api/v1/health",
            headers={"X-Request-ID": "invalid request id"},
        )

    assert response.headers["x-request-id"] != "invalid request id"
    UUID(response.headers["x-request-id"])


def _client() -> AsyncClient:
    app = create_app(Settings(log_level="WARNING"))
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )
