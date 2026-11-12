"""Accounts and sessions. B4 replaces this file and keeps load_session_user()."""

from relay.extensions import db
from relay.models import User


def load_session_user(session_id: str) -> User | None:
    """Resolve a "<user_id>:<session_version>" session id to a user who is still allowed in."""
    try:
        user_id, version = (int(part) for part in session_id.split(":"))
    except (ValueError, AttributeError):
        return None
    user = db.session.get(User, user_id)
    if not user or user.session_version != version or user.banned_at:
        return None
    return user
