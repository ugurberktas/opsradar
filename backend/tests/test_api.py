"""Tests for important REST endpoints using TestClient fixture."""

import app.models as m
from app import parsers, redact
from app import simulation as sim_mod


def _seed(client_app_db):
    """Seed services + logs + incidents into the given session."""
    session, client = client_app_db
    events = sim_mod.generate_events(seed=42, total_events=200)
    normalized = [parsers.normalize_event(e) for e in events]
    service_cache = {}
    for ev in normalized:
        ev["message"] = redact.redact_text(ev["message"])
        ev["raw"] = redact.redact_text(ev.get("raw") or "")
        key = (ev["service"], ev["environment"])
        svc = service_cache.get(key)
        if svc is None:
            svc = (
                session.query(m.Service)
                .filter(m.Service.name == ev["service"])
                .filter(m.Service.environment == ev["environment"])
                .first()
            )
            if svc is None:
                svc = m.Service(name=ev["service"], environment=ev["environment"], status="healthy")
                session.add(svc)
                session.flush()
            service_cache[key] = svc
        le = m.LogEvent(
            service_id=svc.id,
            service=ev["service"],
            environment=ev["environment"],
            timestamp=ev["timestamp"],
            level=ev["level"],
            message=ev["message"],
            raw=ev["raw"],
            redacted=True,
        )
        session.add(le)
    session.flush()
    from app.detectors import detect_and_correlate

    recent = session.query(m.LogEvent).all()
    norm_detect = [
        {
            "service": r.service,
            "environment": r.environment,
            "timestamp": r.timestamp,
            "level": r.level,
            "message": r.message,
        }
        for r in recent
    ]
    detect_and_correlate(session, norm_detect)
    session.commit()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_returns_stats(client, db_session):
    _seed((db_session, client))
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    data = r.json()
    for key in [
        "total_services",
        "healthy_services",
        "warning_services",
        "critical_services",
        "active_incidents",
        "incidents_by_severity",
        "incidents_by_status",
        "recent_events",
        "error_trend",
        "service_health",
    ]:
        assert key in data, f"Missing dashboard key: {key}"
    assert isinstance(data["error_trend"], list)
    assert len(data["service_health"]) >= 6
    assert data["total_services"] >= 6


def test_list_incidents(client, db_session):
    _seed((db_session, client))
    r = client.get("/api/incidents")
    assert r.status_code == 200
    incidents = r.json()
    assert isinstance(incidents, list)
    assert len(incidents) >= 1


def test_list_services(client, db_session):
    _seed((db_session, client))
    r = client.get("/api/services")
    assert r.status_code == 200
    services = r.json()
    assert len(services) >= 6
    names = {s["name"] for s in services}
    expected = {
        "payment-api",
        "order-service",
        "inventory-svc",
        "user-session",
        "notification-svc",
        "catalog-api",
    }
    assert expected.issubset(names)
