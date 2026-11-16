import pytest

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Message, User
from relay.services import messages, rooms


def _member(username, room_id):
    user = User(username=username, password_hash="unused")
    db.session.add(user)
    db.session.flush()
    rooms.add_member(room_id, user.id)
    db.session.commit()
    return user


def test_send_trims_body_and_retry_returns_original_message(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)

        first, created = messages.send(alice.id, room.id, "  hello  ", client_id="retry-1")
        retry, created_again = messages.send(alice.id, room.id, "ignored", client_id="retry-1")

        assert created is True and created_again is False
        assert first.id == retry.id
        assert first.body == "hello"
        assert Message.query.count() == 1


def test_send_rejects_nonmember_and_invalid_payloads(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        outsider = User(username="bob", password_hash="unused")
        db.session.add(outsider)
        db.session.commit()

        with pytest.raises(RelayError) as nonmember:
            messages.send(outsider.id, room.id, "hello")
        assert nonmember.value.code == "NOT_FOUND"

        for body in (None, "  ", "bad\x00body", "x" * 4001):
            with pytest.raises(RelayError) as invalid:
                messages.send(alice.id, room.id, body)
            assert invalid.value.code == "VALIDATION_ERROR"


def test_send_rejects_duplicate_client_id_from_another_sender(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        messages.send(alice.id, room.id, "hello", client_id="same-id")

        with pytest.raises(RelayError) as error:
            messages.send(bob.id, room.id, "hello", client_id="same-id")

        assert error.value.code == "VALIDATION_ERROR"


def test_muted_member_cannot_send(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        alice.muted_until = alice.created_at.replace(year=alice.created_at.year + 1)
        db.session.commit()

        with pytest.raises(RelayError) as error:
            messages.send(alice.id, room.id, "hello")

        assert error.value.code == "MUTED"
        assert "until" in error.value.details


def test_edit_requires_ownership_and_sets_edited_timestamp(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        bob = _member("bob", room.id)
        msg, _ = messages.send(alice.id, room.id, "before")

        updated = messages.edit(alice.id, msg.id, " after ")

        assert updated.body == "after"
        assert updated.edited_at is not None
        with pytest.raises(RelayError) as error:
            messages.edit(bob.id, msg.id, "no")
        assert error.value.code == "FORBIDDEN"


def test_delete_soft_deletes_and_is_idempotent(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        msg, _ = messages.send(alice.id, room.id, "keep ordering")

        deleted = messages.delete(alice.id, msg.id)
        deleted_again = messages.delete(alice.id, msg.id)

        assert deleted.id == deleted_again.id == msg.id
        assert deleted.deleted_at is not None
        assert deleted.to_dict()["deleted"] is True
        assert deleted.to_dict()["body"] == ""
        assert Message.query.count() == 1


def test_history_is_oldest_first_with_exclusive_before_cursor_and_requires_membership(app):
    with app.app_context():
        room = rooms.general_room()
        alice = _member("alice", room.id)
        outsider = User(username="bob", password_hash="unused")
        db.session.add(outsider)
        db.session.commit()
        sent = [messages.send(alice.id, room.id, f"message {i}")[0] for i in range(4)]

        page = messages.history(alice.id, room.id, before=sent[3].id, limit=2)

        assert [message.id for message in page] == [sent[1].id, sent[2].id]
        assert messages.last_id(room.id) == sent[3].id
        assert messages.last_id(999) == 0
        with pytest.raises(RelayError) as error:
            messages.history(outsider.id, room.id)
        assert error.value.code == "NOT_FOUND"
