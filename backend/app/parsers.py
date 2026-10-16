"""JSONL log parsing and normalization."""

import json
from datetime import UTC, datetime
from typing import Any

from app.time_utils import to_utc_naive, utc_now

MAX_MESSAGE_LENGTH = 10_000
MAX_RAW_LENGTH = 40_000
MAX_SERVICE_LENGTH = 100
MAX_ENVIRONMENT_LENGTH = 50
ALLOWED_LEVELS = {"DEBUG", "INFO", "WARN", "ERROR", "FATAL"}


def parse_jsonl(content: str) -> list[dict[str, Any]]:
    """Parse JSONL content into a list of raw dict objects.

    Malformed lines are marked so ingestion can count and skip them without
    failing the valid records in the same file.
    """
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                obj = {
                    "raw": line,
                    "message": f"Non-object JSON value on line {line_no}",
                    "_parse_error": True,
                }
        except json.JSONDecodeError:
            events.append(
                {
                    "raw": line,
                    "message": f"Malformed log line {line_no}",
                    "level": "ERROR",
                    "timestamp": utc_now().isoformat(),
                    "service": "unknown",
                    "environment": "unknown",
                    "_parse_error": True,
                }
            )
            continue
        events.append(obj)
    return events


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw parsed event into a canonical dict.

    Tolerates many timestamp / service / level field names.
    """
    ts_raw = (
        raw.get("timestamp")
        or raw.get("ts")
        or raw.get("@timestamp")
        or raw.get("time")
        or raw.get("datetime")
    )
    dt: datetime
    if ts_raw:
        try:
            if isinstance(ts_raw, (int, float)):
                seconds = float(ts_raw)
                if seconds > 10_000_000_000:
                    seconds /= 1000
                dt = datetime.fromtimestamp(seconds, UTC)
            else:
                dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            dt = to_utc_naive(dt)
        except (TypeError, ValueError, OverflowError):
            dt = utc_now()
    else:
        dt = utc_now()

    service = str(
        raw.get("service")
        or raw.get("serviceName")
        or raw.get("service_name")
        or raw.get("component")
        or "unknown"
    ).strip()[:MAX_SERVICE_LENGTH] or "unknown"
    environment = str(
        raw.get("environment")
        or raw.get("env")
        or raw.get("environment_name")
        or "production"
    ).strip()[:MAX_ENVIRONMENT_LENGTH] or "production"
    level = str(raw.get("level") or raw.get("severity") or "INFO").upper().strip()
    if level == "WARNING":
        level = "WARN"
    if level not in ALLOWED_LEVELS:
        level = "INFO"
    message = str(raw.get("message") or raw.get("msg") or raw.get("text") or "")

    return {
        "timestamp": dt,
        "service": service,
        "environment": environment,
        "level": level,
        "message": message[:MAX_MESSAGE_LENGTH],
        "raw": json.dumps(raw, default=str, ensure_ascii=False)[:MAX_RAW_LENGTH],
    }
