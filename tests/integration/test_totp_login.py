"""Password + TOTP login for owners/admins (LLD 12.1), and the new-device alert
through the notification interface (TASK-003 acceptance criteria)."""

from uuid import uuid4

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.settings import Settings
from tests.integration.conftest import RecordingHandler, SeededUser, seed_login_user

pytestmark = pytest.mark.anyio

_PASSWORD = "correct horse battery staple"  # noqa: S105 — test fixture, not a real secret
_TOTP_SECRET = pyotp.random_base32()


@pytest.fixture
async def seeded_owner(
    system_sessionmaker: async_sessionmaker[AsyncSession], identity_settings: Settings
) -> SeededUser:
    return await seed_login_user(
        system_sessionmaker,
        identity_settings=identity_settings,
        phone=f"+9198765{uuid4().int % 100000:05d}",
        permissions=["settings.manage", "member.manage", "role.manage"],
        password=_PASSWORD,
        totp_secret=_TOTP_SECRET,
    )


async def _get_pending_token(client: AsyncClient, seeded_owner: SeededUser) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": seeded_owner.phone, "password": _PASSWORD},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["pending_token"])


async def test_password_and_totp_login_end_to_end(
    identity_client: AsyncClient, seeded_owner: SeededUser
) -> None:
    pending_token = await _get_pending_token(identity_client, seeded_owner)

    response = await identity_client.post(
        "/api/v1/auth/totp/verify",
        json={
            "pending_token": pending_token,
            "code": pyotp.TOTP(_TOTP_SECRET).now(),
            "device_id": "owner-laptop",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]
    assert "refresh_token" in response.cookies


async def test_new_device_login_emits_an_alert(
    identity_client: AsyncClient,
    seeded_owner: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    pending_token = await _get_pending_token(identity_client, seeded_owner)

    response = await identity_client.post(
        "/api/v1/auth/totp/verify",
        json={
            "pending_token": pending_token,
            "code": pyotp.TOTP(_TOTP_SECRET).now(),
            "device_id": "a-brand-new-laptop",
        },
    )
    assert response.status_code == 200, response.text
    assert "New sign-in" in dev_sender_logs.text
    assert "login_alert" in dev_sender_logs.text


async def test_wrong_password_is_rejected(
    identity_client: AsyncClient, seeded_owner: SeededUser
) -> None:
    response = await identity_client.post(
        "/api/v1/auth/login",
        json={"identifier": seeded_owner.phone, "password": "not the password"},
    )
    assert response.status_code == 401


async def test_wrong_totp_code_is_rejected(
    identity_client: AsyncClient, seeded_owner: SeededUser
) -> None:
    pending_token = await _get_pending_token(identity_client, seeded_owner)
    response = await identity_client.post(
        "/api/v1/auth/totp/verify",
        json={"pending_token": pending_token, "code": "000000", "device_id": "owner-laptop"},
    )
    assert response.status_code == 401
