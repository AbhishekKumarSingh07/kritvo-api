"""Shared FastAPI app construction for the API and gateway processes."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kritvo import __version__
from kritvo.core.db import create_engine, create_sessionmaker
from kritvo.core.errors import install_error_handlers
from kritvo.core.health import router as health_router
from kritvo.core.logging import configure_logging
from kritvo.core.request_context import RequestIdMiddleware
from kritvo.core.settings import Settings, get_settings


def _lifespan(settings: Settings) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        # database_url is optional so the app can still start (e.g. in tests that never
        # touch the database) without a live PostgreSQL instance configured.
        if settings.database_url is not None:
            engine = create_engine(settings.database_url)
            app.state.db_sessionmaker = create_sessionmaker(engine)
            try:
                yield
            finally:
                await engine.dispose()
        else:
            yield

    return lifespan


def build_app(title: str, *, enable_cors: bool, settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title=title,
        version=__version__,
        lifespan=_lifespan(settings),
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.add_middleware(RequestIdMiddleware)
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "If-Match"],
            expose_headers=["ETag", "X-Request-ID"],
        )
    install_error_handlers(app)
    app.include_router(health_router)
    return app
