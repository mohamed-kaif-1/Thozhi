# THOZHI (தோழி) — Multilingual AI-Powered Personal Planning Assistant

[![Python Tests](https://img.shields.io/badge/pytest-125%20passed-brightgreen.svg)]()
[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)]()
[![Primary ASR](https://img.shields.io/badge/Primary%20ASR-Gnani%20AI%20Prisma%20v3-orange.svg)]()
[![Theme](https://img.shields.io/badge/UI%20Theme-Neo--Brutalism%20Obsidian-blue.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()

> **Core Principle: "The AI proposes. The user decides."**  
> *Zero silent task creation. Zero unconfirmed schedule modifications. Zero raw audio persistence.*

---

## 📌 Product Overview

**THOZHI (தோழி)** is an intelligent multilingual personal planning assistant specifically engineered to understand natural, unstructured speech and text in **Tamil, Tanglish (Tamil-English code-mixing), and English**. 

Unlike conventional productivity tools that demand rigid form-filling, or generic AI chat assistants that hallucinate deadlines and clutter calendars, THOZHI transforms chaotic thoughts into structured, realistic action plans through a strict **proposal, clarification, and human-approval workflow**.

---

## 🏗 Complete Engineering Stages & Verification Audit

| Stage | Name | Status | Key Deliverables & Test Verification |
| :---: | :--- | :---: | :--- |
| **Stage 0** | **Product Validation & Evidence Audit** | **COMPLETE** | 20 research documents in `research/stage-0/` verifying ASR pricing, competitor capabilities, and opportunity scorecards. |
| **Stage 1** | **Product & Engineering Specification** | **COMPLETE** | 15 engineering specifications in `research/stage-1/` covering PRD, Algorithmic Specs, 14-table database schema, and security architecture. |
| **Stage 2** | **UI/UX Design System** | **COMPLETE** | Neo-Brutalism Obsidian Black (`#080B11`) theme with blue grid background, radiant amber accents, high-contrast borders, and responsive sidebar navigation. |
| **Stage 3** | **Development Foundation** | **COMPLETE** | Next.js 14 frontend initialized, FastAPI backend structure, 14 Supabase SQL migrations (`001_initial_schema.sql`, `002_rls_policies.sql`), RFC 7807 problem details handler. |
| **Stage 4** | **Core AI Understanding System** | **COMPLETE** | Primary ASR (**Gnani AI Prisma v3**) + commercial failover (**Sarvam AI Saaras v3**) dispatcher with Zero Raw Audio Retention. Gemini 2.5 Flash NLU intent extraction with Pydantic schemas. |
| **Stage 5** | **Intelligent Planning & Task Engine** | **COMPLETE** | Deterministic DAG topological scheduler (Kahn's algorithm) with cycle detection (`SchedulingCycleException`), interval capacity math, duplicate prevention, and smart rescheduling. |
| **Stage 6** | **Contextual Memory & Personalization** | **COMPLETE** | Sovereign privacy preference store (`/api/v1/memory/preferences`) with explicit consent gates, duration learning prior engine, data portability export, and right-to-be-forgotten purge. |
| **Stage 7** | **Full System Integration** | **COMPLETE** | Seamless pipeline connecting Capture $\rightarrow$ Clarification $\rightarrow$ Proposals $\rightarrow$ Tasks $\rightarrow$ Planner $\rightarrow$ Memory with real-time UI synchronization and accessible toast error boundaries. |
| **Stage 8** | **Testing, AI Evaluation & Quality Assurance** | **COMPLETE** | **65/65 passing backend tests** (`python -m pytest backend/tests -v`), Next.js production build passing with 0 errors across 18 static routes, 11 synthetic Indic scenarios evaluated, 18/18 Master PRD Section 20 criteria passed. |
| **Stage 9** | **Production Deployment & Release** | **COMPLETE** | Production runbook documented in `DEPLOYMENT.md`, multi-stage Docker build verified, standalone containerization ready for cloud deployment. |

---

## 💡 Key Architectural Capabilities

### 1. Multilingual Thought Capture (Voice & Text)
- Supports voice and text input across Tamil, Tanglish, and English.
- **Primary Speech Engine:** Authenticated **Gnani AI Prisma v3** (`https://api.vachana.ai/stt/v3`, header `X-API-Key-ID: <KEY>`, `model="prisma-v3.0"`).
- **Zero Raw Audio Retention:** Spoken audio is processed strictly in-memory and purged immediately upon transcription.

### 2. High-Fidelity Intent Classification & Uncertainty Guardrails
- Distinguishes `COMMITMENT`, `TASK`, `CONDITIONAL_INTENTION`, `IDEA`, `WISH`, `COMPLETED`, and `CANCELLED`.
- Never converts uncertain statements into confirmed tasks without explicit human review.
- Generates focused clarification questions when dates, times, or dependencies are ambiguous.

### 3. Deterministic Planning & Conflict Intelligence
- **Kahn's DAG Topological Scheduler:** Guarantees tasks with prerequisites execute in proper order. Cyclic dependencies are rejected with HTTP 422.
- **Interval Capacity Math:** Computes daily focus budgets, accounts for busy blocks, and alerts when deadlines exceed capacity (`DEADLINE_EXCEEDED`, `OVERCAPACITY`).
- **One-Click Rescheduling:** Proposes optimal postponement slots for displaced tasks during schedule shocks.

### 4. Sovereign Personal Memory & Duration Learning
- **Zero Hallucination Priors:** Analyzes historical completed tasks (estimated vs. actual duration) to suggest realistic duration buffers.
- **Sovereign Data Portability:** Downloadable full JSON archive (`POST /api/v1/memory/export`).
- **Sovereign Right to be Forgotten:** Instant, permanent wipe of all tenant tasks, proposals, and preferences (`DELETE /api/v1/memory/purge`).

---

## 🚀 Quick Start Guide

### 1. Run Automated Test Suite
```bash
python -m pytest backend/tests -v
```
All 125 tests pass in ~70 seconds.

### 2. Run Backend (FastAPI)
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Frontend (Next.js 14)
```bash
cd frontend
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

### 4. Docker Deployment
```bash
docker compose up --build -d
```

---

## 🔒 Security & Privacy Guarantees

1. **Zero Raw Audio Retention:** Audio streams are held exclusively in RAM during speech-to-text conversion and purged immediately upon response generation.
2. **Strict RLS Policies:** Every database table enforces Row-Level Security ensuring tenant data isolation.
3. **Idempotency Protection:** All proposal approvals require client-generated idempotency keys to eliminate double-booking or duplicated task creation.
4. **Deterministic Scheduling:** All calendar conflict detection and topological sort calculations are deterministic. The LLM does not hallucinate time slots.

