# THOZHI — Atomic Proposal Approval RPC & Repository Integration Design

**Author:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Technical Specification for `commit_proposal_atomic` Stored Procedure & `SupabaseRepository` Replacement
**Status:** **DESIGN & SPECIFICATION COMPLETE**

---

## 1. Architectural Motivation

In the current `SupabaseRepository.approve_proposal()` implementation, a single human decision is executed via **7 separate sequential HTTP requests** across 5 PostgREST tables:
1. `GET /approval_idempotency`
2. `GET /proposals`
3. `POST /tasks` (in a Python loop for each approved item)
4. `PATCH /proposal_items` (in a Python loop)
5. `PATCH /proposals`
6. `PATCH /captures`
7. `POST /approval_idempotency` & `POST /audit_logs`

### Verified Vulnerabilities of the Current Approach:
- **Race Condition on Double-Click / Concurrency:** Two concurrent requests using the same idempotency key both execute Step 1 simultaneously (cache miss), proceed to Step 3, and insert duplicate tasks into the database before either reaches Step 7.
- **Partial Failure & Split-Brain State:** If a network interruption or server restart occurs at Step 5, tasks are already created and proposal items are marked committed, but the proposal remains `PENDING_REVIEW` and no idempotency record exists. A user retry duplicates the tasks.
- **High Network Latency:** 7 to 15 sequential HTTP roundtrips to Supabase (50–100ms each) result in a 500ms–1500ms response time for a simple approval action.

---

## 2. Technical Specification of `commit_proposal_atomic`

The stored procedure `commit_proposal_atomic` consolidates all operations into a single atomic PostgreSQL transaction.

### 2.1 Function Signature
```sql
CREATE OR REPLACE FUNCTION commit_proposal_atomic(
    p_user_id UUID,
    p_proposal_id UUID,
    p_idempotency_key VARCHAR(255),
    p_item_decisions JSONB
) RETURNS JSONB
```

### 2.2 Parameter Definitions & Types
| Parameter | Type | Validation & Semantics |
|---|---|---|
| `p_user_id` | `UUID` | Target user ID. If called via authenticated JWT, must match `request.jwt.claim.sub` (`42501 Unauthorized` if mismatched). |
| `p_proposal_id` | `UUID` | ID of the proposal being committed. Must exist and belong to user (`P0002 Not Found` if nonexistent). |
| `p_idempotency_key` | `VARCHAR(255)` | Unique client-generated token (UUID or hash). Guarantees exactly-once execution. |
| `p_item_decisions` | `JSONB` | JSON array of human decision objects. |

### 2.3 Input Payload Schema (`p_item_decisions`)
```json
[
  {
    "id": "e4b2d3f1-0000-0000-0000-000000000001",
    "is_approved": true,
    "proposed_title": "Custom edited title (or null to keep original)",
    "estimated_duration_min": 45,
    "priority": "P1_CRITICAL",
    "scheduled_date": "2026-11-09",
    "rejection_reason": null
  },
  {
    "id": "e4b2d3f1-0000-0000-0000-000000000002",
    "is_approved": false,
    "rejection_reason": "Not feasible this week"
  }
]
```

### 2.4 Output Response Schema (Matches `ProposalApproveResponse`)
```json
{
  "proposal_id": "f8c3e2a1-0000-0000-0000-000000000000",
  "approved_tasks_count": 1,
  "rejected_items_count": 1,
  "created_task_ids": [
    "7a1b2c3d-0000-0000-0000-000000000001"
  ],
  "message": "Human decision recorded atomically. Tasks explicitly committed to schedule."
}
```

---

## 3. Transaction Isolation, Concurrency & Security Model

### 3.1 Row-Level Serialization (`SELECT ... FOR UPDATE`)
To prevent concurrent requests from racing, the function executes:
```sql
SELECT * INTO v_proposal
FROM proposals
WHERE id = p_proposal_id AND user_id = v_effective_user_id
FOR UPDATE;
```
- If Request A and Request B arrive simultaneously for the same proposal:
  - Request A acquires the row exclusive lock.
  - Request B blocks on the lock.
  - Request A completes, updates `status = 'COMMITTED'`, writes the idempotency cache, and commits.
  - Request B unblocks, inspects the locked proposal, finds `status = 'COMMITTED'`, checks the idempotency cache, returns the cached result, or raises `23505 Proposal has already been committed`.
- **Outcome:** Zero duplicate tasks, zero double commitments.

### 3.2 Caller Identity Validation & Anti-Spoofing
```sql
BEGIN
    v_auth_uid := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
EXCEPTION WHEN OTHERS THEN
    v_auth_uid := NULL;
END;

IF v_auth_uid IS NOT NULL THEN
    IF v_auth_uid != p_user_id THEN
        RAISE EXCEPTION 'Access denied: authenticated caller % does not match target user_id %',
            v_auth_uid, p_user_id USING ERRCODE = '42501';
    END IF;
    v_effective_user_id := v_auth_uid;
ELSE
    v_effective_user_id := p_user_id;
END IF;
```
- When called by an authenticated user in PostgREST, the user ID is securely derived from the verified JWT claim. A caller cannot supply another user's ID to commit their proposal.
- When called by the service role or in local test suites (where JWT claim is empty), it validates against `p_user_id`.

### 3.3 Foreign Item Injection Prevention
Every item in `p_item_decisions` is verified against the database:
```sql
SELECT * INTO v_prop_item
FROM proposal_items
WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id
FOR UPDATE;

IF NOT FOUND THEN
    RAISE EXCEPTION 'Proposal item % does not belong to proposal % or user %',
        v_item_id, p_proposal_id, v_effective_user_id USING ERRCODE = 'P0002';
END IF;
```
A caller cannot inject foreign proposal item IDs or items belonging to other proposals or tenants.

### 3.4 SECURITY DEFINER & Search Path Hardening
The function is declared with:
```sql
SECURITY DEFINER
SET search_path = public, extensions, pg_temp;
```
- **Why `SECURITY DEFINER`?** Allows the function to atomically perform coordinate writes across `tasks`, `proposals`, `proposal_items`, `captures`, `approval_idempotency`, and `audit_logs` without requiring granular permissive grants on every single underlying table for the `authenticated` role.
- **Why `SET search_path`?** Prevents CWE-426 search_path hijack attacks by locking execution strictly to `public` and `extensions`.
- **Privilege Grants:**
  ```sql
  REVOKE ALL ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) FROM PUBLIC;
  GRANT EXECUTE ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) TO authenticated, service_role;
  ```

---

## 4. Repository Integration Design (`SupabaseRepository`)

### 4.1 Interface Replacement
In `backend/app/db/repositories/supabase.py`, replace the multi-step loop in `approve_proposal()` with a direct invocation of `client.rpc_sync()`:

```python
def approve_proposal(
    self,
    proposal_id: UUID,
    user_id: UUID,
    request: ProposalApproveRequest
) -> ProposalApproveResponse:
    # 1. Transform request into JSONB decisions payload
    item_decisions = []
    for item in request.items:
        decision_dict = {
            "id": str(item.id),
            "is_approved": item.is_approved,
            "proposed_title": item.proposed_title,
            "estimated_duration_min": item.estimated_duration_min,
            "priority": item.priority.value if item.priority else None,
            "scheduled_date": item.scheduled_date.isoformat() if getattr(item, "scheduled_date", None) else None,
            "rejection_reason": getattr(item, "rejection_reason", None)
        }
        item_decisions.append(decision_dict)

    rpc_params = {
        "p_user_id": str(user_id),
        "p_proposal_id": str(proposal_id),
        "p_idempotency_key": request.idempotency_key,
        "p_item_decisions": item_decisions
    }

    try:
        # 2. Execute single ACID transaction in Supabase
        raw_result = self.client.rpc_sync("commit_proposal_atomic", rpc_params)

        # 3. Parse and return typed response
        created_task_uuids = [
            UUID(t) if isinstance(t, str) else t
            for t in raw_result.get("created_task_ids", [])
        ]

        return ProposalApproveResponse(
            proposal_id=UUID(raw_result["proposal_id"]) if isinstance(raw_result["proposal_id"], str) else raw_result["proposal_id"],
            approved_tasks_count=raw_result.get("approved_tasks_count", 0),
            rejected_items_count=raw_result.get("rejected_items_count", 0),
            created_task_ids=created_task_uuids,
            message=raw_result.get("message", "Human decision recorded atomically.")
        )
    except SupabaseQueryError as exc:
        # Map PostgreSQL error codes back to domain exceptions
        err_msg = str(exc.detail).lower()
        if "p0002" in err_msg or "not found" in err_msg:
            raise ResourceNotFoundException(
                detail=f"Proposal {proposal_id} or item not found",
                resource_type="proposal",
                resource_id=str(proposal_id)
            )
        elif "23505" in err_msg or "already been committed" in err_msg:
            raise IdempotencyConflictException("Proposal has already been approved and committed.")
        elif "22023" in err_msg or "already been rejected" in err_msg:
            raise ProposalExpiredException("Proposal has already been rejected.")
        elif "42501" in err_msg or "access denied" in err_msg:
            raise PermissionDeniedException("Access denied for this proposal.")
        raise
```

### 4.2 Backward Compatibility Guarantees
1. **Contract Invariance:** The signature `approve_proposal(proposal_id: UUID, user_id: UUID, request: ProposalApproveRequest) -> ProposalApproveResponse` remains 100% unchanged.
2. **Schema Invariance:** `ProposalApproveResponse` continues to receive identical fields: `proposal_id`, `approved_tasks_count`, `rejected_items_count`, `created_task_ids`, and `message`.
3. **Exception Invariance:** Callers expecting `ResourceNotFoundException`, `IdempotencyConflictException`, or `ProposalExpiredException` continue to receive the identical exceptions.
4. **Audit Invariance:** `audit_logs` and `approval_idempotency` records continue to be written with identical schemas.
