# THOZHI — Phase 2.0: Stage 1 Baseline Authentication & Authorization Audit

**Document:** `docs/architecture/30_PHASE_2_0_AUTHENTICATION_BASELINE_AUDIT.md`
**Date:** 2026-11-08
**Author:** Backend Security Engineer & System Architect
**Status:** COMPLETE — Stage 1 Approved Baseline

---

## 1. Executive Summary

This audit assesses the authentication, authorization, and tenant isolation posture of the THOZHI system prior to Phase 2.0 implementation.

### Critical Findings:
1. **Zero Endpoint Authentication:** None of the 39 user-facing API endpoints require an `Authorization` header or cryptographically verify identity.
2. **Hardcoded Identity Fallback:** All task, plan, proposal approval, user profile, and memory operations default to a fixed UUID: `00000000-0000-0000-0000-000000000001` (`store.default_user_id`).
3. **Identity Spoofing Vulnerability:** Endpoints in `/api/v1/captures` accept untrusted `user_id` values from HTTP query parameters, form data, and JSON bodies.
4. **Unscoped Cross-Tenant Modification:** Critical endpoints (including `GET /api/v1/proposals/{proposal_id}`, `POST /api/v1/proposals/{proposal_id}/reject`, `POST /api/v1/proposals/{proposal_id}/clarify`, `PATCH /api/v1/proposals/{proposal_id}/items/{item_id}`) do not inspect or verify user ownership.
5. **Database RLS Bypass in API Layer:** `SupabaseRepository` calls `SupabaseClient` without propagating a user JWT, defaulting to `SUPABASE_KEY` (`service_role`), effectively bypassing Row Level Security in the PostgreSQL database.
6. **Frontend Complete Absence of Auth:** `frontend/src/lib/api.ts` dispatches plain `fetch` requests with no bearer tokens, and no auth state or session manager exists in the frontend tree.

---

## 2. API Endpoint Inventory and Classification

Total endpoints audited across `backend/app/main.py` and `backend/app/routers/`: **41 endpoints**.

| Category | Endpoint Count | Description |
| :--- | :--- | :--- |
| **Public** | 2 (+docs) | Health checks, root system metadata, OpenAPI schema. |
| **User-Authenticated (Protected)** | 39 | Endpoints requiring cryptographic user identity derivation. |
| **Internal / Admin** | 0 | (No administrative endpoints currently defined). |

### Detailed Router Audit Catalog

#### 2.1 Root & System Endpoints (`backend/app/main.py`)
- `GET /` — **Public**. Returns system welcome and links to `/docs` and `/health`.
- `GET /health` — **Public**. Returns service health, ASR/NLU configuration, and database connectivity.
- `GET /docs`, `GET /redoc`, `GET /openapi.json` — **Public**. OpenAPI documentation.

#### 2.2 Captures Router (`backend/app/routers/captures.py`)
- `POST /api/v1/captures/audio`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts untrusted `user_id: Optional[UUID] = Form(None)`. If omitted, passes `None` to store.
  - **Risk:** High (Caller can forge capture ownership or inject audio into arbitrary tenant).
- `POST /api/v1/captures/text`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts untrusted `user_id: Optional[UUID] = None` in JSON body.
  - **Risk:** High (Identity spoofing via JSON payload).
- `GET /api/v1/captures`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts untrusted `user_id: Optional[UUID] = Query(None)`.
  - **Risk:** High (Tenant data enumeration).
- `GET /api/v1/captures/{capture_id}`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts optional query parameter `user_id: Optional[UUID] = None`.
  - **Risk:** High (Direct object reference without tenant verification).
- `DELETE /api/v1/captures/{capture_id}`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts optional query parameter `user_id: Optional[UUID] = None`.
  - **Risk:** High (Unauthorized data deletion).
- `POST /api/v1/captures/clear`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Calls `store.clear_captures()` without user identity.
  - **Risk:** Critical (Any anonymous caller can wipe captures globally).

#### 2.3 Proposals & Approvals Router (`backend/app/routers/proposals.py`)
- `GET /api/v1/proposals`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Accepts untrusted query param `user_id: Optional[UUID] = None`.
  - **Risk:** High (Unauthorized queue surveillance).
- `POST /api/v1/proposals/batch/approve`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Hardcoded `store.default_user_id`.
  - **Risk:** High (Cross-tenant task generation under default user).
- `POST /api/v1/proposals/batch/reject`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Hardcoded `store.default_user_id`.
  - **Risk:** High.
- `GET /api/v1/proposals/{proposal_id}`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Unscoped. Calls `store.get_proposal(proposal_id)`.
  - **Risk:** High (Cross-tenant proposal inspection).
- `POST /api/v1/proposals/{proposal_id}/reject`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Unscoped.
  - **Risk:** High (Unauthorized cancellation of another user's proposal).
- `POST /api/v1/proposals/{proposal_id}/translate`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Unscoped.
  - **Risk:** Medium.
- `PATCH /api/v1/proposals/{proposal_id}/items/{item_id}`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Unscoped.
  - **Risk:** High (Tampering with proposal items before approval).
- `POST /api/v1/proposals/{proposal_id}/clarify`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Unscoped.
  - **Risk:** High (Injecting unauthorized clarification answers).
- `POST /api/v1/proposals/{proposal_id}/approve`
  - **Classification:** User-Authenticated.
  - **Current Auth:** None.
  - **Current User Resolution:** Hardcoded `store.default_user_id`.
  - **Risk:** High (Tasks committed under static default user regardless of proposal origin).

#### 2.4 Tasks Router (`backend/app/routers/tasks.py`)
All 9 endpoints (`GET /`, `POST /`, `GET /{task_id}`, `PATCH /{task_id}`, `DELETE /{task_id}`, `POST /{task_id}/complete`, `POST /{task_id}/reopen`, `POST /{task_id}/dependencies/{...}`, `DELETE /{task_id}/dependencies/{...}`) are **User-Authenticated**.
- **Current Auth:** None.
- **Current User Resolution:** Every handler hardcodes `user_id = store.default_user_id`.
- **Risk:** High (All clients share the exact same user identity; zero multi-tenant separation).

#### 2.5 Planning & Capacity Router (`backend/app/routers/plans.py`)
All 4 endpoints (`POST /generate`, `GET /today`, `GET /date/{target_date}`, `POST /reschedule/apply`) are **User-Authenticated**.
- **Current Auth:** None.
- **Current User Resolution:** Hardcoded `user_id = store.default_user_id`.
- **Risk:** High (Daily schedules and calendar availability computed only for the static default tenant).

#### 2.6 Personalization & Memory Router (`backend/app/routers/memory.py`)
All 9 endpoints (`GET /preferences`, `POST /preferences`, `GET /preferences/{pref_id}`, `PATCH /preferences/{pref_id}`, `DELETE /preferences/{identifier}`, `POST /preferences/{pref_id}/toggle`, `GET /duration-priors/suggestions`, `POST /export`, `DELETE /purge`) are **User-Authenticated**.
- **Current Auth:** None.
- **Current User Resolution:** Hardcoded `user_id = store.default_user_id`.
- **Risk:** Critical (An anonymous caller invoking `DELETE /api/v1/memory/purge` immediately destroys all data for the default tenant).

#### 2.7 User Profile Router (`backend/app/routers/users.py`)
Both endpoints (`GET /me`, `PATCH /me`) are **User-Authenticated**.
- **Current Auth:** None.
- **Current User Resolution:** Hardcoded `store.default_user_id`.
- **Risk:** High (Anonymous callers can read and overwrite profile settings for the default user).

---

## 3. Frontend Request Layer Audit (`frontend/src/`)

1. **API Client (`frontend/src/lib/api.ts`):**
   - 22 exported functions executing `fetch()` requests against `API_BASE`.
   - Headers defined across requests include only `"Content-Type": "application/json"`.
   - **Zero** `Authorization` headers are sent.
   - `listCaptures(userId?: string)` explicitly appends `userId` to the URL query string if passed.
2. **State Management & Contexts:**
   - `frontend/src/store`: Uses Zustand for client-side task/filter UI state.
   - `frontend/src/context`: Contains only `ThemeContext.tsx`.
   - **No session token, auth context, or auth store exists.**
3. **Hardcoded User References:**
   - Frontend components do not store user UUIDs, relying entirely on the backend to assume `store.default_user_id`.
   - The unlinked sovereign memory features (`exportPersonalData`, `purgeAllPersonalData`) communicate directly without tenant authorization.

---

## 4. Repository and Database Persistence Layer Audit

1. **Repository Abstraction (`BaseRepository`):**
   - Defines class attribute `default_user_id = UUID("00000000-0000-0000-0000-000000000001")`.
   - Several method signatures treat `user_id` as `Optional[UUID] = None`.
2. **`SupabaseClient` (`backend/app/db/supabase_client.py`):**
   - Method `_get_headers(user_token=...)` correctly allows supplying an authenticated user's JWT (`auth_bearer = user_token if user_token else self.api_key`).
   - However, `SupabaseRepository` never passes `user_token`.
3. **RLS Interaction:**
   - In PostgreSQL, RLS policies require `auth.uid() = user_id`.
   - Because `SupabaseRepository` uses `self.api_key` (`service_role`), all queries currently run with superuser-like permissions, bypassing PostgreSQL RLS entirely.
   - In order for PostgreSQL RLS to protect tenant boundaries, `SupabaseClient` MUST receive the authenticated user's JWT so PostgREST executes queries with role `authenticated` and `auth.uid() = <user_uuid>`.

---

## 5. Audit Conclusions & Remediation Imperatives

| Vulnerability ID | Vulnerability Description | Remediation Required in Phase 2.0 |
| :--- | :--- | :--- |
| **VULN-AUTH-01** | Missing JWT Authentication across all endpoints. | Implement FastAPI security dependency (`get_current_user`) enforcing valid Bearer JWT. |
| **VULN-AUTH-02** | User identity spoofing via query/body/form parameter. | Strip untrusted `user_id` parameters; derive identity strictly from cryptographically verified JWT `sub` claim. |
| **VULN-AUTH-03** | Hardcoded `default_user_id` across router handlers. | Inject verified `current_user.id` into all repository calls. |
| **VULN-AUTH-04** | Unscoped proposal endpoints (`/{proposal_id}`). | Ensure proposal retrieval, rejection, items patching, and clarification verify ownership against `current_user.id`. |
| **VULN-AUTH-05** | Service-role key RLS bypass in `SupabaseRepository`. | Propagate authenticated user JWT to `SupabaseClient` for tenant-scoped queries. |
| **VULN-AUTH-06** | Frontend lacks token management & interceptor. | Implement session storage and automatic `Authorization: Bearer <token>` injection in `frontend/src/lib/api.ts`. |

**Baseline Audit Verdict:** AUDIT COMPLETE — Full vulnerability landscape mapped. Ready to proceed to Stage 2 (Architecture Specification).
