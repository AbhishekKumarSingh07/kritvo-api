# kritvo-api — instructions for Claude Code

Kritvo is a multi-tenant, WhatsApp-first field operations SaaS for Indian service contractors.
This repository: Python 3.13 + FastAPI, Pydantic v2, SQLAlchemy 2 async, PostgreSQL 16 with
row-level security, WhatsApp gateway, worker, Terraform, and ALL project documentation.
The UI is a separate repository, `kritvo-web`, usually checked out at `../kritvo-web`.

Current state: @docs/status/STATUS.md

## Where things are (read on demand, do not load everything)

- Product and architecture: `docs/architecture/HLD.md` (large; read the section you need)
- Tables, APIs, algorithms, task plan: `docs/architecture/LLD.md` (large; search it)
- One-page overview: `docs/architecture/ARCHITECTURE.md`
- Decisions: `docs/adr/` (index in `docs/adr/README.md`)
- Tasks for both repositories: `docs/planning/TASKS.md`; live status in GitHub issues
- Standards: `docs/engineering/CODING_STANDARDS.md`, `docs/engineering/GIT_WORKFLOW.md`,
  `docs/engineering/DEFINITION_OF_DONE.md`
- API contract for the UI: `openapi/openapi.json`
- Old v1.0 design (Opsly): `docs/architecture/archive/` — history only, never follow it

## Backend stack (fixed by ADR-0007)

Python 3.13 · FastAPI + Uvicorn · Pydantic v2 · SQLAlchemy 2 async + asyncpg · Alembic · uv ·
Ruff · mypy strict · pytest · import-linter. Never add another web framework, language or
service; propose an ADR instead. FastAPI conventions are in `.claude/rules/api-python.md`.

## Layout

- `src/kritvo/main_api.py` — FastAPI app for web, PWA and portal (`/api/v1`)
- `src/kritvo/main_gateway.py` — FastAPI app for WhatsApp webhooks
- `src/kritvo/core/` — settings, errors (problem details), logging, request IDs, app factory
- `src/kritvo/shared/` — pure helpers; `src/kritvo/modules/<name>/` — feature modules (`/new-module`)
- `src/kritvo/tools/openapi.py` — `kritvo-openapi` contract export
- `tests/`, `migrations/` (TASK-002), `openapi/`, `infra/`, `docs/`, `scripts/`

## Commands

- Setup: `uv sync` (creates `.venv` with Python 3.13)
- Run API: `uv run uvicorn kritvo.main_api:app --reload` → <http://localhost:8000/docs>
- Run gateway: `uv run uvicorn kritvo.main_gateway:app --port 8001 --reload`
- Full stack with PostgreSQL: `docker compose up --build`
- Checks: `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy src` · `uv run lint-imports` · `uv run pytest`
- Contract: `uv run kritvo-openapi` (writes `openapi/openapi.json`; a test fails if it is stale)
- Add a dependency: `uv add <package>` (dev: `uv add --dev <package>`); commit `uv.lock`
- Docs lint: `npx markdownlint-cli2 "**/*.md"`
- Document history: `scripts/doc-version.sh list docs/architecture/HLD.md`

## How we work

- One task per branch: `<type>/TASK-###-short-name`. Never commit to `main` directly.
- Start with `/task-start TASK-###`; finish with `/task-finish`; end sessions with `/status-update`.
- New feature module: `/new-module <name> <resource-path>`.
- Commit and PR titles: Conventional Commits ending with the task ID,
  e.g. `feat(identity): add OTP login (TASK-003)`.
- Every PR updates `CHANGELOG.md` (Unreleased).
- API changes must be backward-compatible; regenerate `openapi/openapi.json` in the same PR.
  Removing or renaming fields needs a follow-up PR after `kritvo-web` stops using them.

## Non-negotiable engineering rules

- Tenant isolation: every tenant table has `tenant_id` and forced RLS. Never bypass it,
  never build SQL with string formatting, never read `tenant_id` from request bodies.
- No secrets in code, tests, docs or commits. Use environment variables; update `.env.example`.
- Money is integer paise; time is `timestamptz` in UTC; IDs are UUIDv7.
- Field actions are append-only events with `client_op_id` for idempotency.
- Job state changes only through the workflow engine (LLD section 4).
- Never invent library APIs or config keys. If unsure, check the installed package or ask.

## Documentation rules

- `main` of this repository is the source of truth for all docs. Claude Docs and chat drafts are working copies.
- Changing `HLD.md` or `LLD.md` requires `/doc-change`: bump Version, add a Revision history row,
  and write an ADR if a decision changes. CI enforces the version bump.
- Accepted ADRs are never edited; supersede them with a new ADR (`/adr-new`).
- Never edit files in `docs/architecture/archive/`.
- If code and docs disagree, stop and say so; fix one of them in the same PR.

## Git safety

- Never force-push, rewrite published history, or delete tags.
- Ask before `git push`, `gh pr merge`, or any command that changes GitHub settings.

## Session rules

- "start TASK-###" / "start BIZ-###" → run `/task-start`: read the task and its LLD/HLD detail,
  check dependencies, create the branch, then show a short plan and wait for approval before code.
- "finish the task" → run `/task-finish`.
- Explain actions in plain language, a couple of sentences at a time; assume no developer
  background, and give a one-line explanation for any jargon.
- Ask one question at a time. Never ask for specifications already in the docs.
- PR/commit titles: `type(scope): summary (TASK-###)`. PR body: `Closes #<issue>` if fully done,
  `Refs #<issue>` if partial. Web tasks reference issues as `AbhishekKumarSingh07/kritvo-api#<number>`.
- Never edit files in `../kritvo-web` from this repository. Never push or merge without asking.
- On failure, explain the error in plain language with the likely cause and the options, before
  changing anything.
