# 09 — API Contracts & OpenAPI 3.1 Specification

## 1. Document Control & Protocol Overview
- **Protocol:** HTTPS RESTful API + JSON
- **Specification Standard:** OpenAPI 3.1.0
- **Base Path:** `/api/v1`
- **Authentication Scheme:** `BearerAuth` (HTTP Authorization header carrying verified Supabase JWT).
- **Error Format:** RFC 7807 Problem Details (`application/problem+json`).
- **Reference Document:** Master Product Requirements Document ([`Masterprd.md`](file:///c:/Users/moham/OneDrive - ELCOT/Projects/Thozhi/Masterprd.md) Section 13).

---

## 2. Complete Master Endpoint Catalog

### 2.1 Capture Endpoints (Master PRD Section 13.2)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/captures/text` | Ingests raw text thought; initiates NLU parsing and proposal creation. |
| `POST` | `/api/v1/captures/audio` | Ingests 16kHz WAV audio; transcribes via Gnani/Sarvam; creates proposal. |
| `GET` | `/api/v1/captures` | Lists historical captures for the authenticated user. |
| `GET` | `/api/v1/captures/{capture_id}` | Retrieves a single capture record and its transcript metadata. |
| `DELETE`| `/api/v1/captures/{capture_id}` | Deletes a capture and purges its transcript text. |

### 2.2 Proposal Endpoints (Master PRD Section 13.3)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/proposals` | Lists pending and past proposals for the user. |
| `GET` | `/api/v1/proposals/{proposal_id}` | Fetches full proposal object and all extracted `proposal_items`. |
| `PATCH`| `/api/v1/proposals/{proposal_id}/items/{item_id}` | Modifies a proposed item inline (title, duration, deadline, priority). |
| `POST` | `/api/v1/proposals/{proposal_id}/approve` | **The Human Approval Gate:** Promotes approved proposal items to active `tasks`. |
| `POST` | `/api/v1/proposals/{proposal_id}/reject` | Explicitly rejects a proposal; updates status to `REJECTED`. |

### 2.3 Task Endpoints (Master PRD Section 13.4)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/tasks` | Fetches active tasks with date and status filters (`?date=YYYY-MM-DD&status=PENDING`). |
| `POST` | `/api/v1/tasks` | Allows manual explicit creation of a task without AI proposal. |
| `GET` | `/api/v1/tasks/{task_id}` | Fetches detail of a single task including its predecessor/successor dependencies. |
| `PATCH`| `/api/v1/tasks/{task_id}` | Updates task attributes (title, deadline, priority, description). |
| `DELETE`| `/api/v1/tasks/{task_id}` | Soft-deletes or cancels a task. |
| `POST` | `/api/v1/tasks/{task_id}/complete` | Marks a task as completed; records `completed_at` timestamp. |

### 2.4 Planning Endpoints (Master PRD Section 13.5)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/plans` | Generates a proposed schedule session for a target date using Kahn's DAG math. |
| `GET` | `/api/v1/plans/{plan_id}` | Fetches a generated plan, allocated time slots, and capacity deficit explanation. |
| `PATCH`| `/api/v1/plans/{plan_id}` | Manually adjusts task time allocations within a plan. |
| `POST` | `/api/v1/plans/{plan_id}/recalculate` | Re-evaluates plan feasibility after user edits or unexpected delays. |

### 2.5 Availability Endpoints (Master PRD Section 13.6)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/availability` | Retrieves user's working hour windows and recurring schedule bounds. |
| `POST` | `/api/v1/availability` | Creates a new available working window. |
| `PATCH`| `/api/v1/availability/{id}` | Updates an existing availability window. |
| `DELETE`| `/api/v1/availability/{id}` | Removes an availability window. |

### 2.6 Memory & Privacy Endpoints (Master PRD Section 13.7)
| Method | Path | Summary & Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/memory/preferences` | Lists stored user duration priors and planning preferences. |
| `PATCH`| `/api/v1/memory/preferences` | Updates personal memory settings (e.g. toggle duration learning). |
| `DELETE`| `/api/v1/memory/preferences/{id}` | Deletes a specific learned duration prior. |
| `POST` | `/api/v1/privacy/export` | Generates a machine-readable JSON export of all user data (DPDP Act). |
| `DELETE`| `/api/v1/account/data` | Cascades complete account deletion and data purge across all tables. |

---

## 3. Core Schema Definitions & Sample Payloads

### 3.1 Approval Payload (`POST /api/v1/proposals/{proposal_id}/approve`)
```json
{
  "idempotency_key": "user9b1_prop3fa_202611071200",
  "approved_item_ids": [
    "c8a1e2f3-1111-4000-a000-111111111111",
    "d9b2f3a4-2222-4000-b000-222222222222"
  ],
  "rejected_item_ids": [
    "e0c3a4b5-3333-4000-c000-333333333333"
  ],
  "postponed_item_ids": [],
  "target_date": "2026-11-08"
}
```

### 3.2 Approval Response (`201 Created`)
```json
{
  "status": "APPROVED",
  "proposal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_tasks_count": 2,
  "tasks": [
    {
      "id": "77777777-8888-9999-aaaa-bbbbbbbbbbbb",
      "source_proposal_item_id": "c8a1e2f3-1111-4000-a000-111111111111",
      "title": "Prepare client presentation draft",
      "deadline": "2026-11-08T10:00:00+05:30",
      "estimated_duration_min": 60,
      "priority": "P1_CRITICAL",
      "status": "PENDING"
    },
    {
      "id": "88888888-9999-aaaa-bbbb-cccccccccccc",
      "source_proposal_item_id": "d9b2f3a4-2222-4000-b000-222222222222",
      "title": "Attend client sync call",
      "deadline": "2026-11-08T11:00:00+05:30",
      "estimated_duration_min": 60,
      "priority": "P1_CRITICAL",
      "status": "PENDING"
    }
  ]
}
```
