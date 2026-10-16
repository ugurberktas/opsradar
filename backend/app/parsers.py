"""JSONL log parsing and normalization."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_jsonl(content: str) -> List[Dict[str, Any]]:
    """Parse JSONL content into a list of raw dict objects.

    Malformed lines are captured gracefully as synthetic error events
    instead of failing the entire ingestion.
    """
    events: List[Dict[str, Any]] = []
    for line_no, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                obj = {"message": str(obj), "level": "ERROR"}
        except json.JSONDecodeError:
            events.append(
                {
                    "raw": line,
                    "message": f"Malformed log line {line_no}",
                    "level": "ERROR",
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "unknown",
                    "environment": "unknown",
                    "_parse_error": True,
                }
            )
            continue
        events.append(obj)
    return events


def normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
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
            dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
        except Exception:
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()

    return {
        "timestamp": dt,
        "service": str(
            raw.get("service")
            or raw.get("serviceName")
            or raw.get("service_name")
            or raw.get("component")
            or "unknown"
        ),
        "environment": str(
            raw.get("environment")
            or raw.get("env")
            or raw.get("environment_name")
            or "production"
        ),
        "level": str(raw.get("level") or raw.get("severity") or "INFO").upper(),
        "message": str(raw.get("message") or raw.get("msg") or raw.get("text") or ""),
        "raw": json.dumps(raw, default=str)[:4000],
    }
