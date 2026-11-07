# 12 — Stage 0 Product & Technical Risk Register

## 1. Executive Summary
This document provides a comprehensive risk assessment for Project **THOZHI**. Risks are identified across six domains:
1. **Technical & Algorithmic Risks (TECH)**
2. **Product & UX Adoption Risks (UX)**
3. **Market & Commercialization Risks (MKT)**
4. **Data Privacy & Regulatory Risks (PRIV)**
5. **Operational & Third-Party Dependency Risks (OPS)**
6. **Execution & Scope Creep Risks (EXEC)**

**Risk Scoring Formula:** $\text{Severity Score} = \text{Probability (1–5)} \times \text{Impact (1–5)}$  
- **Red Zone (15–25):** Critical threats that can terminate the project; requires immediate mitigation.
- **Amber Zone (8–14):** Significant risks requiring architectural or operational controls.
- **Green Zone (1–7):** Manageable operational risks.

---

## 2. Master Risk Register

| Risk ID | Domain | Risk Description | Prob (1-5) | Imp (1-5) | Score | Root Cause | Preventative Mitigation | Contingency Action / Fallback | Early Warning Trigger |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| **R-TECH-01** | TECH | **Gnani Prisma Account Access Lockout:** Inability to provision self-serve API keys or exhaustion of challenge credits. | 4 | 5 | **20 (RED)** | Gnani operates strictly as an enterprise sales provider without a self-serve credit card checkout. | Abstract backend ASR behind a generic provider interface. | **Immediately switch to Sarvam AI (Saaras API)**, which has instant self-serve pricing (₹0.49/min). | Challenge key returns `401 Unauthorized` or takes $> 48\text{h}$ to renew. |
| **R-MKT-01** | MKT | **Zero Consumer Willingness-to-Pay (WTP):** Retail users refuse to pay $\ge ₹299/\text{mo}$ for an independent task assistant when WhatsApp and Google Calendar are free. | 4 | 5 | **20 (RED)** | High price sensitivity in Indian consumer tech; habituation to ad-funded free utilities. | Target high-pain Freelancers / Solo Consultants who expense tools for business ROI. | Pivot to a B2B SaaS model or freemium affiliate/calendar integration model. | User research interviews (Task 0.1.4) show $0\%$ of participants have ever paid for a productivity tool. |
| **R-TECH-02** | TECH | **ASR Concept Error Rate (CER) on Tanglish Speech:** Spoken Tamil-English phonetics transcribed incorrectly, corrupting task titles and dates. | 3 | 4 | **12 (AMBER)** | Non-standardized phonetic spelling in Latin script; acoustic noise in Tier-2 accents. | Configure ASR in Native/Code-Mix script mode; ground downstream LLM with phonology correction prompts. | Allow rapid one-tap audio replay and manual inline title editing on the proposal review card. | Concept error rate on synthetic audio test-bed exceeds $15\%$. |
| **R-TECH-03** | TECH | **LLM Temporal Arithmetic & Scheduling Hallucinations:** Pure LLM schedules overlapping tasks or miscalculates available calendar hours. | 4 | 4 | **16 (RED)** | Autoregressive language models cannot reliably solve multi-variable constraint satisfaction problems (bin-packing). | **Strictly decouple LLM from scheduling.** LLM extracts entities; Python deterministic algorithms (DAG/CSP) calculate time. | Enforce schema validation: Reject any schedule generated purely by LLM text without algorithmic validation. | Any test run where two tasks are scheduled into the same calendar minute. |
| **R-UX-01** | UX | **Mobile Web Audio Permission & Capture Friction:** Web application (Next.js) cannot provide lock-screen audio capture or background listening on mobile OS. | 4 | 4 | **16 (RED)** | Apple iOS WebKit and Android Chrome sandbox background microphone recording for web apps. | Build PWA with fast audio caching; optimize for quick 1-tap web recording when open. | Stage 2 mobile wrapper (React Native / Flutter) to enable home screen lock-screen audio widgets. | Test users report that opening browser $\rightarrow$ typing URL $\rightarrow$ tapping record takes too long compared to WhatsApp. |
| **R-UX-02** | UX | **Proposal Review Fatigue ("Too Many Clicks"):** Users find reviewing, editing, and approving proposed tasks more tedious than typing them. | 3 | 4 | **12 (AMBER)** | Bad UI design that forces 5 separate approval clicks for a 3-task voice dump. | Implement a **"Batch Approve All Valid"** single-tap action with prominent veto swipe gestures. | Streamline proposal card to show only conflicts and missing data; auto-approve non-conflicting tasks. | Beta users abandon the proposal review step on $\ge 30\%$ of sessions. |
| **R-PRIV-01** | PRIV | **Audio & Personal Task Data Exposure:** Recording sensitive personal, legal, or financial thoughts via cloud third-party APIs. | 2 | 4 | **8 (AMBER)** | Spoken rambles contain sensitive PII (client names, account numbers, family medical details). | Strip audio immediately after transcription; enforce strict data retention zero-logging policies with LLM/ASR vendors. | Provide client-side local audio deletion; encrypt task text at rest in Supabase using AES-256. | User objection during interview consent phase regarding voice recording privacy. |
| **R-MKT-02** | MKT | **Big Tech Feature Encroachment:** Google Gemini or Apple Intelligence releases colloquial Tanglish voice task capture directly into OS. | 3 | 4 | **12 (AMBER)** | Apple Intelligence and Google Gemini are advancing multimodal OS-level integrations. | Focus differentiation on **conflict detection math** and **agency ("AI proposes, user decides")**, which OS tools lack. | Position THOZHI as a specialized power-planning layer that connects to Google/Apple calendars rather than competing on basic capture. | Google announces native Tanglish NLP task parsing inside Google Tasks. |
| **R-EXEC-01**| EXEC | **Stage 0 Scope Creep & Early Coding Temptation:** Engineering team starts coding frontend/backend before human problem validation is approved. | 3 | 4 | **12 (AMBER)** | Developer instinct to "build first, ask questions later." | Strict enforcement of Stage 0 Master Execution Prompt rules; zero application repositories initialized. | Human project owner audits repository to guarantee only research artifacts exist in `research/stage-0/`. | Any commit introducing `package.json`, `main.py`, or UI prototypes before human gate sign-off. |

---

## 3. High-Priority Risk Mitigation Playbooks

### 3.1 Playbook RED-01: Gnani Prisma Decoupling (R-TECH-01)
1. **Immediate Architectural Action:** Define an abstract ASR interface in the technical design.
2. **Benchmark Test:** Run parallel evaluations of identical Tanglish audio clips through both Gnani Prisma and Sarvam AI Saaras.
3. **Trigger Point:** If challenge credentials for Gnani are not delivered or are rate-limited during early prototyping, transition primary routing to Sarvam AI without altering any downstream LLM or database code.

### 3.2 Playbook RED-02: LLM Scheduling Drift (R-TECH-03)
1. **Mandatory Architectural Rule:** Never pass a prompt like: *"Generate a schedule for these tasks: 9 AM to 5 PM."* to an LLM.
2. **Correct Pipeline:**
   - LLM: `Input Text` $\rightarrow$ `JSON {title, duration_min, deadline_iso, dependencies}`.
   - Python Backend: Calculate interval intersections, perform Kahn's DAG topological sort, check for deficit:
     $$\text{Deficit} = \sum \text{Durations} - \text{Available Free Window}$$
   - Python Backend: Format schedule proposal into a deterministic JSON object.
   - Frontend: Render proposal card for human approval.

### 3.3 Playbook RED-03: Mobile Web Friction (R-UX-01)
1. **MVP Boundary Realism:** Acknowledge in the Stage 0 report that a Next.js web application is a desktop/laptop or active mobile-browser utility.
2. **Validation Requirement:** During field interviews, determine whether users plan their day at a desk/laptop (where web apps excel) or exclusively while driving/walking (where native mobile widgets are mandatory).
3. **Contingency:** If field data proves desk usage is $<20\%$, the project owner must mandate a cross-platform mobile shell (React Native / Expo) for Stage 1.

