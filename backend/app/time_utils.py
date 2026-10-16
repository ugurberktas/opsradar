"""UTC helpers used across persistence and API code."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time as a naive UTC datetime for SQLite."""
    return datetime.now(UTC).replace(tzinfo=None)


def to_utc_naive(value: datetime) -> datetime:
    """Normalize an aware or naive datetime to the database UTC convention."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def utc_iso(value: datetime) -> str:
    """Serialize a database datetime with an explicit UTC designator."""
    return to_utc_naive(value).replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
