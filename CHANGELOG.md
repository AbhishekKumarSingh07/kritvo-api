# Changelog

All notable changes to `kritvo-api` are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use [Semantic Versioning](https://semver.org/).
Document versions (HLD, LLD) are tracked in each document's Revision history and with `hld-v*` / `lld-v*` tags.

## [Unreleased]

### Added

- HLD v2.0 and LLD v1.2 for Kritvo in `docs/architecture/` (BIZ-000).
- Opsly HLD v1.0 archived in `docs/architecture/archive/`.
- ADR-0001 to ADR-0007; ADR-0006 records the split into `kritvo-api` and `kritvo-web`; ADR-0007 fixes the backend stack on Python 3.13 and FastAPI.
- ADR-0008 (stub outbound notification delivery until a channel exists) and ADR-0009 (rate-limit auth with Postgres counters, not Redis, until ADR-0003), both Accepted (TASK-003).
- `CLAUDE.md`: rule that the notification-sending interface (ADR-0008) has exactly one production implementation, never a log-based or no-op sender, and its startup guard is never relaxed (TASK-003).
- FastAPI scaffold: API and gateway apps, settings, problem-details errors, JSON logging, request IDs, health endpoints, `kritvo-openapi` contract export, tests, Ruff/mypy/import-linter config, Dockerfile and Docker Compose (TASK-001).
- Claude Code `/new-module` skill and FastAPI rules for backend code.
- Repository foundations: Claude Code instructions, rules and skills; GitHub templates; CI, docs, PR-title and secret-scan workflows; GitHub bootstrap script for both repositories (TASK-000).
- Database foundation and tenant isolation: `kritvo_owner` / `kritvo_app` / `kritvo_system` roles (`scripts/bootstrap-db.sql`); Alembic migrations for `tenants`, `users`, `roles`, `memberships`, `customers`, `sites` with forced row-level security; the `enable_tenant_rls()` migration helper; `core/db.py`'s tenant-scoped sessions with the PgBouncer-safe transaction-local context from ADR-0001; the `tests/isolation/` suite (coverage, behaviour, portal, no-context and connection-reuse checks) against a real, throwaway PostgreSQL (TASK-002).
- Identity: OTP login (field/portal), password + TOTP login (owners/admins), JWT access tokens with kid-based signing-key rotation, opaque rotating refresh tokens with reuse-family revocation, and `switch-tenant` — seven endpoints under `/api/v1/auth` (LLD 12.1-12.2). New tables `devices`, `otp_codes`, `refresh_tokens`, `auth_rate_limits`, plus `roles.perms_ver` and its `roles_bump_perms_ver` trigger (undocumented in LLD before this — flagged for `/doc-change`). Six `kritvo_system`-owned `SECURITY DEFINER` lookup functions for the pre-tenant-context phone/refresh-token/membership lookups. Postgres-backed auth rate limits (`modules/identity/rate_limit.py`, ADR-0009). `core/deps.py`'s `get_principal`/`get_db`/`require_permission`, closing the TASK-002 handoff; `core/tokens.py` (`KeyRing`) and `core/principal.py` (`Principal`, `PermissionsCache`) so `core` never imports a feature module. `modules/notifications/`: the `NotificationSender` interface and the ADR-0008 logging sender, with a fail-closed startup guard wired into `main_api.py`. `shared/ids.py`'s `uuid7()`. Argon2id, HMAC-SHA256 and Fernet helpers in `modules/identity/security.py`. Full integration/unit/isolation test coverage against a real PostgreSQL (TASK-003).

### Changed

- `status-update` skill: commit message and PR title now end with a task ID, so they pass the pr-title check (TASK-000).
- `CLAUDE.md`: added a Session rules section covering task-start/task-finish triggers, plain-language explanations, one question at a time, PR conventions, and never editing `kritvo-web` from this repo (TASK-000).
- CI: dropped the `pyproject.toml` presence guard now that the scaffold is in place, so Ruff, mypy, import-linter, pytest, the Docker build and the OpenAPI check always run (TASK-001).
- ADR-0001 accepted: added the local-install deployment-mode rationale and made the PgBouncer/prepared-statement mitigation (`SET LOCAL` semantics, `statement_cache_size=0`) an explicit decision point rather than an implementation detail (BIZ-012).
- ADR-0002: added a build requirement that TASK-013 resolve outbound WhatsApp sending per tenant (via `wa_accounts`) from the start, so moving a tenant onto its own number later is a data change, not a rebuild (BIZ-012).
- LLD to v1.3: added `otp_codes`, `refresh_tokens` and `auth_rate_limits` tables for TASK-003; noted the stubbed notification delivery (ADR-0008) and Postgres-backed auth rate limiting (ADR-0009) (TASK-003).
- LLD to v1.4: ADR-0008 accepted with binding exit conditions; documented the local/dev-only logging-sender carve-out in 12.4; raised TASK-019's risk to Medium and added stub-removal preconditions to TASK-013, TASK-019 and TASK-022 (TASK-003).
- `docs/planning/TASKS.md`: added acceptance-criteria checkboxes recording ADR-0008's stub-removal exit conditions against TASK-013, TASK-019 and TASK-022 (TASK-003).
- LLD to v1.5: added `roles.perms_ver`; corrected the phone_hash/refresh-token/membership/TOTP-secret lookups from `kritvo_owner` to `kritvo_system` in Sections 2.1 and 3.2, since `FORCE ROW LEVEL SECURITY` applies even to a table's owner — gaps found while building TASK-003's identity module (TASK-003).
- ADR-0002 accepted: removed the "Phase 2, Business plan" gate on a tenant connecting its own WhatsApp number — every tenant defaults to Kritvo's shared number, but a tenant can opt into its own number from day one of the MVP, since the per-tenant `wa_accounts` lookup already makes both cases free to support with one code path (BIZ-012).
- HLD to v2.1: 7.2's decision column now says a tenant's own WhatsApp number is available opt-in from day one, not gated behind Phase 2 or a plan tier (ADR-0002) (BIZ-012).
- LLD to v1.6: 6.9 renamed from "Phase 2: tenant-owned numbers" to "Tenant-owned numbers (opt-in from day one)"; `wa_accounts` documented as covering the default shared account too (ADR-0002) (BIZ-012).

### Fixed

- Secret scan: pin `gitleaks-action` to gitleaks 8.30.1 and switch `.gitleaks.toml` to the single `[allowlist]` table so the sample idempotency key in the LLD is allowlisted correctly; set real code owners in `.github/CODEOWNERS` (TASK-000).
- `migrations/env.py`: `fileConfig(..., disable_existing_loggers=False)` — the default silently disabled every Python logger already created in the process, including the app's own, whenever migrations ran in-process rather than as their own command (TASK-003).

### Security

- `scripts/bootstrap-db.sql`: `kritvo_owner` can now hand a function's ownership to `kritvo_system` (needed so a migration-created `SECURITY DEFINER` lookup can run with `kritvo_system`'s `BYPASSRLS` for the pre-tenant-context identity lookups), and `kritvo_system` gets `CREATE` on schema `public`, which PostgreSQL requires to accept that ownership transfer. `kritvo_owner` itself does not gain `BYPASSRLS` (TASK-003).
