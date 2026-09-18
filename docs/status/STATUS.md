# Status

Last updated: 2026-09-18 · Phase 0 (Foundations)

## Summary

Design documents are done (HLD 2.0, LLD 1.2). Both repositories are on GitHub with green CI, and the project now lives in `~/code/kritvo` (moved out of iCloud, which had hidden `.pth` files and broke local `lint-imports`). The FastAPI scaffold (TASK-001), web scaffold (TASK-023) and the database foundation with tenant isolation (TASK-002) are all verified and closed. The product is named Kritvo, pending availability checks.

## Next up

1. TASK-003: identity — users, memberships, roles, OTP and password + TOTP login, tokens (`kritvo-api`).
2. BIZ-012: review and accept the remaining ADRs (0002, 0004, 0005).
3. BIZ-001: domain and trademark checks for "Kritvo" (pushed to the end of the priority list).

## Blocked

- TASK-007 waits for DG-set template data (BIZ-009).
- TASK-013 waits for Meta Business verification (BIZ-005).

## Decisions pending

- Accept ADR-0002, 0004, 0005 (BIZ-012); ADR-0001 accepted 2026-09-18.
- ADR-0003 queue choice (TASK-004).
- Meta pricing for in-window replies from 1 Oct 2026 (BIZ-010).

## Latest document versions

| Document | Version | Tag |
| --- | --- | --- |
| HLD | 2.0 | `hld-v2.0` |
| LLD | 1.2 | `lld-v1.2` |
