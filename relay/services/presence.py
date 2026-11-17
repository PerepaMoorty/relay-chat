"""Who is connected, and on which sockets (CHAT-F-009, F-013, F-015, F-052; CHAT-SR-005).

The registry is in memory and local to this process by design (docs/architecture.md section 15).
"""

import threading
from datetime import datetime

from relay.models._time import utcnow


class PresenceRegistry:
    """Thread-safe two-way map between Socket.IO session ids and user ids."""

    def __init__(self):
        self._lock = threading.Lock()
        self._user_by_sid: dict[str, int] = {}
        self._connected_at: dict[str, datetime] = {}
        self._sids_by_user: dict[int, set[str]] = {}

    def add(self, sid: str, user_id: int) -> bool:
        """Register a socket. Returns True if this is the user's first live socket."""
        with self._lock:
            self._user_by_sid[sid] = user_id
            self._connected_at[sid] = utcnow()
            sids = self._sids_by_user.setdefault(user_id, set())
            sids.add(sid)
            return len(sids) == 1

    def remove(self, sid: str) -> tuple[int | None, bool]:
        """Unregister a socket. Returns (user_id, was_last_socket); an unknown sid gives (None, False)."""
        with self._lock:
            user_id = self._user_by_sid.pop(sid, None)
            self._connected_at.pop(sid, None)
            if user_id is None:
                return None, False
            sids = self._sids_by_user.get(user_id, set())
            sids.discard(sid)
            if sids:
                return user_id, False
            self._sids_by_user.pop(user_id, None)
            return user_id, True

    def user_for(self, sid: str) -> int | None:
        with self._lock:
            return self._user_by_sid.get(sid)

    def sids_for(self, user_id: int) -> list[str]:
        with self._lock:
            return list(self._sids_by_user.get(user_id, ()))

    def is_online(self, user_id: int) -> bool:
        with self._lock:
            return user_id in self._sids_by_user

    def online_user_ids(self) -> list[int]:
        with self._lock:
            return list(self._sids_by_user)

    def snapshot(self) -> list[dict]:
        """Every live socket as {"sid", "user_id", "connected_at"} (copies, safe to iterate)."""
        with self._lock:
            return [{"sid": sid, "user_id": uid, "connected_at": self._connected_at.get(sid)}
                    for sid, uid in self._user_by_sid.items()]

    def clear(self) -> None:
        with self._lock:
            self._user_by_sid.clear()
            self._connected_at.clear()
            self._sids_by_user.clear()


registry = PresenceRegistry()
