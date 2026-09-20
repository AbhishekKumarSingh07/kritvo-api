"""Production-like environments must fail to start with no real sender registered —
a hard failure, not a warning or a silent fallback (ADR-0008 condition a)."""

import pytest

from kritvo.core.settings import Settings
from kritvo.main_api import create_app
from kritvo.modules.notifications.registry import NoRealSenderConfiguredError, build_sender
from kritvo.modules.notifications.senders.logging_sender import LoggingNotificationSender

pytestmark = pytest.mark.anyio


def test_logging_sender_allowed_in_local_and_test() -> None:
    for env in ("local", "test"):
        sender = build_sender(Settings(app_env=env))
        assert isinstance(sender, LoggingNotificationSender)


def test_logging_sender_rejected_outside_local_and_test() -> None:
    for env in ("staging", "production"):
        with pytest.raises(NoRealSenderConfiguredError):
            build_sender(Settings(app_env=env))


async def test_app_refuses_to_start_in_production_without_a_real_sender() -> None:
    app = create_app(Settings(app_env="production"))
    with pytest.raises(NoRealSenderConfiguredError):
        async with app.router.lifespan_context(app):
            pytest.fail("startup should have raised before this point")
