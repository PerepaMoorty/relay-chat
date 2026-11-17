"""Server activity log and the connected-client view for administrators (CHAT-F-052)."""

from relay.extensions import db
from relay.models import Activity, User
from relay.models._time import iso
from relay.services.presence import registry


def log(kind: str, user_id: int | None = None, detail: str = "") -> None:
    """Record a connect, disconnect or handled error. kind is "connect" | "disconnect" | "error"."""
    db.session.add(Activity(kind=kind, user_id=user_id, detail=(detail or "")[:200]))
    db.session.commit()


def recent(limit: int = 200) -> list[Activity]:
    return Activity.query.order_by(Activity.id.desc()).limit(limit).all()


def connected_clients() -> list[dict]:
    sockets = registry.snapshot()
    if not sockets:
        return []
    ids = {s["user_id"] for s in sockets}
    names = {u.id: u.username for u in User.query.filter(User.id.in_(ids)).all()}
    return [{"sid": s["sid"][:8], "username": names.get(s["user_id"], "?"), "connected_at": iso(s["connected_at"])}
            for s in sockets]
