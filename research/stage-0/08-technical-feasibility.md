# 08 — Technical Feasibility & System Pipeline Architecture

## 1. Executive Summary
This document analyzes the end-to-end technical feasibility of the proposed **THOZHI** workflow:
$$\text{Spoken/Typed Input} \longrightarrow \text{ASR} \longrightarrow \text{NLU Entity Extraction} \longrightarrow \text{Constraint Solving} \longrightarrow \text{Proposal Card} \longrightarrow \text{User Approval} \longrightarrow \text{Task Store}$$

The central architectural finding of this feasibility analysis is:
> **Pure LLM scheduling is dangerous and technically unviable.** LLMs suffer from non-deterministic temporal arithmetic drift, inability to guarantee bin-packing feasibility, and hallucinations regarding calendar availability. Therefore, THOZHI must implement a **Strictly Hybrid Architecture**: LLMs handle linguistic parsing and semantic extraction, while deterministic algorithms (DAG Topological Sort, Constraint Satisfaction, and Interval Scheduling) handle all temporal calculations and conflict detection.

---

## 2. End-to-End Architectural Pipeline

```
[ User Input: Audio (Tanglish) or Text ]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 1. Speech Recognition Layer (ASR)                      │
│    - Primary Target: Gnani Prisma STT (REST/Streaming) │
│    - Commercial Fallback: Sarvam AI Saaras STT        │
│    - Output: Raw Transcript (Tamil Script / Latin)     │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 2. Semantic Extraction & Classification Layer (LLM)    │
│    - Engine: Gemini 2.0 Flash / GPT-4o-mini            │
│    - Strict Pydantic JSON Schema Enforcement           │
│    - Extraction: Modality (Commitment vs Idea vs Wish) │
│    - Temporal Expressions (Tamil & English Normalized) │
│    - Relative Deadlines & Explicit Dependencies        │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 3. Deterministic Planning & Constraint Engine (Code)   │
│    - Dependency Graph: Directed Acyclic Graph (DAG)    │
│    - Topological Sorting & Circular Dependency Check   │
│    - Calendar Deficit Math: Available Free Slots vs.   │
│      Sum of Estimated Durations                        │
│    - Conflict Detection Flagging (Deterministic 100%)  │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 4. Interactive Proposal & Clarification UI (Next.js)   │
│    - "AI Proposes, User Decides" Approval Card         │
│    - Interactive Toggles: Approve / Edit / Reject      │
│    - Highlighted Conflict Warnings & Missing Info      │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 5. Task Persistence & Memory Layer (Backend / DB)      │
│    - Supabase PostgreSQL (Approved Tasks Only)         │
│    - Hybrid Memory: Relational Tasks + Vector Store    │
│      (for user preferences & historical durations)     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Allocation of Responsibility: Deterministic Code vs. LLM Reasoning

A critical failure mode of modern AI products is offloading arithmetic and logical constraint satisfaction to probabilistic language models. The table below delineates the strict boundary between probabilistic and deterministic layers:

| Pipeline Capability | Optimal Approach | Technical Justification | Failure Mode if Violated |
| :--- | :--- | :--- | :--- |
| **Spoken Vernacular Transcription** | **Specialized Indic ASR** (Gnani / Sarvam) | Acoustic phonetics require dedicated training on Indian dialects and telephony channels. | General Whisper translates away or garbles Tanglish phonetics. |
| **Intent & Modality Classification** (Commitment vs. Idea) | **LLM Reasoning** (Gemini Flash) | Linguistic semantics and colloquial nuances require deep contextual language understanding. | Regex/rules fail completely on nuanced human phrasing (*"I was thinking maybe..."*). |
| **Date & Time Entity Normalization** | **LLM + Python `dateutil`** | LLM maps *"naalaiki sayanthiram 5 maniki"* to ISO-8601 relative timestamp, verified by Python code. | Off-by-one errors; timezone confusion if pure LLM does temporal arithmetic. |
| **Dependency Mapping & Validation** | **Deterministic DAG Algorithm** | Graph cycle detection (Tarjan’s or Kahn’s topological sort) guarantees no circular deadlocks ($A \rightarrow B \rightarrow A$). | LLM hallucinates non-existent prerequisites or misses direct blocking links. |
| **Calendar Deficit & Overload Math** | **Deterministic Code** | Calculating whether $\sum \text{Task Durations} > \text{Free Calendar Minutes}$ is basic arithmetic ($O(N)$). | LLMs frequently claim 8 hours of work can fit into a 4-hour window (arithmetic hallucination). |
| **Schedule Slot Assignment (Bin-Packing)** | **Deterministic Greedy / CSP** | Constraint Satisfaction Problem (CSP) / Interval Scheduling guarantees non-overlapping blocks. | LLM schedules two 1-hour tasks into the exact same 2:00 PM–3:00 PM time block. |
| **Clarification Prompt Generation** | **LLM Reasoning** | Generates empathetic, concise clarifying questions (*"Which client proposal did you mean?"*). | Rigid hard-coded forms feel robotic and irritating. |
| **Task Persistence Execution** | **Deterministic DB Transaction** | ACID transactions in PostgreSQL guarantee zero task loss or duplication. | State corruption if LLM handles data storage directly. |

---

## 4. Algorithmic Scheduling Logic: Preventing LLM Drift

To guarantee schedule feasibility, THOZHI’s scheduling module must execute the following deterministic algorithm in Python (FastAPI backend):

### 4.1 Step 1: Calendar Space Calculation
1. Fetch all external events (e.g., from Google Calendar) for target date $D$.
2. Define working hours: $[T_{\text{start}}, T_{\text{end}}]$ (e.g., 09:00 to 18:00).
3. Compute free time windows:
   $$\mathcal{W} = \{ w_1, w_2, \dots, w_k \}$$
   where each $w_i = [\text{start}_i, \text{end}_i]$ represents an unbooked calendar interval.
4. Calculate Total Free Capacity:
   $$C_{\text{free}} = \sum_{i=1}^{k} (\text{end}_i - \text{start}_i)$$

### 4.2 Step 2: Task Graph & Duration Summation
1. For extracted candidate tasks $\{t_1, t_2, \dots, t_m\}$ with estimated durations $\{d_1, d_2, \dots, d_m\}$:
   $$D_{\text{total}} = \sum_{j=1}^{m} d_j$$
2. Build Directed Acyclic Graph (DAG) based on extracted dependencies:
   $$\text{Edge } (t_a \rightarrow t_b) \implies t_a \text{ must complete before } t_b \text{ starts.}$$
3. Execute Kahn’s Algorithm:
   - If a cycle is detected $\implies$ **Raise Circular Dependency Flag** for user clarification.
   - Else $\implies$ Produce linear execution sequence $\mathcal{S}$.

### 4.3 Step 3: Deficit & Conflict Checking
- If $D_{\text{total}} > C_{\text{free}}$:
  $$\text{Deficit} = D_{\text{total}} - C_{\text{free}}$$
  $$\implies \mathbf{CRITICAL\_OVERLOAD\_FLAG}(\text{Deficit minutes})$$
- The system **DOES NOT** squeeze or truncate tasks silently. It explicitly marks low-priority tasks with a proposed postponement flag:
  > *"You have 6.5 hours of work planned, but only 4.0 hours of open time. Proposal: Postpone [Task X] and [Task Y] to tomorrow?"*

---

## 5. Technical Feasibility Scorecard & Verdict

| Component | Technical Feasibility | Primary Bottleneck / Risk | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Vernacular Audio Capture (Web)** | **Medium-High** | Browser Web Audio API mic permissions; mobile background audio restrictions. | Progressive Web App (PWA) with standard MediaStream API; audio recorded in chunks. |
| **Tanglish Speech-to-Text (ASR)** | **Medium** | Enterprise account access and credit availability on Gnani Prisma. | Pre-integrate **Sarvam AI Saaras API** as a turnkey, pay-as-you-go alternative. |
| **Structured Entity Extraction** | **Very High** | Strict adherence to JSON schema; handling date ambiguity. | Gemini 2.0 Flash structured outputs via Pydantic; fallback validation layer. |
| **Deterministic Conflict Engine** | **Very High** | Low technical risk; standard graph algorithms and interval math. | Implement lightweight Python CSP module (`pulp` or custom greedy interval packer). |
| **Interactive Proposal UI** | **Very High** | State management in Next.js; maintaining undo/redo. | React state machine (Zustand or XState) for the proposal review card. |
| **Database Persistence & Memory** | **High** | Vector similarity latency vs. relational speed. | PostgreSQL on Supabase with `pgvector` for hybrid memory. |

**Final Technical Feasibility Verdict:**  
**FEASIBLE (with strict hybrid architecture).** The proposed workflow is entirely achievable using modern web standards, provided that LLMs are restricted strictly to language parsing, and all scheduling math is governed by deterministic algorithms.

