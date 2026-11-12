"""Development and LAN entry point: python run.py"""

import socket

from relay import create_app
from relay.extensions import socketio

app = create_app()


def lan_address() -> str | None:
    """Best-effort LAN IP, so teammates know which URL to open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))  # no packet is sent; this only picks the outgoing interface
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    port = app.config["PORT"]
    print(f"\n  Relay is running:\n    this computer:   http://localhost:{port}")
    if app.config["HOST"] == "0.0.0.0" and (ip := lan_address()):
        print(f"    same Wi-Fi/LAN:  http://{ip}:{port}")
    print("  Press Ctrl+C to stop.\n")
    # The Werkzeug server is fine for the LAN demo; it is not a production server.
    socketio.run(app, host=app.config["HOST"], port=port, debug=app.config["DEBUG"], allow_unsafe_werkzeug=True)
