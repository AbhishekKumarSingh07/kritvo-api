"""The authenticated caller of a request (LLD 12.2-12.3).

Built by ``core.deps.get_principal`` from a decoded access token plus a permissions
lookup. Every module that needs "who is making this request" depends on this type,
never on identity's token or session internals directly.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    tenant_id: UUID
    membership_id: UUID
    kind: str  # office | field | portal (LLD 3.2 memberships.kind)
    portal_customer_id: UUID | None
    device_id: UUID | None
    perms_ver: int
    permissions: frozenset[str]

    def has_permission(self, code: str) -> bool:
        return code in self.permissions


@dataclass(frozen=True)
class CachedMembership:
    permissions: frozenset[str]
    portal_customer_id: UUID | None


class PermissionsCache:
    """In-process cache keyed ``(membership_id, perms_ver)`` (LLD 12.3).

    ``perms_ver`` is part of the key, so a role-permission change (which bumps it, via
    the ``roles_bump_perms_ver`` trigger) is a cache miss, not stale data — no explicit
    invalidation needed. A single process-local dict, not Redis: ADR-0009's reasoning
    (no second stateful system before ADR-0003) applies here too, and correctness does
    not depend on sharing the cache across processes — a miss just costs one query.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[UUID, int], CachedMembership] = {}

    def get(self, membership_id: UUID, perms_ver: int) -> CachedMembership | None:
        return self._cache.get((membership_id, perms_ver))

    def set(self, membership_id: UUID, perms_ver: int, entry: CachedMembership) -> None:
        self._cache[(membership_id, perms_ver)] = entry
