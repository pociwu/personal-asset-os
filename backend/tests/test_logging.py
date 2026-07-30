import json
import logging
from datetime import datetime

from app.core.logging import JsonFormatter


def test_json_formatter_emits_machine_readable_request_context() -> None:
    record = logging.LogRecord(
        name="personal_asset_os.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request_completed",
        args=(),
        exc_info=None,
    )
    record.event = "http_request_completed"
    record.request_id = "phase0-smoke-001"
    record.status_code = 200

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "personal_asset_os.http"
    assert payload["message"] == "http_request_completed"
    assert payload["event"] == "http_request_completed"
    assert payload["request_id"] == "phase0-smoke-001"
    assert payload["status_code"] == 200
    datetime.fromisoformat(payload["timestamp"])
