"""Postgres-backed auth rate limits (ADR-0009, LLD 12.4).

Fixed windows, not a true sliding window: ``window_start`` is the window length's own
floor of "now", so every caller hitting the same scope/key within a window converges on
one row and a single atomic ``INSERT ... ON CONFLICT DO UPDATE`` serializes concurrent
increments at the database level — correct under concurrency without a separate lock.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kritvo.core.errors import AppError


async def check_and_increment(
    session: AsyncSession,
    *,
    scope: str,
    scope_key: str,
    window: timedelta,
    limit: int,
) -> None:
    """Raise ``AppError`` (429) if this scope/key has exceeded ``limit`` in this window."""
    bucket_seconds = int(window.total_seconds())
    now_epoch = int(datetime.now(UTC).timestamp())
    window_start = datetime.fromtimestamp((now_epoch // bucket_seconds) * bucket_seconds, tz=UTC)
    result = await session.execute(
        text(
            "INSERT INTO auth_rate_limits (scope, scope_key, window_start, count) "
            "VALUES (:scope, :scope_key, :window_start, 1) "
            "ON CONFLICT (scope, scope_key, window_start) "
            "DO UPDATE SET count = auth_rate_limits.count + 1 "
            "RETURNING count"
        ),
        {"scope": scope, "scope_key": scope_key, "window_start": window_start},
    )
    count = result.scalar_one()
    if count > limit:
        raise AppError(
            "RATE_LIMITED",
            status=429,
            detail=f"Too many {scope} attempts. Try again later.",
        )
