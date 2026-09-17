# ADR-0006: Separate repositories for API and web

Date: 2026-09-17 | Status: Accepted | Deciders: Project lead | Related: LLD 1.1 (v1.2)

## Context

Kritvo has a Python backend and a React UI that deploy separately. A monorepo was proposed in LLD 1.1; the project lead prefers separate repositories.

## Decision

Use two repositories:

- `kritvo-api`: backend, WhatsApp gateway, worker, migrations, `openapi/` contract, `infra/` Terraform, and all documentation in `docs/`.
- `kritvo-web`: office app, technician PWA and client portal.

The API contract is the committed `openapi/openapi.json`. Developers clone both repositories side by side; Claude Code in `kritvo-web` reads `../kritvo-api/docs` and `../kritvo-api/openapi` through `permissions.additionalDirectories`.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| One monorepo | Owner preference: separate ownership, access and release cadence for UI and backend |
| Third repository for docs | One more repository to keep in sync; most design detail is backend-facing |
| Docs copied into both repositories | Copies drift apart |

## Consequences

- Positive: independent CI, releases and access (a UI contractor can get web-only access); clear ownership; a future mobile app consumes the same contract.
- Negative: cross-cutting changes need two PRs; the web repository depends on a sibling checkout for design docs; the web CI contract check needs a read-only token for the private API repository.
- Risks and mitigations: contract drift → committed OpenAPI file, CI check in both repositories, backward-compatible API changes merged first.
