"""Domain errors shared by REST responses and socket acks (docs/architecture.md section 5.6)."""

HTTP_STATUS = {
    "AUTH_REQUIRED": 401,
    "INVALID_CREDENTIALS": 401,
    "FORBIDDEN": 403,
    "BANNED": 403,
    "MUTED": 403,
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 400,
    "INVALID_INVITE": 400,
    "USERNAME_TAKEN": 409,
    "PAYLOAD_TOO_LARGE": 413,
    "UNSUPPORTED_TYPE": 415,
    "INTERNAL": 500,
}


class RelayError(Exception):
    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    @property
    def status(self) -> int:
        return HTTP_STATUS.get(self.code, 400)

    def to_dict(self) -> dict:
        err = {"code": self.code, "message": self.message}
        if self.details:
            err["details"] = self.details
        return err


def ok(data=None) -> dict:
    return {"ok": True, "data": data if data is not None else {}}


def fail(err: RelayError) -> dict:
    return {"ok": False, "error": err.to_dict()}
