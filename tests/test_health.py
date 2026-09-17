import pytest
from httpx import AsyncClient

from kritvo import __version__

pytestmark = pytest.mark.anyio


async def test_healthz_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


async def test_request_id_is_generated(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert len(response.headers["x-request-id"]) == 32


async def test_valid_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": "abc12345-test"})
    assert response.headers["x-request-id"] == "abc12345-test"


async def test_malformed_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": "bad id!"})
    assert response.headers["x-request-id"] != "bad id!"


async def test_gateway_app_serves_health() -> None:
    from httpx import ASGITransport

    from kritvo.main_gateway import create_app

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        response = await c.get("/healthz")
    assert response.status_code == 200
