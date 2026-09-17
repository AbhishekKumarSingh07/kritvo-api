# ADR-0007: Python and FastAPI for the backend

Date: 2026-09-17 | Status: Accepted | Deciders: Project lead | Related: HLD 8.1, LLD 1, TASK-001

## Context

Kritvo's backend serves a JSON API, a WhatsApp webhook gateway and background workers, and later AI features such as the tender-document parser. The stack must stay consistent so Claude Code and any future developer never mix frameworks.

## Decision

All backend code in `kritvo-api` uses:

| Concern | Choice |
| --- | --- |
| Language | Python 3.13 |
| Web framework | FastAPI (API and WhatsApp gateway), served by Uvicorn |
| Validation and settings | Pydantic v2, pydantic-settings |
| Database access | SQLAlchemy 2 (async) with asyncpg; Alembic migrations |
| Dependencies and tooling | uv, Ruff, mypy (strict), pytest, import-linter |
| Packaging | One package `kritvo` in `src/`, three processes: `kritvo.main_api`, `kritvo.main_gateway`, worker |

New backend services, scripts and integrations use the same stack. Adding another language or web framework requires a new ADR.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Django + Django REST Framework | Heavier; synchronous-first ORM; its admin and templates are not needed |
| Node.js (NestJS or Express) | Splits the team across languages; Python is stronger for data and AI work planned in Phase 3 |
| Go | Faster runtime, but slower feature delivery for a small team; weaker ecosystem for the planned AI features |
| Flask | No built-in async, validation or OpenAPI generation |

## Consequences

- Positive: automatic OpenAPI contract for `kritvo-web`; type-checked request and response models; one language for API, worker and AI features.
- Negative: async code must never call blocking libraries; CPU-heavy work (PDFs, image hashing) runs in the worker.
- Risks and mitigations: blocking calls in async code → Ruff `ASYNC` rules and review checklist; framework drift → `CLAUDE.md` rule and `.claude/rules/api-python.md`.
