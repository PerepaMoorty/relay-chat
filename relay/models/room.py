from relay.extensions import db
from relay.models._time import iso, utcnow

GENERAL = "general"


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)  # public (#general) | group | direct
    name = db.Column(db.String(40))
    visibility = db.Column(db.String(10), nullable=False, default="public")  # group rooms: public | private
    invite_code = db.Column(db.String(16), unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    # "<min_uid>:<max_uid>" for direct rooms, so each pair has exactly one conversation (CHAT-F-006)
    dm_key = db.Column(db.String(32), unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    members = db.relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")


class RoomMember(db.Model):
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, index=True)
    role = db.Column(db.String(10), nullable=False, default="member")  # owner | member
    # Receipt watermarks: the highest message id delivered to / read by this member (CHAT-F-027, F-040)
    delivered_up_to = db.Column(db.Integer, nullable=False, default=0)
    read_up_to = db.Column(db.Integer, nullable=False, default=0)
    joined_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    room = db.relationship("Room", back_populates="members")
    user = db.relationship("User")


def room_to_dict(room: Room, viewer_id: int) -> dict:
    """The Room object of the contract, as seen by viewer_id (0 = a broadcast to the whole room)."""
    data = {
        "id": room.id,
        "kind": room.kind,
        "name": room.name,
        "visibility": room.visibility,
        "owner_id": room.owner_id,
        "member_count": len(room.members),
        "created_at": iso(room.created_at),
    }
    if room.kind == "direct" and viewer_id:
        peer = next((m.user for m in room.members if m.user_id != viewer_id), None)
        data["peer"] = peer.to_public() if peer else None
        data["name"] = peer.username if peer else "(unknown)"
    if room.kind == "group" and viewer_id and room.owner_id == viewer_id:
        data["invite_code"] = room.invite_code
    return data
