"""Conversations and membership: #general, group rooms and private (1:1) conversations
(CHAT-F-005, F-006, F-022, F-023; CHAT-SR-003, SR-008)."""

import secrets

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Room, RoomMember, User
from relay.models.room import GENERAL


def _get_room(room_id) -> Room | None:
    # bool is a subclass of int, so check the exact type
    return db.session.get(Room, room_id) if type(room_id) is int else None


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


def require_member(room_id, user_id: int) -> Room:
    room = _get_room(room_id)
    # Non-members get NOT_FOUND rather than FORBIDDEN, so room ids cannot be probed.
    if not room or not db.session.get(RoomMember, (room.id, user_id)):
        raise RelayError("NOT_FOUND", "Conversation not found")
    return room


def open_direct(user_id: int, peer_id) -> tuple[Room, bool]:
    """Return the single direct conversation for this pair, creating it if needed."""
    peer = db.session.get(User, peer_id) if type(peer_id) is int else None
    if not peer:
        raise RelayError("NOT_FOUND", "User not found")
    if peer.id == user_id:
        raise RelayError("VALIDATION_ERROR", "You cannot message yourself")
    key = f"{min(user_id, peer.id)}:{max(user_id, peer.id)}"
    room = Room.query.filter_by(dm_key=key).first()
    if room:
        return room, False
    room = Room(kind="direct", dm_key=key)
    db.session.add(room)
    db.session.flush()
    add_member(room.id, user_id)
    add_member(room.id, peer.id)
    db.session.commit()
    return room, True


def create_group(owner_id: int, name, visibility) -> Room:
    name = name.strip() if isinstance(name, str) else ""
    if not 1 <= len(name) <= 40:
        raise RelayError("VALIDATION_ERROR", "Room name must be 1-40 characters")
    if visibility not in ("public", "private"):
        raise RelayError("VALIDATION_ERROR", "Visibility must be public or private")
    code = secrets.token_urlsafe(8)[:10] if visibility == "private" else None
    room = Room(kind="group", name=name, visibility=visibility, owner_id=owner_id, invite_code=code)
    db.session.add(room)
    db.session.flush()
    add_member(room.id, owner_id, role="owner")
    db.session.commit()
    return room


def public_rooms() -> list[Room]:
    """#general first, then public group rooms by name. Private rooms are never listed."""
    groups = Room.query.filter_by(kind="group", visibility="public").order_by(Room.name, Room.id).all()
    return [general_room(), *groups]


def join_public(user_id: int, room_id) -> tuple[Room, bool]:
    room = _get_room(room_id)
    if not room or not (room.kind == "public" or (room.kind == "group" and room.visibility == "public")):
        raise RelayError("NOT_FOUND", "Room not found")
    added = add_member(room.id, user_id)
    db.session.commit()
    return room, added


def join_by_invite(user_id: int, code) -> tuple[Room, bool]:
    code = code.strip() if isinstance(code, str) else ""
    room = Room.query.filter_by(kind="group", visibility="private", invite_code=code).first() if code else None
    if not room:
        raise RelayError("INVALID_INVITE", "That invite code is not valid")
    added = add_member(room.id, user_id)
    db.session.commit()
    return room, added


def leave(user_id: int, room_id) -> Room:
    room = require_member(room_id, user_id)
    if room.kind != "group":
        raise RelayError("VALIDATION_ERROR", "Only group rooms can be left")
    db.session.delete(db.session.get(RoomMember, (room.id, user_id)))
    db.session.commit()
    return room


def rooms_for(user_id: int) -> list[Room]:
    return Room.query.join(RoomMember).filter(RoomMember.user_id == user_id).order_by(Room.id).all()


def member_ids(room_id: int) -> list[int]:
    return [m.user_id for m in RoomMember.query.filter_by(room_id=room_id).order_by(RoomMember.user_id)]
