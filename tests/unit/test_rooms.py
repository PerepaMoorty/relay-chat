import pytest

from relay.errors import RelayError
from relay.extensions import db
from relay.models import RoomMember, User
from relay.services import rooms


def _user(username):
    user = User(username=username, password_hash="unused")
    db.session.add(user)
    db.session.flush()
    return user


def test_create_group_trims_name_and_makes_creator_owner_and_member(app):
    with app.app_context():
        owner = _user("alice")

        room = rooms.create_group(owner.id, "  project team  ", "public")

        assert room.name == "project team"
        assert room.kind == "group"
        assert room.owner_id == owner.id
        assert room.visibility == "public"
        assert room.invite_code is None
        assert db.session.get(RoomMember, (room.id, owner.id)).role == "owner"


@pytest.mark.parametrize(("name", "visibility"), [("", "public"), ("x" * 41, "public"), ("valid", "secret")])
def test_create_group_rejects_invalid_name_or_visibility(app, name, visibility):
    with app.app_context(), pytest.raises(RelayError) as error:
        rooms.create_group(1, name, visibility)

    assert error.value.code == "VALIDATION_ERROR"


def test_public_room_list_excludes_private_groups(app):
    with app.app_context():
        owner = _user("alice")
        rooms.create_group(owner.id, "visible", "public")
        private = rooms.create_group(owner.id, "hidden", "private")

        listed = rooms.public_rooms()

        assert [room.name for room in listed] == ["general", "visible"]
        assert private not in listed


def test_join_public_is_idempotent_and_private_rooms_are_not_joinable(app):
    with app.app_context():
        owner = _user("alice")
        member = _user("bob")
        public = rooms.create_group(owner.id, "visible", "public")
        private = rooms.create_group(owner.id, "hidden", "private")

        joined, added = rooms.join_public(member.id, public.id)
        joined_again, added_again = rooms.join_public(member.id, public.id)

        assert joined.id == public.id and added is True
        assert joined_again.id == public.id and added_again is False
        assert len(RoomMember.query.filter_by(room_id=public.id, user_id=member.id).all()) == 1
        with pytest.raises(RelayError) as error:
            rooms.join_public(member.id, private.id)
        assert error.value.code == "NOT_FOUND"


def test_join_by_invite_validates_code_and_is_idempotent(app):
    with app.app_context():
        owner = _user("alice")
        member = _user("bob")
        private = rooms.create_group(owner.id, "hidden", "private")

        joined, added = rooms.join_by_invite(member.id, f" {private.invite_code} ")
        repeated, added_again = rooms.join_by_invite(member.id, private.invite_code)

        assert joined.id == repeated.id == private.id
        assert added is True and added_again is False
        with pytest.raises(RelayError) as error:
            rooms.join_by_invite(member.id, "invalid")
        assert error.value.code == "INVALID_INVITE"


def test_direct_room_is_unique_for_pair_and_rejects_self_or_unknown_user(app):
    with app.app_context():
        alice = _user("alice")
        bob = _user("bob")

        direct, created = rooms.open_direct(alice.id, bob.id)
        same_direct, created_again = rooms.open_direct(bob.id, alice.id)

        assert created is True and created_again is False
        assert direct.id == same_direct.id
        assert set(rooms.member_ids(direct.id)) == {alice.id, bob.id}
        with pytest.raises(RelayError) as self_error:
            rooms.open_direct(alice.id, alice.id)
        assert self_error.value.code == "VALIDATION_ERROR"
        with pytest.raises(RelayError) as missing_error:
            rooms.open_direct(alice.id, 999)
        assert missing_error.value.code == "NOT_FOUND"


def test_leave_removes_group_member_but_rejects_direct_room(app):
    with app.app_context():
        alice = _user("alice")
        bob = _user("bob")
        group = rooms.create_group(alice.id, "project", "public")
        rooms.join_public(bob.id, group.id)
        direct, _ = rooms.open_direct(alice.id, bob.id)

        rooms.leave(bob.id, group.id)

        assert rooms.member_ids(group.id) == [alice.id]
        with pytest.raises(RelayError) as error:
            rooms.leave(alice.id, direct.id)
        assert error.value.code == "VALIDATION_ERROR"
