import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import BaseModel

from kritvo.core.errors import PROBLEM_JSON, AppError

pytestmark = pytest.mark.anyio


class Item(BaseModel):
    name: str
    qty: int


def _add_test_routes(app: FastAPI) -> None:
    @app.post("/_test/items")
    async def create_item(item: Item) -> Item:
        return item

    @app.get("/_test/app-error")
    async def app_error() -> None:
        raise AppError("GUARD_FAILED", status=422, title="Job cannot be completed yet")


async def test_unknown_route_is_problem_json(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_JSON)
    assert response.json()["code"] == "NOT_FOUND"


async def test_validation_error_lists_fields(app: FastAPI, client: AsyncClient) -> None:
    _add_test_routes(app)
    response = await client.post("/_test/items", json={"name": "filter", "qty": "many"})
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "qty"


async def test_app_error_keeps_code_and_title(app: FastAPI, client: AsyncClient) -> None:
    _add_test_routes(app)
    response = await client.get("/_test/app-error")
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "GUARD_FAILED"
    assert body["title"] == "Job cannot be completed yet"
    assert body["type"].endswith("/guard-failed")
