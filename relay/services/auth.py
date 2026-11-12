"""Accounts and credentials (CHAT-F-002, F-003, F-018, F-019; CHAT-SR-002, SR-006, SR-013)."""

import re

from werkzeug.security import check_password_hash, generate_password_hash

from relay.errors import RelayError
from relay.extensions import db
from relay.models import User
from relay.services import rooms

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")
MIN_PASSWORD = 8


def normalize_username(raw) -> str:
    return str(raw or "").strip().lower()


def register(username, password, role: str = "user") -> User:
    """Create an account (scrypt hash, CHAT-SR-006) and make the user a member of #general."""
    username = normalize_username(username)
    if not USERNAME_RE.fullmatch(username):
        raise RelayError("VALIDATION_ERROR", "Username must be 3-20 letters, digits or underscores")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD:
        raise RelayError("VALIDATION_ERROR", f"Password must be at least {MIN_PASSWORD} characters")
    if User.query.filter_by(username=username).first():
        raise RelayError("USERNAME_TAKEN", "That username is already taken")
    user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.flush()
    rooms.add_member(rooms.general_room().id, user.id)
    db.session.commit()
    return user


def authenticate(username, password) -> User:
    user = User.query.filter_by(username=normalize_username(username)).first()
    # One answer for an unknown user and a wrong password, so usernames cannot be probed.
    if not user or not isinstance(password, str) or not check_password_hash(user.password_hash, password):
        raise RelayError("INVALID_CREDENTIALS", "Invalid username or password")
    if user.banned_at:
        raise RelayError("BANNED", "This account has been banned")
    return user


def revoke_sessions(user: User) -> None:
    """Bump the session version so every existing cookie of this user stops working."""
    user.session_version += 1
    db.session.commit()


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
