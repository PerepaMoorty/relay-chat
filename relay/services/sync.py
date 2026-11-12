"""Reconnect catch-up (CHAT-F-021, F-028; CHAT-NF-007): what was created after the client's last known message."""

from relay.models import Message
from relay.models.room import room_to_dict
from relay.services import receipts, rooms

MAX_PER_ROOM = 200


def _cursor(cursors: dict, room_id: int) -> int:
    # JSON object keys arrive as strings, but accept int keys too; bad values count as 0
    value = cursors.get(str(room_id), cursors.get(room_id, 0))
    if type(value) is bool:
        return 0
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def catch_up(user_id: int, cursors) -> dict:
    cursors = cursors if isinstance(cursors, dict) else {}
    my_rooms = rooms.rooms_for(user_id)
    missed = []
    for room in my_rooms:
        after = _cursor(cursors, room.id)
        if not after:
            continue  # the client has not loaded this room yet; it fetches history when the room is opened
        rows = (Message.query.filter(Message.room_id == room.id, Message.id > after)
                .order_by(Message.id).limit(MAX_PER_ROOM).all())
        missed.extend(m.to_dict() for m in rows)
    return {
        "rooms": [room_to_dict(r, user_id) for r in my_rooms],
        "messages": missed,
        "unread": receipts.unread_counts(user_id),
    }
