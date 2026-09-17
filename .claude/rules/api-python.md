---
paths:
  - "src/**"
  - "tests/**"
  - "migrations/**"
  - "pyproject.toml"
---

# Backend rules (Python + FastAPI)

The stack is fixed by ADR-0007: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 async, asyncpg,
Alembic, uv. Do not add another web framework (Flask, Django, a raw Starlette app) or another
language/service. Propose an ADR instead.

## FastAPI conventions

- Each module's `api.py` exposes `router = APIRouter(prefix="/<resource>", tags=["<module>"])`;
  `kritvo/main_api.py` includes it under `/api/v1`. WhatsApp routes go in `main_gateway.py`.
- Endpoints are `async def` and thin: validate input, call the module's `service.py`, return a schema.
- Request and response models live in `schemas.py` (Pydantic v2). Input models use
  `model_config = ConfigDict(extra="forbid")`. Every endpoint declares its return type or `response_model`.
- Dependencies use `Annotated[..., Depends(...)]` (database session, current principal, permission checks).
- Errors: raise `kritvo.core.errors.AppError("CODE", status=...)`. Never return error dicts or raise
  `HTTPException` with free text.
- Settings only through `kritvo.core.settings.get_settings()`; never read `os.environ` in modules.
- No blocking I/O in async code: use `httpx.AsyncClient`, async SQLAlchemy, `anyio.sleep`.
  CPU-heavy or slow work (PDFs, images, WhatsApp sends) goes to the worker queue, not `BackgroundTasks`.
- Use `datetime.now(UTC)`; never naive datetimes.
- New modules: use the `/new-module` skill.

## Data and safety

- Every tenant table: `tenant_id`, `enable_tenant_rls()` in the same migration, isolation tests.
- Services own transactions; dependencies never commit.
- Bind SQL parameters; no f-strings or `%` formatting in SQL.
- State-changing endpoints accept `Idempotency-Key`; field actions carry `client_op_id`.
- Job state changes only through `jobs.service.transition`.
- Money in paise, time in UTC, UUIDv7 IDs.
- Any API change: keep it backward-compatible and run `uv run kritvo-openapi` so
  `openapi/openapi.json` is committed with it.

## Before finishing

`uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run lint-imports && uv run pytest`
