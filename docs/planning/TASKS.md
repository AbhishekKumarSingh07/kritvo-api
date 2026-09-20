# Task plan

This is the plan index. Live progress is tracked in GitHub issues (in the repository named in the **Repo** column) and on the Kritvo Roadmap project board, which spans both repositories. `/status-update` keeps the **Status** column here in step with the issues.
Task details and acceptance criteria: LLD section 14 (engineering) and HLD sections 1.4 and 13 (business).

- Status values: Done · In progress · Ready · Blocked · Backlog
- Repo values: `api` = kritvo-api, `web` = kritvo-web. For `web + api`, the issue lives in the first repository and the other repository's PR references it.

## Phase 0 — Foundations (business)

All business issues live in `kritvo-api`.

| ID | Title | Depends on | Status | Notes |
| --- | --- | --- | --- | --- |
| BIZ-000 | Design docs: HLD 2.0, LLD 1.2 | — | Done | 2026-09-17 |
| BIZ-001 | Name checks: domains, IP India Classes 9 and 42, MCA, social handles, Play Store | — | Ready | HLD 1.4 |
| BIZ-002 | Buy `.com` and `.in` domains | BIZ-001 | Backlog | |
| BIZ-003 | Reserve company name and incorporate | BIZ-001 | Backlog | |
| BIZ-004 | File trademark in Classes 9 and 42 | BIZ-001 | Backlog | |
| BIZ-005 | Meta Business verification and WhatsApp test number | BIZ-003 | Backlog | Unblocks TASK-013 |
| BIZ-006 | Design-partner agreement with Rahul Electricals | — | Ready | HLD 5.5 |
| BIZ-007 | Answer HLD 13.3 open questions | — | Ready | |
| BIZ-008 | Interview 10 contractors; validate pricing | BIZ-007 | Backlog | HLD 4.3, 5.1 |
| BIZ-009 | Collect DG-set template data (intervals, checklists, parts) | BIZ-006 | Backlog | Unblocks TASK-007 |
| BIZ-010 | Confirm Meta pricing for in-window replies from 1 Oct 2026 | — | Ready | HLD 7.6 |
| BIZ-011 | Counsel review: DPDP staff notice and processor terms | — | Backlog | Unblocks TASK-021 |
| BIZ-012 | Review and accept ADR-0001, 0002, 0004, 0005 | — | In progress | ADR-0001 accepted 2026-09-18; 0002/0004/0005 pending |

## Phase 1 — MVP (engineering)

| ID | Title | Repo | Type | Depends on | Risk | Status |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-000 | Repository foundations for both repositories (docs, Claude Code setup, GitHub templates, CI skeleton) | api + web | chore | — | Low | Done |
| TASK-001 | API scaffolding (FastAPI), tooling, CI and OpenAPI export | api | feat | TASK-000 | Low | Done |
| TASK-023 | Web scaffolding, tooling, CI and `pnpm gen:api` | web | feat | TASK-000 | Low | Done |
| TASK-002 | Database foundation: roles, tenancy helpers, RLS pattern, isolation tests | api | security | 001 | High | Done |
| TASK-003 | Identity: users, memberships, roles, OTP and password + TOTP login, tokens | api | security | 002 | High | Done |
| TASK-004 | Spike: task queue and scheduler leader; write ADR-0003 | api | refactor | 002 | Medium | Backlog |
| TASK-005 | Audit trigger with per-tenant hash chain | api | security | 002 | Medium | Backlog |
| TASK-006 | Customers, sites, asset types, assets, custom fields, Excel import | api | feat | 003 | Medium | Backlog |
| TASK-007 | Template loader and DG-set template | api | feat | 006, BIZ-009 | Medium | Blocked |
| TASK-008 | Workflow engine, jobs, assignments, transactional outbox | api | feat | 004, 006 | High | Backlog |
| TASK-009 | Presigned uploads, evidence items, media worker | api | feat | 004 | Medium | Backlog |
| TASK-010 | Attendance, risk scoring in shadow mode, review queue | api | feat | 008, 009 | High | Backlog |
| TASK-011 | Inventory ledger and part obligations | api | feat | 008 | High | Backlog |
| TASK-012 | Contracts, maintenance plans, AMC generator, escalations | api | feat | 004, 008 | Medium | Backlog |
| TASK-013 | WhatsApp gateway: webhook, inbox, sender, metering, template registry | api | feat | 003, 004, BIZ-005 | High | Blocked |
| TASK-014 | WhatsApp bot state machine, Flows, data endpoint | api | feat | 008, 010, 013 | High | Backlog |
| TASK-015 | Customer OTP verification and service report PDF | api | feat | 008, 013 | Medium | Backlog |
| TASK-016 | Office web app: dispatch board, jobs, customers, review queue, inventory | web | feat | 008, 010, 011, 023 | Medium | Backlog |
| TASK-017 | Technician PWA and offline outbox; sync API | web + api | feat | 008, 009, 023 | High | Backlog |
| TASK-018 | Owner dashboard, daily WhatsApp summary, parts variance report | web + api | feat | 011, 012, 013, 023 | Low | Backlog |
| TASK-019 | Notification router and preferences | api | feat | 013 | Medium | Backlog |
| TASK-020 | Terraform production, observability, alerts, backups, restore drill | api | perf | 001, BIZ-002 | Medium | Backlog |
| TASK-021 | Privacy: staff notice, retention purge, export and erase tools | api + web | security | 009, 010, BIZ-011 | Medium | Backlog |
| TASK-022 | Pilot at Rahul Electricals: import, training, shadow-mode calibration | api | docs | All | Medium | Backlog |

## Acceptance criteria added by ADR-0008

The notification-delivery stub (ADR-0008) is deliberately temporary. These checkboxes record its
exit conditions where the tasks that must clear them are actually planned, so removal is not
forgotten. See ADR-0008's "Follow-up required" section for the full list.

- [ ] TASK-013: Real sender registered behind the TASK-003 notification interface.
- [ ] TASK-019: ADR-0008 logging sender is no longer reachable in staging or production; startup-guard test passes.
- [ ] TASK-022: Pilot environment does not resolve to the ADR-0008 logging sender.
