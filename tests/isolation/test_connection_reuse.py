"""Connection-reuse check (ADR-0001, LLD section 13.2's "run the same query through
PgBouncer in transaction mode" test idea).

Behind PgBouncer in transaction-pooling mode, one physical connection is handed to a
different, unrelated caller as soon as a transaction ends. This simulates that directly
with a single asyncpg connection reused across two transactions, without going through
PgBouncer itself — what matters is whether the *setting* survives a transaction
boundary, which is exactly what PgBouncer's reuse would expose.
"""

import asyncpg
import pytest

pytestmark = pytest.mark.anyio

_TENANT_A = "11111111-1111-1111-1111-111111111111"
_TENANT_B = "22222222-2222-2222-2222-222222222222"


def _app_dsn(postgres_urls: dict[str, str]) -> str:
    # asyncpg.connect() wants a plain DSN; SQLAlchemy's "+asyncpg" dialect marker isn't one.
    return postgres_urls["app"].replace("postgresql+asyncpg://", "postgresql://")


async def test_transaction_local_setting_does_not_leak_to_the_next_caller(
    postgres_urls: dict[str, str],
) -> None:
    conn = await asyncpg.connect(_app_dsn(postgres_urls))
    try:
        # Caller 1's transaction. The third set_config argument (true) is what
        # open_tenant_session uses (kritvo/core/db.py) — transaction-local, SET LOCAL
        # semantics (ADR-0001).
        async with conn.transaction():
            await conn.execute("select set_config('app.tenant_id', $1, true)", _TENANT_A)
            seen = await conn.fetchval("select current_setting('app.tenant_id', true)")
            assert seen == _TENANT_A

        # Caller 2 reuses the same physical connection, as PgBouncer would, and sets
        # nothing — it must never see caller 1's tenant.
        async with conn.transaction():
            leaked = await conn.fetchval("select current_setting('app.tenant_id', true)")
        assert leaked in (None, "")
    finally:
        await conn.close()


async def test_session_level_setting_would_have_leaked(postgres_urls: dict[str, str]) -> None:
    """Negative control: proves the previous test is actually exercising the mechanism
    that matters. A session-level set (the third argument false, instead of true) really
    does survive a transaction boundary on the same connection — which is exactly the
    silent leak ADR-0001 calls out, and exactly why open_tenant_session never does this."""
    conn = await asyncpg.connect(_app_dsn(postgres_urls))
    try:
        async with conn.transaction():
            await conn.execute("select set_config('app.tenant_id', $1, false)", _TENANT_B)

        async with conn.transaction():
            leaked = await conn.fetchval("select current_setting('app.tenant_id', true)")
        assert leaked == _TENANT_B
    finally:
        await conn.close()
