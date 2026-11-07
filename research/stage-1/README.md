# THOZHI — Stage 1 System Architecture & Technical Design Specification

## Overview

- **Project:** THOZHI (Multilingual AI-Powered Personal Planning Assistant)
- **Stage:** 01 — Product Requirements, System Architecture & Detailed Technical Specification
- **Status:** Architectural Specification Complete (Implementation Strictly Prohibited)
- **Scope Authority:** Human Project Owner Exclusively
- **Root Directory:** `research/stage-1/`

---

## Executive Summary of Stage 1

Following the Stage 0 Problem Discovery and Independent Evidence Audit ([`research/stage-0/`](file:///c:/Users/moham/OneDrive - ELCOT/Projects/Thozhi/research/stage-0/README.md)), Stage 1 formalizes the technical and architectural blueprint for THOZHI. 

This stage takes the core validated premise—**bilingual conversational capture in Tamil/Tanglish/English, deterministic capacity and dependency verification, and human-in-the-loop governance ("The AI proposes. The user decides.")**—and translates it into an exhaustive, implementation-ready engineering specification.

The architecture is explicitly designed as a **clean, modular monolith** deployable on standard development hardware and cloud-native serverless infrastructure (Next.js + FastAPI + Supabase PostgreSQL), deliberately avoiding unnecessary distributed systems overhead (no Kubernetes, no Redis, no microservices, no heavy multi-agent frameworks).

---

## Document Index & Traceability Map

| File | Document Title | Primary Contents & Focus |
| :--- | :--- | :--- |
| [`01_PRODUCT_REQUIREMENTS_DOCUMENT.md`](./01_PRODUCT_REQUIREMENTS_DOCUMENT.md) | **Product Requirements Document (PRD)** | Problem framing, reconciled user personas (Freelancers vs. Students vs. ASHA), feature tiers, user journeys, and acceptance metrics. |
| [`02_PRODUCT_WORKFLOW_SPECIFICATION.md`](./02_PRODUCT_WORKFLOW_SPECIFICATION.md) | **Product Workflow Specification** | Complete state transitions across the 10-step lifecycle: Capture $\rightarrow$ NLU $\rightarrow$ Constraint Math $\rightarrow$ Proposal Card $\rightarrow$ User Decision $\rightarrow$ Execution. |
| [`03_FUNCTIONAL_REQUIREMENTS.md`](./03_FUNCTIONAL_REQUIREMENTS.md) | **Functional Requirements Specification** | Exhaustive FR catalog (FR-01 to FR-42) covering input modalities, intent taxonomy, constraint validation, approval logic, and memory controls. |
| [`04_NON_FUNCTIONAL_REQUIREMENTS.md`](./04_NON_FUNCTIONAL_REQUIREMENTS.md) | **Non-Functional Requirements (NFR)** | Latency budgets (ASR $<1.5\text{s}$, LLM $<1.2\text{s}$), throughput, DPDP Act compliance, WCAG 2.1 accessibility, and uptime metrics. |
| [`05_SYSTEM_ARCHITECTURE.md`](./05_SYSTEM_ARCHITECTURE.md) | **System Architecture & C4 Models** | C4 Context & Container diagrams, modular monolith structure, dataflow pipelines, component interaction diagrams, and hardware footprint. |
| [`06_DATABASE_ARCHITECTURE.md`](./06_DATABASE_ARCHITECTURE.md) | **Database Architecture & Schema** | Complete PostgreSQL DDL, relational entities, constraints, Row-Level Security (RLS) policies, indexes, and pgvector schema evaluation. |
| [`07_AI_ARCHITECTURE.md`](./07_AI_ARCHITECTURE.md) | **AI & LLM Pipeline Specification** | Gnani Prisma v3 STT integration, Sarvam Saaras failover adapter, Replaceable NLU extraction adapter, Pydantic schemas, and Tanglish prompts. |
| [`08_MEMORY_ARCHITECTURE.md`](./08_MEMORY_ARCHITECTURE.md) | **Memory & Context Architecture** | Three-layer memory model: Operational Task Memory, User-Controlled Explicit Memory, and Contextual Summaries; strict deletion protocols. |
| [`09_API_SPECIFICATION.md`](./09_API_SPECIFICATION.md) | **API Contracts & OpenAPI Schema** | Comprehensive OpenAPI 3.1 REST contracts for captures, proposals, tasks, conflicts, and calendar syncing, with sample payloads. |
| [`10_SECURITY_AND_PRIVACY.md`](./10_SECURITY_AND_PRIVACY.md) | **Security, Privacy & DPDP Compliance** | Zero-retention audio policy, transcript privacy, encryption at rest/transit, Supabase JWT auth, rate limiting, and synthetic challenge data. |
| [`11_TESTING_AND_EVALUATION_STRATEGY.md`](./11_TESTING_AND_EVALUATION_STRATEGY.md) | **Testing & Evaluation Strategy** | Test suites for intent classification, negation parsing, Tanglish ASR Concept Error Rate, Kahn's DAG cycle detection, and approval enforcement. |
| [`12_TECHNICAL_DECISION_RECORDS.md`](./12_TECHNICAL_DECISION_RECORDS.md) | **Technical Decision Records (TDR)** | Architectural TDRs (TDR-01 to TDR-10) with context, options considered, trade-offs, consequences, costs, and reversibility ratings. |
| [`13_ASSUMPTIONS_AND_OPEN_DECISIONS.md`](./13_ASSUMPTIONS_AND_OPEN_DECISIONS.md) | **Assumptions & Open Decisions** | Traceability matrix linking Stage 0 findings to architectural decisions; open product decisions requiring human owner approval. |
| [`14_STAGE_1_ARCHITECTURE_REVIEW.md`](./14_STAGE_1_ARCHITECTURE_REVIEW.md) | **Stage 1 Architecture Review & Readiness** | Cross-document consistency verification, contract parity audit, complexity check, and formal Stage 2 readiness assessment. |

---

## Strict Architectural Governance

In strict accordance with the Stage 1 Master Execution Prompt:
1. **Zero application code** has been or will be written in this stage.
2. **Zero dependencies or packages** (`npm`, `pip`, `poetry`, `uv`) have been installed.
3. **Zero database migrations or cloud services** have been provisioned.
4. **No external paid API endpoints** have been invoked.
5. All specifications remain strictly bound by the core tenet: **The AI proposes. The user decides.**

