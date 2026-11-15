import pytest

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Message, User
from relay.services import messages, receipts, rooms


def _member(username, room_id):
    user = User(username=username, password_hash="unused")
    db.session.add(user)
    db.session.flush()
    rooms.add_member(room_id, user.id)
    db.session.commit()
    return user


def test_receipt_watermarks_only_move_forward_and_read_implies_delivered(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        sent = [messages.send(bob.id, room.id, f"message {i}")[0] for i in range(3)]

        member, changed = receipts.update(alice.id, room.id, delivered_up_to=sent[1].id)
        assert changed is True
        assert member.delivered_up_to == sent[1].id
        assert member.read_up_to == 0

        member, changed = receipts.update(alice.id, room.id, read_up_to=sent[2].id)
        assert changed is True
        assert member.read_up_to == sent[2].id
        assert member.delivered_up_to == sent[2].id

        member, changed = receipts.update(alice.id, room.id, delivered_up_to=sent[0].id, read_up_to=sent[1].id)
        assert changed is False
        assert member.delivered_up_to == sent[2].id
        assert member.read_up_to == sent[2].id


def test_receipt_watermarks_cap_at_latest_message_and_ignore_non_integer_values(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        latest, _ = messages.send(bob.id, room.id, "newest")

        member, changed = receipts.update(alice.id, room.id, delivered_up_to=latest.id + 100)
        assert changed is True
        assert member.delivered_up_to == latest.id

        member, changed = receipts.update(alice.id, room.id, delivered_up_to=True, read_up_to="1")
        assert changed is False
        assert member.delivered_up_to == latest.id
        assert member.read_up_to == 0


def test_receipt_requires_membership_and_lists_room_members_in_order(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        outsider = User(username="carol", password_hash="unused")
        db.session.add(outsider)
        db.session.commit()

        with pytest.raises(RelayError) as error:
            receipts.update(outsider.id, room.id, delivered_up_to=1)

        assert error.value.code == "NOT_FOUND"
        assert [entry["user_id"] for entry in receipts.for_room(room.id)] == sorted([alice.id, bob.id])


def test_unread_counts_exclude_own_deleted_and_already_read_messages(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        own, _ = messages.send(alice.id, room.id, "my message")
        unread_one, _ = messages.send(bob.id, room.id, "unread one")
        unread_two, _ = messages.send(bob.id, room.id, "unread two")
        deleted, _ = messages.send(bob.id, room.id, "deleted")
        messages.delete(bob.id, deleted.id)

        assert receipts.unread_counts(alice.id) == {room.id: 2}
        receipts.update(alice.id, room.id, read_up_to=unread_one.id)
        assert receipts.unread_counts(alice.id) == {room.id: 1}
        assert receipts.unread_counts(bob.id) == {room.id: 1}
        assert db.session.get(Message, own.id) is not None


