"""Behaviour check (LLD section 2.4): tenant A can never read or write tenant B's rows,
in any of the six tables TASK-002 owns."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.isolation.conftest import TenantFixture

pytestmark = pytest.mark.anyio

# (table, id column read back, cross-tenant insert statement)
_TABLES = ["roles", "customers", "sites", "memberships"]


@pytest.mark.parametrize("table", _TABLES)
async def test_tenant_sees_only_its_own_rows(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
    table: str,
) -> None:
    fixture_a, _fixture_b = two_full_tenants
    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        result = await session.execute(text(f"SELECT tenant_id FROM {table}"))  # noqa: S608
        rows = result.fetchall()
    assert [row[0] for row in rows] == [fixture_a.tenant_id]


@pytest.mark.parametrize("table", _TABLES)
async def test_cross_tenant_insert_is_rejected(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
    table: str,
) -> None:
    """Even naming tenant B's id explicitly in an INSERT must fail while the session is
    scoped to tenant A — this is the WITH CHECK half of the policy, not just USING."""
    fixture_a, fixture_b = two_full_tenants
    statement_by_table = {
        "roles": text(
            "INSERT INTO roles (id, tenant_id, name, permissions) "
            "VALUES (gen_random_uuid(), :tenant_id, 'x', ARRAY[]::text[])"
        ),
        "customers": text(
            "INSERT INTO customers (id, tenant_id, name) "
            "VALUES (gen_random_uuid(), :tenant_id, 'x')"
        ),
        "sites": text(
            "INSERT INTO sites (id, tenant_id, customer_id, name, lat, lng) "
            "VALUES (gen_random_uuid(), :tenant_id, :customer_id, 'x', 0, 0)"
        ),
        "memberships": text(
            "INSERT INTO memberships (id, tenant_id, user_id, role_id, kind) "
            "VALUES (gen_random_uuid(), :tenant_id, :user_id, :role_id, 'office')"
        ),
    }
    params_by_table = {
        "roles": {"tenant_id": fixture_b.tenant_id},
        "customers": {"tenant_id": fixture_b.tenant_id},
        "sites": {"tenant_id": fixture_b.tenant_id, "customer_id": fixture_b.customer_id},
        "memberships": {
            "tenant_id": fixture_b.tenant_id,
            "user_id": fixture_b.user_id,
            "role_id": fixture_b.role_id,
        },
    }
    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        with pytest.raises(DBAPIError):
            async with session.begin():
                await session.execute(statement_by_table[table], params_by_table[table])


async def test_tenant_sees_only_its_own_tenant_row(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
) -> None:
    """tenants uses its own "own_tenant" policy (keyed by id, not tenant_id) — checked
    separately from the generic tenant_isolation pattern the other tables share."""
    fixture_a, _fixture_b = two_full_tenants
    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        result = await session.execute(text("SELECT id FROM tenants"))
        rows = result.fetchall()
    assert [row[0] for row in rows] == [fixture_a.tenant_id]


async def test_tenant_sees_only_its_own_members(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
) -> None:
    """users has no tenant_id at all — visibility comes from the users_via_membership
    policy, checked separately from the tenant_id-keyed tables."""
    fixture_a, _fixture_b = two_full_tenants
    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        result = await session.execute(text("SELECT id FROM users"))
        rows = result.fetchall()
    assert [row[0] for row in rows] == [fixture_a.user_id]
