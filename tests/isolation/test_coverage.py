"""Coverage check (LLD section 2.4): no tenant table may be missing RLS.

This is the safety net for every future migration: if someone adds a new table with a
``tenant_id`` column and forgets ``enable_tenant_rls()``, this test fails the build
before the gap ever ships.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio

_COVERAGE_QUERY = """
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
WHERE n.nspname = 'public'
  AND c.relkind IN ('r', 'p')
  AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity)
"""


async def test_every_tenant_table_has_forced_rls(
    system_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with system_sessionmaker() as session:
        result = await session.execute(text(_COVERAGE_QUERY))
        offenders = [row[0] for row in result.fetchall()]
    assert offenders == [], f"tables missing forced RLS: {offenders}"
