# 04 — Backend, Database & API Report

## 1. API Architecture & Routing
The backend exposes RESTful endpoints using **FastAPI** with structured **RFC 7807 Problem Details** for error recovery.

| Router | Path Prefix | Operations | Verification Status |
| :--- | :--- | :--- | :---: |
| **Captures** | `/api/v1/captures` | `POST /text`, `POST /audio` | **PASS (FIXED)** |
| **Proposals** | `/api/v1/proposals` | `GET /{id}`, `PATCH /{id}/items/{item_id}`, `POST /{id}/clarify`, `POST /{id}/approve` | **PASS** |
| **Tasks** | `/api/v1/tasks` | `GET /`, `POST /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` | **PASS** |
| **Planning** | `/api/v1/planning` | `POST /schedule`, `POST /reschedule` | **PASS** |
| **Memory** | `/api/v1/memory` | `GET /preferences`, `POST /preferences`, `DELETE /preferences/{id}`, `GET /export`, `DELETE /purge` | **PASS** |
| **System** | `/health`, `/` | Diagnostic metadata & welcome routes | **PASS** |

---

## 2. Security & Tenant Isolation Audit
- **Multi-Tenant Boundary:** Verified User A cannot access or mutate User B's records (`test_tenant_data_isolation_audit`).
- **Sovereign Purge (Right to be Forgotten):** Verified `DELETE /api/v1/memory/purge` completely deletes active tasks, proposals, and preferences (`test_sovereign_privacy_purge_audit`).
- **Zero Raw Audio Retention:** Confirmed audio streams are held exclusively in RAM (`io.BytesIO`) during ASR and discarded immediately upon response generation.
- **Input Validation:** Empty text payloads return HTTP 422; zero-byte audio returns HTTP 400; malformed UUID path parameters return HTTP 422 with RFC 7807 problem details.
- **Idempotency Protection:** Proposal approvals enforce client-generated idempotency keys preventing replay duplication.

---

## 3. Database Schema & RLS
- **Migrations:** 14 relational tables defined in `supabase/migrations/001_initial_schema.sql`.
- **Row-Level Security:** Applied in `002_rls_policies.sql` ensuring tenant isolation at database engine level.
