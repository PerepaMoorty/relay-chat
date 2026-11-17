from flask_login import UserMixin

from relay.extensions import db
from relay.models._time import iso, utcnow


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")  # user | admin
    # Bumped on logout and ban. It is part of the session id, so old cookies stop working (CHAT-SR-013).
    session_version = db.Column(db.Integer, nullable=False, default=1)
    banned_at = db.Column(db.DateTime)
    muted_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime)

    def get_id(self) -> str:
        return f"{self.id}:{self.session_version}"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_muted(self) -> bool:
        return bool(self.muted_until and self.muted_until > utcnow())

    def to_public(self) -> dict:
        return {"id": self.id, "username": self.username, "role": self.role, "last_seen_at": iso(self.last_seen_at)}

    def to_admin(self) -> dict:
        return {
            **self.to_public(),
            "banned": self.banned_at is not None,
            "muted_until": iso(self.muted_until) if self.is_muted else None,
            "created_at": iso(self.created_at),
        }
