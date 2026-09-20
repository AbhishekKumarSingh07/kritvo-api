"""Identity business logic: OTP, password+TOTP login, tokens (LLD 12.1-12.2).

Every function opens and closes its own session(s) and owns its own transactions —
these run before a `Principal`/tenant-scoped session can exist (OTP request/verify,
login, refresh all start with only an opaque credential), sometimes discovering the
tenant only partway through, which is why they take a sessionmaker rather than an
already-opened session. A bare ``sessionmaker(info={"tenant_id": ...})`` is used for
the tenant-scoped phase (documented as fine by ``core.db.open_tenant_session``'s own
docstring) rather than that generator helper, since these functions need to ``return``
from inside the transaction rather than ``yield`` through it.
"""

import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.errors import AppError
from kritvo.core.principal import Principal
from kritvo.core.settings import Settings
from kritvo.core.tokens import KeyRing
from kritvo.modules.identity import rate_limit, security
from kritvo.modules.notifications.interface import NotificationKind, NotificationSender
from kritvo.shared.ids import uuid7

OTP_TTL = timedelta(minutes=5)
OTP_MAX_ATTEMPTS = 5
REFRESH_TOKEN_TTL = timedelta(days=30)
REFRESH_IDLE_TTL = timedelta(days=7)
PENDING_TOTP_TTL = timedelta(minutes=5)


async def request_otp(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    phone: str,
    device_id: str,
    settings: Settings,
    sender: NotificationSender,
) -> None:
    phone_hash = security.hash_phone(phone, settings.phone_hmac_key)
    async with sessionmaker() as session, session.begin():
        await rate_limit.check_and_increment(
            session,
            scope="otp_phone",
            scope_key=phone_hash.hex(),
            window=timedelta(minutes=15),
            limit=3,
        )
        await rate_limit.check_and_increment(
            session,
            scope="otp_device",
            scope_key=device_id,
            window=timedelta(hours=1),
            limit=10,
        )
        user_id = (
            await session.execute(text("SELECT user_id_by_phone_hash(:h)"), {"h": phone_hash})
        ).scalar_one()
        if user_id is None:
            return  # no account-enumeration: behave identically for an unknown phone
        code = security.generate_otp_code()
        code_hash = security.hash_otp_code(code, settings.otp_hmac_key)
        await session.execute(
            text("SELECT otp_create(:id, :uid, :ch, 'login', :dev, :exp)"),
            {
                "id": uuid7(),
                "uid": user_id,
                "ch": code_hash,
                "dev": device_id,
                "exp": datetime.now(UTC) + OTP_TTL,
            },
        )
        # Sent inside the transaction: if sending somehow raises, the rollback also
        # removes the OTP it would have announced, rather than leaving one no one
        # was told about.
        await sender.send(
            user_id=user_id,
            kind=NotificationKind.OTP,
            message=f"Your Kritvo login code is {code}. It expires in 5 minutes.",
        )


async def _issue_tokens(
    session: AsyncSession,
    *,
    user_id: UUID,
    tenant_id: UUID,
    membership_id: UUID,
    kind: str,
    device_row_id: UUID | None,
    key_ring: KeyRing,
    family_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> tuple[str, str]:
    perms_ver = (
        await session.execute(
            text(
                "SELECT r.perms_ver FROM roles r "
                "JOIN memberships m ON m.role_id = r.id WHERE m.id = :mid"
            ),
            {"mid": membership_id},
        )
    ).scalar_one()
    access_token = key_ring.encode(
        {
            "sub": str(user_id),
            "tid": str(tenant_id),
            "mid": str(membership_id),
            "perms_ver": perms_ver,
            "kind": kind,
            "dev": str(device_row_id) if device_row_id else None,
            "jti": str(uuid7()),
        }
    )
    refresh_token = security.generate_refresh_token()
    refresh_hash = security.hash_refresh_token(refresh_token)
    await session.execute(
        text(
            "INSERT INTO refresh_tokens "
            "  (id, tenant_id, user_id, membership_id, device_id, token_hash,"
            "   family_id, expires_at) "
            "VALUES (:id, :tid, :uid, :mid, :dev, :th, :fid, :exp)"
        ),
        {
            "id": uuid7(),
            "tid": tenant_id,
            "uid": user_id,
            "mid": membership_id,
            "dev": device_row_id,
            "th": refresh_hash,
            "fid": family_id or uuid7(),
            "exp": expires_at or (datetime.now(UTC) + REFRESH_TOKEN_TTL),
        },
    )
    return access_token, refresh_token


async def _upsert_device(
    session: AsyncSession, *, tenant_id: UUID, user_id: UUID, fingerprint: str, platform: str
) -> tuple[UUID, bool]:
    """Returns (device row id, whether this fingerprint is new for this user)."""
    existing = (
        await session.execute(
            text(
                "SELECT id FROM devices "
                "WHERE tenant_id = :tid AND user_id = :uid AND fingerprint = :fp"
            ),
            {"tid": tenant_id, "uid": user_id, "fp": fingerprint},
        )
    ).first()
    device_row_id = existing[0] if existing else uuid7()
    await session.execute(
        text(
            "INSERT INTO devices (id, tenant_id, user_id, fingerprint, platform) "
            "VALUES (:id, :tid, :uid, :fp, :platform) "
            "ON CONFLICT (tenant_id, user_id, fingerprint) DO UPDATE SET last_seen_at = now()"
        ),
        {
            "id": device_row_id,
            "tid": tenant_id,
            "uid": user_id,
            "fp": fingerprint,
            "platform": platform,
        },
    )
    return device_row_id, existing is None


async def verify_otp(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    phone: str,
    code: str,
    device_id: str,
    platform: str,
    settings: Settings,
    key_ring: KeyRing,
) -> tuple[str, str]:
    phone_hash = security.hash_phone(phone, settings.phone_hmac_key)
    async with sessionmaker() as session, session.begin():
        await rate_limit.check_and_increment(
            session,
            scope="otp_verify_device",
            scope_key=device_id,
            window=timedelta(minutes=15),
            limit=5,
        )
        user_id = (
            await session.execute(text("SELECT user_id_by_phone_hash(:h)"), {"h": phone_hash})
        ).scalar_one()
        if user_id is None:
            raise AppError("INVALID_OTP", status=401, detail="Invalid code")
        row = (
            (
                await session.execute(
                    text("SELECT * FROM otp_get_active(:uid, 'login')"), {"uid": user_id}
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise AppError("INVALID_OTP", status=401, detail="Invalid or expired code")
        if row["attempts"] >= OTP_MAX_ATTEMPTS:
            raise AppError("INVALID_OTP", status=401, detail="Too many attempts")
        expected_hash = security.hash_otp_code(code, settings.otp_hmac_key)
        if not hmac.compare_digest(expected_hash, bytes(row["code_hash"])):
            await session.execute(text("SELECT otp_register_attempt(:id)"), {"id": row["id"]})
            raise AppError("INVALID_OTP", status=401, detail="Invalid code")
        await session.execute(text("SELECT otp_consume(:id)"), {"id": row["id"]})
        memberships = (
            (
                await session.execute(
                    text("SELECT * FROM memberships_for_user(:uid)"), {"uid": user_id}
                )
            )
            .mappings()
            .all()
        )
        if not memberships:
            raise AppError("NO_MEMBERSHIP", status=403, detail="No active tenant membership")
        membership = memberships[0]

    tenant_id = membership["tenant_id"]
    async with sessionmaker(info={"tenant_id": tenant_id}) as session, session.begin():
        device_row_id, _ = await _upsert_device(
            session, tenant_id=tenant_id, user_id=user_id, fingerprint=device_id, platform=platform
        )
        return await _issue_tokens(
            session,
            user_id=user_id,
            tenant_id=tenant_id,
            membership_id=membership["id"],
            kind=membership["kind"],
            device_row_id=device_row_id,
            key_ring=key_ring,
        )


async def login(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    identifier: str,
    password: str,
    settings: Settings,
    key_ring: KeyRing,
) -> str:
    """Returns a short-lived pending-TOTP token; the caller still has to pass TOTP."""
    is_email = "@" in identifier
    phone_hash = None if is_email else security.hash_phone(identifier, settings.phone_hmac_key)
    async with sessionmaker() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("SELECT * FROM user_auth_lookup(:ph, :em)"),
                    {"ph": phone_hash, "em": identifier if is_email else None},
                )
            )
            .mappings()
            .first()
        )
        if row is None or row["password_hash"] is None:
            raise AppError("INVALID_CREDENTIALS", status=401, detail="Invalid credentials")
        user_id = row["id"]
        password_hash = row["password_hash"]
        has_totp = row["totp_secret_enc"] is not None

    if not security.verify_password(password, password_hash):
        async with sessionmaker() as session, session.begin():
            await rate_limit.check_and_increment(
                session,
                scope="login_failure",
                scope_key=str(user_id),
                window=timedelta(minutes=15),
                limit=5,
            )
        raise AppError("INVALID_CREDENTIALS", status=401, detail="Invalid credentials")
    if not has_totp:
        raise AppError(
            "TOTP_NOT_CONFIGURED", status=403, detail="TOTP is not set up for this account"
        )

    return key_ring.encode({"sub": str(user_id), "typ": "totp_pending"}, ttl=PENDING_TOTP_TTL)


async def verify_totp(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    pending_token: str,
    code: str,
    device_id: str,
    platform: str,
    settings: Settings,
    key_ring: KeyRing,
    sender: NotificationSender,
) -> tuple[str, str]:
    try:
        claims = key_ring.decode(pending_token)
    except jwt.InvalidTokenError as exc:
        raise AppError(
            "INVALID_PENDING_TOKEN", status=401, detail="Invalid or expired login"
        ) from exc
    if claims.get("typ") != "totp_pending":
        raise AppError("INVALID_PENDING_TOKEN", status=401, detail="Invalid or expired login")
    user_id = UUID(claims["sub"])

    async with sessionmaker() as session, session.begin():
        await rate_limit.check_and_increment(
            session,
            scope="totp_attempt",
            scope_key=str(user_id),
            window=timedelta(minutes=15),
            limit=5,
        )
        encrypted = (
            await session.execute(text("SELECT user_totp_secret(:uid)"), {"uid": user_id})
        ).scalar_one()
        if encrypted is None:
            raise AppError("TOTP_NOT_CONFIGURED", status=403, detail="TOTP is not set up")
        secret = security.decrypt_totp_secret(bytes(encrypted), settings.totp_enc_key)
        if not security.verify_totp_code(secret, code):
            raise AppError("INVALID_TOTP", status=401, detail="Invalid code")
        memberships = (
            (
                await session.execute(
                    text("SELECT * FROM memberships_for_user(:uid)"), {"uid": user_id}
                )
            )
            .mappings()
            .all()
        )
        if not memberships:
            raise AppError("NO_MEMBERSHIP", status=403, detail="No active tenant membership")
        membership = memberships[0]

    tenant_id = membership["tenant_id"]
    async with sessionmaker(info={"tenant_id": tenant_id}) as session, session.begin():
        device_row_id, is_new_device = await _upsert_device(
            session, tenant_id=tenant_id, user_id=user_id, fingerprint=device_id, platform=platform
        )
        access_token, refresh_token = await _issue_tokens(
            session,
            user_id=user_id,
            tenant_id=tenant_id,
            membership_id=membership["id"],
            kind=membership["kind"],
            device_row_id=device_row_id,
            key_ring=key_ring,
        )

    if is_new_device:
        await sender.send(
            user_id=user_id,
            kind=NotificationKind.LOGIN_ALERT,
            message=f"New sign-in to your Kritvo account on a new device ({platform}).",
        )
    return access_token, refresh_token


async def refresh(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    refresh_token: str,
    key_ring: KeyRing,
) -> tuple[str, str]:
    token_hash = security.hash_refresh_token(refresh_token)
    async with sessionmaker() as session:
        row = (
            (
                await session.execute(
                    text("SELECT * FROM refresh_token_lookup(:h)"), {"h": token_hash}
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        raise AppError("INVALID_REFRESH_TOKEN", status=401, detail="Unknown refresh token")

    tenant_id = row["tenant_id"]
    now = datetime.now(UTC)

    if row["revoked_at"] is not None:
        # Reuse of an already-rotated token: kill the whole family, not just this token.
        async with sessionmaker(info={"tenant_id": tenant_id}) as session, session.begin():
            await session.execute(
                text(
                    "UPDATE refresh_tokens SET revoked_at = now() "
                    "WHERE family_id = :fid AND revoked_at IS NULL"
                ),
                {"fid": row["family_id"]},
            )
        raise AppError(
            "REFRESH_TOKEN_REUSED", status=401, detail="Refresh token already used; session revoked"
        )

    if row["expires_at"] <= now or (now - row["last_used_at"]) > REFRESH_IDLE_TTL:
        raise AppError("REFRESH_TOKEN_EXPIRED", status=401, detail="Refresh token expired")

    async with sessionmaker(info={"tenant_id": tenant_id}) as session, session.begin():
        await session.execute(
            text("UPDATE refresh_tokens SET revoked_at = now() WHERE id = :id"),
            {"id": row["id"]},
        )
        membership = (
            await session.execute(
                text("SELECT kind, status FROM memberships WHERE id = :mid"),
                {"mid": row["membership_id"]},
            )
        ).first()
        if membership is None or membership[1] != "active":
            raise AppError("NO_MEMBERSHIP", status=403, detail="Membership no longer active")
        return await _issue_tokens(
            session,
            user_id=row["user_id"],
            tenant_id=tenant_id,
            membership_id=row["membership_id"],
            kind=membership[0],
            device_row_id=row["device_id"],
            key_ring=key_ring,
            family_id=row["family_id"],
            expires_at=row["expires_at"],  # preserves the 30-day absolute ceiling
        )


async def logout(sessionmaker: async_sessionmaker[AsyncSession], *, refresh_token: str) -> None:
    token_hash = security.hash_refresh_token(refresh_token)
    async with sessionmaker() as session:
        row = (
            (
                await session.execute(
                    text("SELECT * FROM refresh_token_lookup(:h)"), {"h": token_hash}
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        return  # already gone; logout is idempotent
    async with sessionmaker(info={"tenant_id": row["tenant_id"]}) as session, session.begin():
        await session.execute(
            text(
                "UPDATE refresh_tokens SET revoked_at = now() WHERE id = :id AND revoked_at IS NULL"
            ),
            {"id": row["id"]},
        )


async def switch_tenant(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    principal: Principal,
    target_tenant_id: UUID,
    key_ring: KeyRing,
) -> tuple[str, str]:
    async with sessionmaker() as session, session.begin():
        memberships = (
            (
                await session.execute(
                    text("SELECT * FROM memberships_for_user(:uid)"), {"uid": principal.user_id}
                )
            )
            .mappings()
            .all()
        )
    target = next((m for m in memberships if m["tenant_id"] == target_tenant_id), None)
    if target is None:
        raise AppError("NO_MEMBERSHIP", status=403, detail="Not a member of that tenant")

    async with sessionmaker(info={"tenant_id": target_tenant_id}) as session, session.begin():
        return await _issue_tokens(
            session,
            user_id=principal.user_id,
            tenant_id=target_tenant_id,
            membership_id=target["id"],
            kind=target["kind"],
            device_row_id=principal.device_id,
            key_ring=key_ring,
        )
