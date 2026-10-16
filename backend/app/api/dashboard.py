"""Dashboard statistics endpoint."""


from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import DashboardStats
from app.time_utils import utc_iso, utc_now

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    service_counts = dict(
        db.query(models.Service.status, func.count(models.Service.id))
        .group_by(models.Service.status)
        .all()
    )
    total_services = sum(service_counts.values())
    healthy = service_counts.get("healthy", 0)
    warning = service_counts.get("warning", 0)
    critical = service_counts.get("critical", 0)

    active_filter = models.Incident.status.in_(("open", "acknowledged"))
    active_incidents = db.query(models.Incident).filter(active_filter).count()

    sev_rows = (
        db.query(models.Incident.severity, func.count(models.Incident.id))
        .filter(active_filter)
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
            "timestamp": utc_iso(r.timestamp) if r.timestamp else None,
            "level": r.level,
            "message": r.message,
        }
        for r in recent
    ]

    # Error trend: count of ERROR/FATAL per hour over last 24 hours (buckets)
    from datetime import timedelta

    now = utc_now()
    first_bucket = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
    error_rows = (
        db.query(models.LogEvent.timestamp)
        .filter(
            models.LogEvent.level.in_(["ERROR", "FATAL"]),
            models.LogEvent.timestamp >= first_bucket,
        )
        .all()
    )
    counts_by_hour: dict = {}
    for (timestamp,) in error_rows:
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        counts_by_hour[hour] = counts_by_hour.get(hour, 0) + 1
    buckets: list[dict] = []
    for i in range(23, -1, -1):
        start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
        buckets.append({"ts": utc_iso(start), "count": counts_by_hour.get(start, 0)})

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
