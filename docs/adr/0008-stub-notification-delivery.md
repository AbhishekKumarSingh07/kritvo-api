# ADR-0008: Stub outbound notification delivery until a channel exists

Date: 2026-09-19 | Status: Accepted | Deciders: Project lead | Related: TASK-003, TASK-013, TASK-019, TASK-022, LLD 3.3, LLD 12.1, LLD 12.4

## Context

TASK-003 (identity) needs to deliver one-time codes to field staff and portal clients, and login
alerts to owners and admins. HLD and LLD both assume WhatsApp (with SMS as a fallback for staff)
as the delivery channel. But the two tasks that build real delivery — TASK-013 (WhatsApp gateway)
and TASK-019 (notification router) — are not built yet, and TASK-013 is itself blocked on BIZ-005
(Meta Business verification), which has no committed date. Making TASK-003 wait for either would
stall all login and identity work indefinitely.

BIZ-005 is not blocked on Meta alone: Meta requires a verified business whose name matches the
WhatsApp display name, which itself requires an incorporated company — and whether Kritvo
incorporates as a separate company is still an open question (HLD 5.5, 13.3). The real chain is
incorporate → verify → build the gateway, not just "wait for Meta", and blocking identity on any
part of that chain stalls roughly 19 of the 23 MVP tasks, since nearly everything depends on being
able to log in. Blocking also buys nothing on the demo side: an end-to-end WhatsApp login demo
needs TASK-013 regardless of when TASK-003 starts, so waiting only delays login and everything
downstream of it, without moving a real WhatsApp demo any closer.

## Decision

TASK-003 defines a small notification-sending interface (one method: send a code or alert to a
user) and ships one implementation behind it — a logging sender that writes the code to structured
logs, gated to non-production environments only. No real WhatsApp or SMS call is made from TASK-003.
When TASK-013 and TASK-019 land, a real sender is written to the same interface and swapped in;
the identity module does not change.

Accepted with four binding conditions:

- (a) Production must fail to start if no real sender is configured outside local/dev — a hard
  startup failure, not a warning or a silent fallback — with a test asserting this.
- (b) The notification-sending interface lives in `modules/notifications`, not `identity`, since
  `modules/notifications` already owns `notification_prefs` and `outbound_messages` (LLD 3.3).
- (c) LLD 12.4 is amended with an explicit carve-out documenting the logging sender's local/dev-only
  scope.
- (d) The exit conditions for removing this stub are recorded outside this ADR (LLD 14.1's task
  table and `docs/planning/TASKS.md`), so they stay visible wherever TASK-013, TASK-019 and
  TASK-022 are actually planned, not only here.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Build a minimal WhatsApp send path inside TASK-003 | Duplicates work TASK-013 will do properly; blurs task boundaries in `docs/planning/TASKS.md` |
| Integrate a third-party SMS provider directly as an interim channel | Adds an unbudgeted vendor dependency and a channel not called for in HLD/LLD. Also doesn't avoid the wait: Indian SMS OTP requires TRAI DLT registration of the sender header and message templates, which itself requires a registered entity — the same incorporation prerequisite as Meta verification |
| Block TASK-003 until TASK-013 unblocks | TASK-013 depends on BIZ-005 (Meta verification, itself gated on incorporation) with no committed date; blocking identity indefinitely is unacceptable |

## Consequences

- Positive: TASK-003 proceeds without waiting on Meta verification, incorporation or the gateway build.
- Positive: the real channel (TASK-013/TASK-019) plugs in behind the same interface with no changes to identity code.
- Positive: the stub is not throwaway — a non-production sender stays permanently useful for local development, CI and automated tests, so those do not incur real per-message cost or consume Meta's rate limits on every test run.
- Negative: in local/dev only, OTP codes must be read from logs rather than received on WhatsApp, until the real sender is wired in; staging and production both require a real sender or fail to start (condition a).
- Risks and mitigations: the logging sender leaking into production is a sharper risk than an ordinary log line, because logs are retained 180 days in India for CERT-In (HLD 11.2) and mirrored to Sentry (LLD 13.1) — a leaked OTP would persist in a readable store rather than being transient. Mitigated by the fail-closed startup guard (condition a), not by an environment flag alone.

## Follow-up required

- [ ] TASK-019 ships a real sender behind the same interface.
- [ ] The logging sender is registered only for local/dev, and the startup-guard test (condition a) passes.
- [ ] The LLD 12.4 carve-out (condition c) is narrowed or removed.
- [ ] TASK-022 does not start while the pilot tenant resolves to the logging sender.

When all four are done, a short ADR marks this one Superseded.
