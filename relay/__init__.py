"""Relay: real-time chat server built on Flask and Flask-SocketIO."""

import os

from flask import Flask, jsonify

from relay.config import Config
from relay.extensions import db, login_manager, socketio

CSP = "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)
    os.makedirs(app.instance_path, exist_ok=True)

    # Socket handlers must be registered before socketio.init_app(). Flask-SocketIO only replays
    # handlers declared while no server exists, so a later import would lose them on a second app.
    from relay import events  # noqa: F401

    db.init_app(app)
    login_manager.init_app(app)
    # None means same-origin only, on any address the server is reached by (CHAT-SR-014)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"] or None)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(ok=False, error={"code": "AUTH_REQUIRED", "message": "Please log in"}), 401

    @app.errorhandler(413)
    def too_large(_err):
        return jsonify(ok=False, error={"code": "PAYLOAD_TOO_LARGE", "message": "Files can be at most 10 MB"}), 413

    @app.after_request
    def security_headers(resp):
        # CHAT-SR-009: no inline scripts and nothing loaded from other origins
        resp.headers.setdefault("Content-Security-Policy", CSP)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    from relay.api import api_bp
    from relay.cli import register_cli
    from relay.views import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    register_cli(app)

    with app.app_context():
        from relay.services import rooms

        db.create_all()
        rooms.general_room()
        db.session.commit()

    return app
