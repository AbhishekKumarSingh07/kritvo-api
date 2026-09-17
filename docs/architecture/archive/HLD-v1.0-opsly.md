# Opsly — High-Level Design & Solution Document

**Version:** 1.0  
**Product:** Opsly
**Business:** Rahul Electricals & Creative Solutions  
**Prepared for:** Owner / Project Lead  

---

## Table of Contents

1. [Business Context & Goals](#1-business-context--goals)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Repository Strategy](#3-repository-strategy)
4. [Module Breakdown](#4-module-breakdown)
5. [Edge Case & Anti-Abuse Strategy](#5-edge-case--anti-abuse-strategy)
6. [Data Model Overview](#6-data-model-overview)
7. [API Design Conventions](#7-api-design-conventions)
8. [Security Architecture](#8-security-architecture)
9. [Mobile-First UI Strategy](#9-mobile-first-ui-strategy)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Future Scope](#11-future-scope)

---

## 1. Business Context & Goals

### 1.1 Pain Points Being Solved

| # | Pain Point | Business Impact |
|---|-----------|----------------|
| 1 | WhatsApp/phone-based dispatch | No audit trail, miscommunication, lost tickets |
| 2 | Missed AMC/PM schedules | Client penalties, equipment damage, trust erosion |
| 3 | Spare parts leakage / theft | Direct inventory loss, inflated re-orders |
| 4 | Buddy punching & attendance fraud | Inflated payroll, ghost employees |
| 5 | Tender document chaos | Missed deadlines, lost bids, cash flow disruption |
| 6 | Client disputes on proof of work | Difficult billing, credibility damage |
| 7 | No centralized financial view | Owner blind to per-tender profitability |

### 1.2 Success Criteria

- Zero ambiguity on who is where at any given time.
- Inventory variance < 1% between physical stock and system stock.
- 100% of AMC deadlines flagged 7 days in advance, automatically.
- All field operations functional with zero connectivity for up to 8 hours.
- All roles can complete their core workflow without needing phone calls.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                              │
│  Browser (Desktop) │ Mobile Browser (PWA) │ Client Portal  │
└────────────┬───────────────┬──────────────────┬────────────┘
             │               │                  │
             ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              React.js + Vite (PWA)  [Frontend Repo]        │
│  Tailwind CSS │ React Query │ IndexedDB (Offline) │ Zustand │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI (Python 3.12+)  [Backend Repo]           │
│  JWT Auth │ RBAC Middleware │ Background Tasks (APScheduler)│
│  Pydantic V2 │ SQLAlchemy ORM │ Alembic Migrations          │
└──────┬─────────────┬─────────────────────┬─────────────────┘
       │             │                     │
       ▼             ▼                     ▼
┌──────────┐  ┌──────────────┐   ┌─────────────────────┐
│PostgreSQL│  │ Cloud Storage│   │  Redis (Cache +     │
│(Primary) │  │ (S3/GCS)     │   │  Background Queues) │
└──────────┘  └──────────────┘   └─────────────────────┘
```

### 2.1 Core Principles

- **Offline-First:** PWA with Service Workers and IndexedDB. The app is usable without any network.
- **Server-Side Truth:** Every sensitive action (timestamps, GPS validation, token expiry) is validated server-side. The client is never trusted.
- **Defense in Depth:** RBAC enforced at the middleware layer, not just the UI layer. A technician calling the owner's API endpoint directly will receive a 403.
- **Audit Everything:** Every mutation to critical entities (inventory, attendance, tickets) writes to an immutable audit log table.
- **Idempotency:** All sync payloads from the offline queue carry a client-generated UUID to prevent duplicate processing on re-sync.

---

## 3. Repository Strategy

### Recommendation: Two Repositories (Monorepo optional later)

**`opsly-backend`** (Python / FastAPI)
- Pure API server, no HTML rendering.
- Owns DB migrations, background jobs, business logic.
- Exposes OpenAPI/Swagger docs automatically.

**`opsly-frontend`** (React / Vite)
- Purely a client. No business logic.
- Communicates only via REST API.
- Deployable independently (Vercel / Netlify / S3 + CloudFront).

**Why two repos over a monorepo?**
- Separate deployment pipelines (frontend can redeploy in seconds without touching the backend).
- Separate teams / contributors with different skill sets.
- Independent versioning and rollback.
- Easier to add a mobile native app later targeting the same API.

---

## 4. Module Breakdown

### 4.1 Authentication & RBAC

**Implementation:**
- Access token: 15-minute JWT (short-lived, stored in memory).
- Refresh token: 7-day JWT (stored in HttpOnly cookie, not localStorage).
- Token rotation on every refresh (old refresh token is invalidated on use).
- Role embedded in the JWT payload; backend middleware validates on every request.

**Role Permission Matrix:**

| Permission | Owner | Moderator | Staff |
|-----------|-------|-----------|-------|
| View own tickets | ✅ | ✅ | ✅ |
| Create / assign tickets | ✅ | ✅ | ❌ |
| Approve attendance | ✅ | ✅ | ❌ |
| Check out inventory | ✅ | ✅ | ❌ |
| View financial dashboards | ✅ | ❌ | ❌ |
| View audit logs | ✅ | ❌ | ❌ |
| Delete records | ✅ | ❌ | ❌ |
| Override system blocks | ✅ | ❌ | ❌ |
| Modify employee pay | ✅ | ❌ | ❌ |

### 4.2 Ticketing & Dispatch Module

**Ticket Lifecycle State Machine:**

```
OPEN → ASSIGNED → EN_ROUTE → IN_PROGRESS → WAITING_FOR_PARTS → COMPLETED → INVOICED
                                                     ↑___________|
                                                  (parts request)
         ↘ CANCELLED (Moderator only)
```

**Key Features:**
- Office creates ticket with: site name, GPS coords, DG set ID, reported issue, priority.
- Moderator assigns technician(s); technician gets push notification.
- Technician updates status from mobile; each transition is timestamped server-side.
- Ticket closure requires: at least one "After" photo, parts consumption log, and (if critical parts were used) both before/after photo of the part.

### 4.3 Geofenced & Verified Attendance

**Punch-In Flow:**

```
Staff opens app → Requests Camera + GPS permissions
    ↓
App captures: { live_selfie, gps_coords, device_timestamp }
    ↓
POST /api/v1/attendance/punch-in
    ↓
Server validates:
  1. GPS coords vs assigned site (or office) — tolerance: 100m
  2. Server-side timestamp (ignores device timestamp)
  3. Liveness signal from selfie (basic blur/motion detection)
    ↓
If valid → Creates attendance record, status: PENDING_MODERATOR_APPROVAL
    ↓
Moderator sees dashboard of pending check-ins with selfie + GPS map pin
    ↓
Moderator approves / flags → Record updated with approver_id + approval_timestamp
```

**Anti-Abuse Design:**
- GPS is re-validated server-side using Haversine formula.
- Selfie stored with request metadata (IP, User-Agent, device time) for audit.
- If a staff member has no assigned ticket for the day, the app shows "No assignment today" and blocks punch-in for that location.
- Moderator approval creates a DB record with `approved_by` (FK to moderator's user ID) and `approved_at` — full traceability.

### 4.4 Closed-Loop Inventory & Anti-Theft

**Flow:**

```
New Part Arrives → Intake Scan (Barcode/QR) → Inventory Ledger (status: IN_STOCK)
    ↓
Moderator assigns part to Ticket → (status: CHECKED_OUT, ticket_id = X)
    ↓
Technician installs part at site:
  - Uploads photo: new part installed
  - Uploads photo: old defective part
  → (status: PENDING_RETURN)
    ↓
Technician returns defective part to office:
  - Moderator scans defective part barcode
  → (status: CONSUMED, ticket closed for parts)
    ↓
Inventory ledger finalized; defective part logged for disposal/warranty claim
```

**Anti-Theft Controls:**
- A part cannot be checked out without being bound to a specific ticket.
- Ticket cannot reach COMPLETED status if any of its parts are still in PENDING_RETURN.
- Owner dashboard shows a real-time "Parts in Field" count — any part in field > 48 hours triggers an alert.
- Daily reconciliation report emailed to owner: parts checked out vs. parts returned.

### 4.5 AMC & Preventive Maintenance Automation

**Data Model:** Each DG set has: `install_date`, `service_interval_hours`, `service_interval_days`, `last_service_date`, `running_hours` (manually updated or from IoT if available).

**Cron Job (runs daily at 6 AM):**
1. Scans all active AMC contracts.
2. Calculates: `days_until_due = next_service_date - today`.
3. If `days_until_due <= 7` and no open ticket exists for this DG set: auto-creates a DRAFT ticket and notifies assigned Moderator.
4. If `days_until_due <= 0` and still no completed ticket: escalates to Owner with an overdue alert.

### 4.6 Tender & Project Management

**Tender State Machine:**
```
BIDDING → WON → PROCUREMENT → INSTALLATION → COMMISSIONING → INVOICED → CLOSED
       ↘ LOST
```

**Key Features:**
- Document vault per tender (PDF uploads with version control).
- Milestone tracker with payment tranches (e.g., "30% on delivery, 40% on installation").
- Each milestone has: expected_date, actual_date, payment_status, uploaded_proof.
- Visual Gantt-style progress view on the owner dashboard.

### 4.7 Expense & Fuel Reimbursement

- Technician snaps receipt photo → uploads via app → links to ticket.
- Moderator approves/rejects with notes.
- Approved expenses are aggregated per ticket for true cost-of-service calculation.
- Owner sees per-ticket P&L: invoice value vs. (parts cost + labor cost + expenses).

### 4.8 Client Read-Only Portal

- Separate login flow (client credentials).
- Scoped to their own asset data only (enforced at DB query level with client_id filter).
- Can view: DG set list, AMC expiry dates, last service date, open tickets, and download signed service reports (PDF generated server-side).

---

## 5. Edge Case & Anti-Abuse Strategy

### 5.1 Connectivity Abuse ("My internet was too slow")

This is a common loophole. The system handles it as follows:

| Scenario | System Response |
|---------|----------------|
| No network at site | PWA caches assigned tickets for offline use. Technician works offline; sync occurs automatically on reconnect. |
| Staff claims upload failed | Offline queue stores all actions in IndexedDB with retry logic (exponential backoff). If sync fails 3 times, the ticket is flagged for manual review by Moderator. |
| Photo upload deliberately skipped | Ticket cannot reach COMPLETED without required photos. App UI blocks the button; backend validates the same before accepting status change. |
| Staff forges GPS offline | GPS captured at punch-in time is stored in the offline queue payload. When synced, server validates the stored coordinates. If coordinates don't match site, the check-in is flagged, not rejected silently — Moderator sees it highlighted. |
| Part photo taken at office, not site | GPS coordinates are embedded in photo metadata server-side at capture time. App uses browser Geolocation API to tag images on upload. |

### 5.2 Selfie Bypass Attempts

| Attempt | Mitigation |
|---------|-----------|
| Hold a printed photo to camera | Basic liveness detection: require face movement (e.g., blink or slight head turn) before capture. |
| Use a phone screen with someone else's photo | Liveness detection + stored selfie comparison on server using face embeddings (lightweight ML model). |
| Send selfie from a different device | Selfie is paired with GPS data from the same session. Mismatch between device location and GPS triggers a flag. |

### 5.3 Attendance Manipulation

- If staff punch-in GPS is validated but Moderator does not approve within 4 hours, the attendance record is auto-flagged for owner review.
- Moderator cannot approve their own attendance (system enforces different approver).
- Attendance records are immutable once approved; only the Owner can amend with a mandatory reason note.

### 5.4 Inventory Bypass

- Parts cannot be "self-checked-out" by field staff. Only Moderator role can initiate checkout.
- QR/barcode scan is mandatory; manual entry of part serial numbers is not allowed.
- If a technician claims they returned a part but it wasn't scanned, the ticket stays open. There is no workaround that bypasses the return scan.

### 5.5 Race Conditions & Sync Conflicts

- All offline actions carry a `client_generated_uuid` and `local_timestamp`.
- On sync, server uses `last_write_wins` with the server timestamp, but logs both in the audit table.
- Conflicts (e.g., two moderators assign the same tech) are handled by optimistic locking (`version` field on critical records).

---

## 6. Data Model Overview

### Core Entities (Simplified)

```
users               → id, name, role, phone, email, hashed_password, is_active
sites               → id, name, gps_lat, gps_lng, client_id, address
dg_sets             → id, site_id, model, serial_no, install_date, last_service_date, amc_expiry
tickets             → id, dg_set_id, assigned_to[], status, created_by, created_at, ...
ticket_photos       → id, ticket_id, photo_type (BEFORE/AFTER/PART_NEW/PART_OLD), s3_url, gps_lat, gps_lng
attendance          → id, user_id, punch_in_time, punch_out_time, gps_in, gps_out, selfie_url, approved_by, status
inventory_items     → id, part_name, part_number, serial_no, status, current_ticket_id, quantity_in_stock
inventory_movements → id, item_id, from_status, to_status, ticket_id, actor_id, timestamp
tenders             → id, title, client_name, status, bid_amount, awarded_amount, ...
tender_milestones   → id, tender_id, name, due_date, completion_date, payment_pct, payment_status
expenses            → id, ticket_id, submitted_by, amount, receipt_url, status, approved_by
audit_log           → id, table_name, record_id, action, old_value, new_value, actor_id, timestamp
clients             → id, name, contact_person, email, portal_password_hash, ...
```

---

## 7. API Design Conventions

- **Versioned routes:** All routes prefixed `/api/v1/`.
- **Resource-oriented:** `GET /api/v1/tickets`, `POST /api/v1/tickets`, `PATCH /api/v1/tickets/{id}/status`.
- **Consistent error format:**
  ```json
  { "status": 422, "code": "VALIDATION_ERROR", "detail": [{"field": "gps_lat", "msg": "Required"}] }
  ```
- **Pagination:** All list endpoints return `{ items: [], total: 0, page: 1, size: 20 }`.
- **Soft deletes:** No records are hard-deleted. `is_deleted` flag + `deleted_at` + `deleted_by`.
- **File uploads:** Multipart form data to `/api/v1/uploads`; returns `{ s3_url, key }` for subsequent use.

---

## 8. Security Architecture

| Layer | Mechanism |
|-------|----------|
| Transport | HTTPS only (TLS 1.2+). HTTP redirected to HTTPS. |
| Auth | JWT (access: 15min, refresh: 7d in HttpOnly cookie). |
| RBAC | FastAPI Depends() middleware on every protected route. |
| Input Validation | Pydantic V2 on all request bodies. Regex on GPS, phone, email fields. |
| File Upload | MIME type validation server-side (not just extension). Max file size: 10MB. Virus scan via ClamAV or cloud equivalent. |
| SQL Injection | SQLAlchemy ORM with parameterized queries; no raw SQL strings. |
| Rate Limiting | SlowAPI (FastAPI rate limiter) on auth endpoints (5 req/min per IP). |
| CORS | Explicit allow-list of frontend domains only. |
| Secrets | All credentials in environment variables. No secrets in code. |
| Audit | Every write to critical tables logs to `audit_log` via SQLAlchemy event hooks. |

---

## 9. Mobile-First UI Strategy

### Design Principles
- **Touch-first:** All tap targets minimum 48×48px. No hover-only interactions.
- **Thumb-friendly layout:** Primary actions at the bottom of the screen (bottom nav bar).
- **Progressive disclosure:** Field technician view is stripped down to only what they need. Admin view is feature-rich.
- **Low-bandwidth optimization:** Images compressed before upload (client-side). Lazy-loaded lists. No heavy animations on data pages.

### PWA Offline Capabilities
- Service Worker caches the app shell (HTML, JS, CSS) indefinitely.
- On login, the technician's tickets for the current day are fetched and stored in IndexedDB.
- Offline sync queue: all actions (status updates, photo uploads, attendance) are queued in IndexedDB and synced in the background via Background Sync API.
- Visual indicator: banner shown when offline, queue size shown ("3 actions pending sync").

### Key Mobile Screens
1. **Technician Home:** Today's ticket list, punch-in button, sync status indicator.
2. **Ticket Detail:** Site map, DG set info, status update buttons, photo capture buttons.
3. **Attendance:** Selfie capture UI + GPS confirmation screen.
4. **Parts Consumption:** Barcode scanner + dual photo upload (installed + defective).
5. **Expense Submission:** Quick receipt photo + amount entry.

---

## 10. Deployment Architecture

```
                    ┌─────────────────────┐
                    │   GitHub Actions CI  │
                    └──────┬──────────────┘
                           │
          ┌────────────────┴─────────────────┐
          ▼                                  ▼
   ┌─────────────┐                  ┌───────────────┐
   │ Frontend    │                  │ Backend        │
   │ Vercel /    │                  │ AWS EC2 /      │
   │ Cloudflare  │                  │ Railway /      │
   │ Pages       │                  │ Render         │
   └─────────────┘                  └───────┬────────┘
                                            │
                         ┌──────────────────┼──────────────────┐
                         ▼                  ▼                  ▼
                  ┌─────────────┐  ┌───────────────┐  ┌──────────────┐
                  │ PostgreSQL  │  │ AWS S3        │  │ Redis        │
                  │ (RDS /      │  │ (File Storage)│  │ (Cache)      │
                  │  Supabase)  │  └───────────────┘  └──────────────┘
                  └─────────────┘
```

### Recommended Stack for Cost-Effective Start

| Service | Provider | Estimated Cost |
|---------|---------|---------------|
| Frontend hosting | Vercel (free tier) | ₹0 |
| Backend hosting | Railway / Render | ~₹800/month |
| PostgreSQL | Supabase (free tier → paid) | ₹0 → ₹400/month |
| File Storage | AWS S3 | ~₹200/month |
| Redis | Upstash (free tier) | ₹0 |
| Domain + SSL | Namecheap / Cloudflare | ~₹1,000/year |

---

## 11. Future Scope

### Phase 2 (6–12 months)
- **IoT Integration:** DG set running hour meters feeding data directly to the AMC module via MQTT.
- **SMS Notifications:** Twilio/AWS SNS for offline staff alerts (no app needed for basic notifications).
- **WhatsApp Bot:** Staff can update ticket status via WhatsApp message (using Twilio WhatsApp API).

### Phase 3 (12–24 months)
- **Agentic AI — Tender Parser:** LLM agent (Claude API) that ingests a 50-page government tender PDF and automatically extracts: DG set specifications, delivery milestones, penalty clauses, compliance requirements, and pre-fills the tender module.
- **Predictive Maintenance:** ML model trained on service history to predict next likely failure mode per DG set model.
- **Financial Intelligence:** AI-generated monthly report for owner: cost per service call, most profitable client, technician efficiency scores.

---

*Document Version 1.0 — Opsly by Rahul Electricals & Creative Solutions*