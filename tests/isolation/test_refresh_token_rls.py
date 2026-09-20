"""refresh_tokens row-level security (LLD 3.2, 12.2, TASK-003): the same tenant
isolation guarantee TASK-002's tables have, extended to this new table."""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.isolation.conftest import TenantFixture

pytestmark = pytest.mark.anyio

_INSERT_REFRESH_TOKEN = text(
    "INSERT INTO refresh_tokens "
    "  (id, tenant_id, user_id, membership_id, token_hash, family_id, expires_at) "
    "VALUES (gen_random_uuid(), :tid, :uid, :mid, :th, gen_random_uuid(),"
    "  now() + interval '30 days')"
)


async def _seed_refresh_token(
    system_sessionmaker: async_sessionmaker[AsyncSession], fixture: TenantFixture
) -> None:
    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            _INSERT_REFRESH_TOKEN,
            {
                "tid": fixture.tenant_id,
                "uid": fixture.user_id,
                "mid": fixture.membership_id,
                "th": hashlib.sha256(str(uuid4()).encode()).digest(),
            },
        )


async def test_tenant_sees_only_its_own_refresh_tokens(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    system_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
) -> None:
    fixture_a, fixture_b = two_full_tenants
    await _seed_refresh_token(system_sessionmaker, fixture_a)
    await _seed_refresh_token(system_sessionmaker, fixture_b)

    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        result = await session.execute(text("SELECT tenant_id FROM refresh_tokens"))
        rows = result.fetchall()
    assert [row[0] for row in rows] == [fixture_a.tenant_id]


async def test_cross_tenant_refresh_token_insert_is_rejected(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_full_tenants: tuple[TenantFixture, TenantFixture],
) -> None:
    """Even naming tenant B's id explicitly in an INSERT must fail while the session is
    scoped to tenant A — the WITH CHECK half of the policy, not just USING."""
    fixture_a, fixture_b = two_full_tenants
    async with app_sessionmaker(info={"tenant_id": fixture_a.tenant_id}) as session:
        with pytest.raises(DBAPIError):
            async with session.begin():
                await session.execute(
                    _INSERT_REFRESH_TOKEN,
                    {
                        "tid": fixture_b.tenant_id,
                        "uid": fixture_b.user_id,
                        "mid": fixture_b.membership_id,
                        "th": hashlib.sha256(b"cross-tenant").digest(),
                    },
                )
