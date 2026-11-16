import pytest

from relay.errors import RelayError
from relay.extensions import db
from relay.models import RoomMember
from relay.services import auth


def test_register_normalizes_username_hashes_password_and_joins_general(app):
    with app.app_context():
        user = auth.register(" Alice ", "long-password")

        assert user.username == "alice"
        assert user.password_hash != "long-password"
        assert auth.authenticate("ALICE", "long-password").id == user.id
        general_member = RoomMember.query.filter_by(user_id=user.id).one()
        assert general_member.room.kind == "public"
        assert general_member.room.name == "general"


@pytest.mark.parametrize(
    ("username", "password"),
    [("ab", "long-password"), ("bad-name", "long-password"), ("alice", "short")],
)
def test_register_rejects_invalid_credentials(app, username, password):
    with app.app_context(), pytest.raises(RelayError) as error:
        auth.register(username, password)

    assert error.value.code == "VALIDATION_ERROR"


def test_register_rejects_duplicate_username(app):
    with app.app_context():
        auth.register("alice", "long-password")

        with pytest.raises(RelayError) as error:
            auth.register("ALICE", "another-password")

        assert error.value.code == "USERNAME_TAKEN"


def test_authenticate_rejects_wrong_password_and_banned_account(app):
    with app.app_context():
        user = auth.register("alice", "long-password")

        with pytest.raises(RelayError) as wrong_password:
            auth.authenticate("alice", "wrong-password")
        assert wrong_password.value.code == "INVALID_CREDENTIALS"

        user.banned_at = user.created_at
        db.session.commit()
        with pytest.raises(RelayError) as banned:
            auth.authenticate("alice", "long-password")
        assert banned.value.code == "BANNED"


def test_load_session_user_and_revoke_sessions(app):
    with app.app_context():
        user = auth.register("alice", "long-password")
        old_session_id = user.get_id()
        assert auth.load_session_user(old_session_id).id == user.id

        auth.revoke_sessions(user)

        assert auth.load_session_user(old_session_id) is None
        assert auth.load_session_user(user.get_id()).id == user.id
        assert auth.load_session_user("invalid") is None



