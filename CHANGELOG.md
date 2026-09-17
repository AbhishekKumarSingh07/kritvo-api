# Changelog

All notable changes to `kritvo-api` are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use [Semantic Versioning](https://semver.org/).
Document versions (HLD, LLD) are tracked in each document's Revision history and with `hld-v*` / `lld-v*` tags.

## [Unreleased]

### Added

- HLD v2.0 and LLD v1.2 for Kritvo in `docs/architecture/` (BIZ-000).
- Opsly HLD v1.0 archived in `docs/architecture/archive/`.
- ADR-0001 to ADR-0007; ADR-0006 records the split into `kritvo-api` and `kritvo-web`; ADR-0007 fixes the backend stack on Python 3.13 and FastAPI.
- FastAPI scaffold: API and gateway apps, settings, problem-details errors, JSON logging, request IDs, health endpoints, `kritvo-openapi` contract export, tests, Ruff/mypy/import-linter config, Dockerfile and Docker Compose (TASK-001).
- Claude Code `/new-module` skill and FastAPI rules for backend code.
- Repository foundations: Claude Code instructions, rules and skills; GitHub templates; CI, docs, PR-title and secret-scan workflows; GitHub bootstrap script for both repositories (TASK-000).

### Changed

- `status-update` skill: commit message and PR title now end with a task ID, so they pass the pr-title check (TASK-000).
- `CLAUDE.md`: added a Session rules section covering task-start/task-finish triggers, plain-language explanations, one question at a time, PR conventions, and never editing `kritvo-web` from this repo (TASK-000).
- CI: dropped the `pyproject.toml` presence guard now that the scaffold is in place, so Ruff, mypy, import-linter, pytest, the Docker build and the OpenAPI check always run (TASK-001).

### Fixed

- Secret scan: pin `gitleaks-action` to gitleaks 8.30.1 and switch `.gitleaks.toml` to the single `[allowlist]` table so the sample idempotency key in the LLD is allowlisted correctly; set real code owners in `.github/CODEOWNERS` (TASK-000).
