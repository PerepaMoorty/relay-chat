"""Extension singletons. They are bound to the app in create_app(), which avoids circular imports."""

from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="threading")


@login_manager.user_loader
def load_user(session_id: str):
    # The session id is "<user_id>:<session_version>"; bumping the version revokes old cookies.
    from relay.services.auth import load_session_user

    return load_session_user(session_id)
