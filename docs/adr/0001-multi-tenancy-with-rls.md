# ADR-0001: Shared schema with PostgreSQL row-level security

Date: 2026-09-17 | Status: Accepted | Deciders: Project lead | Related: HLD 8.3, LLD 2, TASK-002

## Context

Kritvo serves hundreds of small tenants from one deployment. A missed tenant filter in any query would leak one contractor's data to a competitor.

The same design also has to serve a second deployment shape: a single contractor running Kritvo entirely on their own server ("local install") rather than on the shared cloud. The schema must not need a different architecture for that case.

## Decision

All tenants share one schema. Every tenant table has `tenant_id` and forced RLS policies based on `app.tenant_id`, which the app sets on every transaction. A separate `kritvo_system` role bypasses RLS only in platform code.

Tenant context is set with `set_config('app.tenant_id', ..., true)` — the `true` flag makes it transaction-local (`SET LOCAL` semantics), not session-level — and asyncpg's prepared-statement cache is disabled (`statement_cache_size=0`). Both are required, not optional tuning: behind PgBouncer in transaction-pooling mode, a database connection is reused across different callers between transactions. A session-level setting or a cached prepared statement can carry one tenant's context onto the next caller's transaction on the same connection — silently, with no error — which would defeat RLS rather than just break something loudly. This mitigation is implemented in `src/kritvo/core/db.py` (LLD section 2.3).

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Filter in application code only | One forgotten filter leaks data |
| Schema per tenant | Migrations and connection pools get heavy at hundreds of tenants |
| Database per tenant | Highest cost and operations effort for small tenants |

## Consequences

- Positive: isolation enforced by the database; cheap to run; one migration path.
- Positive: a local install is just a one-tenant deployment of the same codebase and migrations — no separate architecture, schema or code path for self-hosted customers.
- Negative: every session must set tenant context; asyncpg behind PgBouncer needs the statement cache off.
- Risks and mitigations: missing policy on a new table → CI coverage test fails the build.
- Risks and mitigations: PgBouncer transaction pooling reuses connections across callers → tenant context is always set with transaction-local (`SET LOCAL`-equivalent) scope and the prepared-statement cache is disabled, so a stale tenant setting can never carry over to the next caller on a reused connection.
