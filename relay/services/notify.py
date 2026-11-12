"""The only module that emits Socket.IO events or changes socket channels (docs/architecture.md 4.1, rule 4)."""

from relay.extensions import socketio
from relay.models import Message, Room, RoomMember, User
from relay.models.room import room_to_dict
from relay.services.presence import registry

NS = "/"
PRESENCE = "presence"


def room_channel(room_id: int) -> str:
    return f"room:{room_id}"


def user_channel(user_id: int) -> str:
    return f"user:{user_id}"


def _emit(event: str, data: dict, to: str, skip_sid: str | None = None) -> None:
    socketio.emit(event, data, to=to, namespace=NS, skip_sid=skip_sid)


def message_created(msg: Message) -> None:
    _emit("message:new", {"message": msg.to_dict()}, room_channel(msg.room_id))


def message_updated(msg: Message) -> None:
    """Edits and deletions (own or by an admin) share one event (CHAT-F-029, F-030, F-047)."""
    _emit("message:updated", {"message": msg.to_dict()}, room_channel(msg.room_id))


def receipt_updated(member: RoomMember) -> None:
    _emit("receipt:updated", {"room_id": member.room_id, "user_id": member.user_id,
                              "delivered_up_to": member.delivered_up_to, "read_up_to": member.read_up_to},
          room_channel(member.room_id))


def typing(room_id: int, user: User, is_typing: bool, skip_sid: str | None) -> None:
    """Typing state goes to everyone in the room except the sending socket (CHAT-F-026)."""
    _emit("typing", {"room_id": room_id, "user": {"id": user.id, "username": user.username}, "is_typing": is_typing},
          room_channel(room_id), skip_sid=skip_sid)


def presence_changed(user: User, online: bool) -> None:
    """Online-list update; clients also show it as a join/leave notice in #general (CHAT-F-009…F-011)."""
    _emit("presence", {"user": user.to_public(), "online": online}, PRESENCE)


def presence_snapshot(sid: str, users: list[User]) -> None:
    _emit("presence:snapshot", {"users": [u.to_public() for u in users]}, sid)


def subscribe(user_id: int, room: Room) -> None:
    """Put every live socket of a user into a room channel, then tell their clients about the room."""
    for sid in registry.sids_for(user_id):
        socketio.server.enter_room(sid, room_channel(room.id), namespace=NS)
    _emit("room:added", {"room": room_to_dict(room, user_id)}, user_channel(user_id))


def unsubscribe(user_id: int, room: Room) -> None:
    for sid in registry.sids_for(user_id):
        socketio.server.leave_room(sid, room_channel(room.id), namespace=NS)
    _emit("room:removed", {"room_id": room.id}, user_channel(user_id))


def room_updated(room: Room) -> None:
    """Member count changes. Sent with viewer_id=0, so no invite code and no DM peer leak to the room."""
    _emit("room:updated", {"room": room_to_dict(room, viewer_id=0)}, room_channel(room.id))


def terminate_sessions(user_id: int, reason: str) -> None:
    """Logout or ban: tell every tab of the user, then drop their sockets (CHAT-F-014, SR-013)."""
    _emit("session:terminated", {"reason": reason}, user_channel(user_id))
    for sid in registry.sids_for(user_id):
        socketio.server.disconnect(sid, namespace=NS)
