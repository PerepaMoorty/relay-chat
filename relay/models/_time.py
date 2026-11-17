"""Timestamps are stored as naive UTC and sent to clients as ISO-8601 strings ending in Z."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    # SQLite has no time zones, so values are stored naive and are always UTC by convention.
    return datetime.now(UTC).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") + "Z" if dt else None
