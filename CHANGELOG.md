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
