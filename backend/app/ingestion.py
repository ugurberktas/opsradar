"""Shared, transactional log-ingestion service."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app import models, parsers, redact
from app.detectors import detect_and_correlate


@dataclass(frozen=True)
class IngestionResult:
    ingested: int
    skipped: int
    incidents_created: int


def ingest_events(db: Session, raw_events: Iterable[dict[str, Any]]) -> IngestionResult:
    """Normalize, redact, deduplicate, persist, and correlate a batch.

    The caller owns the transaction and must commit or roll it back.
    """
    service_cache: dict[tuple[str, str], models.Service] = {}
    normalized_rows: list[dict[str, Any]] = []
    pending_keys: set[tuple[Any, ...]] = set()
    skipped = 0

    for raw in raw_events:
        if raw.get("_parse_error"):
            skipped += 1
            continue
        try:
            event = parsers.normalize_event(raw)
        except (TypeError, ValueError, OverflowError):
            skipped += 1
            continue

        original_message = event["message"]
        original_raw = event.get("raw") or ""
        event["message"] = redact.redact_text(original_message)
        event["raw"] = redact.redact_text(original_raw)
        was_redacted = redact.is_sensitive(original_message) or redact.is_sensitive(original_raw)

        identity = (
            event["service"],
            event["environment"],
            event["timestamp"],
            event["level"],
            event["message"],
        )
        if identity in pending_keys:
            skipped += 1
            continue
        duplicate = (
            db.query(models.LogEvent.id)
            .filter(
                models.LogEvent.service == event["service"],
                models.LogEvent.environment == event["environment"],
                models.LogEvent.timestamp == event["timestamp"],
                models.LogEvent.level == event["level"],
                models.LogEvent.message == event["message"],
            )
            .first()
        )
        if duplicate:
            skipped += 1
            continue
        pending_keys.add(identity)

        service_key = (event["service"], event["environment"])
        service = service_cache.get(service_key)
        if service is None:
            service = (
                db.query(models.Service)
                .filter(
                    models.Service.name == event["service"],
                    models.Service.environment == event["environment"],
                )
                .first()
            )
            if service is None:
                service = models.Service(
                    name=event["service"],
                    environment=event["environment"],
                    status="healthy",
                    last_heartbeat=event["timestamp"],
                )
                db.add(service)
                db.flush()
            service_cache[service_key] = service

        if service.last_heartbeat is None or event["timestamp"] > service.last_heartbeat:
            service.last_heartbeat = event["timestamp"]
        log_event = models.LogEvent(
            service_id=service.id,
            service=event["service"],
            environment=event["environment"],
            timestamp=event["timestamp"],
            level=event["level"],
            message=event["message"],
            raw=event["raw"],
            redacted=was_redacted,
        )
        db.add(log_event)
        normalized_rows.append(
            {
                **event,
                "_model": log_event,
                "_service_id": service.id,
            }
        )

    db.flush()
    detector_events = [
        {
            **event,
            "_log_event_id": event["_model"].id,
        }
        for event in normalized_rows
    ]
    detection = detect_and_correlate(db, detector_events)
    return IngestionResult(
        ingested=len(normalized_rows),
        skipped=skipped,
        incidents_created=len(detection.incidents),
    )
