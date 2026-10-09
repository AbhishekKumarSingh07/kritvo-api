# ADR-0004: Events for field actions, versions for office edits

Date: 2026-09-17 | Status: Accepted | Deciders: Project lead | Related: HLD 8.2, LLD 3 and 7

## Context

Technicians work offline for hours; office staff edit the same jobs. v1.0 mixed last-write-wins with optimistic locking.

## Decision

Field actions (status, checklist, photos, punches, parts used) are append-only events with a client operation ID. Office-editable fields use a `version` column and `If-Match`.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Last-write-wins on server time | Server time at sync is not action time; silent data loss |
| CRDTs | Too complex for the MVP |

## Consequences

- Positive: no conflicts for field data; full audit trail.
- Negative: current state is a projection that must stay consistent.
- Risks and mitigations: projection bugs → property tests and replay checks.
