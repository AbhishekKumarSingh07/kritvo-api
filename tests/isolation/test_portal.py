"""Portal check (LLD section 2.4): a client-portal session for customer X sees only X's
own rows, even among other customers of the same tenant."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


async def test_portal_session_sees_only_its_own_customer_and_sites(
    system_sessionmaker: async_sessionmaker[AsyncSession],
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_tenants: tuple[UUID, UUID],
) -> None:
    tenant_a, _tenant_b = two_tenants
    customer_x, customer_y = uuid4(), uuid4()
    site_x, site_y = uuid4(), uuid4()

    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            text("INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tenant_id, :name)"),
            [
                {"id": customer_x, "tenant_id": tenant_a, "name": "Customer X"},
                {"id": customer_y, "tenant_id": tenant_a, "name": "Customer Y"},
            ],
        )
        await session.execute(
            text(
                "INSERT INTO sites (id, tenant_id, customer_id, name, lat, lng) "
                "VALUES (:id, :tenant_id, :customer_id, :name, 28.6, 77.2)"
            ),
            [
                {"id": site_x, "tenant_id": tenant_a, "customer_id": customer_x, "name": "Site X"},
                {"id": site_y, "tenant_id": tenant_a, "customer_id": customer_y, "name": "Site Y"},
            ],
        )

    async with app_sessionmaker(info={"tenant_id": tenant_a, "customer_id": customer_x}) as session:
        customers = (await session.execute(text("SELECT id FROM customers"))).scalars().all()
        sites = (await session.execute(text("SELECT id FROM sites"))).scalars().all()

    assert customers == [customer_x]
    assert sites == [site_x]


async def test_office_session_sees_both_customers(
    system_sessionmaker: async_sessionmaker[AsyncSession],
    app_sessionmaker: async_sessionmaker[AsyncSession],
    two_tenants: tuple[UUID, UUID],
) -> None:
    """No customer_id in the session (an office user, not a portal user) means the
    restrictive portal_scope policy is a no-op — only the tenant boundary applies."""
    tenant_a, _tenant_b = two_tenants
    customer_x, customer_y = uuid4(), uuid4()

    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            text("INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tenant_id, :name)"),
            [
                {"id": customer_x, "tenant_id": tenant_a, "name": "Customer X"},
                {"id": customer_y, "tenant_id": tenant_a, "name": "Customer Y"},
            ],
        )

    async with app_sessionmaker(info={"tenant_id": tenant_a}) as session:
        customers = (await session.execute(text("SELECT id FROM customers"))).scalars().all()

    assert set(customers) == {customer_x, customer_y}
