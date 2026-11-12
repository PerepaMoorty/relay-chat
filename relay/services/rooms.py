"""Conversations and membership. B5 replaces this file and keeps general_room() and add_member()."""

from relay.extensions import db
from relay.models import Room, RoomMember
from relay.models.room import GENERAL


def general_room() -> Room:
    """The single public room, #general, created on first use."""
    room = Room.query.filter_by(kind="public", name=GENERAL).first()
    if not room:
        room = Room(kind="public", name=GENERAL)
        db.session.add(room)
        db.session.flush()
    return room


def add_member(room_id: int, user_id: int, role: str = "member") -> bool:
    """Add a member; returns False when the user is already in the room."""
    if db.session.get(RoomMember, (room_id, user_id)):
        return False
    db.session.add(RoomMember(room_id=room_id, user_id=user_id, role=role))
    return True
