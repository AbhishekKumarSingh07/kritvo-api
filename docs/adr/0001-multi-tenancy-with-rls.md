# ADR-0001: Shared schema with PostgreSQL row-level security

Date: 2026-09-17 | Status: Proposed | Related: HLD 8.3, LLD 2, TASK-002

## Context

Kritvo serves hundreds of small tenants from one deployment. A missed tenant filter in any query would leak one contractor's data to a competitor.

## Decision

All tenants share one schema. Every tenant table has `tenant_id` and forced RLS policies based on `app.tenant_id`, which the app sets on every transaction. A separate `kritvo_system` role bypasses RLS only in platform code.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Filter in application code only | One forgotten filter leaks data |
| Schema per tenant | Migrations and connection pools get heavy at hundreds of tenants |
| Database per tenant | Highest cost and operations effort for small tenants |

## Consequences

- Positive: isolation enforced by the database; cheap to run; one migration path.
- Negative: every session must set tenant context; asyncpg behind PgBouncer needs the statement cache off.
- Risks and mitigations: missing policy on a new table → CI coverage test fails the build.
