"""Seed helpers for the TASK-002 tenancy tables, on top of the container fixtures in
the root ``tests/conftest.py`` (``postgres_urls``, ``app_sessionmaker``,
``system_sessionmaker``)."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


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
