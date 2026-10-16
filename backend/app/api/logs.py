"""Log ingestion and exploration endpoints."""


from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, parsers
from app.database import get_db
from app.ingestion import ingest_events
from app.schemas import LogEventOut, LogIngestRequest, LogIngestResponse

router = APIRouter(tags=["logs"])
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_UPLOAD_SUFFIXES = (".jsonl", ".log", ".txt")


@router.post("/logs/ingest", response_model=LogIngestResponse)
def ingest_logs(payload: LogIngestRequest, db: Session = Depends(get_db)):
    """Ingest raw log event objects (already parsed)."""
    try:
        result = ingest_events(db, payload.events)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return LogIngestResponse(**result.__dict__)


@router.post("/logs/ingest/file", response_model=LogIngestResponse)
def ingest_log_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and ingest a JSONL log file."""
    filename = (file.filename or "").lower()
    if not filename.endswith(ALLOWED_UPLOAD_SUFFIXES):
        raise HTTPException(status_code=415, detail="Upload a .jsonl, .log, or .txt file")
    body = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Log upload exceeds the 5 MiB limit",
        )
    content = body.decode("utf-8", errors="replace")
    raw_events = parsers.parse_jsonl(content)
    if not raw_events:
        raise HTTPException(status_code=422, detail="The uploaded file contains no log records")
    payload = LogIngestRequest(events=raw_events)
    return ingest_logs(payload, db)


@router.get("/logs", response_model=list[LogEventOut])
def list_logs(
    service: str | None = None,
    level: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
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
