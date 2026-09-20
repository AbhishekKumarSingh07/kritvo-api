"""Refresh rotation and reuse detection (LLD 12.2): rotating advances the session;
replaying an already-rotated token revokes the whole family, not just itself."""

import re

import pytest
from httpx import AsyncClient

from tests.integration.conftest import RecordingHandler, SeededUser

pytestmark = pytest.mark.anyio


async def _login(client: AsyncClient, logs: RecordingHandler, *, phone: str, device_id: str) -> str:
    await client.post("/api/v1/auth/otp/request", json={"phone": phone, "device_id": device_id})
    match = re.search(r"login code is (\d{6})", logs.text)
    assert match, logs.text
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "code": match.group(1), "device_id": device_id},
    )
    assert response.status_code == 200, response.text
    return response.cookies["refresh_token"]


async def test_refresh_rotates_the_token(
    identity_client: AsyncClient,
    seeded_field_user: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    original = await _login(
        identity_client, dev_sender_logs, phone=seeded_field_user.phone, device_id="device-1"
    )

    response = await identity_client.post("/api/v1/auth/refresh")
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]
    assert response.cookies["refresh_token"] != original


async def test_reused_refresh_token_revokes_the_whole_family(
    identity_client: AsyncClient,
    seeded_field_user: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    original = await _login(
        identity_client, dev_sender_logs, phone=seeded_field_user.phone, device_id="device-2"
    )

    first_refresh = await identity_client.post("/api/v1/auth/refresh")
    assert first_refresh.status_code == 200
    rotated = first_refresh.cookies["refresh_token"]

    # Replay the token that was already rotated away.
    replay = await identity_client.post("/api/v1/auth/refresh", cookies={"refresh_token": original})
    assert replay.status_code == 401

    # The reuse revoked the whole family: even the legitimately rotated token is dead.
    denied = await identity_client.post("/api/v1/auth/refresh", cookies={"refresh_token": rotated})
    assert denied.status_code == 401


async def test_refresh_without_a_cookie_is_rejected(identity_client: AsyncClient) -> None:
    response = await identity_client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_unknown_refresh_token_is_rejected(identity_client: AsyncClient) -> None:
    response = await identity_client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": "not-a-real-token"}
    )
    assert response.status_code == 401
