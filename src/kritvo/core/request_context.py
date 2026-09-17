"""Per-request context (request ID) shared by middleware and logging."""

import re
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
HEADER = "x-request-id"


def current_request_id() -> str | None:
    return _request_id.get()


class RequestIdMiddleware:
    """Accepts a well-formed X-Request-ID or creates one, and echoes it on the response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(HEADER.encode(), b"").decode("latin-1")
        request_id = incoming if _VALID_ID.match(incoming) else uuid.uuid4().hex
        token = _request_id.set(request_id)

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((HEADER.encode(), request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            _request_id.reset(token)
