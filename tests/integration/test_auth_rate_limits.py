"""Auth rate limits hold under concurrent requests from more than one process
(ADR-0009): the Postgres UPSERT is what makes this correct, not application locking."""

import asyncio
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from kritvo.core.settings import Settings
from kritvo.main_api import create_app

pytestmark = pytest.mark.anyio


async def _start_app(settings: Settings) -> tuple[AsyncClient, Any]:
    """A fresh app (own engine/connection pool), like a second API server process
    sharing the same Postgres — the scenario ADR-0009's design has to hold up under."""
    app = create_app(settings)
    lifespan_cm = app.router.lifespan_context(app)
    await lifespan_cm.__aenter__()
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, lifespan_cm


async def test_otp_phone_rate_limit_holds_across_two_processes(
    identity_settings: Settings,
) -> None:
    client_a, ctx_a = await _start_app(identity_settings)
    client_b, ctx_b = await _start_app(identity_settings)
    try:
        phone = "+919812345678"
        clients = [client_a, client_b]
        responses = await asyncio.gather(
            *[
                clients[i % 2].post(
                    "/api/v1/auth/otp/request",
                    json={"phone": phone, "device_id": f"device-{i}"},
                )
                for i in range(5)
            ]
        )
        statuses = [r.status_code for r in responses]
        # The limit is 3 per phone per 15 minutes (LLD 12.4); five concurrent requests
        # for the same phone, split across two independent connection pools, must still
        # land on exactly 3 successes — not 5 or 6, which sequential-looking but
        # unsynchronised counters could produce.
        assert statuses.count(200) == 3, statuses
        assert statuses.count(429) == 2, statuses
    finally:
        await client_a.aclose()
        await client_b.aclose()
        await ctx_a.__aexit__(None, None, None)
        await ctx_b.__aexit__(None, None, None)
