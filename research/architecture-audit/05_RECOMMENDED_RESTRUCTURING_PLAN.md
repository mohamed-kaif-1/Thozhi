# THOZHI — Recommended Repository Restructuring & Cleanup Plan

## 1. Executive Summary

This plan provides an actionable, four-phase roadmap for bringing the THOZHI repository into an optimal architectural state.

In strict adherence to the project audit rules:
- **Phase 1 (Safe Immediate Cleanup):** Fixes verified bugs, dead code, missing packaging files, and documentation defects without touching public API contracts or breaking existing functionality.
- **Phase 2 (Database Alignment Migration):** Creates a non-destructive SQL migration (`003_schema_alignment.sql`) to resolve critical PostgreSQL DDL drift.
- **Phase 3 (Service Layer & Repository De-monolithization):** Decomposes `repository.py` and extracts router orchestration into services (requires user approval).
- **Phase 4 (Secondary Routes & Persistence Mode):** Integrates `/calendar` with the real plan and connects Supabase dual-mode persistence.

---

## 2. Master Findings & Action Matrix

| Issue ID | Severity | Category | File Path | Proposed Action | Phase |
|---|:---:|---|---|---|:---:|
| **RS-01** | **P0** | Git Hygiene | `README.md` | Remove unresolved merge conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`). | **Phase 1** |
| **DB-01** | **P0** | Database | `supabase/migrations/` | Create `003_schema_alignment.sql` to add `proposal_status_enum` values (`PENDING_REVIEW`, `COMMITTED`, `REJECTED`, etc.). | **Phase 2** |
| **DB-02** | **P0** | Database | `supabase/migrations/` | Add missing columns to `captures`, `proposals`, `proposal_items`, `users`, and `memory_preferences`. | **Phase 2** |
| **BA-01** | **P1** | Packaging | `backend/app/` | Create missing `__init__.py` files across 7 subpackages. | **Phase 1** |
| **BA-02** | **P1** | Architecture | `backend/app/db/` | Design dual-mode repository (InMemory / Supabase) to connect `supabase_client.py`. | **Phase 3** |
| **FA-01** | **P1** | Dead Code | `frontend/src/components/layout/Navbar.tsx` | Delete unused `Navbar.tsx` component. | **Phase 1** |
| **FA-02** | **P1** | UX Architecture | `frontend/src/app/calendar/page.tsx` | Wire `/calendar` to real `getPlanForDate()` API instead of static mock events. | **Phase 4** |
| **TD-01** | **P1** | CI / Automation | `.github/workflows/ci.yml` | Add `master` branch to GitHub Actions CI triggers. | **Phase 1** |
| **TD-02** | **P1** | CI / Automation | `.github/workflows/ci.yml` | Switch CI pip install to `pip install -r backend/requirements.txt`. | **Phase 1** |
| **RS-02** | **P2** | Git Hygiene | `research/stage-1.zip` | Remove redundant tracked binary zip archive. | **Phase 1** |
| **RS-03** | **P2** | Asset Hygiene | `frontend/public/` | Deduplicate public brand icons and point manifest to canonical assets. | **Phase 1** |
| **BA-03** | **P2** | Architecture | `backend/app/routers/captures.py` | Extract NLU fallback & language preference logic into service layer. | **Phase 3** |
| **BA-04** | **P2** | Architecture | `backend/app/db/repository.py` | Decompose monolithic 1,156-line `repository.py` into domain repositories. | **Phase 3** |
| **BA-05** | **P2** | Dependencies | `backend/requirements.txt` | Add `av>=11.0.0` for in-memory audio normalization. | **Phase 1** |
| **FA-03** | **P2** | Dependencies | `frontend/package.json` | Remove unused packages (`@tanstack/react-query`, `class-variance-authority`). | **Phase 1** |
| **FA-05** | **P2** | Type Safety | `frontend/src/types/index.ts` | Normalize enum types (`AUDIO` vs `VOICE`, remove legacy lowercase status). | **Phase 1** |
| **FA-04** | **P3** | Code Structure | `frontend/src/lib/useUserProfile.ts` | Relocate custom React hook to `frontend/src/hooks/useUserProfile.ts`. | **Phase 1** |
| **RS-05** | **P3** | Documentation | `README.md` & `Stages.md` | Update test pass metrics from 65 to actual 125/125 passed tests. | **Phase 1** |

---

## 3. Phased Implementation Roadmap

### Phase 1: Safe Immediate Cleanup (Zero Functional Risk)
*Can be implemented immediately without breaking APIs, databases, or existing behavior:*
1. **Resolve `README.md` merge conflict:** Eliminate `<<<<<<< HEAD`, `=======`, `>>>>>>> origin/main` markers and update test badge to **125 passed**.
2. **Add missing `__init__.py` files:** Add clean empty `__init__.py` in `backend/app/core/`, `backend/app/schemas/`, `backend/app/providers/`, `backend/app/providers/asr/`, `backend/app/providers/nlu/`, `backend/app/modules/`, and `backend/app/modules/planning/`.
3. **Delete unused `Navbar.tsx`:** Remove `frontend/src/components/layout/Navbar.tsx`.
4. **Fix GitHub Actions CI:** Update `.github/workflows/ci.yml` to trigger on `master` and install from `requirements.txt`.
5. **Add `av` to `requirements.txt`:** Ensure PyAV is installed for in-memory audio transcoding.
6. **Remove `research/stage-1.zip`:** Remove redundant tracked binary zip.
7. **Clean `frontend/package.json`:** Remove unimported `@tanstack/react-query` and `class-variance-authority`.
8. **Relocate `useUserProfile.ts`:** Move to `frontend/src/hooks/useUserProfile.ts` with backward-compatible re-export in `lib/`.
9. **Normalize frontend types:** Align `CaptureRecord.input_type` with `"AUDIO" | "TEXT"` in `frontend/src/types/index.ts`.

---

### Phase 2: Database Alignment Migration (`003_schema_alignment.sql`)
*Requires user review of SQL DDL:*
1. Author `supabase/migrations/003_schema_alignment.sql`:
   - Expand `proposal_status_enum` or transition to validated `VARCHAR(64)` supporting `PENDING_REVIEW`, `COMMITTED`, `REJECTED`, `FAILED`, `ARCHIVED`.
   - Add missing columns to `captures`: `lifecycle_status`, `original_transcript`, `translated_transcript`, `proposal_ids`.
   - Add missing columns to `proposals`: `transcript_text`, `original_transcript`, `translated_transcript`, `display_language`, `translation_status`, `intent_summary`.
   - Add missing columns to `proposal_items`: `action`, `object`, `translated_title`, `translated_description`, `original_title`, `original_description`, confidence metrics, and `decision_state`.
   - Add missing columns to `users`: `full_name`, `locale`.
   - Add missing columns to `memory_preferences`: `category`, `description`, `confidence_score`, `consent_granted`, `consent_level`.
   - Create performance indexes on `captures(user_id, lifecycle_status, created_at DESC)` and `proposals(user_id, status, created_at DESC)`.

---

### Phase 3: Architectural Decoupling & Dual-Mode Persistence
*Requires explicit architectural sign-off:*
1. **Decompose `repository.py`:** Create `backend/app/db/repositories/`:
   - `capture_repo.py`, `proposal_repo.py`, `task_repo.py`, `plan_repo.py`, `user_repo.py`, `memory_repo.py`.
   - Retain `store` facade in `backend/app/db/repository.py` for 100% backward compatibility.
2. **Extract Router Orchestration:** Move NLU fallback and preference translation from `routers/captures.py` into a domain service layer (`backend/app/services/capture_service.py`).
3. **Pluggable Persistence Adapter:** Connect `supabase_client.py` to allow live PostgreSQL database persistence when Supabase credentials are configured in `.env`, falling back to `InMemoryStore` for offline execution and fast test suite runs.

---

### Phase 4: Secondary Routes & UX Polish
1. **Wire `/calendar` to Live Plan:** Replace `MOCK_EVENTS` in `frontend/src/app/calendar/page.tsx` with dynamic task data from `getPlanForDate()`.
2. **Prototype Route Labeling:** Add clear visual "Stage 2 Prototype Preview" banners on `/goals`, `/projects`, `/assistant`, `/insights`, and `/notifications` until their respective backend services are scheduled.
