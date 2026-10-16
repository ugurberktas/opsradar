"""Log ingestion and exploration endpoints."""

import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models, parsers, redact
from app.schemas import LogEventOut, LogIngestRequest, LogIngestResponse

router = APIRouter(tags=["logs"])


@router.post("/logs/ingest", response_model=LogIngestResponse)
def ingest_logs(payload: LogIngestRequest, db: Session = Depends(get_db)):
    """Ingest raw log event objects (already parsed)."""
    ingested = 0
    skipped = 0
    service_cache: dict = {}

    for raw in payload.events:
        try:
            ev = parsers.normalize_event(raw)
        except Exception:
            skipped += 1
            continue

        ev["message"] = redact.redact_text(ev["message"])
        ev["raw"] = redact.redact_text(ev.get("raw") or "")

        svc_name = ev["service"]
        svc = service_cache.get(svc_name)
        if svc is None:
            svc = (
                db.query(models.Service)
                .filter(models.Service.name == svc_name)
                .filter(models.Service.environment == ev["environment"])
                .first()
            )
            if svc is None:
                svc = models.Service(
                    name=svc_name, environment=ev["environment"], status="healthy"
                )
                db.add(svc)
                db.flush()
            service_cache[svc_name] = svc

        le = models.LogEvent(
            service_id=svc.id,
            service=ev["service"],
            environment=ev["environment"],
            timestamp=ev["timestamp"],
            level=ev["level"],
            message=ev["message"],
            raw=ev["raw"],
            redacted=True,
        )
        db.add(le)
        ingested += 1

    db.flush()
    from app.detectors import detect_and_correlate

    # Build normalized list for detector from what we just inserted
    recent = (
        db.query(models.LogEvent)
        .order_by(desc(models.LogEvent.timestamp))
        .limit(ingested)
        .all()
    )
    normalized_for_detect = [
        {
            "service": r.service,
            "environment": r.environment,
            "timestamp": r.timestamp,
            "level": r.level,
            "message": r.message,
        }
        for r in recent
    ]
    detect_and_correlate(db, normalized_for_detect)
    db.commit()

    return LogIngestResponse(
        ingested=ingested, skipped=skipped, incidents_created=0
    )


@router.post("/logs/ingest/file", response_model=LogIngestResponse)
def ingest_log_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and ingest a JSONL log file."""
    content = file.file.read().decode("utf-8", errors="replace")
    raw_events = parsers.parse_jsonl(content)
    payload = LogIngestRequest(events=raw_events)
    return ingest_logs(payload, db)


@router.get("/logs", response_model=List[LogEventOut])
def list_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(models.LogEvent).order_by(desc(models.LogEvent.timestamp))
    if service:
        q = q.filter(models.LogEvent.service.ilike(f"%{service}%"))
    if level:
        q = q.filter(models.LogEvent.level == level.upper())
    if search:
        like = f"%{search}%"
        q = q.filter(models.LogEvent.message.ilike(like))
    return q.limit(limit).all()
