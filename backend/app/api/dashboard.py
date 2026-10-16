"""Dashboard statistics endpoint."""

from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app import models
from app.schemas import DashboardStats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    total_services = db.query(models.Service).count()
    healthy = db.query(models.Service).filter(models.Service.status == "healthy").count()
    warning = db.query(models.Service).filter(models.Service.status == "warning").count()
    critical = db.query(models.Service).filter(models.Service.status == "critical").count()

    active_incidents = (
        db.query(models.Incident).filter(models.Incident.status == "open").count()
    )

    sev_rows = (
        db.query(models.Incident.severity, func.count(models.Incident.id))
        .group_by(models.Incident.severity)
        .all()
    )
    incidents_by_severity = {r[0]: r[1] for r in sev_rows}

    status_rows = (
        db.query(models.Incident.status, func.count(models.Incident.id))
        .group_by(models.Incident.status)
        .all()
    )
    incidents_by_status = {r[0]: r[1] for r in status_rows}

    recent = (
        db.query(models.LogEvent)
        .order_by(desc(models.LogEvent.timestamp))
        .limit(20)
        .all()
    )
    recent_events = [
        {
            "id": r.id,
            "service": r.service,
            "environment": r.environment,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "level": r.level,
            "message": r.message,
        }
        for r in recent
    ]

    # Error trend: count of ERROR/FATAL per hour over last 24 hours (buckets)
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    buckets: List[Dict] = []
    for i in range(23, -1, -1):
        start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
        end = start + timedelta(hours=1)
        cnt = (
            db.query(models.LogEvent)
            .filter(models.LogEvent.level.in_(["ERROR", "FATAL"]))
            .filter(models.LogEvent.timestamp >= start)
            .filter(models.LogEvent.timestamp < end)
            .count()
        )
        buckets.append({"ts": start.isoformat(), "count": cnt})

    service_health = [
        {
            "name": s.name,
            "environment": s.environment,
            "status": s.status,
        }
        for s in db.query(models.Service).order_by(models.Service.name).all()
    ]

    return DashboardStats(
        total_services=total_services,
        healthy_services=healthy,
        warning_services=warning,
        critical_services=critical,
        active_incidents=active_incidents,
        incidents_by_severity=incidents_by_severity,
        incidents_by_status=incidents_by_status,
        recent_events=recent_events,
        error_trend=buckets,
        service_health=service_health,
    )
