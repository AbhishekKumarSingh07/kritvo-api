# ADR-0002: One Kritvo WhatsApp number in MVP

Date: 2026-09-17 | Status: Proposed | Related: HLD 7.2, LLD 6.9, TASK-013

## Context

Field staff and end customers need WhatsApp messages. Each tenant connecting its own number needs Meta verification per tenant.

## Decision

The MVP uses one Kritvo-owned number for staff and customer messages, with the tenant name as a template variable. Phase 2 lets Business-plan tenants connect their own numbers, onboarded as a Meta Tech Provider or through a partner BSP.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Tenant numbers from day one | Slows onboarding and pilot |
| Unofficial WhatsApp automation | Breaks WhatsApp terms; numbers get banned |

## Consequences

- Positive: fast onboarding, one verification, simple metering.
- Negative: customers see Kritvo, not the contractor's brand, in the MVP.
- Risks and mitigations: one number's quality rating affects all tenants → utility-only templates, per-tenant caps, standby number.
