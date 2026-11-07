# 14 — Provisional MVP Scope & Functional Boundaries

## 1. Executive Summary
This document establishes the provisional **Minimum Viable Product (MVP)** boundaries for Project **THOZHI**. 

The goal of the MVP is not to build a bloated competitor to Motion or Todoist. The goal is to build the smallest possible software artifact capable of validating the core value loop:
$$\text{Spoken Tanglish Thought} \longrightarrow \text{Accurate Task & Conflict Extraction} \longrightarrow \text{Actionable Proposal Card} \longrightarrow \text{User Approval}$$

Using the **MoSCoW Prioritization Framework**, all capabilities are strictly segregated into:
- **P0: Must-Have (Core MVP)**
- **P1: Should-Have (Stage 2 Post-Validation)**
- **P2: Could-Have (Future Roadmap)**
- **Out of Scope: Strictly Prohibited in MVP**

---

## 2. MoSCoW Functional Boundary Breakdown

| Capability Domain | P0: Must-Have (Core MVP) | P1: Should-Have (Stage 2) | P2: Could-Have (Roadmap) | Out-of-Scope (Anti-Scope) |
| :--- | :--- | :--- | :--- | :--- |
| **User Authentication** | Simple Magic Link / Supabase Auth (Email + Google OAuth). Zero-friction onboarding. | Multi-factor authentication; enterprise SSO (SAML/Okta). | Social logins (Apple, GitHub). | Complex enterprise team RBAC, workspace organizations, user roles. |
| **Input Methods** | 1. Audio recording via browser Web Audio API (Mono 16kHz WAV).<br>2. Typed text input box (supporting Tanglish & English). | File upload (pre-recorded `.mp3` / `.m4a` / WhatsApp audio forward). | Telegram / WhatsApp bot webhook ingestion. | Real-time continuous streaming microphone listening (hotword "Hey Thozhi"). |
| **Speech Recognition (ASR)** | Gnani Prisma REST STT (with automated failover to Sarvam AI Saaras API). Batch audio transcription. | Real-time streaming WebSocket transcription with live interim text display. | Custom phonetic acoustic tuning on regional accents. | On-device offline ASR models (Whisper.tflite). |
| **Semantic & Intent Extraction** | Gemini 2.0 Flash with Pydantic JSON schema: Extracts Title, Modality (Commitment vs Idea vs Wish), Estimated Duration, Deadline ISO, Dependencies. | Multi-turn conversational clarification for ambiguous tasks. | Sentiment analysis, stress level detection. | Autonomous web research or external agentic tool use. |
| **Conflict & Planning Engine** | **Deterministic Python Module:**<br>1. Calculates working hours free time.<br>2. Checks $\sum \text{Durations} > \text{Capacity}$.<br>3. Topological Sort for DAG dependencies.<br>4. Flags circular dependencies and overloaded days. | Heuristic bin-packing that assigns tasks to specific morning/afternoon time-blocks. | Machine-learning personalized duration estimation based on historical completion time. | Autonomous calendar rescheduling without human approval (the Motion failure mode). |
| **Proposal Review & Approval UI** | **The Core Approval Card:**<br>Displays extracted tasks with category tags, estimated durations, and red warning badges for conflicts. One-click "Approve All", inline edit, and one-click "Reject/Postpone". | Drag-and-drop manual re-ordering of proposed tasks. | Interactive voice corrections (*"Change that 4 PM task to 5 PM"*). | Gamification, streak counters, badges, confetti animations. |
| **Task Persistence & Memory** | Supabase PostgreSQL tables: `tasks`, `user_profiles`, `daily_plans`. Approved tasks saved with status (`PENDING`, `DONE`, `CANCELLED`). | Local-first sync with IndexedDB / offline caching. | Semantic hybrid memory via `pgvector` for past notes search. | Complex multi-project Jira-style issue tracking, sprint boards, Gantt charts. |
| **Calendar Synchronization** | Basic `.ics` calendar export OR one-way push of approved tasks to user's Google Calendar. | Bi-directional real-time Google & Outlook Calendar two-way sync. | Multi-calendar corporate conflict checking. | Building a custom proprietary calendar view that replaces Google Calendar. |

---

## 3. Explicit Anti-Scope: What THOZHI Will NOT Build in the MVP

To prevent engineering failure, the team must adhere to the following **Strict Anti-Scope Directives**:

1. **NO Autonomous Calendar Rescheduling:**  
   THOZHI will never move an event or task on a user's calendar without an explicit human tap. The core differentiator is **human agency**.
2. **NO Proprietary Full-Featured Calendar:**  
   THOZHI will not build a month-view/week-view calendar grid from scratch. Users will view their daily schedule in standard Google Calendar or as an interactive daily checklist proposal in THOZHI.
3. **NO Social Collaboration or Chat:**  
   No shared team tasks, assignment delegation, or internal team messaging. THOZHI is strictly a single-player personal planning assistant for the MVP.
4. **NO Native Mobile App Development (Initially):**  
   Do not build separate Swift/Kotlin native codebases in Stage 1. Build a high-performance Progressive Web App (PWA) with responsive mobile layouts. Native wrappers (React Native / Capacitor) are reserved for Stage 2.
5. **NO Complex Project Management Hierarchy:**  
   No epics, sprints, story points, custom issue types, or burndown charts. Tasks are discrete commitments with durations and deadlines.

---

## 4. Provisional System Data Model (Schema Design Specification)

```
┌────────────────────────────────────────────────────────┐
│ PROVISIONAL DATA MODEL ENTITIES (POSTGRESQL)           │
├────────────────────────────────────────────────────────┤
│ 1. users                                               │
│    - id (UUID, PK)                                     │
│    - email (VARCHAR)                                   │
│    - timezone (VARCHAR, default 'Asia/Kolkata')        │
│    - working_hours_start (TIME, default '09:00')       │
│    - working_hours_end (TIME, default '18:00')         │
│                                                        │
│ 2. raw_captures                                        │
│    - id (UUID, PK)                                     │
│    - user_id (UUID, FK -> users.id)                    │
│    - input_type ('AUDIO' | 'TEXT')                     │
│    - raw_audio_url (VARCHAR, nullable)                 │
│    - transcript_text (TEXT)                            │
│    - asr_provider ('GNANI' | 'SARVAM')                 │
│    - created_at (TIMESTAMPTZ)                          │
│                                                        │
│ 3. task_proposals                                      │
│    - id (UUID, PK)                                     │
│    - capture_id (UUID, FK -> raw_captures.id)          │
│    - raw_snippet (TEXT)                                │
│    - proposed_title (VARCHAR)                          │
│    - modality ('COMMITMENT' | 'IDEA' | 'CONDITIONAL')  │
│    - estimated_duration_min (INT)                      │
│    - target_deadline (TIMESTAMPTZ, nullable)           │
│    - dependencies (TEXT[])                             │
│    - conflict_flags (TEXT[])                           │
│    - approval_status ('PENDING'|'APPROVED'|'REJECTED') │
│                                                        │
│ 4. saved_tasks                                         │
│    - id (UUID, PK)                                     │
│    - user_id (UUID, FK -> users.id)                    │
│    - proposal_id (UUID, FK -> task_proposals.id)       │
│    - title (VARCHAR)                                   │
│    - scheduled_date (DATE)                             │
│    - scheduled_start (TIME, nullable)                  │
│    - status ('PENDING' | 'COMPLETED' | 'POSTPONED')    │
│    - completed_at (TIMESTAMPTZ, nullable)              │
└────────────────────────────────────────────────────────┘
```

---

## 5. Scope Approval Checklist

- [x] Does the MVP strictly test the core hypothesis? **Yes.**
- [x] Can the MVP be built without enterprise sales cycles? **Yes.**
- [x] Does the MVP protect user agency? **Yes ("AI proposes, user decides").**
- [x] Are third-party dependencies de-risked with fallbacks? **Yes (Sarvam fallback for Gnani).**
- [x] Is the scope achievable for a lean engineering team? **Yes (approx 4–6 weeks for architecture and implementation).**

