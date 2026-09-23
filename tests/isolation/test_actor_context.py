"""Actor context (core/db.py, TASK-003 follow-up ahead of TASK-005's audit trigger):
the actor is optional, unlike the tenant, since scheduled work (the obligation
sweeper, AMC generation, retention purge) runs with no human behind it. An absent
actor must not raise, and a present one must survive a commit and a new transaction
on the same session, exactly like the tenant setting (test_session_reuse.py)."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


async def test_actor_context_is_reapplied_after_commit_in_the_same_session(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_tenants: tuple[UUID, UUID],
) -> None:
    tenant_a, _tenant_b = two_tenants
    actor = uuid4()
    async with app_sessionmaker(info={"tenant_id": tenant_a, "actor_id": actor}) as session:
        async with session.begin():
            seen_first = await session.execute(text("SELECT current_setting('app.actor_id', true)"))
            assert seen_first.scalar_one() == str(actor)

        # The first transaction committed here. A second transaction on the same
        # session object must still see the actor context applied.
        async with session.begin():
            seen_second = await session.execute(
                text("SELECT current_setting('app.actor_id', true)")
            )
            assert seen_second.scalar_one() == str(actor)


async def test_session_with_no_actor_works_rather_than_raising(
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_tenants: tuple[UUID, UUID],
) -> None:
    """Unlike a missing tenant_id (TenantContextMissingError), a missing actor is
    legitimate — e.g. a worker task with no human caller — and must not block the
    session from running SQL."""
    tenant_a, _tenant_b = two_tenants
    async with app_sessionmaker(info={"tenant_id": tenant_a}) as session, session.begin():
        row = await session.execute(text("SELECT current_setting('app.actor_id', true)"))
        assert row.scalar_one() == ""
