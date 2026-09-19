# ADR-0009: Rate-limit auth with Postgres counters, not Redis, until ADR-0003

Date: 2026-09-19 | Status: Accepted | Deciders: Project lead | Related: TASK-003, TASK-004, ADR-0003, LLD 12.4

## Context

LLD 12.4 sets fixed rate limits for authentication: 3 OTP requests per phone per 15 minutes,
10 per device per hour, 5 login failures per account per 15 minutes then backoff, and a
per-IP ceiling of 300 requests per minute. Enforcing these needs a shared counter store that
every API process can read and update. The obvious store for this kind of short-lived counter
is Redis, but whether Kritvo runs Redis at all is not decided yet — ADR-0003 is still open, and
its leading option (TASK-004) is a Postgres-backed queue with no Redis. Adding Redis just for
TASK-003's rate limits would commit the project to a second stateful system ahead of that
decision, and would need to be undone or duplicated if ADR-0003 lands on the Postgres option.

## Decision

TASK-003 implements the auth rate limits in this ADR using tenant-scoped Postgres counters
(e.g. a small table keyed by phone/device/account/IP and time window, matching the schema's
existing row-level-security pattern), not Redis. If ADR-0003 later adopts Redis for the
background queue, rate limiting can move onto the same store as a follow-up change; until
then it stays on Postgres so TASK-003 does not introduce infrastructure ADR-0003 has not
approved.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Redis counters (e.g. `INCR` with `EXPIRE`) | Introduces a second stateful system before ADR-0003 decides whether Kritvo runs Redis at all |
| In-process memory counters | Do not work once the API runs more than one process/instance; limits could be bypassed by hitting different instances |

## Consequences

- Positive: TASK-003 ships without waiting on ADR-0003, and without pre-committing to Redis.
- Positive: consistent with ADR-0003's leading option (Postgres-backed queue), so the stack stays on one stateful store for now.
- Negative: Postgres counters carry more write load than Redis would under heavy abuse traffic; acceptable at MVP scale.
- Risks and mitigations: counter-table growth and write contention under abuse → short retention with periodic cleanup, and revisit on Redis if ADR-0003 adopts it.
