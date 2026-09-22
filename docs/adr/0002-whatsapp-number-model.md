# ADR-0002: Kritvo's shared WhatsApp number by default, tenant's own number opt-in from day one

Date: 2026-09-17 | Status: Accepted | Deciders: Project lead | Related: HLD 7.2, LLD 6.9, TASK-013

## Context

Field staff and end customers need WhatsApp messages. Each tenant connecting its own number needs Meta verification per tenant, which takes real time and paperwork and would slow onboarding if required up front for everyone.

## Decision

Every tenant defaults to one Kritvo-owned WhatsApp number for staff and customer messages, with the tenant name as a template variable — no setup needed, available immediately. A tenant that wants its own number for its own branding can opt in from day one of the MVP, not gated behind a later phase or a specific plan tier: Kritvo onboards that tenant's WhatsApp account as a Meta Tech Provider (or through a partner BSP), which stays a Kritvo-staff-brokered action since Meta requires it, not a self-service flow.

TASK-013 builds outbound sending against a per-tenant lookup ("which WhatsApp account does this tenant use") from the start, backed by the `wa_accounts` table (LLD section 6.9), rather than hardcoding the shared number. Most tenants' lookups resolve to the same shared account by default; a tenant that opts into its own number gets its own `wa_accounts` row instead. Both cases go through the same lookup and the same sending code path — there is no separate "Phase 2" code path to build later.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Tenant numbers required from day one | Slows onboarding and pilot for every tenant, even those who don't care about branding |
| Own number as a later phase / paid-plan-only upsell | Delays branding for tenants who want it immediately and have their own Meta Business number ready; the per-tenant lookup already makes this free to support now |
| Unofficial WhatsApp automation | Breaks WhatsApp terms; numbers get banned |

## Consequences

- Positive: fast default onboarding (no setup needed) for tenants who don't need their own number.
- Positive: no artificial delay for tenants who already have a Meta Business number ready and want their own branding immediately.
- Positive: one lookup and one sending code path for both cases, since every tenant resolves through `wa_accounts` — supporting "own number" from day one costs nothing extra in code.
- Negative: some Kritvo-staff onboarding effort (Tech Provider verification per opting-in tenant) has to be ready from the MVP's first tenant, not deferred until there's paid-plan volume to justify it.
- Risks and mitigations: one shared number's quality rating affects every tenant still on it → utility-only templates, per-tenant caps, standby number. A tenant opting into its own number removes it from that shared blast radius.
