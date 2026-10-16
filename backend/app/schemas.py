"""Pydantic schemas for OpsRadar API."""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


# ---------- Services ----------
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(default="production", max_length=50)
    status: str = Field(default="healthy", max_length=20)


class ServiceCreate(ServiceBase):
    pass


class ServiceOut(ServiceBase):
    id: int
    last_heartbeat: Optional[datetime] = None
    log_count: int = 0
    incident_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------- Logs ----------
class LogEventBase(BaseModel):
    service: str
    environment: str = "production"
    timestamp: datetime
    level: str = "INFO"
    message: str
    raw: Optional[str] = None


class LogEventCreate(LogEventBase):
    pass


class LogEventOut(LogEventBase):
    id: int
    service_id: Optional[int] = None
    signature: Optional[str] = None
    redacted: bool = False

    model_config = ConfigDict(from_attributes=True)


class LogIngestRequest(BaseModel):
    events: List[dict]  # raw parsed JSONL objects


class LogIngestResponse(BaseModel):
    ingested: int
    skipped: int
    incidents_created: int


# ---------- Incidents ----------
class IncidentBase(BaseModel):
    title: str
    severity: str
    status: str = "open"
    service: str
    environment: str = "production"
    signature: str
    event_count: int = 1
    confidence: float = 0.0
    root_cause: Optional[str] = None
    root_cause_confidence: Optional[str] = None
    suggested_steps: Optional[List[str]] = None
    suggested_remediation: Optional[List[str]] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None


class IncidentOut(IncidentBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    related_log_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------- Dashboard ----------
class DashboardStats(BaseModel):
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    active_incidents: int
    incidents_by_severity: dict  # {INFO: n, WARNING: n, CRITICAL: n}
    incidents_by_status: dict
    recent_events: List[dict]
    error_trend: List[dict]  # [{ts, count}]
    service_health: List[dict]


# ---------- Simulation ----------
class SimulationResponse(BaseModel):
    events_generated: int
    incidents_detected: int
    scenario: str
