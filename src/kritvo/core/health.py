"""Liveness and readiness endpoints (no auth, no data)."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from kritvo import __version__

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: Literal["ok"]
    version: str


@router.get("/healthz", response_model=Health)
async def healthz() -> Health:
    return Health(status="ok", version=__version__)


@router.get("/readyz", response_model=Health)
async def readyz() -> Health:
    # TASK-002 adds a database check here.
    return Health(status="ok", version=__version__)
