"""Core API for the web app, PWA and client portal.

Run locally: uv run uvicorn kritvo.main_api:app --reload
"""

from fastapi import APIRouter, FastAPI

from kritvo.core.app_factory import build_app
from kritvo.core.principal import PermissionsCache
from kritvo.core.settings import Settings
from kritvo.core.tokens import KeyRing
from kritvo.modules.identity.api import router as identity_router
from kritvo.modules.notifications.registry import build_sender

API_PREFIX = "/api/v1"


def _build_key_ring(settings: Settings) -> KeyRing:
    directory = settings.jwt_signing_keys_dir
    if directory.is_dir() and any(directory.glob("*.pem")):
        return KeyRing.from_directory(directory, settings.jwt_active_kid)
    if settings.app_env not in {"local", "test"}:
        raise RuntimeError(
            f"No JWT signing key found in {directory} and APP_ENV={settings.app_env!r} "
            "is not local/test; generate one (see .env.example) before starting."
        )
    return KeyRing.generate_ephemeral(settings.jwt_active_kid)


def _on_startup(app: FastAPI, settings: Settings) -> None:
    # ADR-0008 condition (a): runs at startup, before the app accepts requests, and
    # raises (refusing to start) if this environment has no real sender registered.
    app.state.notification_sender = build_sender(settings)
    app.state.key_ring = _build_key_ring(settings)
    app.state.permissions_cache = PermissionsCache()


def create_app(settings: Settings | None = None) -> FastAPI:
    app = build_app("Kritvo API", enable_cors=True, settings=settings, on_startup=_on_startup)
    v1 = APIRouter(prefix=API_PREFIX)
    v1.include_router(identity_router)
    # Further feature routers are included here, e.g.:
    # from kritvo.modules.jobs.api import router as jobs_router
    # v1.include_router(jobs_router)
    app.include_router(v1)
    return app


app = create_app()
