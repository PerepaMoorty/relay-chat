from relay.extensions import db
from relay.models._time import iso, utcnow


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(64), unique=True, nullable=False)  # random token (CHAT-SR-010)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.original_name, "mime": self.mime_type, "size": self.size_bytes,
                "is_image": self.is_image, "url": f"/api/files/{self.id}"}


class Message(db.Model):
    # The autoincrement id is the global message order (CHAT-NF-006).
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    client_id = db.Column(db.String(64), unique=True)  # makes retried sends idempotent
    kind = db.Column(db.String(10), nullable=False, default="text")  # text | file
    body = db.Column(db.Text, nullable=False, default="")
    attachment_id = db.Column(db.Integer, db.ForeignKey("attachment.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    edited_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)  # soft delete keeps ordering, receipts and reports intact

    sender = db.relationship("User")
    attachment = db.relationship("Attachment")

    __table_args__ = (db.Index("ix_message_room_id_id", "room_id", "id"),)

    def to_dict(self) -> dict:
        deleted = self.deleted_at is not None
        return {
            "id": self.id,
            "room_id": self.room_id,
            "client_id": self.client_id,
            "kind": self.kind,
            "body": "" if deleted else self.body,
            "attachment": None if deleted or not self.attachment else self.attachment.to_dict(),
            "sender": {"id": self.sender.id, "username": self.sender.username} if self.sender else None,
            "created_at": iso(self.created_at),
            "edited_at": iso(self.edited_at),
            "deleted": deleted,
        }


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="open")  # open | resolved | dismissed
    resolved_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolved_at = db.Column(db.DateTime)

    message = db.relationship("Message")
    reporter = db.relationship("User", foreign_keys=[reporter_id])

    __table_args__ = (db.UniqueConstraint("message_id", "reporter_id"),)

    def to_dict(self) -> dict:
        msg = self.message
        deleted = msg.deleted_at is not None
        return {
            "id": self.id,
            "reason": self.reason,
            "status": self.status,
            "created_at": iso(self.created_at),
            "reporter": self.reporter.username,
            "message": {
                "id": msg.id,
                "room_id": msg.room_id,
                "body": "" if deleted else msg.body,
                "deleted": deleted,
                "sender": msg.sender.username if msg.sender else None,
                "created_at": iso(msg.created_at),
            },
        }


class AuditLog(db.Model):
    """Append-only record of administrative actions (CHAT-F-051, SR-012). No update or delete path exists."""

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    actor = db.relationship("User")

    def to_dict(self) -> dict:
        return {"id": self.id, "actor": self.actor.username, "action": self.action, "target_type": self.target_type,
                "target_id": self.target_id, "reason": self.reason, "created_at": iso(self.created_at)}


class Activity(db.Model):
    """Server activity log: connections, disconnections and handled errors (CHAT-F-052)."""

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)  # connect | disconnect | error
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    detail = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "user": self.user.username if self.user else None,
                "detail": self.detail, "created_at": iso(self.created_at)}
