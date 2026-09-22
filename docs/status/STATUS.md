# Status

Last updated: 2026-09-22 · Phase 1 (MVP, engineering) / Phase 0 (Foundations, business)

## Summary

Design documents are in progress (HLD 2.1, LLD 1.6). Both repositories are on GitHub with green CI, and the project lives in `~/code/kritvo`. The FastAPI scaffold (TASK-001), web scaffold (TASK-023), the database foundation with tenant isolation (TASK-002), and identity — OTP and password+TOTP login, tokens, rate limits (TASK-003) — are all built, tested against a real PostgreSQL, and merged (`kritvo-api` PR #45, #46). ADR-0002 (WhatsApp number model) is now Accepted: every tenant defaults to Kritvo's shared WhatsApp number, but can opt into connecting its own number from day one of the MVP rather than waiting for a later phase or paid plan; HLD 7.2 and LLD 6.9 updated to match. ADR-0004 and ADR-0005 are still awaiting accept/reject. The product is named Kritvo, pending availability checks.

## Next up

1. BIZ-012: review and accept the remaining ADRs (0004, 0005).
2. TASK-004: spike task queue/scheduler leader and write ADR-0003, or TASK-005/006 (audit trigger; customers, sites, assets) — next engineering work now that TASK-003 is done.
3. BIZ-001: domain and trademark checks for "Kritvo" (pushed to the end of the priority list).

## Blocked

- TASK-007 waits for DG-set template data (BIZ-009).
- TASK-013 waits for Meta Business verification (BIZ-005).

## Decisions pending

- Accept ADR-0004, 0005 (BIZ-012); ADR-0001 accepted 2026-09-18, ADR-0008 and ADR-0009 accepted 2026-09-19, ADR-0002 accepted 2026-09-22.
- ADR-0003 queue choice (TASK-004).
- Meta pricing for in-window replies from 1 Oct 2026 (BIZ-010).

## Latest document versions

| Document | Version | Tag |
| --- | --- | --- |
| HLD | 2.1 | `hld-v2.0` (not yet re-tagged for 2.1) |
| LLD | 1.6 | `lld-v1.2` (not yet re-tagged for 1.3/1.4/1.5/1.6) |
