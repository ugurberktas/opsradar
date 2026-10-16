"""Incident management endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import IncidentOut, IncidentUpdate

router = APIRouter(tags=["incidents"])


def _to_schema(inc: models.Incident, related: int) -> IncidentOut:
    return IncidentOut(
        id=inc.id,
        title=inc.title,
        severity=inc.severity,
        status=inc.status,
        service=inc.service,
        environment=inc.environment,
        signature=inc.signature,
        event_count=inc.event_count,
        confidence=inc.confidence,
        root_cause=inc.root_cause,
        root_cause_confidence=inc.root_cause_confidence,
        suggested_steps=inc.suggested_steps.split("\n") if inc.suggested_steps else [],
        suggested_remediation=(
            inc.suggested_remediation.split("\n") if inc.suggested_remediation else []
        ),
        first_seen=inc.first_seen,
        last_seen=inc.last_seen,
        acknowledged_at=inc.acknowledged_at,
        resolved_at=inc.resolved_at,
        created_at=inc.created_at,
        related_log_count=related,
    )


@router.get("/incidents", response_model=list[IncidentOut])
def list_incidents(
    status: Literal["open", "acknowledged", "resolved"] | None = None,
    severity: Literal["INFO", "WARNING", "CRITICAL"] | None = None,
    service: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(models.Incident).order_by(desc(models.Incident.last_seen))
    if status:
        q = q.filter(models.Incident.status == status)
    if severity:
        q = q.filter(models.Incident.severity == severity.upper())
    if service:
        q = q.filter(models.Incident.service.ilike(f"%{service}%"))
    incidents = q.limit(limit).all()
    incident_ids = [incident.id for incident in incidents]
    counts = {
        row[0]: row[1]
        for row in db.query(
            models.IncidentEvent.incident_id,
            func.count(models.IncidentEvent.id),
        )
        .filter(models.IncidentEvent.incident_id.in_(incident_ids))
        .group_by(models.IncidentEvent.incident_id)
        .all()
    } if incident_ids else {}
    return [_to_schema(incident, counts.get(incident.id, 0)) for incident in incidents]


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.get(models.Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    related = db.query(models.IncidentEvent).filter(
        models.IncidentEvent.incident_id == inc.id
    ).count()
    return _to_schema(inc, related)


@router.patch("/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db)
):
    inc = db.get(models.Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    allowed = {
        "open": {"open", "acknowledged", "resolved"},
        "acknowledged": {"acknowledged", "resolved"},
        "resolved": {"resolved"},
    }
    if payload.status not in allowed[inc.status]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition incident from {inc.status} to {payload.status}",
        )

    from app.detectors import recompute_service_status
    from app.time_utils import utc_now

    inc.status = payload.status
    if payload.status == "acknowledged" and not inc.acknowledged_at:
        inc.acknowledged_at = utc_now()
    if payload.status == "resolved" and not inc.resolved_at:
        inc.resolved_at = utc_now()
    try:
        db.flush()
        recompute_service_status(db, inc.service_id)
        db.commit()
        db.refresh(inc)
    except Exception:
        db.rollback()
        raise
    related = db.query(models.IncidentEvent).filter(
        models.IncidentEvent.incident_id == inc.id
    ).count()
    return _to_schema(inc, related)
