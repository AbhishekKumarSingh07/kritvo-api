# Status

Last updated: 2026-09-17 · Phase 0 (Foundations)

## Summary

Design documents are done (HLD 2.0, LLD 1.2). Code lives in two repositories: `kritvo-api` (with all docs) and `kritvo-web`. The product is named Kritvo, pending availability checks. The repository foundation (TASK-000) is being set up.

## Next up

1. Finish TASK-000: push `kritvo-api` and `kritvo-web`, run `scripts/bootstrap-github.sh`, connect the Claude.ai project.
2. BIZ-001: domain and trademark checks for "Kritvo".
3. TASK-001: the FastAPI scaffold is in the starter; finish it by confirming CI (including the Docker build) is green on GitHub and `docker compose up` works locally. Then TASK-023 (web scaffolding).

## Blocked

- TASK-007 waits for DG-set template data (BIZ-009).
- TASK-013 waits for Meta Business verification (BIZ-005).

## Decisions pending

- Accept ADR-0001, 0002, 0004, 0005 (BIZ-012).
- ADR-0003 queue choice (TASK-004).
- Meta pricing for in-window replies from 1 Oct 2026 (BIZ-010).

## Latest document versions

| Document | Version | Tag |
| --- | --- | --- |
| HLD | 2.0 | `hld-v2.0` (create after first push) |
| LLD | 1.2 | `lld-v1.2` (create after first push) |
