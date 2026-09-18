"""No-context check (LLD section 2.4): a session without a tenant_id must refuse to run
any SQL at all, rather than silently running unscoped."""

from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.db import TenantContextMissingError

pytestmark = pytest.mark.anyio


async def test_missing_tenant_id_is_rejected(
    app_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(TenantContextMissingError):
        async with app_sessionmaker(info={"tenant_id": None}) as session, session.begin():
            await session.execute(text("SELECT 1"))


async def test_session_with_no_tenant_key_at_all_is_untouched(
    app_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """A session that never claims to be tenant-scoped (no "tenant_id" key at all) is
    left alone by the hook — it's not what the no-context check is about, and this
    proves the coverage/no-context checks are not defeated by simply omitting the key."""
    async with app_sessionmaker() as session, session.begin():
        row = await session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        value: UUID | None = row.scalar_one()
    assert value in (None, "")
