"""Core API for the web app, PWA and client portal.

Run locally: uv run uvicorn kritvo.main_api:app --reload
"""

from fastapi import APIRouter, FastAPI

from kritvo.core.app_factory import build_app

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = build_app("Kritvo API", enable_cors=True)
    v1 = APIRouter(prefix=API_PREFIX)
    # Feature routers are included here, e.g.:
    # from kritvo.modules.jobs.api import router as jobs_router
    # v1.include_router(jobs_router)
    app.include_router(v1)
    return app


app = create_app()
