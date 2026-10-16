"""Integration tests for ingestion safety, idempotency, and lifecycle behavior."""

from datetime import timedelta

from app import models
from app.ingestion import ingest_events
from app.time_utils import utc_now


def _jdbc_event(timestamp: str, environment: str = "production") -> dict:
    return {
        "timestamp": timestamp,
        "service": "checkout-api",
        "environment": environment,
        "level": "ERROR",
        "message": "java.sql.SQLException: Connection refused password=synthetic-secret",
    }


def test_ingestion_is_idempotent_and_redacts_before_persistence(client, db_session):
    timestamp = "2026-10-16T09:00:00Z"
    first = client.post("/api/logs/ingest", json={"events": [_jdbc_event(timestamp)]})
    assert first.status_code == 200
    assert first.json() == {"ingested": 1, "skipped": 0, "incidents_created": 1}

    duplicate = client.post("/api/logs/ingest", json={"events": [_jdbc_event(timestamp)]})
    assert duplicate.status_code == 200
    assert duplicate.json() == {"ingested": 0, "skipped": 1, "incidents_created": 0}

    persisted = db_session.query(models.LogEvent).one()
    assert "synthetic-secret" not in persisted.message
    assert "synthetic-secret" not in (persisted.raw or "")
    assert persisted.redacted is True
    incident = db_session.query(models.Incident).one()
    assert incident.event_count == 1
    assert incident.root_cause.startswith("Potential cause:")

    logs_response = client.get("/api/logs")
    incident_response = client.get(f"/api/incidents/{incident.id}")
    dashboard_response = client.get("/api/dashboard")
    assert logs_response.json()[0]["timestamp"].endswith("Z")
    assert incident_response.json()["created_at"].endswith("Z")
    assert dashboard_response.json()["error_trend"][0]["ts"].endswith("Z")


def test_file_ingestion_skips_malformed_lines_and_rejects_unsafe_uploads(client):
    content = (
        b'{"timestamp":"2026-10-16T09:00:00Z","service":"api","level":"INFO","message":"ok"}\n'
        b"not-json\n"
    )
    response = client.post(
        "/api/logs/ingest/file",
        files={"file": ("events.jsonl", content, "application/x-ndjson")},
    )
    assert response.status_code == 200
    assert response.json()["ingested"] == 1
    assert response.json()["skipped"] == 1

    wrong_type = client.post(
        "/api/logs/ingest/file",
        files={"file": ("events.exe", b"{}", "application/octet-stream")},
    )
    assert wrong_type.status_code == 415

    oversized = client.post(
        "/api/logs/ingest/file",
        files={"file": ("events.jsonl", b"x" * (5 * 1024 * 1024 + 1), "application/x-ndjson")},
    )
    assert oversized.status_code == 413


def test_incident_lifecycle_updates_service_health(client, db_session):
    response = client.post(
        "/api/logs/ingest",
        json={"events": [_jdbc_event("2026-10-16T09:00:00Z")]},
    )
    assert response.status_code == 200
    incident = db_session.query(models.Incident).one()
    service = db_session.query(models.Service).one()
    assert service.status == "critical"

    acknowledged = client.patch(
        f"/api/incidents/{incident.id}", json={"status": "acknowledged"}
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["acknowledged_at"] is not None
    assert service.status == "critical"

    resolved = client.patch(
        f"/api/incidents/{incident.id}", json={"status": "resolved"}
    )
    assert resolved.status_code == 200
    db_session.refresh(service)
    assert service.status == "healthy"

    invalid_reopen = client.patch(
        f"/api/incidents/{incident.id}", json={"status": "open"}
    )
    assert invalid_reopen.status_code == 409
    invalid_status = client.patch(
        f"/api/incidents/{incident.id}", json={"status": "deleted"}
    )
    assert invalid_status.status_code == 422


def test_same_service_name_can_exist_in_multiple_environments(client, db_session):
    events = [
        _jdbc_event("2026-10-16T09:00:00Z", "production"),
        _jdbc_event("2026-10-16T09:00:01Z", "staging"),
    ]
    response = client.post("/api/logs/ingest", json={"events": events})
    assert response.status_code == 200
    assert db_session.query(models.Service).count() == 2
    assert db_session.query(models.Incident).count() == 2


def test_correlation_window_splits_distant_events(db_session):
    start = utc_now() - timedelta(hours=2)
    events = [
        {**_jdbc_event(start.isoformat()), "message": "java.sql.SQLException: Connection refused"},
        {**_jdbc_event((start + timedelta(hours=1)).isoformat()), "message": "java.sql.SQLException: Connection refused"},
    ]
    result = ingest_events(db_session, events)
    db_session.commit()
    assert result.incidents_created == 2
    assert db_session.query(models.Incident).count() == 2


def test_warning_rules_require_repeated_evidence(db_session):
    result = ingest_events(
        db_session,
        [{
            "timestamp": utc_now().isoformat(),
            "service": "web-api",
            "environment": "production",
            "level": "ERROR",
            "message": "HTTP/1.1 500 Internal Server Error",
        }],
    )
    assert result.incidents_created == 0


def test_warning_threshold_accumulates_across_ingestion_requests(db_session):
    start = utc_now() - timedelta(minutes=5)
    for index in range(2):
        result = ingest_events(
            db_session,
            [{
                "timestamp": (start + timedelta(minutes=index)).isoformat(),
                "service": "web-api",
                "environment": "production",
                "level": "ERROR",
                "message": "HTTP/1.1 500 Internal Server Error",
            }],
        )
        db_session.commit()
        assert result.incidents_created == 0

    result = ingest_events(
        db_session,
        [{
            "timestamp": (start + timedelta(minutes=2)).isoformat(),
            "service": "web-api",
            "environment": "production",
            "level": "ERROR",
            "message": "HTTP/1.1 503 Service Unavailable",
        }],
    )
    db_session.commit()
    assert result.incidents_created == 1
    incident = db_session.query(models.Incident).one()
    assert incident.event_count == 3
    assert len(incident.events) == 3
