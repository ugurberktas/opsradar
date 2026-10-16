"""SQLAlchemy models for OpsRadar."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

from app.database import Base

UTC = None  # placeholder; we use naive UTC datetimes consistently


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    environment = Column(String, nullable=False, default="production")
    status = Column(String, nullable=False, default="healthy")  # healthy | warning | critical
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

    logs = relationship("LogEvent", back_populates="service_rel", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="service_rel", cascade="all, delete-orphan")


class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True, index=True)
    service = Column(String, index=True, nullable=False)
    environment = Column(String, index=True, nullable=False, default="production")
    timestamp = Column(DateTime, index=True, nullable=False)
    level = Column(String, index=True, nullable=False)  # INFO | WARN | ERROR | FATAL | DEBUG
    message = Column(Text, nullable=False)
    raw = Column(Text, nullable=True)
    signature = Column(String, index=True, nullable=True)
    redacted = Column(Boolean, default=False)

    service_rel = relationship("Service", back_populates="logs")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)  # INFO | WARNING | CRITICAL
    status = Column(String, nullable=False, default="open")  # open | acknowledged | resolved
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True, index=True)
    service = Column(String, index=True, nullable=False)
    environment = Column(String, index=True, nullable=False, default="production")
    signature = Column(String, index=True, nullable=False)
    first_seen = Column(DateTime, index=True, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    event_count = Column(Integer, default=1)
    confidence = Column(Float, default=0.0)
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(String, nullable=True)  # speculative | likely | confirmed
    suggested_steps = Column(Text, nullable=True)  # JSON string
    suggested_remediation = Column(Text, nullable=True)  # JSON string
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    service_rel = relationship("Service", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    log_event_id = Column(Integer, ForeignKey("log_events.id"), nullable=False, index=True)

    incident = relationship("Incident", back_populates="events")


Index("ix_log_events_service_ts", LogEvent.service, LogEvent.timestamp)
Index("ix_incidents_service_status", Incident.service, Incident.status)
