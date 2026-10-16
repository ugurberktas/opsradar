"""Sensitive-data redaction for log messages before storage/display.

Patterns redact passwords, tokens, API keys, secrets, and Bearer auth headers.
This is a best-effort safeguard, not a complete data-loss-prevention system.
"""

import re

# (compiled_regex, replacement)
SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # key: value forms
    (
        re.compile(
            r"([\"']?(?:password|passwd|pwd|secret|api[_-]?key|api[_-]?secret|"
            r"access[_-]?token|refresh[_-]?token|client[_-]?secret|private[_-]?key|"
            r"db[_-]?password|token)[\"']?\s*[:=]\s*)[\"']?([^\"'\s,&}]+)",
            re.IGNORECASE,
        ),
        r"\1***REDACTED***",
    ),
    # Authorization: Bearer <token>
    (
        re.compile(r"(Authorization\s*:\s*)Bearer\s+[A-Za-z0-9\-\._\+\/]+={0,2}", re.IGNORECASE),
        r"\1Bearer ***REDACTED***",
    ),
    # standalone Bearer token
    (
        re.compile(r"Bearer\s+[A-Za-z0-9\-\._\+\/]+={0,2}", re.IGNORECASE),
        "Bearer ***REDACTED***",
    ),
    # jwt-like tokens (three base64url segments)
    (
        re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
        "***REDACTED***",
    ),
    # Credentials embedded in URLs.
    (
        re.compile(r"(\b[a-z][a-z0-9+.-]*://[^\s:/]+:)[^\s/@]+(@)", re.IGNORECASE),
        r"\1***REDACTED***\2",
    ),
    # Common cloud access-key identifier. The corresponding secret is caught above.
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "***REDACTED***"),
)


def redact_text(text: str) -> str:
    """Return text with sensitive values replaced by ***REDACTED***."""
    if not text:
        return text
    result = text
    for pattern, repl in SENSITIVE_PATTERNS:
        result = pattern.sub(repl, result)
    return result


def is_sensitive(text: str) -> bool:
    """Return True if the text contains a sensitive pattern."""
    if not text:
        return False
    return any(pattern.search(text) for pattern, _ in SENSITIVE_PATTERNS)
