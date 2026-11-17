"""Typing indicators (CHAT-F-026). Online/offline presence lives in connection.py.

Nothing is stored: the event only goes to the other sockets in the room.
"""

from flask import request
from flask_login import current_user

from relay.events._ack import acked
from relay.extensions import socketio
from relay.services import notify, rooms


def _typing(payload: dict, is_typing: bool) -> dict:
    room = rooms.require_member(payload.get("room_id"), current_user.id)
    notify.typing(room.id, current_user, is_typing, skip_sid=request.sid)
    return {}


@socketio.on("typing:start")
@acked
def on_typing_start(payload):
    return _typing(payload, True)


@socketio.on("typing:stop")
@acked
def on_typing_stop(payload):
    return _typing(payload, False)
