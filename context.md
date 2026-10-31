# Grid-Guard AI — Project Context

> **Reusable context file.** Paste this into any AI session to give it full project context instantly.
> Last updated: August 2026 | Author: Noor Eman | Version: 1.0

---

## 1. What Is This Project?

**Grid-Guard AI** is a Final Year Project (FYP) / portfolio project that uses Machine Learning (specifically XGBoost/Random Forest) to detect **electricity theft** in a power distribution system.

It has **three major components**:
1. **ML Pipeline** — trains the model offline on benchmark/synthetic data (SGCC/PRECON dataset), producing a `model.pkl` file.
2. **Backend REST API** — FastAPI (Python) service that loads the model, handles all business logic, stores state in PostgreSQL, and serves both clients.
3. **Web Admin Dashboard** — Next.js app for Revenue Protection Officers (RPOs) to triage flagged consumers, assign inspection cases, and view analytics.
4. **Mobile Field-Inspection App** — Flutter app for field inspectors (linemen) to receive assigned cases, conduct inspections, and submit results offline.

**Key concept:** Every risk flag must be **explainable** (using SHAP values translated to plain English). The system is audit-ready and designed for demo/portfolio purposes — it does NOT use live DISCO billing data.

---

## 2. Users / Personas

| Persona | Surface | What They Need |
|---|---|---|
| Revenue Protection Officer | Web Dashboard | Ranked list of at-risk consumers, SHAP explanations, case assignment |
| Field Inspector / Lineman | Mobile App | Assigned case queue, offline inspection form with photo + GPS |
| Circle Manager (v1.1) | Web Dashboard (read-only) | Aggregate performance stats across feeders |

---

## 3. Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| ML Inference | Python + scikit-learn/XGBoost + joblib | Matches training pipeline; loaded in-process in backend |
| Backend API | FastAPI (Python) | Same language as ML; easy async support; auto-generates OpenAPI docs |
| Database | PostgreSQL | Relational model fits case/consumer/inspection data; free tier on Render/Supabase |
| Object Storage | Cloudflare R2 (free tier, 10GB) | S3-compatible; for inspection photos |
| Web Frontend | Next.js (React) | Fast dashboard development; free deployment on Vercel |
| Mobile App | Flutter | Single codebase; strong offline/SQLite support via `sqflite` package |
| Mobile Local DB | SQLite (sqflite Flutter package) | Enables offline-first requirement (MOB-5) |
| Auth | JWT (JSON Web Tokens) | Stateless; works across both web and mobile clients |
| Web Hosting | Vercel (frontend) + Render (backend + PostgreSQL) | Free tier sufficient for portfolio traffic |
| Photo Hosting | Cloudflare R2 | S3-compatible; abstracted behind single upload function |

---

## 4. Database Schema (7 Tables)

### 4.1 `users`
```
id            UUID, PK
name          text
role          enum('officer', 'inspector', 'circle_manager')
email         text, unique  <- login identifier
password_hash text          <- bcrypt, NEVER plaintext
last_seen_at  timestamp, nullable  <- updated on every authenticated request (piggybacked on JWT verification, no separate heartbeat endpoint); drives the "active session" indicator on the Assign Case modal
created_at    timestamp
```
**Availability rule:** an inspector is considered "active" if `last_seen_at` is within the last 15 minutes (threshold defined in config, not hardcoded). This is presence-by-recent-activity, not a real-time session table — no websockets, no separate sessions table.

### 4.2 `consumers`
```
id            UUID, PK
external_ref  text          <- meter/consumer ID from source dataset
address       text
feeder        text          <- used for WEB-1 filtering and map (WEB-6)
tariff_class  text
meter_type    enum('Single Phase', 'Three Phase', 'CT-Metered')
latitude      float, nullable  <- populated once at seed/ingest time (see Feeder Map decision below)
longitude     float, nullable
is_demo_data  boolean, default true  <- drives "demo data" UI label
```

### 4.3 `risk_scores`
```
id               UUID, PK
consumer_id      UUID, FK -> consumers.id
score               float (0-1)
risk_band           enum('high', 'medium', 'low')
explanation_text_en text    <- plain-language SHAP explanation, English (precomputed)
explanation_text_ur text    <- plain-language SHAP explanation, Urdu (precomputed — see note below)
explanation_raw     jsonb   <- raw SHAP feature/value pairs (for debugging)
scored_at           timestamp
```

### 4.4 `cases`
```
id               UUID, PK
consumer_id      UUID, FK -> consumers.id
risk_score_id    UUID, FK -> risk_scores.id
assigned_by      UUID, FK -> users.id   <- officer who assigned
assigned_to      UUID, FK -> users.id   <- inspector
status           enum('assigned', 'in_progress', 'closed_confirmed',
                       'closed_false_positive', 'closed_inconclusive')
assignment_note  text (optional)
created_at       timestamp
updated_at       timestamp
```

### 4.5 `inspections`
```
id              UUID, PK
case_id         UUID, FK -> cases.id
inspector_id    UUID, FK -> users.id
outcome         enum('confirmed', 'false_positive', 'inconclusive')
tampering_type  text[]   <- checklist selections
note            text
photo_url       text     <- path/URL in object storage
gps_lat         float
gps_lng         float
submitted_at    timestamp  <- device-local time (may predate server receipt)
synced_at       timestamp, nullable  <- null while pending mobile sync
```

### 4.6 `consumption_history`
```
id            UUID, PK
consumer_id   UUID, FK -> consumers.id
period_start  date          <- first day of the billing month
kwh           float         <- billed/recorded consumption for that period
created_at    timestamp
```
Populated at data-ingest time from the source dataset (SGCC/PRECON), one row per consumer per billing month. This is the sole source for the Consumer Detail 12-month trend chart (WEB-2/WEB-3) — it is separate from `explanation_raw`, which holds SHAP debug values, not raw usage.

### 4.7 `audit_log` (append-only, never updated/deleted)
```
id            UUID, PK
actor_id      UUID, FK -> users.id, nullable  <- null = system event
action        text   <- e.g. 'flag_generated', 'case_assigned', 'inspection_submitted'
entity_type   text
entity_id     UUID
details       jsonb
created_at    timestamp
```

---

## 5. ML Output Schema (Contract Between ML & Backend)

The `score()` function in the ML wrapper **always** returns this fixed shape:
```json
{
  "consumer_id": "uuid",
  "score": 0.91,
  "risk_band": "high",
  "explanation_text_en": "Consumption dropped 60% in the last 3 months...",
  "explanation_text_ur": "پچھلے 3 مہینوں میں بجلی کے استعمال میں 60 فیصد کمی...",
  "explanation_raw": { "feature": "consumption_drop_3mo", "shap_value": 0.42 }
}
```
**How the Urdu text is generated:** not live machine translation. The `_generate_text()` step already builds the English sentence from a small set of templates keyed by the top SHAP feature (see `backend/app/ml/scorer.py`). Each template gets a hand-written Urdu counterpart in the same lookup table, so `_generate_text()` returns both strings from one dictionary lookup — deterministic, no translation-API dependency or cost, and it matches how the mobile wireframe already expects both languages pre-supplied (`c.expl.en` / `c.expl.ur`) rather than translated client-side.

**Risk band thresholds** (defined in one config module, never hardcoded):
- `score >= 0.7` -> **high**
- `score 0.4-0.69` -> **medium**
- `score < 0.4` -> **low**

---

## 6. REST API Endpoints

Base URL: `https://api.grid-guard.example/v1` (placeholder)
Auth: `Authorization: Bearer <JWT>` on all endpoints except `/auth/login`

| Method | Endpoint | Used By | Purpose |
|---|---|---|---|
| POST | `/auth/login` | Web, Mobile | Authenticate; returns JWT + user info |
| GET | `/consumers/risk-queue` | Web | Ranked, filterable list of at-risk consumers |
| GET | `/consumers/{id}/explanation` | Web, Mobile | Plain-language SHAP explanation (both `explanation_text_en` and `explanation_text_ur`) |
| GET | `/consumers/{id}/consumption-history` | Web | Monthly kWh series for the trend chart (from `consumption_history` table) |
| GET | `/users?role=inspector` | Web | List inspectors with a computed `available` flag (`last_seen_at` within 15 min) — backs the Assign Case modal |
| POST | `/cases` | Web | Create + assign a new case |
| GET | `/cases` | Web | All cases (filterable by status/feeder) |
| GET | `/cases/mine` | Mobile | Inspector's own assigned cases |
| GET | `/cases/{id}` | Web, Mobile | Full case detail with embedded explanation |
| GET | `/cases/{id}/audit-log` | Web | Case state-change history |
| POST | `/cases/{id}/inspection` | Mobile | Submit inspection outcome + photo + GPS |
| GET | `/model-performance` | Web | Confirmed/FP/inconclusive rates over time |

**Conventions:**
- All bodies are JSON (except photo upload = `multipart/form-data`)
- All timestamps are ISO 8601 UTC
- Pagination via `?page=&page_size=` (default `page_size=25`)
- Standard error shape: `{ "error": { "code": "NOT_FOUND", "message": "..." } }`

---

## 7. Repository Structure

```
grid-guard-ai/                    <- monorepo root
|-- backend/
|   |-- app/
|   |   |-- models/               <- SQLAlchemy ORM models
|   |   |-- routers/              <- one file per resource (consumers, cases, inspections, auth)
|   |   |-- schemas/              <- Pydantic request/response schemas
|   |   |-- services/             <- business logic layer
|   |   |-- ml/                   <- model loading + scoring wrapper
|   |   |-- auth/                 <- JWT issuing/verification
|   |   `-- main.py               <- FastAPI app entry point
|   |-- ml-artifact/
|   |   `-- model.pkl             <- trained model from ML pipeline
|   `-- requirements.txt
|-- web/                          <- Next.js app
|   `-- src/
|       |-- pages/                <- one file per screen
|       `-- components/
|-- mobile/                       <- Flutter app
|   `-- lib/
|       |-- screens/
|       |-- local_db/             <- sqflite schema + offline sync queue
|       `-- api/                  <- API client
`-- docs/                         <- PRD, Architecture, Technical Design, API Spec, UI/UX Flow
```

---

## 8. Web Dashboard Screens

| Screen | PRD Req | Purpose |
|---|---|---|
| Login | WEB-8 | Auth for officer/circle manager |
| Risk Queue | WEB-1, WEB-2 | Ranked, filterable flagged consumer list (landing screen) |
| Consumer Detail | WEB-2, WEB-3 | SHAP explanation + "Assign Case" action |
| Assign Case (modal) | WEB-3 | Pick inspector + optional note |
| Case List | WEB-4 | All cases with status tracking |
| Case Detail (read-only) | WEB-4, WEB-5 | Full case record including outcome once closed |
| Feeder Map | WEB-6 | Geographic heatmap of flagged consumers |
| Model Performance Panel | WEB-7 | Confirmed-theft rate trends over time |
| Audit Log | WEB-5 | Immutable case history, reached from Case Detail |

---

## 9. Mobile App Screens

| Screen | PRD Req | Purpose |
|---|---|---|
| Login | - | Auth for inspector; session persists across restarts |
| My Cases | MOB-1 | Inspector's assigned case queue (works offline from cache) |
| Case Detail | MOB-2 | Address, meter ID, plain-language risk reason, assignment note |
| Inspection Form | MOB-3, MOB-4 | Outcome selector + tampering checklist + photo + GPS; writes locally first |
| Sync Status / History | MOB-7, MOB-8 | Pending vs synced submissions; manual retry |

---

## 10. Key Architecture Decisions

| Decision | What was decided | Why |
|---|---|---|
| Thin-client architecture | All scoring/business logic in backend only | Both clients always see consistent state |
| ML loaded in-process | model.pkl loaded directly in FastAPI, not a separate service | No cross-language serialization needed at this scale |
| Offline-first mobile | Local SQLite write first, background sync later | Inspectors often work with no connectivity |
| Monorepo | All three components in one repo | Solo builder - no multi-team versioning overhead |
| No message queue | Direct DB writes | Demo-scale write volume doesn't need it |
| No push notifications | In-app queue refresh only | Would require persistent FCM service; deferred to v2 |
| No automated retraining | Feedback data captured but retraining is manual/offline | v2 feature; ML pipeline is separate |
| JWT auth | Stateless tokens with role in claims | Works across web and mobile; no server-side sessions |

---

## 11. Security Rules

- **Auth:** bcrypt password hashing; JWT signed with secret key; expiry 7 days (mobile), shorter (web)
- **Authorization:** Role checked from JWT claims; inspector can only access their own cases
- **PII:** Only meter/consumer ID and address stored - no name, CNIC, phone
- **Photos/GPS:** Linked to a case only; never exposed via unauthenticated URL
- **Transport:** All traffic over HTTPS; no credentials in logs
- **Secrets:** All via environment variables; `.env.example` in repo, never real `.env`

---

## 12. Functional Requirements Summary

### Web (MoSCoW)
| ID | Requirement | Priority |
|---|---|---|
| WEB-1 | Ranked, filterable risk queue (feeder, tariff class, meter type, risk band) | Must |
| WEB-2 | SHAP-based plain-language explanation panel | Must |
| WEB-3 | Assign case to inspector with optional note | Must |
| WEB-4 | Case list with status tracking | Must |
| WEB-5 | Append-only audit trail with timestamp + actor | Must |
| WEB-6 | Feeder-level map / heatmap | Should |
| WEB-7 | Model performance panel (confirmed% vs FP% trend) | Should |
| WEB-8 | Auth with role separation (officer vs circle manager) | Should |
| WEB-9 | CSV export of filtered case list | Could |
| WEB-10 | Multi-DISCO/multi-tenant | Won't (v1) |

### Mobile (MoSCoW)
| ID | Requirement | Priority |
|---|---|---|
| MOB-1 | Assigned-case queue sorted by priority | Must |
| MOB-2 | Address, meter ID, plain-language risk reason per case | Must |
| MOB-3 | Inspection form (outcome selector, tampering checklist, free-text note) | Must |
| MOB-4 | Photo + auto-GPS at inspection time | Must |
| MOB-5 | Full offline functionality with sync-on-reconnect | Must |
| MOB-6 | English + Urdu UI text | Should |
| MOB-7 | Sync-status indicator per case | Should |
| MOB-8 | Inspector's closed-case history | Could |
| MOB-9 | Push notifications for new assignments | Won't (v1) |

---

## 13. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Explainability | Every risk flag must have a human-readable reason - no bare probability score |
| Offline resilience | Mobile core functions work with zero connectivity |
| Auditability | Every state change logged with timestamp + actor; logs never editable |
| Data honesty | UI always labels data as "demo/benchmark data" - never claims live DISCO accuracy |
| Performance | Web risk-queue loads < 3 seconds for up to 10,000 consumers on broadband |
| Language | Mobile UI available in both English and Urdu |
| Security | Authenticated access only; minimal PII; no plaintext secrets |

---

## 14. Release Phases

| Phase | Scope |
|---|---|
| **MVP** | Backend API + ML inference service + Web: Risk Queue, Consumer Detail, Case List (WEB-1-WEB-4) |
| **V1** | Web: Audit Log, Feeder Map, Model Performance (WEB-5-WEB-7) + Mobile: My Cases, Case Detail, Inspection Form, offline (MOB-1-MOB-5) |
| **V1.1 / stretch** | Auth roles (WEB-8), Urdu localization (MOB-6), sync-status polish (MOB-7), CSV export (WEB-9) |

---

## 15. Deployment Topology

```
Internet
  |-- Vercel          <- Web Dashboard (Next.js, static + SSR)
  |       |
  |       v HTTPS
  |-- Render          <- Backend API (FastAPI container)
  |       |
  |       |---> Render PostgreSQL (managed DB, free tier)
  |       `---> Cloudflare R2 (photo storage, 10GB free)
  |
  `-- Mobile APK      <- Distributed as APK/TestFlight for demo
       (talks to the same Render backend over HTTPS)
```

---

## 16. What This Is NOT (Scope Boundaries)

- No live DISCO billing system integration - uses public/synthetic benchmark data
- No multi-tenant / multi-DISCO support (v1 = single org)
- No payment, billing correction, or legal case management
- No real-time AMI streaming - batch/periodic data loads only
- No push notifications (v1) - uses in-app refresh
- No automated model retraining - manual offline process
- No microservices - single deployable backend service
- No SMS/USSD channel for low-end phones (v2 consideration)

---

*This context file is derived from: PRD v1.0, Architecture Document v1.0, Technical Design Document v1.0, API Specification v1.0, and UI/UX Flow Specification v1.0 - all authored by Noor Eman, August 2026.*
