# ADR-0003: Background queue and scheduler leader

Date: 2026-09-17 | Status: Proposed (open until TASK-004) | Related: LLD 10, TASK-004

## Context

v1.0 ran APScheduler inside the API, which duplicates jobs when scaled. Kritvo needs reliable tasks and exactly one scheduler.

## Decision

To be confirmed by the TASK-004 spike. Leading option: a Postgres-backed queue (for example Procrastinate) with `SKIP LOCKED`, and a scheduler leader chosen by a PostgreSQL advisory lock.

## Alternatives considered

| Option | Why not chosen (yet) |
| --- | --- |
| Celery + Redis | Adds a second stateful system at MVP; kept as fallback |
| APScheduler in API | Duplicate runs when scaled |

## Consequences

- Positive: one fewer system to run; transactional enqueue.
- Negative: library maturity must be verified.
- Risks and mitigations: queue load on PostgreSQL → monitor queue depth; move to Celery if needed.
