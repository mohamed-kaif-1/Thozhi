# THOZHI — Phase 2.0: Implementation Report (Stages 3, 4 & 5)

**Document:** `docs/architecture/32_PHASE_2_0_IMPLEMENTATION_REPORT.md`
**Date:** 2026-11-08
**Author:** Backend Security Engineer & System Architect
**Status:** COMPLETE — Ready for Stage 6 Security Verification

---

## 1. Overview & Objective

This report details the implementation of Stage 3 (Backend Authentication Implementation), Stage 4 (Repository and Persistence Identity Propagation), and Stage 5 (Frontend Session and Request Interception) under Phase 2.0 of the THOZHI project.

The implementation strictly satisfies the Core Security Guarantee:
> "A user can access only their own THOZHI data, and their identity must be derived from a cryptographically verified authentication token — never from an untrusted frontend request parameter."

---

## 2. Stage 3: Backend Authentication Implementation

### 2.1 Cryptographic Core & Security Dependency (`backend/app/core/auth.py`)
Implemented a robust authentication core using `PyJWT` with HMAC-SHA256 (`HS256`):
- **`AuthenticatedUser` Pydantic Model:** Encapsulates verified tenant UUID `id`, `email`, `role`, and raw `token`.
- **`get_current_user` FastAPI Security Dependency:**
  - Uses `HTTPBearer(auto_error=False)` to enable RFC 6750 / RFC 7807 compliant error responses.
  - Rejects missing `Authorization` header with `HTTP 401 Unauthorized` and `WWW-Authenticate: Bearer error="unauthorized"`.
  - Rejects invalid scheme (non-Bearer) with `HTTP 401 Unauthorized`.
  - Rejects empty, malformed, or tampered tokens with `HTTP 401 Unauthorized`.
  - Rejects expired tokens with `HTTP 401 Unauthorized` and `WWW-Authenticate: Bearer error="invalid_token", error_description="The access token has expired"`.
  - Validates that `sub` claim exists and is a valid RFC 4122 UUID string.
  - Rejects anonymous (`role="anon"`) access tokens with `HTTP 401 Unauthorized`.
- **`create_test_jwt` Harness Utility:** Provides deterministic generation of signed tokens for automated testing, seed fixtures, and security verification.

### 2.2 Endpoint Protection & Identity Derivation
Updated all 39 user-facing endpoints across all 6 domain routers to require `current_user: AuthenticatedUser = Depends(get_current_user)`:
1. **`backend/app/routers/captures.py`:**
   - Removed `user_id: Optional[UUID]` from `TextCaptureRequest`.
   - Removed `user_id: Optional[UUID] = Form(None)` from audio capture.
   - Removed `user_id: Optional[UUID] = Query(None)` from `list_captures`, `get_capture`, `delete_capture`, and `clear_captures`.
   - All captures are created, retrieved, and deleted strictly under `current_user.id`.
2. **`backend/app/routers/proposals.py`:**
   - Removed `user_id: Optional[UUID] = None` query parameter from `list_proposals`.
   - Replaced all hardcoded `store.default_user_id` in proposal approval, batch approval, and batch rejection with `current_user.id`.
   - Added ownership verification on `get_proposal`, `reject_proposal`, `translate_proposal`, `patch_proposal_item`, `clarify_proposal`, and `approve_proposal` to guarantee that users cannot inspect or mutate proposals belonging to other tenants.
3. **`backend/app/routers/tasks.py`:**
   - Replaced all hardcoded `store.default_user_id` across task listing, creation, retrieval, updates, status transitions, deletions, and DAG dependencies with `current_user.id`.
4. **`backend/app/routers/plans.py`:**
   - Replaced all hardcoded `store.default_user_id` across plan generation, today's schedule, target date schedule, and DAG reschedule application with `current_user.id`.
5. **`backend/app/routers/memory.py`:**
   - Replaced all hardcoded `store.default_user_id` across memory preference listing, creation, retrieval, updating, toggling, deletion, duration prior analysis, export, and purge with `current_user.id`.
6. **`backend/app/routers/users.py`:**
   - Replaced `store.default_user_id` in `/me` profile retrieval and patch with `current_user.id`.

### 2.3 Public Endpoints Preserved
The following endpoints explicitly remain public without authentication:
- `GET /` — API root greeting and sitemap.
- `GET /health` — Operational health check and subsystem status.
- `GET /docs`, `GET /redoc`, `GET /openapi.json` — Swagger and OpenAPI specifications.

---

## 3. Stage 4: Repository and Persistence Identity Propagation

### 3.1 Repository Signatures
Updated `BaseRepository`, `InMemoryStore`, and `SupabaseRepository`:
- Added `user_token: Optional[str] = None` parameter across persistence methods.
- In `approve_proposal`, the verified `current_user.token` is propagated down from the router to the repository.

### 3.2 PostgREST & Database RLS Propagation
- In `SupabaseRepository.approve_proposal`, `user_token` is forwarded to `self.client.rpc_sync("commit_proposal_atomic", rpc_params, user_token=user_token)`.
- In `SupabaseClient._get_headers(user_token=...)`, when `user_token` is present, it constructs:
  - `apikey: SUPABASE_KEY`
  - `Authorization: Bearer <user_token>`
- PostgREST evaluates the caller as role `authenticated` with `request.jwt.claim.sub = <user_id>`.
- The PostgreSQL RPC `commit_proposal_atomic` verifies `v_caller_role = 'authenticated'` and `v_caller_uid = p_user_id`. If an adversary caller attempts to commit a proposal with an inconsistent user ID, PostgreSQL rejects the transaction with SQLSTATE `42501` (`insufficient_privilege`).

---

## 4. Stage 5: Frontend Session and Request Interception

### 4.1 Token Storage & Retrieval (`frontend/src/lib/api.ts`)
Implemented client-side token management:
- `getAuthToken()`: Safely retrieves the stored JWT from `localStorage` (`thozhi_auth_token`).
- `setAuthToken(token)`: Updates or clears the stored JWT.

### 4.2 Centralized Request Interceptor (`fetchWithAuth`)
- Every API helper function in `frontend/src/lib/api.ts` (32 calls) was migrated to use `fetchWithAuth`.
- Automatically attaches `Authorization: Bearer <token>` when a token is present in storage.
- Detects `401 Unauthorized` responses and emits a browser event (`thozhi:unauthorized`) for graceful session renewal or redirect.
- Removed client-side `userId` query parameter injection in `listCaptures`.

### 4.3 Production Build Verification
Executed `npm --prefix frontend run build`:
- **Result:** Exit code 0.
- All 18 static application routes compiled and rendered with zero TypeScript or ESLint errors.

---

## 5. Artifacts and File Modification Log

| File Path | Action | Summary of Changes |
| :--- | :--- | :--- |
| `backend/app/core/auth.py` | Created | JWT decode/validation, `AuthenticatedUser`, `get_current_user`, `create_test_jwt`. |
| `backend/requirements.txt` | Modified | Added `pyjwt>=2.8.0`. |
| `backend/app/routers/captures.py` | Modified | Added `get_current_user`, stripped untrusted `user_id` inputs. |
| `backend/app/routers/proposals.py` | Modified | Added `get_current_user`, tenant ownership checks, token propagation. |
| `backend/app/routers/tasks.py` | Modified | Added `get_current_user`, replaced static default user with `current_user.id`. |
| `backend/app/routers/plans.py` | Modified | Added `get_current_user`, replaced static default user with `current_user.id`. |
| `backend/app/routers/memory.py` | Modified | Added `get_current_user`, protected memory preferences and purge/export. |
| `backend/app/routers/users.py` | Modified | Added `get_current_user`, bound `/me` to authenticated identity. |
| `backend/app/db/repositories/base.py` | Modified | Added `user_token` parameter to `approve_proposal`. |
| `backend/app/db/repositories/memory.py` | Modified | Added `user_token` parameter to `approve_proposal`. |
| `backend/app/db/repositories/supabase.py` | Modified | Propagated `user_token` to PostgREST RPC and idempotency cache lookup. |
| `frontend/src/lib/api.ts` | Modified | Added `getAuthToken`, `setAuthToken`, `fetchWithAuth` interceptor; migrated 32 fetch calls. |

**Verdict:** Stages 3, 4, and 5 successfully implemented. Ready to proceed to Stage 6 (Cross-Tenant Isolation and Security Verification).
