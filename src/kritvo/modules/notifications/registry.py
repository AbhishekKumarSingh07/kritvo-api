"""Resolves the configured `NotificationSender` and enforces ADR-0008's startup guard.

Condition (a) of ADR-0008: the application must fail to start, not log a warning or
silently fall back, if it would otherwise run outside local/dev with only the logging
sender available. `core.app_factory` calls `build_sender` during startup (not only from
the send path) so this is a hard, unconditional gate.
"""

from kritvo.core.settings import Settings
from kritvo.modules.notifications.interface import NotificationSender
from kritvo.modules.notifications.senders.logging_sender import LoggingNotificationSender

_NON_PRODUCTION_ENVS = frozenset({"local", "test"})


class NoRealSenderConfiguredError(RuntimeError):
    """Raised at startup: production-like env, but only the ADR-0008 stub is available."""


def build_sender(settings: Settings) -> NotificationSender:
    if settings.app_env not in _NON_PRODUCTION_ENVS:
        raise NoRealSenderConfiguredError(
            f"No real notification sender is registered (only the ADR-0008 logging "
            f"stub exists) and APP_ENV={settings.app_env!r} is not local/test. "
            "Refusing to start: TASK-013/TASK-019 must ship a real sender before this "
            "environment can run identity."
        )
    return LoggingNotificationSender()
