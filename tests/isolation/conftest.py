"""A real, throwaway PostgreSQL for the isolation suite (LLD section 2.4, 13.2).

A fake or mocked database cannot prove that row-level security actually blocks
cross-tenant access — only a real PostgreSQL, with the real policies applied, can. The
container is started once for the whole test session: bootstrapped with the three
database roles (``scripts/bootstrap-db.sql``) and migrated to head, exactly like local
dev and CI would do it.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.community.postgres import PostgresContainer

from kritvo.core.db import create_engine, create_sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_SQL = (REPO_ROOT / "scripts" / "bootstrap-db.sql").read_text()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


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


async def seed_tenant(system_sessionmaker: async_sessionmaker[AsyncSession], *, name: str) -> UUID:
    """Insert a tenant row and return its id. Runs as kritvo_system (bypasses RLS)."""
    tenant_id = uuid4()
    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
            {"id": tenant_id, "name": name, "slug": name.lower().replace(" ", "-")},
        )
    return tenant_id


@pytest.fixture
async def two_tenants(
    system_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[tuple[UUID, UUID]]:
    """Two freshly created tenants, isolated per test by unique ids."""
    tenant_a = await seed_tenant(system_sessionmaker, name=f"Tenant A {uuid4()}")
    tenant_b = await seed_tenant(system_sessionmaker, name=f"Tenant B {uuid4()}")
    yield tenant_a, tenant_b


@dataclass(frozen=True)
class TenantFixture:
    """One row seeded in every table TASK-002 owns, all belonging to one tenant."""

    tenant_id: UUID
    role_id: UUID
    user_id: UUID
    membership_id: UUID
    customer_id: UUID
    site_id: UUID


async def seed_full_tenant(
    system_sessionmaker: async_sessionmaker[AsyncSession], *, name: str
) -> TenantFixture:
    """Seed one row per table (tenants, roles, users, memberships, customers, sites)
    for a single tenant, respecting foreign keys. Runs as kritvo_system."""
    tenant_id = await seed_tenant(system_sessionmaker, name=name)
    role_id, user_id, membership_id, customer_id, site_id = (uuid4() for _ in range(5))
    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            text(
                "INSERT INTO roles (id, tenant_id, name, permissions) "
                "VALUES (:id, :tenant_id, 'Technician', ARRAY['job.read'])"
            ),
            {"id": role_id, "tenant_id": tenant_id},
        )
        await session.execute(
            text(
                "INSERT INTO users (id, full_name, phone_enc, phone_hash) "
                "VALUES (:id, :name, :phone, :phone)"
            ),
            {"id": user_id, "name": name, "phone": str(user_id).encode()},
        )
        await session.execute(
            text(
                "INSERT INTO memberships (id, tenant_id, user_id, role_id, kind) "
                "VALUES (:id, :tenant_id, :user_id, :role_id, 'office')"
            ),
            {
                "id": membership_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role_id": role_id,
            },
        )
        await session.execute(
            text("INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tenant_id, :name)"),
            {"id": customer_id, "tenant_id": tenant_id, "name": name},
        )
        await session.execute(
            text(
                "INSERT INTO sites (id, tenant_id, customer_id, name, lat, lng) "
                "VALUES (:id, :tenant_id, :customer_id, :name, 28.6, 77.2)"
            ),
            {"id": site_id, "tenant_id": tenant_id, "customer_id": customer_id, "name": name},
        )
    return TenantFixture(tenant_id, role_id, user_id, membership_id, customer_id, site_id)


@pytest.fixture
async def two_full_tenants(
    system_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[tuple[TenantFixture, TenantFixture]]:
    """Two tenants, each with one row in every TASK-002 table, isolated per test."""
    fixture_a = await seed_full_tenant(system_sessionmaker, name=f"Tenant A {uuid4()}")
    fixture_b = await seed_full_tenant(system_sessionmaker, name=f"Tenant B {uuid4()}")
    yield fixture_a, fixture_b
