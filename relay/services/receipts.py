"""Delivered/read watermarks and unread counts (CHAT-F-021, F-027, F-040). See SAD section 5.7."""

from sqlalchemy import func

from relay.extensions import db
from relay.models import Message, RoomMember
from relay.services import messages, rooms


def update(user_id: int, room_id, delivered_up_to=None, read_up_to=None) -> tuple[RoomMember, bool]:
    """Advance a member's watermarks. They only move forward and never past the newest message."""
    room = rooms.require_member(room_id, user_id)
    member = db.session.get(RoomMember, (room.id, user_id))
    newest = messages.last_id(room.id)
    changed = False
    for field, value in (("read_up_to", read_up_to), ("delivered_up_to", delivered_up_to)):
        if type(value) is not int:  # ignores None, strings and booleans
            continue
        value = min(value, newest)
        if value > getattr(member, field):
            setattr(member, field, value)
            changed = True
    if member.read_up_to > member.delivered_up_to:  # read implies delivered
        member.delivered_up_to = member.read_up_to
        changed = True
    if changed:
        db.session.commit()
    return member, changed


def for_room(room_id: int) -> list[dict]:
    return [{"user_id": m.user_id, "delivered_up_to": m.delivered_up_to, "read_up_to": m.read_up_to}
            for m in RoomMember.query.filter_by(room_id=room_id).order_by(RoomMember.user_id)]


def unread_counts(user_id: int) -> dict[int, int]:
    """Messages after my read watermark, not sent by me and not deleted, per room (one query)."""
    rows = (db.session.query(Message.room_id, func.count(Message.id))
            .join(RoomMember, (RoomMember.room_id == Message.room_id) & (RoomMember.user_id == user_id))
            .filter(Message.id > RoomMember.read_up_to, Message.deleted_at.is_(None), Message.sender_id != user_id)
            .group_by(Message.room_id).all())
    return {room_id: count for room_id, count in rows}
