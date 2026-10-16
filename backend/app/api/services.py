"""Service endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.schemas import ServiceOut

router = APIRouter(tags=["services"])


@router.get("/services", response_model=List[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    services = db.query(models.Service).order_by(models.Service.name).all()
    result = []
    for s in services:
        log_count = (
            db.query(models.LogEvent)
            .filter(models.LogEvent.service_id == s.id)
            .count()
        )
        incident_count = (
            db.query(models.Incident)
            .filter(models.Incident.service_id == s.id)
            .count()
        )
        result.append(
            ServiceOut(
                id=s.id,
                name=s.name,
                environment=s.environment,
                status=s.status,
                last_heartbeat=s.last_heartbeat,
                log_count=log_count,
                incident_count=incident_count,
            )
        )
    return result


@router.get("/services/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Service).get(service_id)
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
