"""Tests for sensitive-data redaction."""

from app.redact import is_sensitive, redact_text


def test_redacts_password():
    text = "password=supersecret123 user=admin"
    out = redact_text(text)
    assert "supersecret123" not in out
    assert "***REDACTED***" in out
    assert "password=" in out


def test_redacts_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy"
    out = redact_text(text)
    assert "eyJhbGci" not in out
    assert "Bearer ***REDACTED***" in out


def test_redacts_api_key():
    text = "api_key=sk_live_abc123"
    out = redact_text(text)
    assert "sk_live_abc123" not in out
    assert "***REDACTED***" in out


def test_is_sensitive():
    assert is_sensitive("token=abc123") is True
    assert is_sensitive("Bearer secrettoken") is True
    assert is_sensitive("just a normal message") is False
    assert is_sensitive("") is False


def test_redacts_json_and_url_credentials():
    text = '{"password": "correct-horse", "dsn": "postgres://admin:swordfish@db/app"}'
    out = redact_text(text)
    assert "correct-horse" not in out
    assert "swordfish" not in out
    assert out.count("***REDACTED***") == 2
