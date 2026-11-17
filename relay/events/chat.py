"""Message, receipt and sync events (CHAT-F-004, F-005, F-006, F-016, F-027…F-030, F-037).

Each handler is one service call plus one notify call; the contract is in docs/architecture.md section 5.4.
"""

from flask_login import current_user

from relay.events._ack import acked
from relay.extensions import socketio
from relay.services import messages, notify, receipts, sync


@socketio.on("message:send")
@acked
def on_message_send(payload):
    msg, created = messages.send(current_user.id, payload.get("room_id"), payload.get("body"),
                                 payload.get("client_id"), payload.get("attachment_id"))
    if created:  # a retried client_id is acked again without a second broadcast
        notify.message_created(msg)
    return {"message": msg.to_dict()}


@socketio.on("message:edit")
@acked
def on_message_edit(payload):
    msg = messages.edit(current_user.id, payload.get("message_id"), payload.get("body"))
    notify.message_updated(msg)
    return {"message": msg.to_dict()}


@socketio.on("message:delete")
@acked
def on_message_delete(payload):
    msg = messages.delete(current_user.id, payload.get("message_id"))
    notify.message_updated(msg)
    return {}


@socketio.on("receipt:update")
@acked
def on_receipt_update(payload):
    member, changed = receipts.update(current_user.id, payload.get("room_id"),
                                      payload.get("delivered_up_to"), payload.get("read_up_to"))
    if changed:
        notify.receipt_updated(member)
    return {"delivered_up_to": member.delivered_up_to, "read_up_to": member.read_up_to}


@socketio.on("sync")
@acked
def on_sync(payload):
    return sync.catch_up(current_user.id, payload.get("cursors"))
