# 13 — SCHEDULING REGRESSION TEST EXECUTION RESULTS

**Project:** THOZHI Sovereign Indic AI Task Planner  
**Date:** November 8, 2026  
**Test Suite:** `backend/tests/test_scheduling_regression.py`  
**Execution Environment:** Windows 11, Python 3.14.4, Pytest 9.2.0, FastAPI TestClient  
**Status:** 11/11 PASSED (100% Success Rate)  

---

## 1. Executive Summary

A comprehensive, deterministic 11-case regression test suite was constructed and executed to validate the complete overhaul of THOZHI's scheduling and duration estimation engine. The tests verify that:
1. Short tasks receive exact, compact focus slots without arbitrary duration inflation.
2. Large projects (specifically the Raven project scenario) are assigned defensible multi-hour AI estimates (180m) rather than arbitrary 30-minute default slots.
3. User-explicit durations are preserved with zero overrides.
4. Infeasible plans are detected upfront with exact minute-deficit reporting rather than fabricating unworkable schedules.
5. Calendar conflicts and overlapping commitments are flagged with actionable diagnostics.
6. Kahn's DAG topological sort strictly sequences task dependencies.
7. Past deadlines trigger explicit diagnostic warnings.
8. Local timezone calculations (Asia/Kolkata / IST, UTC+5:30) prevent date-slippage.
9. Priority rankings sequence critical work first before deadlines.
10. Dynamic duration adjustments recalculate available capacity without moving deadlines.
11. End-to-end API integration verifies date-specific timeline plan retrieval.

---

## 2. Test Execution Matrix

| Test Case | Scenario Description | Expected Invariant | Actual Result | Status |
|---|---|---|---|---|
| **Case 1** | Short task (`Send an email to client team`, 15m explicit duration, deadline tomorrow 6:00 PM) | Slot duration = 15m; placed before 18:00 deadline; labeled `USER_EXPLICIT`. | Slot: 09:00–09:15 (15m), end <= 18:00, `USER_EXPLICIT`. | **PASSED** |
| **Case 2** | Complex project work (`Complete my Raven project`, unstated duration, deadline tomorrow 6:00 PM) | Must NOT default to 30m. Infers 180m AI estimate; slot placed 09:00–12:00 with 360m buffer before 18:00 deadline. | Slot: 09:00–12:00 (180m), labeled `AI_ESTIMATE`, end <= 18:00. | **PASSED** |
| **Case 3** | Explicit user duration (`Study database systems`, 120m) | Exactly 120m allocated; labeled `USER_EXPLICIT`. | Slot: 09:00–11:00 (120m), `USER_EXPLICIT`. | **PASSED** |
| **Case 4** | Insufficient availability / Overcapacity (Task requires 300m, available window before deadline is 120m) | Not scheduled beyond deadline; unassigned; marked `OVERCAPACITY` with 180m deficit. | Zero slots placed; `OVERCAPACITY` reported with "Deficit: 180 minutes". | **PASSED** |
| **Case 5** | Overlapping busy commitments (Design Review 10–12, Incident 11–13) | Collision detected; conflict code `OVERLAPPING_COMMITMENT`. | Conflict raised with titles of colliding events. | **PASSED** |
| **Case 6** | Dependency DAG (Task A ➔ Task B ➔ Task C) | Kahn's algorithm sequences A then B then C; non-overlapping. | Order strictly enforced: A (09:00–10:00) ➔ B (10:00–11:00) ➔ C (11:00–12:00). | **PASSED** |
| **Case 7** | Missed / past deadline (Task deadline is in the past) | Task flagged with `DEADLINE_ALREADY_PASSED`; not scheduled. | Confirmed: conflict raised; unassigned. | **PASSED** |
| **Case 8** | Timezone preservation (IST Asia/Kolkata, UTC+5:30) | Deadline 18:00 IST preserved on local date; no 5h30m drift. | Scheduled slot end <= 18:00 on local target date. | **PASSED** |
| **Case 9** | Mixed priorities and deadlines (P1 Critical due 12:00, P2 Medium due 16:00, P3 Low due 18:00) | P1 scheduled first in earliest slot; all finished before respective deadlines. | P1 placed at 09:00–10:30 (before 12:00); P2 and P3 placed subsequent. | **PASSED** |
| **Case 10** | User edits task duration (Updated from 180m to 60m) | Plan recalculated; scheduled minutes drop from 180 to 60; deadline untouched. | Slot shrinks to 60m; total scheduled minutes = 60m; 120m capacity released. | **PASSED** |
| **Case 11** | End-to-end Raven API integration (`POST /api/v1/tasks` ➔ `GET /api/v1/plans/date/{tomorrow}`) | Task appears in tomorrow's plan with 180m duration and `AI_ESTIMATE` badge. | Verified via HTTP API client; slot has duration 180m and finishes before 18:00. | **PASSED** |

---

## 3. Full Test Suite Verification

In addition to the 11 targeted regression scenarios, the entire backend automated test suite was executed:
- **Total Test Files:** 16
- **Total Tests Executed:** 113
- **Passed:** 113 (100%)
- **Failed:** 0
- **Duration:** 46.44 seconds

```
====================== 113 passed, 2 warnings in 46.44s =======================
```

### Verified Test Modules:
- `test_e2e_workflow.py` (End-to-End Workflow) — 1/1 PASSED
- `test_extraction_regression.py` (32 NLU Extraction Scenarios) — 32/32 PASSED
- `test_health.py` (Health and Diagnostics) — 2/2 PASSED
- `test_memory.py` (Sovereign Memory Lifecycle) — 1/1 PASSED
- `test_planning_engine.py` (DAG Scheduler & Interval Math) — 4/4 PASSED
- `test_proposals_and_approvals.py` (Zero Silent Task Invariants) — 1/1 PASSED
- `test_scheduling_regression.py` (11 Scheduling Scenarios) — 11/11 PASSED
- `test_stage3_foundation.py` (Multi-tenant & Config Isolation) — 5/5 PASSED
- `test_stage4_ai_understanding.py` (Indic Audio & Tanglish Processing) — 3/3 PASSED
- `test_stage5_planning_and_tasks.py` (CRUD & Reschedule Flow) — 6/6 PASSED
- `test_stage6_memory_and_privacy.py` (GDPR Purge & Data Portability) — 7/7 PASSED
- `test_stage7_full_integration.py` (Full System Integration) — 3/3 PASSED
- `test_stage8_ai_evaluation.py` (AI Evaluation Benchmarks) — 18/18 PASSED
- `test_synthetic_scenarios.py` (Real User Persona Scenarios) — 3/3 PASSED
- `test_translation.py` (Sarvam Multilingual Translation) — 5/5 PASSED

---

## 4. Frontend Type Checking & Production Build Verification

The Next.js frontend was verified using strict ESLint rules and production static page compilation:
```bash
npm run lint --prefix frontend
✔ No ESLint warnings or errors

npm run build --prefix frontend
✓ Compiled successfully
✓ Generating static pages (18/18)
```
All 18 pages compiled cleanly with zero TypeScript errors, including:
- `/` (Dynamic user greeting & agenda)
- `/settings` (User Display Name management, live avatar preview, working hours)
- `/planner` (Date-aware hourly timeline, duration provenance badges, deadline indicators)
- `/tasks`, `/capture`, `/memory`, `/assistant`, `/goals`, `/projects`, `/calendar`, `/insights`, `/notifications`.
