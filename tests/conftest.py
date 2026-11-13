import pytest

from relay import create_app
from relay.config import TestConfig
from relay.extensions import db


@pytest.fixture()
def app():
    """Create a fresh test application for each test."""
    app = create_app(TestConfig)

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provide a Flask test client."""
    return app.test_client()
