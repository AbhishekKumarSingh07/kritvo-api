"""The one interface identity (and every future caller) depends on (ADR-0008).

Other modules import only ``NotificationSender`` and ``NotificationKind`` from this
file — never a concrete class from ``notifications.senders``. import-linter enforces
that boundary so a real sender can replace the logging stub without touching callers.
"""

from enum import StrEnum
from typing import Protocol
from uuid import UUID


class NotificationKind(StrEnum):
    OTP = "otp"
    LOGIN_ALERT = "login_alert"


class NotificationSender(Protocol):
    async def send(self, *, user_id: UUID, kind: NotificationKind, message: str) -> None:
        """Deliver ``message`` (an OTP code or an alert) to ``user_id``."""
        ...
