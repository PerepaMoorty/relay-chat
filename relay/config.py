"""Configuration and limits. Every key here is listed in docs/architecture.md section 6.9."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("DEBUG", "0") == "1"

    # A relative SQLite path resolves inside instance/
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///relay.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Wait for the SQLite write lock instead of failing when several clients write at once
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Extra origins allowed to open a socket. Empty means same origin only, on whatever address
    # the server is reached by (localhost or the LAN IP) (CHAT-SR-014).
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    MAX_UPLOAD_BYTES = 10 * 1024 * 1024
    MAX_CONTENT_LENGTH = MAX_UPLOAD_BYTES + 512 * 1024  # file plus multipart overhead
    MESSAGE_MAX_LEN = 4000
    HISTORY_PAGE_SIZE = 50
    UPLOAD_DIR = "uploads"  # inside instance/

    # Seconds before a user is announced offline, so a page refresh does not flash leave/join
    PRESENCE_GRACE_SECONDS = 3


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PRESENCE_GRACE_SECONDS = 0
