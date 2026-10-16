"""Service endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ServiceOut

router = APIRouter(tags=["services"])


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    log_counts = (
        db.query(models.LogEvent.service_id.label("service_id"), func.count(models.LogEvent.id).label("count"))
        .group_by(models.LogEvent.service_id)
        .subquery()
    )
    incident_counts = (
        db.query(models.Incident.service_id.label("service_id"), func.count(models.Incident.id).label("count"))
        .group_by(models.Incident.service_id)
        .subquery()
    )
    rows = (
        db.query(
            models.Service,
            func.coalesce(log_counts.c.count, 0),
            func.coalesce(incident_counts.c.count, 0),
        )
        .outerjoin(log_counts, log_counts.c.service_id == models.Service.id)
        .outerjoin(incident_counts, incident_counts.c.service_id == models.Service.id)
        .order_by(models.Service.name, models.Service.environment)
        .all()
    )
    result = []
    for service, log_count, incident_count in rows:
        result.append(
            ServiceOut(
                id=service.id,
                name=service.name,
                environment=service.environment,
                status=service.status,
                last_heartbeat=service.last_heartbeat,
                log_count=log_count,
                incident_count=incident_count,
            )
        )
    return result


@router.get("/services/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    s = db.get(models.Service, service_id)
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")
    log_count = (
        db.query(models.LogEvent).filter(models.LogEvent.service_id == s.id).count()
    )
    incident_count = (
        db.query(models.Incident).filter(models.Incident.service_id == s.id).count()
    )
    return ServiceOut(
        id=s.id,
        name=s.name,
        environment=s.environment,
        status=s.status,
        last_heartbeat=s.last_heartbeat,
        log_count=log_count,
        incident_count=incident_count,
    )
