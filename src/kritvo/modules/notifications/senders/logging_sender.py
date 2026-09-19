"""Non-production notification sender (ADR-0008).

Writes the message — including the plain OTP code — to structured logs instead of
delivering it over WhatsApp or SMS, since no real channel exists yet. This is the one
documented exception to LLD 12.4's "no OTPs ... in logs" rule.

Registered only when ``app_env`` is ``local`` or ``test``; ``notifications.registry``
refuses to start the application anywhere else unless a real sender is registered
instead. TASK-013 (WhatsApp gateway) and TASK-019 (notification router) replace this
class behind the same interface. TASK-022 (the Rahul Electricals pilot) must not run
against it — see ADR-0008's "Follow-up required" checklist.
"""

import logging
from uuid import UUID

from kritvo.modules.notifications.interface import NotificationKind

logger = logging.getLogger("kritvo.notifications.dev_sender")


class LoggingNotificationSender:
    """ADR-0008 stub. Non-production only — see module docstring."""

    async def send(self, *, user_id: UUID, kind: NotificationKind, message: str) -> None:
        logger.info(
            "dev_notification user_id=%s kind=%s message=%s",
            user_id,
            kind.value,
            message,
        )
