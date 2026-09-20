"""Fixtures for identity integration tests: a real app wired to the same throwaway
PostgreSQL as the isolation suite (root ``tests/conftest.py``), plus helpers to seed a
login-ready tenant/user without going through a signup endpoint (out of TASK-003's
scope — see ADR-0008's context)."""

import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.settings import Settings
from kritvo.main_api import create_app
from kritvo.modules.identity import security

_TEST_PHONE_HMAC_KEY = "test-phone-hmac-key"
_TEST_OTP_HMAC_KEY = "test-otp-hmac-key"


@pytest.fixture
def identity_settings(postgres_urls: dict[str, str]) -> Settings:
    return Settings(
        app_env="test",
        database_url=postgres_urls["app"],
        phone_hmac_key=_TEST_PHONE_HMAC_KEY,
        otp_hmac_key=_TEST_OTP_HMAC_KEY,
        totp_enc_key=Fernet.generate_key().decode(),
        jwt_active_kid="test",
    )


@pytest.fixture
async def identity_app(identity_settings: Settings) -> AsyncIterator[FastAPI]:
    app = create_app(identity_settings)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def identity_client(identity_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=identity_app)
    # https, not http: the refresh cookie is Secure (LLD 12.2), and httpx's cookie jar
    # — correctly — never resends a Secure cookie to a plain-http URL, so a refresh
    # flow chained across two requests on the same client needs this to work at all.
    async with AsyncClient(transport=transport, base_url="https://test") as c:
        yield c


class RecordingHandler(logging.Handler):
    """A plain handler, independent of pytest's own caplog machinery.

    ``configure_logging`` (run during the app's startup — already done by the time
    ``identity_client`` is ready) replaces the root logger's handlers for clean JSON
    output in production. That also strips out pytest's own caplog handler, and
    caplog's per-phase handler swapping (setup vs. call) means simply re-adding
    ``caplog.handler`` back afterwards is unreliable — the object it points to can
    change between when a fixture attaches it and when the test body reads it. A
    small handler owned entirely by this fixture sidesteps both problems.
    """

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())

    @property
    def text(self) -> str:
        return "\n".join(self.messages)


@pytest.fixture
def dev_sender_logs(identity_client: AsyncClient) -> Iterator[RecordingHandler]:
    """Read what the ADR-0008 logging sender "sent", the way a developer reading real
    logs would — ``.text`` holds every message logged by the dev sender in this test."""
    logger = logging.getLogger("kritvo.notifications.dev_sender")
    handler = RecordingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)


@dataclass(frozen=True)
class SeededUser:
    tenant_id: UUID
    user_id: UUID
    membership_id: UUID
    role_id: UUID
    phone: str


async def seed_login_user(
    system_sessionmaker: async_sessionmaker[AsyncSession],
    *,
    identity_settings: Settings,
    phone: str,
    permissions: list[str] | None = None,
    password: str | None = None,
    totp_secret: str | None = None,
) -> SeededUser:
    tenant_id, role_id, user_id, membership_id = uuid4(), uuid4(), uuid4(), uuid4()
    phone_hash = security.hash_phone(phone, identity_settings.phone_hmac_key)
    password_hash = security.hash_password(password) if password else None
    totp_secret_enc = (
        security.encrypt_totp_secret(totp_secret, identity_settings.totp_enc_key)
        if totp_secret
        else None
    )
    async with system_sessionmaker() as session, session.begin():
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
            {"id": tenant_id, "name": f"Tenant {tenant_id}", "slug": f"tenant-{tenant_id}"},
        )
        await session.execute(
            text(
                "INSERT INTO roles (id, tenant_id, name, permissions) "
                "VALUES (:id, :tid, 'Owner', :perms)"
            ),
            {"id": role_id, "tid": tenant_id, "perms": permissions or []},
        )
        await session.execute(
            text(
                "INSERT INTO users "
                "  (id, full_name, phone_enc, phone_hash, password_hash, totp_secret_enc) "
                "VALUES (:id, :name, :phone_enc, :phone_hash, :password_hash, :totp_secret_enc)"
            ),
            {
                "id": user_id,
                "name": "Test User",
                "phone_enc": phone.encode(),
                "phone_hash": phone_hash,
                "password_hash": password_hash,
                "totp_secret_enc": totp_secret_enc,
            },
        )
        await session.execute(
            text(
                "INSERT INTO memberships (id, tenant_id, user_id, role_id, kind) "
                "VALUES (:id, :tid, :uid, :rid, 'office')"
            ),
            {"id": membership_id, "tid": tenant_id, "uid": user_id, "rid": role_id},
        )
    return SeededUser(tenant_id, user_id, membership_id, role_id, phone)


@pytest.fixture
async def seeded_field_user(
    system_sessionmaker: async_sessionmaker[AsyncSession], identity_settings: Settings
) -> SeededUser:
    """An OTP-login user (no password/TOTP), with one permission to check tokens carry it."""
    return await seed_login_user(
        system_sessionmaker,
        identity_settings=identity_settings,
        phone=f"+9198765{uuid4().int % 100000:05d}",
        permissions=["job.view_assigned"],
    )
