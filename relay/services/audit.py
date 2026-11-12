"""Append-only audit log of administrative actions (CHAT-F-051; CHAT-SR-012).

This module deliberately exposes only record() and recent(): no update or delete path exists (CHAT-NF-011).
"""

from relay.extensions import db
from relay.models import AuditLog


def record(actor_id: int, action: str, target_type: str, target_id: int, reason: str = "") -> None:
    """Add one audit row. The caller commits it together with the action it describes."""
    db.session.add(AuditLog(actor_id=actor_id, action=action, target_type=target_type, target_id=target_id,
                            reason=(reason or "")[:200]))


def recent(limit: int = 200) -> list[AuditLog]:
    return AuditLog.query.order_by(AuditLog.id.desc()).limit(limit).all()
