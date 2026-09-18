"""LLD section 14.2's specific acceptance criterion for TASK-002: "The tenant setting
is applied on every transaction start, including after a commit in the same session."

set_config's transaction-local scope (ADR-0001) means the setting does not
automatically carry over when a session starts a second transaction — the after_begin
hook in kritvo/core/db.py must fire again, every time, not just once per session.
"""

from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


async def test_tenant_context_is_reapplied_after_commit_in_the_same_session(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_tenants: tuple[UUID, UUID],
) -> None:
    tenant_a, _tenant_b = two_tenants
    async with app_sessionmaker(info={"tenant_id": tenant_a}) as session:
        async with session.begin():
            seen_first = await session.execute(
                text("SELECT current_setting('app.tenant_id', true)")
            )
            assert seen_first.scalar_one() == str(tenant_a)

        # The first transaction committed here. A second transaction on the same
        # session object must still see the tenant context applied.
        async with session.begin():
            seen_second = await session.execute(
                text("SELECT current_setting('app.tenant_id', true)")
            )
            assert seen_second.scalar_one() == str(tenant_a)
