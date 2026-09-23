"""Async database engine and tenant-scoped sessions (LLD section 2.3, ADR-0001).

Every request that touches tenant data must open its session through
``open_tenant_session``. That stamps the tenant (and, for portal sessions, the
customer) onto the connection at the start of every transaction, so PostgreSQL's
row-level security policies (migrations, section 2.2) can enforce isolation even if
application code forgets a filter.

``open_tenant_session`` also stamps ``app.actor_id`` when a caller is a real
authenticated user (``core/deps.py``'s ``get_db``). Unlike the tenant, the actor is
optional: scheduled work (the obligation sweeper, AMC generation, retention purge)
runs with no human behind it, so an absent actor sets ``app.actor_id`` to the empty
string rather than raising, mirroring ``customer_id``. Nothing reads it yet — the
audit trigger (TASK-005) is what will add ``app_actor_id()`` and consume it.
"""

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, SessionTransaction


class TenantContextMissingError(RuntimeError):
    """Raised when a tenant-scoped session begins a transaction without a tenant_id."""


def create_engine(database_url: str) -> AsyncEngine:
    """Create an async engine for any of the three roles (LLD section 2.1).

    ``statement_cache_size=0`` disables asyncpg's prepared-statement cache. Behind
    PgBouncer in transaction-pooling mode a physical connection is reused across
    unrelated callers between transactions; a cached prepared statement (or a
    session-level setting instead of a transaction-local one) could otherwise carry
    one caller's state onto the next caller's transaction on the same connection,
    silently rather than with an error. This is an explicit decision point in
    ADR-0001, not incidental tuning.
    """
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(Session, "after_begin")
def _apply_tenant_context(
    session: Session, transaction: SessionTransaction, connection: Connection
) -> None:
    # Sessions that were never opened through open_tenant_session (e.g. a future
    # kritvo_system session for platform code) carry no "tenant_id" key at all and are
    # left alone here — RLS for those connections is governed by the database role,
    # not by this hook. A session that WAS opened through open_tenant_session but
    # somehow ended up with tenant_id=None is the bug this hook exists to catch.
    if "tenant_id" not in session.info:
        return
    tenant_id: UUID | None = session.info.get("tenant_id")
    if tenant_id is None:
        raise TenantContextMissingError("Session opened without tenant_id")
    # set_config's third argument (true) makes the setting transaction-local, the
    # equivalent of SET LOCAL: it is cleared automatically at the end of every
    # transaction rather than lingering on a connection that PgBouncer hands to the
    # next caller (ADR-0001).
    connection.execute(
        text("select set_config('app.tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )
    customer_id: UUID | None = session.info.get("customer_id")
    connection.execute(
        text("select set_config('app.customer_id', :cid, true)"),
        {"cid": str(customer_id) if customer_id else ""},
    )
    actor_id: UUID | None = session.info.get("actor_id")
    connection.execute(
        text("select set_config('app.actor_id', :aid, true)"),
        {"aid": str(actor_id) if actor_id else ""},
    )


async def open_tenant_session(
    sessionmaker: async_sessionmaker[AsyncSession],
    tenant_id: UUID,
    customer_id: UUID | None = None,
    actor_id: UUID | None = None,
) -> AsyncIterator[AsyncSession]:
    """Open a session stamped with the given tenant (and optional portal customer
    and actor).

    A bare ``async with sessionmaker(info=...) as session`` works too (the tests use
    it to seed fixtures) — this wrapper exists so FastAPI's ``Depends`` has a single,
    consistent entry point (``core/deps.py``).
    """
    async with sessionmaker(
        info={"tenant_id": tenant_id, "customer_id": customer_id, "actor_id": actor_id}
    ) as session:
        yield session
