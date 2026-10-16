"""Tests for incident lifecycle: detection, dedup, acknowledge, resolve."""

from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models as m
from app.database import Base, SessionLocal
from app.main import app
from app.time_utils import utc_now


def _make_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Testing = sessionmaker(bind=test_engine)
    session = Testing()
    app.dependency_overrides[SessionLocal] = lambda: session
    return session


def _seed_logs(session):
    now = utc_now()
    svc = m.Service(name="payment-api", environment="production", status="healthy")
    session.add(svc)
    session.flush()
    base = now - timedelta(minutes=10)
    for i in range(5):
        le = m.LogEvent(
            service_id=svc.id,
            service="payment-api",
            environment="production",
            timestamp=base + timedelta(seconds=i),
            level="ERROR",
            message="java.sql.SQLException: Connection refused",
            raw="raw",
            redacted=True,
        )
        session.add(le)
    session.flush()
    return svc.id


def test_detection_creates_incident_and_links_logs():
    session = _make_session()
    try:
        _seed_logs(session)
        from app.detectors import detect_and_correlate

        events = (
            session.query(m.LogEvent)
            .filter(m.LogEvent.service == "payment-api")
            .all()
        )
        normalized = [
            {
                "service": e.service,
                "environment": e.environment,
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
            }
            for e in events
        ]
        result = detect_and_correlate(session, normalized)
        assert result.incidents, "Expected at least one incident"
        inc = result.incidents[0]
        assert inc["severity"] == "CRITICAL"
        assert inc["service"] == "payment-api"
        assert inc["event_count"] == 5

        # Linked incident events exist
        links = session.query(m.IncidentEvent).filter(
            m.IncidentEvent.incident_id == inc["id"]
        ).count()
        assert links == 5

        # Incident persisted
        persisted = session.get(m.Incident, inc["id"])
        assert persisted is not None
        assert persisted.status == "open"
    finally:
        session.close()
        app.dependency_overrides.clear()


def test_deduplication_does_not_duplicate_open_incident():
    session = _make_session()
    try:
        _seed_logs(session)
        from app.detectors import detect_and_correlate

        events = (
            session.query(m.LogEvent)
            .filter(m.LogEvent.service == "payment-api")
            .all()
        )
        normalized = [
            {
                "service": e.service,
                "environment": e.environment,
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
            }
            for e in events
        ]
        r1 = detect_and_correlate(session, normalized)
        assert len(r1.incidents) == 1

        # Same events again -> should not create a second incident
        r2 = detect_and_correlate(session, normalized)
        assert len(r2.incidents) == 0

        total = session.query(m.Incident).count()
        assert total == 1
    finally:
        session.close()
        app.dependency_overrides.clear()


def test_acknowledge_and_resolve_lifecycle():
    session = _make_session()
    try:
        _seed_logs(session)
        from app.detectors import detect_and_correlate

        events = (
            session.query(m.LogEvent)
            .filter(m.LogEvent.service == "payment-api")
            .all()
        )
        normalized = [
            {
                "service": e.service,
                "environment": e.environment,
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
            }
            for e in events
        ]
        result = detect_and_correlate(session, normalized)
        inc_id = result.incidents[0]["id"]

        inc = session.get(m.Incident, inc_id)
        inc.status = "acknowledged"
        inc.acknowledged_at = utc_now()
        session.add(inc)
        session.commit()

        assert session.get(m.Incident, inc_id).status == "acknowledged"
        assert session.get(m.Incident, inc_id).acknowledged_at is not None

        inc.status = "resolved"
        inc.resolved_at = utc_now()
        session.add(inc)
        session.commit()

        assert session.get(m.Incident, inc_id).status == "resolved"
        assert session.get(m.Incident, inc_id).resolved_at is not None
    finally:
        session.close()
        app.dependency_overrides.clear()
