# ADR-0002: One Kritvo WhatsApp number in MVP

Date: 2026-09-17 | Status: Proposed | Related: HLD 7.2, LLD 6.9, TASK-013

## Context

Field staff and end customers need WhatsApp messages. Each tenant connecting its own number needs Meta verification per tenant.

## Decision

The MVP uses one Kritvo-owned number for staff and customer messages, with the tenant name as a template variable. Phase 2 lets Business-plan tenants connect their own numbers, onboarded as a Meta Tech Provider or through a partner BSP.

TASK-013 must build outbound sending against a per-tenant lookup ("which WhatsApp account does this tenant use") from the start, backed by the `wa_accounts` table (LLD section 6.9), rather than hardcoding the shared number. In the MVP every tenant's lookup resolves to the same shared account, so this costs nothing extra to build correctly now — but it means moving one tenant onto its own number later is a data change (add its `wa_accounts` row, flip its status), not a code change. Since Meta requires Kritvo to broker a tenant's own-number onboarding (Tech Provider or BSP), this stays a Kritvo-staff action; no self-service UI is needed until enough tenants are on paid plans to justify building one.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Tenant numbers from day one | Slows onboarding and pilot |
| Unofficial WhatsApp automation | Breaks WhatsApp terms; numbers get banned |

## Consequences

- Positive: fast onboarding, one verification, simple metering.
- Positive: moving a tenant to its own number later is a data change, not a rebuild, because sending is always resolved per-tenant rather than hardcoded to the shared number.
- Negative: customers see Kritvo, not the contractor's brand, in the MVP.
- Risks and mitigations: one number's quality rating affects all tenants → utility-only templates, per-tenant caps, standby number.
