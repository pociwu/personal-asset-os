from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.readiness import ReadinessResult
from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class FakeReadinessProbe:
    result: ReadinessResult

    async def check(self) -> ReadinessResult:
        return self.result

    async def close(self) -> None:
        return None


@pytest.mark.anyio
async def test_readiness_reports_ready_when_dependencies_are_available() -> None:
    response = await _get_readiness(postgres=True, redis=True)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"postgres": "ok", "redis": "ok"},
    }
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("postgres", "redis", "expected_dependencies"),
    [
        (False, True, {"postgres": "unavailable", "redis": "ok"}),
        (True, False, {"postgres": "ok", "redis": "unavailable"}),
        (
            False,
            False,
            {"postgres": "unavailable", "redis": "unavailable"},
        ),
    ],
)
async def test_readiness_returns_503_without_internal_error_details(
    postgres: bool,
    redis: bool,
    expected_dependencies: dict[str, str],
) -> None:
    response = await _get_readiness(postgres=postgres, redis=redis)

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": expected_dependencies,
    }
    assert "password" not in response.text.lower()
    assert "exception" not in response.text.lower()


async def _get_readiness(*, postgres: bool, redis: bool):
    probe = FakeReadinessProbe(ReadinessResult(postgres=postgres, redis=redis))
    app = create_app(Settings(log_level="WARNING"), readiness_probe=probe)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.get("/api/v1/health/ready")
