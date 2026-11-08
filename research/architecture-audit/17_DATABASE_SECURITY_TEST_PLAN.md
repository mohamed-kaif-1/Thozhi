# THOZHI — Database Security, Atomicity & Integration Test Plan

**Author:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Test Specification for Database Remediation, RLS Enforcement, and Atomicity
**Test Categories:** Unit Tests (Mocked Transport), Wire PostgREST Protocol Tests, Real PostgreSQL Integration Tests
**Status:** **SPECIFICATION COMPLETE — READY FOR EXECUTION UPON USER AUTHORIZATION**

---

## 1. Testing Methodology & Pyramid

The test suite ensures regression safety, transaction atomicity, and multi-tenant security across three distinct verification layers:

```
                      +-----------------------------+
                      |   Layer 3: Live PostgreSQL   |
                      |   Integration Tests (Staging)|
                      +-----------------------------+
                                     ^
                                     |
                      +-----------------------------+
                      |   Layer 2: PostgREST Wire   |
                      |   Protocol & Contract Tests |
                      +-----------------------------+
                                     ^
                                     |
                      +-----------------------------+
                      |   Layer 1: Mocked Transport |
                      |   Fast Pytest Unit Tests    |
                      +-----------------------------+
```

1. **Layer 1: Unit Tests (Mocked Transport):** Run rapidly in CI/CD without network dependencies. Mocks `httpx` to verify RPC payload serialization, HTTP routing, header propagation, and error code translation.
2. **Layer 2: PostgREST Protocol Tests:** Verifies exact JSON representations, HTTP status code translation (e.g. `400 Bad Request` on SQL error to custom domain exceptions), and URL parameter encoding.
3. **Layer 3: Real PostgreSQL Integration Tests:** Runs against a real PostgreSQL instance (via testcontainer or Supabase local branch) with all migrations 001–004 applied. Verifies ACID transaction rollback, row locking, and genuine RLS policy enforcement.

---

## 2. Comprehensive Security & Regression Test Specifications

### TEST-01: Duplicate Concurrent Approval (Race Condition Prevention)
- **Target:** `commit_proposal_atomic` RPC
- **Layer:** Layer 1 (Mock) & Layer 3 (Live DB)
- **Objective:** Verify that when two concurrent client threads invoke approval with the same `proposal_id` and `idempotency_key`, exactly one execution succeeds in creating tasks, and the second receives the cached result without creating duplicate tasks.
- **Test Steps:**
  1. Seed Proposal `P1` with 2 items for User `U1`.
  2. Launch 2 parallel asynchronous tasks submitting approval with `idempotency_key = "test-concurrent-key"`.
  3. Await both responses.
  4. Query `tasks` table for `origin_proposal_id = P1`.
- **Expected Assertion:**
  - Both requests return HTTP 200 with identical `created_task_ids`.
  - Exactly 2 tasks exist in `tasks` (not 4).
  - Exactly 1 record exists in `approval_idempotency`.

---

### TEST-02: Mid-Transaction Failure & Rollback Verification
- **Target:** `commit_proposal_atomic` transaction boundary
- **Layer:** Layer 3 (Live DB)
- **Objective:** Verify that if an exception occurs mid-way through item processing (e.g. invalid item ID at index 3), all prior operations (tasks created for index 1 and 2, proposal status changes) are completely rolled back by PostgreSQL.
- **Test Steps:**
  1. Seed Proposal `P2` with 3 items.
  2. Submit approval payload containing: Item 1 (Valid), Item 2 (Valid), Item 3 (Foreign random UUID).
  3. Catch expected exception (`P0002 Proposal item does not belong to proposal`).
  4. Query `tasks` for `origin_proposal_id = P2`.
  5. Query `proposals` for `id = P2`.
- **Expected Assertion:**
  - `tasks` count for `P2` is **0** (zero partial tasks created).
  - `proposals.status` remains `'PENDING_REVIEW'`.
  - Zero records created in `audit_logs` or `approval_idempotency`.

---

### TEST-03: Foreign Proposal Item Injection Attempt
- **Target:** Proposal item validation in stored procedure
- **Layer:** Layer 1 (Mock) & Layer 3 (Live DB)
- **Objective:** Verify that an attacker cannot pass a proposal item ID belonging to User B into an approval request for User A's proposal.
- **Test Steps:**
  1. Create Proposal `PA` for User A with Item `IA`.
  2. Create Proposal `PB` for User B with Item `IB`.
  3. Call `commit_proposal_atomic(p_user_id=User_A, p_proposal_id=PA, p_item_decisions=[{"id": IB, "is_approved": true}])`.
- **Expected Assertion:**
  - Transaction fails with `P0002: Proposal item does not belong to proposal`.
  - Error mapped to `ResourceNotFoundException`.
  - No tasks created.

---

### TEST-04: Cross-User Proposal Commitment Attempt
- **Target:** Tenant isolation on stored procedure
- **Layer:** Layer 1 (Mock) & Layer 3 (Live DB)
- **Objective:** Verify that User A cannot commit User B's proposal even if User A knows User B's proposal UUID.
- **Test Steps:**
  1. Create Proposal `PB` owned by User B.
  2. Execute approval request with `user_id = User A, proposal_id = PB`.
- **Expected Assertion:**
  - Fails with `P0002 Proposal not found for user` (or `42501 Access Denied` under JWT).
  - Proposal `PB` remains unmodified.

---

### TEST-05: Cross-User Dependency Edge Creation in `task_dependencies`
- **Target:** Hardened RLS policy on `task_dependencies`
- **Layer:** Layer 3 (Live DB with RLS enabled)
- **Objective:** Verify that User A cannot create a task dependency referencing a task owned by User B.
- **Test Steps:**
  1. Create Task `TA` owned by User A.
  2. Create Task `TB` owned by User B.
  3. In an authenticated session as User A, attempt to insert:
     `INSERT INTO task_dependencies (user_id, predecessor_task_id, successor_task_id) VALUES (User_A, TB, TA)`.
- **Expected Assertion:**
  - PostgreSQL rejects with `new row violates row-level security policy for table "task_dependencies"`.
  - Edge count remains 0.

---

### TEST-06: Tenant Reassignment Attack Prevention (`WITH CHECK`)
- **Target:** RLS `WITH CHECK` clauses on `tasks` and `proposals`
- **Layer:** Layer 3 (Live DB)
- **Objective:** Verify that User A cannot reassign their task or proposal to User B via `UPDATE`.
- **Test Steps:**
  1. Create Task `TA` owned by User A.
  2. In an authenticated session as User A, execute:
     `UPDATE tasks SET user_id = User_B WHERE id = TA`.
- **Expected Assertion:**
  - Rejected with RLS policy violation.
  - `tasks.user_id` remains User A.

---

### TEST-07: Audit Trail Immutability Verification
- **Target:** Hardened RLS policy on `audit_logs`
- **Layer:** Layer 3 (Live DB)
- **Objective:** Verify that an authenticated user cannot `UPDATE` or `DELETE` rows in `audit_logs`.
- **Test Steps:**
  1. Insert an audit log entry for User A.
  2. In an authenticated session as User A, attempt:
     `UPDATE audit_logs SET event_type = 'TAMPERED' WHERE user_id = User_A`.
  3. Attempt:
     `DELETE FROM audit_logs WHERE user_id = User_A`.
- **Expected Assertion:**
  - Both queries fail with RLS permission denied.
  - Audit log entries remain permanently immutable.

---

### TEST-08: Idempotency Replay Verification
- **Target:** Idempotency caching in `commit_proposal_atomic`
- **Layer:** Layer 1 & Layer 3
- **Objective:** Verify that submitting the exact same approval request twice returns the identical cached JSON response without executing duplicate database mutations.
- **Test Steps:**
  1. Approve proposal `P3` with key `idem-12345`. Note response payload.
  2. Re-submit approval with identical proposal ID and key `idem-12345`.
- **Expected Assertion:**
  - Both responses return identical JSON payloads and created task IDs.
  - Task count remains unchanged.

---

### TEST-09: Complete Sovereign Data Wipe (`purge_user_data`)
- **Target:** `SupabaseRepository.purge_user_data()`
- **Layer:** Layer 1 & Layer 3
- **Objective:** Verify that purging user data deletes all rows across all 11 user-scoped tables and creates an audit record.
- **Test Steps:**
  1. Seed records for User `U_purge` across all tables:
     `captures`, `proposals`, `proposal_items`, `tasks`, `task_dependencies`, `plans`, `plan_items`, `busy_events`, `availability_windows`, `memory_preferences`, `approval_idempotency`, `contextual_summaries`.
  2. Call `purge_user_data(user_id=U_purge)`.
  3. Query each table for `user_id = U_purge`.
- **Expected Assertion:**
  - Every table returns 0 rows for `U_purge`.
  - `audit_logs` contains a single `SOVEREIGN_PURGE` event recording deletion counts.

---

### TEST-10: Proposal Clarifications Persistence & Retrieval
- **Target:** `proposals.clarifications` JSONB persistence
- **Layer:** Layer 1 & Layer 3
- **Objective:** Verify that clarification questions generated during extraction are persisted to `proposals` and retrieved completely on `get_proposal()`.
- **Test Steps:**
  1. Create extraction response with 2 clarification questions (`"What time should this occur?"`, `"Is this urgent?"`).
  2. Call `create_proposal_from_extraction()`.
  3. Call `get_proposal(prop_id)`.
- **Expected Assertion:**
  - `retrieved_proposal.clarifications` contains both questions with non-empty text and options.

---

### TEST-11: Task Completion with Actual Duration
- **Target:** `tasks.actual_duration_min` column
- **Layer:** Layer 1 & Layer 3
- **Objective:** Verify that completing a task with `actual_duration_min = 45` updates the database column and returns the updated metric in `TaskResponse`.
- **Test Steps:**
  1. Create task with `estimated_duration_min = 30`.
  2. Call `complete_task(task_id, actual_duration_min=45)`.
- **Expected Assertion:**
  - Response has `actual_duration_min == 45`, `status == "COMPLETED"`, `completed_at != None`.

---

## 3. Test Execution Command Matrix

| Test Suite | Command | Scope |
|---|---|---|
| **Fast Pytest Mock Suite** | `pytest backend/tests/test_supabase_real_persistence.py` | 100% of Layer 1 Mocked Transport tests |
| **RLS Security Policy Suite** | `pytest backend/tests/test_supabase_rls_security.py` | Layer 1 & Layer 2 policy structure tests |
| **All Backend Regression Tests** | `pytest backend/tests` | All 142 tests must pass with 0 regressions |
| **Frontend Static Verification** | `npm run build --prefix frontend` | 18/18 static routes compile with code 0 |
