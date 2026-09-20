"""A real, throwaway PostgreSQL, shared by every test package that needs one.

A fake or mocked database cannot prove that row-level security, or the identity
SECURITY DEFINER functions, actually behave as designed — only a real PostgreSQL, with
the real policies and functions applied, can (LLD section 2.4, 13.2). The container is
started once for the whole test session: bootstrapped with the three database roles
(``scripts/bootstrap-db.sql``) and migrated to head, exactly like local dev and CI would
do it.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.community.postgres import PostgresContainer

from kritvo.core.db import create_engine, create_sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SQL = (REPO_ROOT / "scripts" / "bootstrap-db.sql").read_text()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def app() -> FastAPI:
    from kritvo.main_api import create_app

    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _bootstrap_roles(superuser_dsn: str) -> None:
    conn = await asyncpg.connect(superuser_dsn)
    try:
        # No bind parameters: asyncpg then uses the simple query protocol, which (like
        # psql) accepts a whole script of semicolon-separated statements, including the
        # DO $$ ... $$ block, in one call.
        await conn.execute(BOOTSTRAP_SQL)
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def postgres_urls() -> Iterator[dict[str, str]]:
    """Start Postgres, bootstrap the roles, run migrations; yield a URL per role."""
    with PostgresContainer(
        "postgres:16",
        username="postgres",
        password="postgres",  # noqa: S106 — throwaway container, not a real credential
        dbname="kritvo",
        driver="asyncpg",
    ) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)

        def url_for(user: str, password: str) -> str:
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/kritvo"

        asyncio.run(_bootstrap_roles(container.get_connection_url(driver=None)))

        owner_url = url_for("kritvo_owner", "change-me")
        os.environ["DATABASE_OWNER_URL"] = owner_url
        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")

        yield {
            "app": url_for("kritvo_app", "change-me"),
            "system": url_for("kritvo_system", "change-me"),
            "owner": owner_url,
        }


@pytest.fixture
async def app_sessionmaker(
    postgres_urls: dict[str, str],
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Sessions made from this always go through kritvo_app — NOBYPASSRLS.

    Function-scoped and disposed at teardown: an AsyncEngine's connection pool is bound
    to the event loop it first ran on, and each test function gets its own event loop
    (anyio's default), so a session-scoped engine would hand out connections from a
    now-foreign loop the moment a second test used it.
    """
    engine = create_engine(postgres_urls["app"])
    try:
        yield create_sessionmaker(engine)
    finally:
        await engine.dispose()


@pytest.fixture
async def system_sessionmaker(
    postgres_urls: dict[str, str],
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """kritvo_system bypasses RLS — used only to seed fixtures across tenants.

    Function-scoped for the same reason as app_sessionmaker above.
    """
    engine = create_engine(postgres_urls["system"])
    try:
        yield create_sessionmaker(engine)
    finally:
        await engine.dispose()
