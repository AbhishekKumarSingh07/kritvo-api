# kritvo-api

FastAPI backend for Kritvo, a WhatsApp-first field operations platform for Indian service and maintenance contractors. This repository also holds the infrastructure code and **all project documentation**. The UI lives in the separate `kritvo-web` repository.

> **Status:** Phase 0 (foundations). FastAPI scaffold with health endpoints, problem-details errors and the OpenAPI contract export is in place (TASK-001). See [docs/status/STATUS.md](docs/status/STATUS.md).
> **Licence:** Proprietary. All rights reserved.

## Repository map

| Path | What lives there |
| --- | --- |
| `src/kritvo/` | Python 3.13 + FastAPI package: `main_api.py`, `main_gateway.py`, `core/`, `shared/`, `modules/` |
| `tests/` | pytest suite |
| `pyproject.toml`, `uv.lock` | Dependencies and tool settings (uv, Ruff, mypy, pytest, import-linter) |
| `Dockerfile`, `docker-compose.yml` | Container image and local stack |
| `openapi/` | Committed API contract used by `kritvo-web` |
| `infra/` | Terraform for AWS Mumbai (TASK-020) |
| `docs/` | All design, planning and status documents ([index](docs/README.md)) |
| `.claude/`, `CLAUDE.md` | Instructions, rules and skills for Claude Code |
| `.github/` | CI workflows, PR and issue templates |
| `scripts/` | Repository helpers, including the GitHub bootstrap for both repositories |
| `kritvo.code-workspace` | VS Code workspace that opens both repositories |

## Key documents

| Document | Purpose |
| --- | --- |
| [HLD](docs/architecture/HLD.md) | Product, market, architecture and roadmap |
| [LLD](docs/architecture/LLD.md) | Tables, APIs, algorithms and build plan |
| [Architecture summary](docs/architecture/ARCHITECTURE.md) | One-page overview |
| [ADRs](docs/adr/README.md) | Architecture decisions and their status |
| [Task plan](docs/planning/TASKS.md) | Tasks for both repositories |
| [Status](docs/status/STATUS.md) | Where the project stands today |
| [Git workflow](docs/engineering/GIT_WORKFLOW.md) | Branches, commits, cross-repo changes, document versions and rollback |
| [Setup guide](docs/setup/SETUP_GUIDE.md) | Step-by-step setup of both repositories and tooling |

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/) (it installs Python 3.13 for you) and, for the full stack, Docker.

```bash
mkdir -p ~/code/kritvo && cd ~/code/kritvo
git clone git@github.com:<you>/kritvo-api.git
git clone git@github.com:<you>/kritvo-web.git
cd kritvo-api

uv sync                                            # install dependencies
cp .env.example .env                               # local settings
uv run uvicorn kritvo.main_api:app --reload        # http://localhost:8000/healthz and /docs
uv run pytest                                      # tests

docker compose up --build                          # API, gateway and PostgreSQL 16
claude                                             # Claude Code reads CLAUDE.md
```

| Command | Purpose |
| --- | --- |
| `uv run ruff check . && uv run ruff format --check .` | Lint and formatting |
| `uv run mypy src` | Type checks (strict) |
| `uv run lint-imports` | Module boundary rules |
| `uv run kritvo-openapi` | Regenerate `openapi/openapi.json` after API changes |

## How work is tracked

1. Every piece of work is a GitHub issue (`BIZ-###` and API tasks here, web tasks in `kritvo-web`), all on one project board.
2. Work happens on a branch named `<type>/TASK-###-short-name`.
3. A pull request with a Conventional Commit title (for example `feat(identity): add OTP login (TASK-003)`) is squash-merged into `main`.
4. `CHANGELOG.md` is updated in every PR; `docs/planning/TASKS.md` and `docs/status/STATUS.md` are refreshed with `/status-update`.
