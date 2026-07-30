import logging
import re
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_logger = logging.getLogger("personal_asset_os.http")


def install_request_context(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = _request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            _logger.exception(
                "http_request_failed",
                extra={
                    "event": "http_request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": _duration_ms(started_at),
                },
            )
            raise

        response.headers["X-Request-ID"] = request_id
        _logger.info(
            "http_request_completed",
            extra={
                "event": "http_request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": _duration_ms(started_at),
            },
        )
        return response


def _request_id(candidate: str | None) -> str:
    if candidate and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid4())


def _duration_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)
