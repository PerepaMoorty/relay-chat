"""Sending, editing, deleting and reading messages
(CHAT-F-004, F-006, F-016, F-020, F-029, F-030, F-037; CHAT-SR-003, SR-004, SR-011)."""

import re

from flask import current_app

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Attachment, Message, User
from relay.models._time import iso, utcnow
from relay.services import rooms

# Control characters, except tab, newline and carriage return
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def validate_body(body, allow_empty: bool = False) -> str:
    if body is None and allow_empty:
        return ""
    if not isinstance(body, str):
        raise RelayError("VALIDATION_ERROR", "Message must be text")
    body = body.strip()
    if not body and not allow_empty:
        raise RelayError("VALIDATION_ERROR", "Message cannot be empty")
    limit = current_app.config["MESSAGE_MAX_LEN"]
    if len(body) > limit:
        raise RelayError("VALIDATION_ERROR", f"Message is longer than {limit} characters")
    if _CONTROL.search(body):
        raise RelayError("VALIDATION_ERROR", "Message contains invalid characters")
    return body


def _require_not_muted(user_id: int) -> None:
    user = db.session.get(User, user_id)
    if user.is_muted:
        raise RelayError("MUTED", "You are muted", until=iso(user.muted_until))


def send(sender_id: int, room_id, body, client_id=None, attachment_id=None) -> tuple[Message, bool]:
    """Persist a message. Returns (message, created); a retried client_id returns the original message."""
    room = rooms.require_member(room_id, sender_id)
    _require_not_muted(sender_id)
    if client_id is not None:
        if not isinstance(client_id, str) or not 1 <= len(client_id) <= 64:
            raise RelayError("VALIDATION_ERROR", "Invalid client_id")
        existing = Message.query.filter_by(client_id=client_id).first()
        if existing:
            if existing.sender_id != sender_id:
                raise RelayError("VALIDATION_ERROR", "Invalid client_id")
            return existing, False
    attachment = None
    if attachment_id is not None:
        attachment = db.session.get(Attachment, attachment_id) if type(attachment_id) is int else None
        used = attachment is not None and Message.query.filter_by(attachment_id=attachment.id).first() is not None
        if not attachment or attachment.uploader_id != sender_id or used:
            raise RelayError("NOT_FOUND", "Attachment not found")
    text = validate_body(body, allow_empty=attachment is not None)
    msg = Message(room_id=room.id, sender_id=sender_id, client_id=client_id, body=text,
                  kind="file" if attachment else "text", attachment_id=attachment.id if attachment else None)
    db.session.add(msg)
    db.session.commit()
    return msg, True


def _own_message(user_id: int, message_id, allow_deleted: bool = False) -> Message:
    msg = db.session.get(Message, message_id) if type(message_id) is int else None
    if not msg or (msg.deleted_at and not allow_deleted):
        raise RelayError("NOT_FOUND", "Message not found")
    rooms.require_member(msg.room_id, user_id)
    if msg.sender_id != user_id:
        raise RelayError("FORBIDDEN", "You can only change your own messages")
    return msg


def edit(user_id: int, message_id, body) -> Message:
    msg = _own_message(user_id, message_id)
    text = validate_body(body, allow_empty=msg.attachment_id is not None)
    if text != msg.body:
        msg.body = text
        msg.edited_at = utcnow()
        db.session.commit()
    return msg


def soft_delete(msg: Message) -> None:
    """Keep the row for ordering, receipts and reports, but drop the content (CHAT-F-030)."""
    msg.deleted_at = utcnow()
    msg.body = ""


def delete(user_id: int, message_id) -> Message:
    """Delete one's own message. Deleting it again returns it unchanged."""
    msg = _own_message(user_id, message_id, allow_deleted=True)
    if not msg.deleted_at:
        soft_delete(msg)
        db.session.commit()
    return msg


def history(user_id: int, room_id, before=None, limit=None) -> list[Message]:
    """One page of a room's history, oldest first. before is an exclusive message id."""
    room = rooms.require_member(room_id, user_id)
    page = current_app.config["HISTORY_PAGE_SIZE"]
    try:
        limit = max(1, min(int(limit) if limit is not None else page, page))
        before = int(before) if before is not None else None
    except (TypeError, ValueError):
        raise RelayError("VALIDATION_ERROR", "before and limit must be integers") from None
    q = Message.query.filter(Message.room_id == room.id)
    if before is not None:
        q = q.filter(Message.id < before)
    newest_first = q.order_by(Message.id.desc()).limit(limit).all()
    return list(reversed(newest_first))


def last_id(room_id: int) -> int:
    last = Message.query.filter_by(room_id=room_id).order_by(Message.id.desc()).first()
    return last.id if last else 0
