"""Tests for JSONL log parsing and normalization."""

from app.parsers import parse_jsonl, normalize_event


def test_parse_jsonl_valid():
    content = '{"service":"payment-api","level":"ERROR","message":"fail"}\n{"service":"order-service","level":"INFO","message":"ok"}\n'
    events = parse_jsonl(content)
    assert len(events) == 2
    assert events[0]["service"] == "payment-api"
    assert events[0]["level"] == "ERROR"


def test_parse_jsonl_skips_blank_and_malformed():
    content = '{"service":"a","level":"INFO","message":"ok"}\n\nnot json at all\n{"service":"b","level":"WARN","message":"x"}\n'
    events = parse_jsonl(content)
    assert len(events) == 3  # 2 valid + 1 malformed synthetic
    assert events[1]["_parse_error"] is True
    assert "Malformed log line" in events[1]["message"]


def test_normalize_event_field_aliases():
    raw = {
        "ts": "2026-10-16T10:00:00Z",
        "serviceName": "pay-api",
        "env": "staging",
        "severity": "error",
        "msg": "boom",
    }
    ev = normalize_event(raw)
    assert ev["service"] == "pay-api"
    assert ev["environment"] == "staging"
    assert ev["level"] == "ERROR"
    assert ev["message"] == "boom"
    assert ev["timestamp"].hour == 10


def test_normalize_event_missing_defaults():
    ev = normalize_event({})
    assert ev["service"] == "unknown"
    assert ev["environment"] == "production"
    assert ev["level"] == "INFO"
    assert ev["message"] == ""
