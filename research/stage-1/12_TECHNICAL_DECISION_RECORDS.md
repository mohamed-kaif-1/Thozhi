# 12 — Technical Decision Records (TDRs)

## 1. Document Control & Index
This document records all foundational architectural decisions governing THOZHI. Each record documents context, alternatives, trade-offs, financial implications, and reversibility.

| Record ID | Architectural Decision Title | Status | Reversibility | Impact Level |
| :--- | :--- | :---: | :---: | :---: |
| **TDR-01** | Modular Monolith Architecture over Microservices | **APPROVED** | High | Critical |
| **TDR-02** | Python FastAPI Backend over Node.js / Go | **APPROVED** | Medium | High |
| **TDR-03** | Next.js App Router & shadcn/ui over Mobile-Native | **PROVISIONAL** | High | High |
| **TDR-04** | Supabase PostgreSQL & Row-Level Security | **APPROVED** | Medium | Critical |
| **TDR-05** | Abstract ASR Adapter with Sarvam AI Failover | **APPROVED** | High | Critical |
| **TDR-06** | Replaceable LLM Provider Adapter with Model Benchmarking | **APPROVED** | High | High |
| **TDR-07** | Deterministic Python Planning Engine over LLM Reasoning | **APPROVED** | Low (Architectural Core) | Critical |
| **TDR-08** | Deferral of `pgvector` to Stage 2 Post-Validation | **APPROVED** | High | Medium |
| **TDR-09** | Rejection of Autonomous Calendar Rescheduling | **APPROVED** | Low (Core Product Value) | Critical |
| **TDR-10** | Ephemeral Audio Zero-Retention Policy | **APPROVED** | High | High |

---

## 2. Detailed Technical Decision Records

### TDR-01: Modular Monolith Architecture over Microservices
- **Context:** Project THOZHI is developed by a lean engineering team running on constrained local hardware. Microservices introduce container orchestration overhead, network serialization latency, and deployment complexity.
- **Decision:** Build the entire backend as a single Python FastAPI modular monolith with strict domain boundaries (`routers/`, `services/`, `adapters/`, `repositories/`).
- **Alternatives Considered:** (1) Polyglot microservices with Docker Compose; (2) AWS Lambda / Serverless micro-functions.
- **Advantages:** Single process debugging; simple in-memory function calls; zero distributed transaction problems; minimal RAM footprint ($< 1.0\text{ GB}$).
- **Disadvantages:** Monolithic scaling (entire app scales together); potential coupling if domain boundaries are breached.
- **Cost Implications:** Near-zero hosting overhead; fits within a single $5/month container or free-tier PaaS.
- **Reversibility:** High. Clean domain services can be carved into microservices later if load demands it.

---

### TDR-02: Python FastAPI Backend over Node.js / Go
- **Context:** The backend coordinates speech processing, LLM structured JSON validation, and complex graph algorithms (DAG Topological Sort).
- **Decision:** Standardize on Python 3.11+ and FastAPI.
- **Alternatives Considered:** (1) Node.js / Express or NestJS; (2) Go (Golang).
- **Advantages:** Native ecosystem for AI/LLM SDKs; Pydantic v2 offers unmatched schema validation performance written in Rust; native graph libraries (`networkx` or lightweight custom DAGs).
- **Disadvantages:** Slower raw I/O execution compared to Go; Global Interpreter Lock (GIL) considerations (mitigated by `asyncio`).
- **Reversibility:** Medium.

---

### TDR-03: Next.js App Router Web Application over Mobile-Native Shell
- **Context:** Target users capture thoughts on-the-go, but building separate native iOS and Android apps in Stage 1 exceeds the MVP capacity of a small team.
- **Decision:** Build a responsive Progressive Web App (PWA) using Next.js 14 App Router, TypeScript, and shadcn/ui.
- **Alternatives Considered:** (1) React Native / Expo; (2) Flutter; (3) Pure Vite SPA.
- **Advantages:** Single cross-platform codebase; instant web deployment via Vercel; zero App Store review delays.
- **Disadvantages:** Mobile web browsers cannot capture audio from the lock-screen or run background hotword listening.
- **Reversibility:** High. A React Native wrapper can wrap the existing API in Stage 2.

---

### TDR-04: Supabase PostgreSQL & Row-Level Security (RLS)
- **Context:** The application requires multi-tenant data isolation, user authentication, and reliable relational persistence without managing custom database infrastructure.
- **Decision:** Adopt Supabase managed PostgreSQL with Row-Level Security (RLS) and Supabase Auth.
- **Alternatives Considered:** (1) Self-hosted PostgreSQL on AWS EC2; (2) MongoDB Atlas; (3) Firebase Firestore.
- **Advantages:** Enterprise-grade PostgreSQL; built-in auth JWTs; database-level security guarantee (`auth.uid() = user_id`); local dev CLI support.
- **Disadvantages:** Vendor dependency on Supabase Cloud.
- **Reversibility:** Medium (standard PostgreSQL schema can be exported to standard RDS/Cloud SQL at any time).

---

### TDR-05: Abstract ASR Adapter with Sarvam AI Failover
- **Context:** Gnani Prisma v3 is the primary Indic ASR engine, but operates under enterprise sales constraints. If challenge credits expire or latency spikes, the product breaks.
- **Decision:** Decouple ASR behind an abstract `SpeechToTextProvider` interface and implement an automated circuit-breaker failover to Sarvam AI Saaras API (₹30/hr).
- **Alternatives Considered:** (1) Hardcoding Gnani only; (2) OpenAI Whisper API only (fails on colloquial Tanglish).
- **Advantages:** 100% operational resilience; zero downtime on credit exhaustion; transparent pay-as-you-go commercial backing.
- **Disadvantages:** Maintaining two client adapter implementations.
- **Reversibility:** High.

---

### TDR-06: Replaceable LLM Provider Adapter with Model Benchmarking
- **Context:** The semantic extraction layer requires strict structured JSON output, native comprehension of Tamil script and Tanglish, and sub-second response times. As mandated by Section 8.5 of Masterprd.md, Gemini 2.0 Flash is not an approved choice due to shutdown/deprecation, and no model should be approved without empirical benchmarking.
- **Decision:** Place all NLU extraction behind a clean `NaturalLanguageUnderstandingProvider` adapter interface. Benchmark candidate models (Google Gemini 1.5 Flash, OpenAI GPT-4o-mini, Anthropic Claude 3.5 Haiku, and Meta Llama 3.3 70B) under identical synthetic evaluation datasets before locking the production default.
- **Alternatives Considered:** (1) Hardcoding OpenAI only; (2) Hardcoding Anthropic only; (3) Multi-agent framework wrappers (LangChain).
- **Advantages:** 100% vendor independence; zero code changes when switching models; allows cost/latency optimization.
- **Disadvantages:** Maintaining adapter interfaces and standardized benchmark suites.
- **Reversibility:** High.

---

### TDR-07: Deterministic Python Planning Engine over LLM Reasoning
- **Context:** Autoregressive language models frequently hallucinate time calculations, double-book slots, and violate graph dependencies when generating full schedules.
- **Decision:** Strictly forbid the LLM from generating final schedules. The LLM extracts task entities; a deterministic Python module runs Kahn’s DAG algorithm and interval deficit arithmetic.
- **Alternatives Considered:** (1) Few-shot prompting an LLM to output a 9 AM to 5 PM schedule; (2) Multi-agent debate frameworks.
- **Advantages:** 100% mathematical reliability; zero calendar overlap; explainable conflict warnings.
- **Disadvantages:** Requires maintaining algorithmic scheduling code.
- **Reversibility:** Low (Core architectural foundation of the product).

---

### TDR-08: Deferral of `pgvector` to Stage 2 Post-Validation
- **Context:** `pgvector` was provisionally proposed for semantic memory.
- **Decision:** Omit `pgvector` from Stage 1. Use purely relational B-tree indexing.
- **Alternatives Considered:** (1) Enabling `pgvector` and embedding every task in OpenAI text-embedding-3-small.
- **Advantages:** Eliminates embedding API costs; reduces RAM overhead; keeps MVP schema simple and fast.
- **Disadvantages:** Cannot perform fuzzy semantic searches across past notes in MVP.
- **Reversibility:** High. `pgvector` can be enabled with a single SQL extension toggle in Stage 2.

---

### TDR-09: Rejection of Autonomous Calendar Rescheduling ("The Anti-Motion Principle")
- **Context:** Motion auto-reschedules tasks dynamically without user input, causing user anxiety and loss of agency.
- **Decision:** Enforce the core axiom: **"The AI Proposes. The user decides."** Zero tasks enter the active schedule without an explicit human approval transaction.
- **Alternatives Considered:** (1) Autonomous auto-scheduling with undo notifications.
- **Advantages:** High user trust; elimination of calendar panic; distinct competitive positioning.
- **Disadvantages:** Requires user to review proposal cards.
- **Reversibility:** Low (Core brand and product philosophy).

---

### TDR-10: Ephemeral Audio Zero-Retention Policy
- **Context:** Processing spoken personal thoughts creates severe privacy and regulatory liability under India's DPDP Act 2023.
- **Decision:** Raw audio is processed in volatile memory and destroyed immediately post-ASR. Zero audio is stored in persistent object buckets.
- **Alternatives Considered:** (1) Retaining audio in S3 for future model fine-tuning.
- **Advantages:** Zero audio breach exposure; simplified DPDP Act compliance; zero cloud object storage costs.
- **Disadvantages:** Cannot re-transcribe past audio if a user disputes transcription accuracy.
- **Reversibility:** High.

