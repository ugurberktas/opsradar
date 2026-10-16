"""Pydantic schemas for OpsRadar API."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.time_utils import utc_iso


class APIModel(BaseModel):
    """Base response model that emits explicit UTC timestamps."""

    @field_serializer("*", when_used="json", check_fields=False)
    def serialize_utc_datetimes(self, value):
        return utc_iso(value) if isinstance(value, datetime) else value


# ---------- Services ----------
class ServiceBase(APIModel):
    name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(default="production", max_length=50)
    status: Literal["healthy", "warning", "critical"] = "healthy"


class ServiceCreate(ServiceBase):
    pass


class ServiceOut(ServiceBase):
    id: int
    last_heartbeat: datetime | None = None
    log_count: int = 0
    incident_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------- Logs ----------
class LogEventBase(APIModel):
    service: str = Field(min_length=1, max_length=100)
    environment: str = Field(default="production", min_length=1, max_length=50)
    timestamp: datetime
    level: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] = "INFO"
    message: str = Field(max_length=10_000)
    raw: str | None = Field(default=None, max_length=40_000)


class LogEventCreate(LogEventBase):
    pass


class LogEventOut(LogEventBase):
    id: int
    service_id: int | None = None
    signature: str | None = None
    redacted: bool = False

    model_config = ConfigDict(from_attributes=True)


class LogIngestRequest(APIModel):
    events: Annotated[list[dict], Field(min_length=1, max_length=5_000)]


class LogIngestResponse(APIModel):
    ingested: int
    skipped: int
    incidents_created: int


# ---------- Incidents ----------
class IncidentBase(APIModel):
    title: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    status: Literal["open", "acknowledged", "resolved"] = "open"
    service: str
    environment: str = "production"
    signature: str
    event_count: int = 1
    confidence: float = 0.0
    root_cause: str | None = None
    root_cause_confidence: str | None = None
    suggested_steps: list[str] | None = None
    suggested_remediation: list[str] | None = None


class IncidentUpdate(APIModel):
    status: Literal["open", "acknowledged", "resolved"]


class IncidentOut(IncidentBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    related_log_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------- Dashboard ----------
class DashboardStats(APIModel):
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    active_incidents: int
    incidents_by_severity: dict  # {INFO: n, WARNING: n, CRITICAL: n}
    incidents_by_status: dict
    recent_events: list[dict]
    error_trend: list[dict]  # [{ts, count}]
    service_health: list[dict]


# ---------- Simulation ----------
class SimulationResponse(APIModel):
    events_generated: int
    incidents_detected: int
    scenario: str
