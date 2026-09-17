# ADR-0005: Risk score instead of hard blocks for location and selfie evidence

Date: 2026-09-17 | Status: Proposed | Related: HLD 10, LLD 8, TASK-010

## Context

Phone location and photos can be faked, and WhatsApp lets users pick a map location. Hard blocks would stop honest staff with bad GPS.

## Decision

Combine signals into a 0–100 score with tenant-tunable weights; auto-accept low scores, queue medium scores for review, flag high scores. Run in shadow mode for the first 4 weeks of the pilot. Customer OTP is the strongest job proof.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Hard geofence block | Fails honest staff; still spoofable |
| Face recognition in MVP | Consent, cost and lighting problems; moved to Phase 3 as optional |

## Consequences

- Positive: fair to staff; tunable; honest about limits.
- Negative: needs coordinator time for reviews.
- Risks and mitigations: review overload → track queue share weekly and tune weights.
