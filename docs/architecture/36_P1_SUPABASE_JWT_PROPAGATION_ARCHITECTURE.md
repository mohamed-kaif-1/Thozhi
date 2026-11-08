# THOZHI — P1 Remediation Architecture: Concurrency-Safe Supabase JWT Propagation

**Document:** `docs/architecture/36_P1_SUPABASE_JWT_PROPAGATION_ARCHITECTURE.md`
**Date:** 2026-11-08
**Author:** Lead Backend Security Engineer & Systems Architect
**Status:** APPROVED ARCHITECTURE — P1 Remediation Specification

---

## 1. Executive Summary & Security Mandate

In Phase 2.0 baseline testing, an architectural vulnerability was identified: while `commit_proposal_atomic` RPC received the user's JWT, all 40 standard CRUD operations in `SupabaseRepository` executed queries against PostgREST without forwarding the end-user JWT. Consequently, `SupabaseClient` fell back to `SUPABASE_KEY` (`service_role`), bypassing PostgreSQL Row Level Security (RLS) policies.

The P1 Remediation establishes the following absolute guarantee:

> **P1 Core Guarantee:**
> Every user-facing Supabase database operation must execute using the verified end-user JWT in the `Authorization: Bearer` header, enabling PostgreSQL Row Level Security (RLS) to independently enforce tenant isolation. Silent fallback to service-role authorization is strictly prohibited. Application-level tenant filters (`user_id = <uuid>`) remain in place as defense in depth.

---

## 2. Concurrency-Safe Request-Scoped Architecture

### 2.1 The Shared-State Concurrency Vulnerability (Prohibited Design)
A common antipattern in client SDKs is mutating shared client instance state:
```python
# PROHIBITED CONCURRENCY VULNERABILITY:
client.set_access_token(user_token)  # Mutates shared singleton!
```
Under asynchronous or multi-threaded execution (e.g., Uvicorn / AnyIO):
1. **Time $t_0$:** Request A (User A) sets `client.token = JWT_A`.
2. **Time $t_1$:** Request B (User B) sets `client.token = JWT_B`.
3. **Time $t_2$:** Request A executes its PostgREST database query using `client.token`.
4. **Vulnerability:** Request A executes using `JWT_B`, reading or mutating User B's private data.

### 2.2 Selected Architecture: Stack-Allocated Per-Request Authorization
To eliminate race conditions, THOZHI implements **Per-Request Immutable Authorization Headers (Option A / Option C)**:

```
[Incoming Request]
       |
       v
FastAPI Dependency (get_current_user)
  --> Returns AuthenticatedUser(id, token) on call stack
       |
       v
Domain Router Handler (e.g. list_tasks)
  --> Calls store.list_tasks(user_id=current_user.id, user_token=current_user.token)
       |
       v
SupabaseRepository.list_tasks
  --> Calls client.list_records_sync(table="tasks", params=..., user_token=user_token)
       |
       v
SupabaseClient._get_headers(user_token=user_token, allow_service_role=False)
  --> Constructs new Dict on function call stack:
      {
        "apikey": self.api_key,
        "Authorization": f"Bearer {user_token}",
        "Prefer": "return=representation"
      }
       |
       v
httpx.Client.request(headers=local_headers_dict)
       |
       v
PostgREST: auth.uid() = User UUID, auth.role() = 'authenticated'
       |
       v
PostgreSQL RLS: Enforces (auth.uid() = user_id)
```

### 2.3 Mathematical Proof of Concurrency Isolation
- No instance variable on `SupabaseClient` or `SupabaseRepository` stores `user_token`.
- `user_token` exists solely as a parameter passed through Python call stack frames.
- Python function arguments and local dictionaries are allocated on the call stack frame belonging exclusively to the executing coroutine/thread.
- User A's execution frame and User B's execution frame share zero mutable state.
- Therefore, cross-request token corruption is impossible.

---

## 3. Fail-Closed Client Specification (`backend/app/db/supabase_client.py`)

### 3.1 Strict Fail-Closed Rule
If an operation is user-facing (`allow_service_role=False`) and `user_token` is `None` or empty:
- The client **MUST NOT** substitute `self.api_key`.
- The client **MUST NOT** send an empty Bearer header.
- The client **MUST** raise `SupabaseAuthError` immediately.
- The HTTP request to PostgREST **MUST NOT** be dispatched.

### 3.2 Method Signatures & Authorization Flags
All sync and async client methods accept `user_token: Optional[str] = None` and `allow_service_role: bool = False`:
```python
def list_records_sync(
    self,
    table: str,
    filters: Optional[Dict[str, str]] = None,
    user_token: Optional[str] = None,
    allow_service_role: bool = False
) -> List[Dict[str, Any]]: ...

def get_record_sync(
    self,
    table: str,
    filters: Dict[str, str],
    user_token: Optional[str] = None,
    allow_service_role: bool = False
) -> Optional[Dict[str, Any]]: ...

def insert_record_sync(
    self,
    table: str,
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    user_token: Optional[str] = None,
    upsert: bool = False,
    allow_service_role: bool = False
) -> Any: ...

def update_record_sync(
    self,
    table: str,
    filters: Dict[str, str],
    data: Dict[str, Any],
    user_token: Optional[str] = None,
    allow_service_role: bool = False
) -> List[Dict[str, Any]]: ...

def delete_record_sync(
    self,
    table: str,
    filters: Dict[str, str],
    user_token: Optional[str] = None,
    allow_service_role: bool = False
) -> int: ...

def rpc_sync(
    self,
    function_name: str,
    params: Dict[str, Any],
    user_token: Optional[str] = None,
    allow_service_role: bool = False
) -> Any: ...
```

---

## 4. Repository Interface & Polymorphism (`base.py`, `supabase.py`, `memory.py`)

1. **`BaseRepository` Interface:**
   Every user-facing abstract method signature accepts `user_token: Optional[str] = None`.
2. **`SupabaseRepository` Implementation:**
   Every user-facing method passes `user_token=user_token, allow_service_role=False` to `self.client.*_sync()`. Missing tokens fail closed.
3. **`InMemoryStore` Implementation:**
   Accepts `user_token: Optional[str] = None` to maintain 100% signature polymorphism. Continues local memory operations without requiring an active PostgREST connection.

---

## 5. Service-Role Access Boundaries

| Context | `user_token` | `allow_service_role` | Permitted? | Justification |
| :--- | :--- | :--- | :--- | :--- |
| Normal User CRUD | Valid JWT | `False` | **YES** | Standard authenticated user operation. |
| Normal User CRUD | `None` | `False` | **NO (Fails Closed)** | Missing credentials must never run as admin. |
| Health Check (`/health`) | `None` | `True` | **YES** | Probes discovery endpoint `GET ""`. No tenant rows accessed. |
| System Migration Script | `None` | `True` | **YES** | Server-side DDL execution during bootstrap. |
| User Data Purge (Audit Log) | Valid JWT | `True` (Audit Log only) | **YES** | PostgreSQL RLS revokes direct INSERT on `audit_logs` from `authenticated`. Server logs sovereign purge event. |

**Architecture Status:** APPROVED for implementation.
