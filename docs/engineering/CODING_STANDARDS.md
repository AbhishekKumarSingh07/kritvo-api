# Coding standards

## General

- IDs: UUIDv7 primary keys; human-readable per-tenant numbers for display.
- Time: `timestamptz` in UTC; display in the tenant's time zone (default `Asia/Kolkata`).
- Money: integer paise (`bigint`) plus currency; never floats.
- Phones: E.164, encrypted at rest, looked up by keyed hash.
- Master data is soft-deleted; events and ledgers are never deleted.
- No secrets in code; configuration from environment variables only.

## Python (`kritvo-api`)

- Stack fixed by ADR-0007: Python 3.13, FastAPI + Uvicorn, Pydantic v2, SQLAlchemy 2 async + asyncpg, Alembic.
- `uv` for dependencies (`uv add`, commit `uv.lock`); Ruff for lint and format; mypy strict for all of `src/`; pytest with `httpx.AsyncClient` for API tests.
- Module layout per LLD 1.2: `api.py`, `service.py`, `models.py`, `schemas.py`, `events.py`, `tasks.py`.
- A module imports only `core`, `shared` and other modules' `service.py` (enforced by import-linter).
- Services own transactions (`async with session.begin()`); FastAPI dependencies never commit.
- Raw SQL only in migrations and tenancy helpers; always bind parameters.
- Errors use RFC 9457 problem details with stable `code` values: raise `kritvo.core.errors.AppError`.
- FastAPI: one `APIRouter` per module in `api.py`; `async def` endpoints; Pydantic schemas in `schemas.py`; dependencies with `Annotated[..., Depends()]`; no blocking I/O in async code; slow work goes to the worker.
- Settings come only from `kritvo.core.settings.get_settings()`.
- Every POST that changes state accepts an `Idempotency-Key`.
- Tests: unit tests for pure logic, integration tests against real PostgreSQL, isolation tests for every tenant table.

## TypeScript (`kritvo-web`)

- Node 24 (see `.nvmrc`), pnpm, TypeScript strict, ESLint, Prettier, Vitest, Testing Library, Playwright.
- API types are generated from `../kritvo-api/openapi/openapi.json` (`pnpm gen:api`); never hand-write response types.
- Server state through TanStack Query; offline outbox in IndexedDB (LLD 7).
- Tap targets at least 48 × 48 px; primary actions reachable by thumb; Hindi and English strings from day one.

## SQL and migrations

- One Alembic revision per change; expand then contract; never edit an applied migration.
- Every new tenant table calls `enable_tenant_rls()` in the same migration.
- Name indexes `<table>_<purpose>_idx`.

## Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Python modules and functions | snake_case | `post_movement` |
| Classes and React components | PascalCase | `JobCard` |
| Database tables and columns | snake_case, plural tables | `stock_movements` |
| API paths | kebab-case nouns, plural | `/planned-visits` |
| Event and error codes | UPPER_SNAKE_CASE | `GUARD_FAILED` |
| Branches | `<type>/TASK-###-short-name` | `feat/TASK-002-tenant-rls` |
