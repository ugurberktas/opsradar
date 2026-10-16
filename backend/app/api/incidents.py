"""Incident management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models
from app.schemas import IncidentOut, IncidentUpdate

router = APIRouter(tags=["incidents"])


def _to_schema(inc: models.Incident, db: Session) -> IncidentOut:
    related = db.query(models.IncidentEvent).filter(
        models.IncidentEvent.incident_id == inc.id
    ).count()
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


@router.get("/incidents", response_model=List[IncidentOut])
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    service: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Incident).order_by(desc(models.Incident.last_seen))
    if status:
        q = q.filter(models.Incident.status == status)
    if severity:
        q = q.filter(models.Incident.severity == severity.upper())
    if service:
        q = q.filter(models.Incident.service.ilike(f"%{service}%"))
    return [_to_schema(inc, db) for inc in q.all()]


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_schema(inc, db)


@router.patch("/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db)
):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    from datetime import datetime

    if payload.status:
        inc.status = payload.status
        if payload.status == "acknowledged" and not inc.acknowledged_at:
            inc.acknowledged_at = datetime.utcnow()
        if payload.status == "resolved" and not inc.resolved_at:
            inc.resolved_at = datetime.utcnow()
    db.add(inc)
    db.commit()
    return _to_schema(inc, db)
