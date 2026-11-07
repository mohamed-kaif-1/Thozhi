# THOZHI — Repository Structure & Hygiene Audit

## 1. Executive Summary

- **Audit Date:** 2026-11-08
- **Auditor:** Independent Principal Software Architect & Repository Auditor
- **Repository:** THOZHI (தோழி) — Multilingual AI-Powered Personal Planning Assistant
- **Target Branches:** `master` / `main`
- **Total Tracked Files:** 137 files across frontend, backend, database, design, and research

This audit evaluates the physical organization, file naming conventions, asset deduplication, and repository hygiene across the entire THOZHI codebase.

---

## 2. Inventory of Tracked Directories

| Directory Path | Purpose / Domain | File Count | Health Status | Key Observations |
|---|---|:---:|:---:|---|
| `.github/workflows/` | CI/CD Automation | 1 | **WARN** | CI workflow only listens on `main` and `develop`, while local default is `master`. Bypasses `requirements.txt`. |
| `backend/app/` | FastAPI Core Application | 21 | **WARN** | Missing `__init__.py` files in 7 subpackages. Pure in-memory repository without Supabase persistence. |
| `backend/tests/` | Pytest Test Suite | 17 | **HEALTHY** | 125 tests passing. Clean isolation and fixtures. |
| `design/stage-2/` | UI/UX Design System Specs | 5 | **HEALTHY** | Comprehensive documentation of color palette, IA, and user flows. |
| `frontend/public/` | Public Assets & Web Manifest | 20 | **WARN** | Triple duplication of icons across `public/`, `public/brand/`, and `src/app/`. |
| `frontend/src/` | Next.js 14 App Router App | 23 | **WARN** | Unused `Navbar.tsx` component; hook located in `src/lib/`; 6 routes operate on mock arrays. |
| `research/qa-audit/` | QA & Forensic Reports | 17 | **HEALTHY** | Detailed audit trails for ASR, NLU, Scheduling, and Capture Queue. |
| `research/stage-0/` | Problem Validation Docs | 21 | **HEALTHY** | Hypotheses, competitive analyses, and synthetic benchmarks. |
| `research/stage-1/` | Product & Engineering Specs | 16 | **WARN** | Redundant binary archive `stage-1.zip` tracked alongside extracted folder. |
| `supabase/migrations/` | PostgreSQL DDL & RLS Policies | 2 | **CRITICAL** | Severe schema drift: missing columns in `captures`, `proposals`, `users`, and `memory_preferences`. |

---

## 3. Detailed Findings: Repository Structure & Hygiene

### Finding RS-01: Unresolved Git Merge Conflict Markers in `README.md`
- **Severity:** `P0 — Critical`
- **Exact File Path:** [`README.md`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/README.md#L1-L102)
- **Evidence:**
  ```markdown
  Line 1: <<<<<<< HEAD
  ...
  Line 100: =======
  Line 101: # Thozhi
  Line 102: >>>>>>> origin/main
  ```
- **Actual Problem:** An un-resolved merge conflict marker from a previous push/pull was committed into `master`. This corrupts documentation rendering on GitHub and npm.
- **Recommended Correction:** Remove the conflict delimiters (`<<<<<<< HEAD`, `=======`, `>>>>>>> origin/main`) and preserve the full, polished README content.
- **Code Change Necessary:** Yes (Safe cleanup).

---

### Finding RS-02: Redundant Binary Archive Tracked in Git (`research/stage-1.zip`)
- **Severity:** `P2 — Medium`
- **Exact File Path:** `research/stage-1.zip` (55,801 bytes)
- **Evidence:** `git ls-files` shows `research/stage-1.zip` is tracked directly alongside the directory `research/stage-1/` containing all 15 markdown specifications.
- **Actual Problem:** Tracking binary zip archives in git bloats repository history, is prone to stale drift, and duplicates existing text files.
- **Recommended Correction:** Remove `research/stage-1.zip` from git tracking (`git rm research/stage-1.zip`) while keeping the extracted markdown files intact.
- **Code Change Necessary:** Yes.

---

### Finding RS-03: Triple Icon and Brand Asset Duplication in Frontend
- **Severity:** `P2 — Medium`
- **Exact File Paths:**
  - `frontend/public/favicon.ico` (16,063 bytes) == `frontend/public/brand/favicon.ico` (16,063 bytes)
  - `frontend/public/icon-192.png` (40,867 bytes) == `frontend/public/brand/icon-192.png` (40,867 bytes)
  - `frontend/public/icon-512.png` (210,693 bytes) == `frontend/public/brand/icon-512.png` (210,693 bytes)
  - `frontend/public/brand/favicon.png` (210,693 bytes) == `frontend/public/icon-512.png` (210,693 bytes)
  - `frontend/src/app/apple-icon.png` (36,804 bytes) == `frontend/public/brand/apple-touch-icon.png` (36,804 bytes)
  - `frontend/src/app/favicon.ico` (16,063 bytes)
  - `frontend/src/app/icon.png` (40,867 bytes)
- **Evidence:** Files have byte-for-byte identical content across multiple paths.
- **Actual Problem:** In Next.js 14, icons placed in `src/app/` automatically serve as route handlers (`/icon.png`, `/favicon.ico`, `/apple-icon.png`), while `frontend/src/app/layout.tsx` concurrently declares static links to `/brand/favicon.ico`, `/brand/favicon.png`, and `/brand/apple-touch-icon.png`, and `public/` stores top-level copies.
- **Recommended Correction:** Keep canonical assets in `frontend/public/brand/`, point `manifest.json` and `layout.tsx` to `frontend/public/brand/`, and eliminate redundant root copies.
- **Code Change Necessary:** Yes.

---

### Finding RS-04: Inconsistent Documentation Naming Conventions Across Stages
- **Severity:** `P3 — Low`
- **Exact File Paths:**
  - `research/stage-0/00-stage-overview.md` (kebab-case with hyphens)
  - `research/stage-1/01_PRODUCT_REQUIREMENTS_DOCUMENT.md` (UPPER_SNAKE_CASE)
  - `design/stage-2/01_DESIGN_SYSTEM.md` (UPPER_SNAKE_CASE)
  - `research/qa-audit/00_QA_AUDIT_SUMMARY.md` (UPPER_SNAKE_CASE)
- **Evidence:** Stage 0 uses lower-case kebab naming (`01-problem-hypothesis.md`), while Stage 1, Stage 2, and QA audits use capitalized snake case.
- **Actual Problem:** Minor inconsistency in naming conventions across project phases.
- **Recommended Correction:** Maintain backward compatibility by keeping existing paths (to preserve internal hyperlinks and citation stability) and adopt `UPPER_SNAKE_CASE` as the project-wide standard for all formal engineering documentation going forward.
- **Code Change Necessary:** No (do not break existing research links).

---

### Finding RS-05: Outdated Test Metrics and Status in Project Documentation
- **Severity:** `P2 — Medium`
- **Exact File Paths:**
  - `README.md:4` (`pytest-65 passed` badge)
  - `README.md:71` (`All 47 tests pass in ~15 seconds`)
  - `Stages.md:667` (`65/65 passing backend tests`)
- **Evidence:** Running `python -m pytest backend/tests` executes **125 tests**, all passing.
- **Actual Problem:** Documentation understates test coverage and fails to reflect the 32 NLU extraction tests, 16 scheduling engine tests, and 12 capture queue tests added during recent stages.
- **Recommended Correction:** Update badges and documentation in `README.md` and `Stages.md` to reflect the actual **125/125 passed** test suite.
- **Code Change Necessary:** Yes.
