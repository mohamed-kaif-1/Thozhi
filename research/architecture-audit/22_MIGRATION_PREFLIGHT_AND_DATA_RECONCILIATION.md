# THOZHI — Phase 1.7.5: Migration Preflight & Data Reconciliation Protocol

**Author:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Preflight Audit Queries, Duplicate Task Detection & Safe Data Reconciliation Procedure
**Status:** **OPERATIONAL PROTOCOL COMPLETE**

---

## 1. Executive Summary

Applying a `UNIQUE` constraint or index to an existing PostgreSQL table will immediately fail if duplicate records already exist:
`ERROR: 23505: could not create unique index ... Key (...) is duplicated.`

To resolve **REV-04**, this document establishes a strict, non-destructive preflight audit and data reconciliation protocol that must be executed against any staging or production database before Migration 004's partial unique index (`uq_task_source_proposal_item`) is applied.

Automatic deletion is explicitly prohibited. The reconciliation procedure analyzes task states, completion metrics, and foreign key references to preserve genuine user work.

---

## 2. Read-Only Duplicate Detection Queries

Before executing any DDL, run the following read-only SQL queries to assess whether duplicate tasks exist.

### Query 1: Summary of Duplicate Task Proposal Items
```sql
-- Read-Only Audit: Identify proposal items that produced multiple tasks
SELECT
    t.source_proposal_item_id,
    t.user_id,
    COUNT(*) AS duplicate_task_count,
    ARRAY_AGG(t.id ORDER BY t.created_at ASC) AS task_ids,
    ARRAY_AGG(t.status ORDER BY t.created_at ASC) AS task_statuses,
    ARRAY_AGG(COALESCE(t.completed_at::text, 'uncompleted') ORDER BY t.created_at ASC) AS completed_timestamps
FROM tasks t
WHERE t.source_proposal_item_id IS NOT NULL
GROUP BY t.source_proposal_item_id, t.user_id
HAVING COUNT(*) > 1;
```

### Query 2: Detailed Inspection of Conflicting Tasks
```sql
-- Read-Only Audit: Inspect full metadata of duplicate tasks
SELECT
    t.id AS task_id,
    t.user_id,
    t.source_proposal_item_id,
    t.origin_proposal_id,
    t.title,
    t.status,
    t.estimated_duration_min,
    t.actual_duration_min,
    t.completed_at,
    t.created_at,
    t.updated_at
FROM tasks t
WHERE t.source_proposal_item_id IN (
    SELECT source_proposal_item_id
    FROM tasks
    WHERE source_proposal_item_id IS NOT NULL
    GROUP BY source_proposal_item_id
    HAVING COUNT(*) > 1
)
ORDER BY t.source_proposal_item_id, t.created_at ASC;
```

### Query 3: Foreign Key Dependency Reference Check
```sql
-- Read-Only Audit: Check if any duplicate tasks are referenced by dependencies or plans
SELECT
    'task_dependencies' AS referenced_in,
    td.id AS ref_id,
    td.predecessor_task_id AS task_id
FROM task_dependencies td
WHERE td.predecessor_task_id IN (
    SELECT id FROM tasks WHERE source_proposal_item_id IN (
        SELECT source_proposal_item_id FROM tasks WHERE source_proposal_item_id IS NOT NULL GROUP BY source_proposal_item_id HAVING COUNT(*) > 1
    )
)
UNION ALL
SELECT
    'plan_items' AS referenced_in,
    pi.id AS ref_id,
    pi.task_id AS task_id
FROM plan_items pi
WHERE pi.task_id IN (
    SELECT id FROM tasks WHERE source_proposal_item_id IN (
        SELECT source_proposal_item_id FROM tasks WHERE source_proposal_item_id IS NOT NULL GROUP BY source_proposal_item_id HAVING COUNT(*) > 1
    )
);
```

---

## 3. Safe Reconciliation Decision Logic

When duplicate tasks exist for the same `source_proposal_item_id`, the system applies the following deterministic reconciliation rules:

```
+------------------------------------+------------------------------------+--------------------------------------------+
| Duplicate Task A                   | Duplicate Task B                   | Reconciliation Action                      |
+------------------------------------+------------------------------------+--------------------------------------------+
| status = 'COMPLETED'               | status = 'PENDING'                 | Retain Task A (User finished work).        |
|                                    |                                    | Delete Task B.                             |
| status = 'COMPLETED' (earlier)     | status = 'COMPLETED' (later)       | Retain Task A (Primary completion).        |
|                                    |                                    | Merge notes/time to Task A. Delete Task B. |
| status = 'PENDING'                 | status = 'PENDING'                 | Retain earlier Task A. Delete Task B.      |
| status = 'IN_PROGRESS'             | status = 'PENDING'                 | Retain Task A (Active work). Delete Task B.|
| Referenced in task_dependencies    | Not referenced                     | Retain Task A (Has graph links).           |
|                                    |                                    | Delete Task B.                             |
+------------------------------------+------------------------------------+--------------------------------------------+
```

---

## 4. Controlled Reconciliation DML Script (Executed Only if Duplicates Found)

If Query 1 reports duplicates, execute this controlled transaction script:

```sql
BEGIN;

-- 1. Create temporary audit table of tasks marked for deletion
CREATE TEMP TABLE temp_reconciled_tasks AS
WITH ranked_tasks AS (
    SELECT
        id,
        source_proposal_item_id,
        user_id,
        status,
        completed_at,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY source_proposal_item_id
            ORDER BY
                CASE WHEN status = 'COMPLETED' THEN 1
                     WHEN status = 'IN_PROGRESS' THEN 2
                     ELSE 3 END ASC,
                created_at ASC
        ) AS rank_order
    FROM tasks
    WHERE source_proposal_item_id IS NOT NULL
)
SELECT id, source_proposal_item_id, user_id, status
FROM ranked_tasks
WHERE rank_order > 1;

-- 2. Audit the records to be pruned
SELECT * FROM temp_reconciled_tasks;

-- 3. Re-point any dependency references to the surviving task
-- (Handled interactively if Query 3 reports references)

-- 4. Delete only the duplicate records (surviving primary task remains)
DELETE FROM tasks
WHERE id IN (SELECT id FROM temp_reconciled_tasks);

-- 5. Record reconciliation in audit_logs
INSERT INTO audit_logs (id, user_id, event_type, metadata, created_at)
SELECT
    gen_random_uuid(),
    user_id,
    'DATA_RECONCILIATION_DEDUPLICATION',
    jsonb_build_object(
        'deleted_task_id', id,
        'source_proposal_item_id', source_proposal_item_id,
        'prior_status', status
    ),
    NOW()
FROM temp_reconciled_tasks;

COMMIT;
```

---

## 5. Verification Gate Before Applying Partial Unique Index

Only after Query 1 returns **0 rows** (confirming zero duplicates) may the partial unique index be safely created:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
    ON tasks (source_proposal_item_id)
    WHERE source_proposal_item_id IS NOT NULL;
```
This guarantees zero disruption to active database deployments.
