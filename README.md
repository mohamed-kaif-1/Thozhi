# THOZHI (தோழி) — Multilingual AI-Powered Personal Planning Assistant

[![Python Tests](https://img.shields.io/badge/pytest-12%20passed-brightgreen.svg)]()
[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()

> **Core Principle: "The AI proposes. The user decides."**  
> Zero silent task creation or unconfirmed schedule modifications.

---

## 📌 Overview

**THOZHI** is an AI-powered multilingual personal planning assistant engineered to capture unstructured spoken or typed thoughts in **Tamil, Tanglish, and English**, extract commitments and tasks with chronological dependencies, and propose realistic daily schedules verified by human approval.

---

## 🏗 System Architecture & Stages Completed

| Stage | Name | Status | Deliverables & Verification |
|---|---|---|---|
| **Stage 0** | Product Validation & Evidence Audit | **Complete** | 20 research documents in `research/stage-0/` verifying ASR pricing, competitor capabilities, and opportunity scorecards. |
| **Stage 1** | Product & Engineering Specification | **Complete** | 15 engineering documents in `research/stage-1/` covering PRD, Algorithmic Specs, 14-table database schema, and security architecture. |
| **Stage 2** | UI/UX Design System | **Complete** | 5 specs in `design/stage-2/` detailing color tokens (Warm Amber for proposals, Emerald for confirmed, Coral for deficits), wireframes, and Zustand prototype specs. |
| **Stage 3** | Development Foundation | **Complete** | Next.js 14 frontend initialized, FastAPI backend structure, Supabase SQL migrations (`001_initial_schema.sql`, `002_rls_policies.sql`). |
| **Stage 4** | Core AI Understanding System | **Complete** | Primary ASR (Gnani Prisma v3) + Commercial Failover (Sarvam Saaras v3) dispatcher with Zero Raw Audio Retention. Replaceable NLU adapter with Pydantic extraction. |
| **Stage 5** | Intelligent Planning & Task Management | **Complete** | Deterministic DAG topological scheduler (Kahn's algorithm) with cycle detection, interval capacity math, and human review card. |
| **Stage 6** | Contextual Memory & Privacy | **Complete** | Privacy preference store (`/api/v1/memory/preferences`) with explicit consent and right-to-be-forgotten deletion. |
| **Stage 7** | System Integration & Deployment | **Complete** | Docker Compose orchestration (`docker-compose.yml`), frontend & backend Dockerfiles, and `.env.example`. |
| **Stage 8** | Testing & Quality Assurance | **Complete** | 12 automated unit and integration tests passing (`python -m pytest backend/tests`). Next.js production build (`next build`) passing with 0 errors. |
| **Stage 9** | Deployment Runbook | **Complete** | Production runbook documented in `DEPLOYMENT.md`. |

---

## 🚀 Getting Started

### 1. Run Automated Test Suite
```bash
python -m pytest backend/tests -v
```

### 2. Run Backend (FastAPI)
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Frontend (Next.js 14)
```bash
cd frontend
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

### 4. Or Run with Docker Compose
```bash
docker compose up --build
```

---

## 🔒 Security & Privacy Guarantees

1. **Zero Audio Retention:** Spoken audio streams are held exclusively in volatile RAM buffers during ASR processing and purged immediately upon response generation.
2. **Strict RLS Policies:** Every database table enforces Row-Level Security ensuring tenant data isolation.
3. **Idempotency Protection:** All proposal approvals require client-generated idempotency keys to eliminate double-booking or duplicated task creation.
4. **Deterministic Scheduling:** All calendar conflict detection and topological sort calculations are deterministic. The LLM does not hallucinate time slots.
