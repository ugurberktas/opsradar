"""Tests for rule-based incident detection and deduplication."""

from datetime import datetime
from app.detectors import detect_signature, signature_for, DETECTION_RULES


def test_detect_jdbc():
    rule = detect_signature("java.sql.SQLException: Connection refused")
    assert rule is not None
    assert rule.name == "jdbc_connection_failure"
    assert rule.severity == "CRITICAL"


def test_detect_oom():
    # "OutOfMemoryError" only matches the oom_killed rule (OOMKilled alone also
    # matches k8s_crash_loop, which is checked first).
    rule = detect_signature("java.lang.OutOfMemoryError: Java heap space")
    assert rule is not None
    assert rule.name == "oom_killed"


def test_detect_crash_loop():
    rule = detect_signature("CrashLoopBackOff: container exited with code 1")
    assert rule is not None
    assert rule.name == "k8s_crash_loop"


def test_detect_http_5xx():
    rule = detect_signature("HTTP/1.1 500 Internal Server Error")
    assert rule is not None
    assert rule.name == "http_5xx_spike"
    assert rule.severity == "WARNING"


def test_detect_redis():
    rule = detect_signature("redis.exceptions.ConnectionError: Connection refused")
    assert rule is not None
    assert rule.name == "redis_connection_error"


def test_detect_none_for_normal():
    assert detect_signature("GET /api/v1/payments 200 45ms") is None


def test_signature_is_stable():
    s1 = signature_for(DETECTION_RULES[0], "payment-api", "production")
    s2 = signature_for(DETECTION_RULES[0], "payment-api", "production")
    assert s1 == s2
    assert "payment-api" in s1
    assert s1 != signature_for(DETECTION_RULES[0], "order-service", "production")


def test_all_rules_have_required_fields():
    for rule in DETECTION_RULES:
        assert rule.name
        assert rule.severity in ("INFO", "WARNING", "CRITICAL")
        assert rule.confidence > 0
        assert rule.root_cause_template
        assert rule.investigation_steps
        assert rule.remediation_actions
        assert rule.root_cause_confidence in ("speculative", "likely", "confirmed")
