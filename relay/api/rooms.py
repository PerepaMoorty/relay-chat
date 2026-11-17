"""Conversations, membership and history (CHAT-F-006, F-020, F-021, F-022, F-023, F-040)."""

from flask import jsonify, request
from flask_login import current_user, login_required

from relay.api import api_bp, json_body
from relay.errors import ok
from relay.models.room import room_to_dict
from relay.services import messages, notify, receipts, rooms


def _room(room) -> dict:
    return room_to_dict(room, current_user.id)


@api_bp.get("/rooms")
@login_required
def list_rooms():
    unread = receipts.unread_counts(current_user.id)
    data = [{**_room(r), "unread": unread.get(r.id, 0)} for r in rooms.rooms_for(current_user.id)]
    return jsonify(ok({"rooms": data}))


@api_bp.get("/rooms/public")
@login_required
def public_rooms():
    mine = {r.id for r in rooms.rooms_for(current_user.id)}
    return jsonify(ok({"rooms": [{**_room(r), "joined": r.id in mine} for r in rooms.public_rooms()]}))


@api_bp.post("/rooms")
@login_required
def create_room():
    body = json_body()
    room = rooms.create_group(current_user.id, body.get("name"), body.get("visibility", "public"))
    notify.subscribe(current_user.id, room)
    return jsonify(ok({"room": _room(room)})), 201


def _joined(room, added: bool):
    # Only a real join changes channels and member counts, so repeated joins stay silent
    if added:
        notify.subscribe(current_user.id, room)
        notify.room_updated(room)
    return jsonify(ok({"room": _room(room)}))


@api_bp.post("/rooms/<int:room_id>/join")
@login_required
def join_room(room_id: int):
    return _joined(*rooms.join_public(current_user.id, room_id))


@api_bp.post("/rooms/join")
@login_required
def join_by_invite():
    return _joined(*rooms.join_by_invite(current_user.id, json_body().get("invite_code")))


@api_bp.post("/rooms/<int:room_id>/leave")
@login_required
def leave_room(room_id: int):
    room = rooms.leave(current_user.id, room_id)
    notify.unsubscribe(current_user.id, room)
    notify.room_updated(room)
    return jsonify(ok())


@api_bp.post("/dms")
@login_required
def open_direct():
    room, created = rooms.open_direct(current_user.id, json_body().get("user_id"))
    if created:
        for uid in rooms.member_ids(room.id):
            notify.subscribe(uid, room)
    return jsonify(ok({"room": _room(room)})), 201 if created else 200


@api_bp.get("/rooms/<int:room_id>/messages")
@login_required
def room_history(room_id: int):
    page = messages.history(current_user.id, room_id, request.args.get("before"), request.args.get("limit"))
    return jsonify(ok({"messages": [m.to_dict() for m in page], "receipts": receipts.for_room(room_id)}))
