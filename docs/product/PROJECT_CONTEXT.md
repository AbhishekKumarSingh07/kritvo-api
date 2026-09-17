# Project context

Paste the block below into section 2 of the Claude.ai project instructions, and keep this file in sync.

```text
Project name:        Kritvo (was "Opsly")
Purpose:             WhatsApp-first field operations SaaS for Indian asset-based service
                     contractors: jobs, dispatch, attendance, closed-loop spare parts, AMC,
                     proof of work, GST invoices. Design partner: Rahul Electricals (DG sets).
Tech stack:          Python 3.13, FastAPI, SQLAlchemy 2 (async), PostgreSQL 16 (RLS), Alembic;
                     React + Vite + TypeScript PWA, Tailwind; WhatsApp Cloud API; S3.
Architecture style:  Multi-tenant modular monolith; separate gateway and worker processes.
Repositories:        kritvo-api (backend, infra, docs, OpenAPI contract), kritvo-web (UI).
Hosting:             AWS Mumbai (ap-south-1); frontend on a CDN.
Key integrations:    Meta WhatsApp Cloud API (+ Flows), Razorpay, SMS fallback, GST provider (Phase 3).
Users & scale:       Year 1 target: 50 tenants, about 1,000 field users; 5–200 field staff per tenant.
Constraints:         Very small team; bootstrap budget; DPDP compliance by 13 May 2027;
                     Hindi-first staff; low-end Android phones; poor connectivity at sites.
```

## Where decisions are recorded

- Design: `docs/architecture/HLD.md`, `docs/architecture/LLD.md`
- Decisions: `docs/adr/`
- Plan and status: `docs/planning/TASKS.md`, `docs/status/STATUS.md`
