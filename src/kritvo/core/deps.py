"""FastAPI dependencies: who is calling, and their tenant-scoped database session.

Closes the handoff left in ``core/db.py`` by TASK-002: ``get_principal`` decodes the
access token and resolves permissions; ``get_db`` opens a session stamped with that
principal's tenant (and portal customer, if any) via ``open_tenant_session``.
"""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header, Request
from fastapi.params import Depends as DependsMarker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.db import open_tenant_session
from kritvo.core.errors import AppError
from kritvo.core.principal import CachedMembership, PermissionsCache, Principal
from kritvo.core.settings import Settings
from kritvo.core.tokens import KeyRing


def get_app_settings(request: Request) -> Settings:
    """The exact Settings this app was built with (``core.app_factory.build_app``),
    never the process-global cached ``kritvo.core.settings.get_settings()`` — a test
    building its own app with overridden keys/database_url must see its own values.
    """
    settings: Settings = request.app.state.settings
    return settings


def get_sessionmaker(request: Request) -> async_sessionmaker[AsyncSession]:
    """For the endpoints that run before a tenant is known at all — OTP request/verify,
    password login, refresh. Those services open their own sessions (some untenanted,
    some tenant-scoped once a tenant is determined mid-flow), so they need the
    sessionmaker itself rather than one session already opened a particular way.
    """
    sessionmaker: async_sessionmaker[AsyncSession] = request.app.state.db_sessionmaker
    return sessionmaker


async def get_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AppError("UNAUTHENTICATED", status=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ")

    key_ring: KeyRing = request.app.state.key_ring
    try:
        claims = key_ring.decode(token)
    except jwt.InvalidTokenError as exc:
        raise AppError("UNAUTHENTICATED", status=401, detail="Invalid or expired token") from exc
    if claims.get("typ", "access") != "access":
        # A TOTP-pending token (identity.service) signed with the same keys but a
        # different "typ" claim, and no mid/perms_ver — must never be accepted here.
        raise AppError("UNAUTHENTICATED", status=401, detail="Not an access token")

    membership_id = UUID(claims["mid"])
    perms_ver = int(claims["perms_ver"])
    tenant_id = UUID(claims["tid"])

    cache: PermissionsCache = request.app.state.permissions_cache
    cached = cache.get(membership_id, perms_ver)
    if cached is None:
        sessionmaker = request.app.state.db_sessionmaker
        async for session in open_tenant_session(sessionmaker, tenant_id):
            result = await session.execute(
                text(
                    "SELECT r.permissions, m.portal_customer_id FROM memberships m "
                    "JOIN roles r ON r.id = m.role_id "
                    "WHERE m.id = :mid AND m.status = 'active'"
                ),
                {"mid": membership_id},
            )
            row = result.first()
        if row is None:
            raise AppError("UNAUTHENTICATED", status=401, detail="Membership is no longer active")
        cached = CachedMembership(permissions=frozenset(row[0]), portal_customer_id=row[1])
        cache.set(membership_id, perms_ver, cached)

    device_id = claims.get("dev")
    return Principal(
        user_id=UUID(claims["sub"]),
        tenant_id=tenant_id,
        membership_id=membership_id,
        kind=claims["kind"],
        portal_customer_id=cached.portal_customer_id,
        device_id=UUID(device_id) if device_id else None,
        perms_ver=perms_ver,
        permissions=cached.permissions,
    )


async def get_db(
    request: Request,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AsyncIterator[AsyncSession]:
    sessionmaker = request.app.state.db_sessionmaker
    async for session in open_tenant_session(
        sessionmaker, principal.tenant_id, principal.portal_customer_id
    ):
        yield session


def require_permission(code: str) -> DependsMarker:
    async def _check(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        if not principal.has_permission(code):
            raise AppError("FORBIDDEN", status=403, detail=f"Missing permission {code!r}")
        return principal

    dependency: DependsMarker = Depends(_check)
    return dependency
