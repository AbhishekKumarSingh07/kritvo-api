"""OTP request -> verify -> access token + refresh cookie, end to end (LLD 12.1),
against a real PostgreSQL, reading the code from the ADR-0008 logging sender."""

import re

import pytest
from httpx import AsyncClient

from tests.integration.conftest import RecordingHandler, SeededUser

pytestmark = pytest.mark.anyio


async def _request_and_read_code(
    client: AsyncClient, logs: RecordingHandler, *, phone: str, device_id: str
) -> str:
    response = await client.post(
        "/api/v1/auth/otp/request", json={"phone": phone, "device_id": device_id}
    )
    assert response.status_code == 200, response.text
    match = re.search(r"login code is (\d{6})", logs.text)
    assert match, f"no OTP code found in logs: {logs.text!r}"
    return match.group(1)


async def test_otp_login_end_to_end(
    identity_client: AsyncClient,
    seeded_field_user: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    code = await _request_and_read_code(
        identity_client, dev_sender_logs, phone=seeded_field_user.phone, device_id="device-1"
    )

    response = await identity_client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": seeded_field_user.phone, "code": code, "device_id": "device-1"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"  # noqa: S105 — the OAuth2 token type, not a credential
    assert "refresh_token" in response.cookies


async def test_unknown_phone_returns_ok_without_enumerating(
    identity_client: AsyncClient, dev_sender_logs: RecordingHandler
) -> None:
    response = await identity_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": "+919000000000", "device_id": "device-x"},
    )
    assert response.status_code == 200
    assert "login code is" not in dev_sender_logs.text


async def test_wrong_code_is_rejected(
    identity_client: AsyncClient,
    seeded_field_user: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    await _request_and_read_code(
        identity_client, dev_sender_logs, phone=seeded_field_user.phone, device_id="device-2"
    )
    response = await identity_client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": seeded_field_user.phone, "code": "000000", "device_id": "device-2"},
    )
    assert response.status_code == 401


async def test_code_cannot_be_reused(
    identity_client: AsyncClient,
    seeded_field_user: SeededUser,
    dev_sender_logs: RecordingHandler,
) -> None:
    code = await _request_and_read_code(
        identity_client, dev_sender_logs, phone=seeded_field_user.phone, device_id="device-3"
    )
    first = await identity_client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": seeded_field_user.phone, "code": code, "device_id": "device-3"},
    )
    assert first.status_code == 200

    second = await identity_client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": seeded_field_user.phone, "code": code, "device_id": "device-3"},
    )
    assert second.status_code == 401
