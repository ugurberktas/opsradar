"""Sensitive-data redaction for log messages before storage/display.

Patterns redact passwords, tokens, API keys, secrets, and Bearer auth headers.
Never stores real credentials.
"""

import re
from typing import Tuple

# (compiled_regex, replacement)
SENSITIVE_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    # key: value forms
    (
        re.compile(
            r"(password|passwd|pwd|secret|api[_-]?key|api[_-]?secret|access[_-]?token|"
            r"refresh[_-]?token|client[_-]?secret|private[_-]?key|db[_-]?password|\btoken\b)\s*[:=]\s*[\"']?([^\"'\s,}]+)",
            re.IGNORECASE,
        ),
        r"\1: ***REDACTED***",
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
