# 02 — Comprehensive Assumption Register

## 1. Document Overview
This register catalogs all foundational assumptions underpinning Project **THOZHI**. Each assumption is categorized, risk-rated, linked to falsification triggers, and assigned an empirical verification methodology.

**Risk Rating Formula:**  
$\text{Criticality Score} = \text{Impact if False (1-5)} \times \text{Probability of Failure (1-5)}$  
- **High Risk (15–25):** Fatal to the current product concept if invalidated; requires immediate empirical de-risking.
- **Medium Risk (8–14):** Requires architectural or scope pivots if invalidated.
- **Low Risk (1–7):** Operational or cosmetic adjustments.

---

## 2. Master Assumption Matrix

| ID | Category | Assumption Statement | Impact (1-5) | Prob (1-5) | Risk Score | Current Evidence Status | Verification Method | Falsification Trigger |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A-BEH-01** | Behavioral | Users experience substantial friction from typing and categorizing tasks into existing to-do apps, causing high abandonment. | 5 | 2 | **10 (Med)** | **Secondary Evidence Strong** (Industry app retention metrics show $<15\%$ D30 retention). | User behavioral interviews (Task 0.1.4). | $\ge 50\%$ of interviewed users report being satisfied with their current manual todo app workflow. |
| **A-BEH-02** | Behavioral | Target users in Tamil Nadu / South India naturally express personal and work obligations using code-mixed Tamil-English (Tanglish) speech. | 5 | 2 | **10 (Med)** | **Linguistic Research Confirmed**; empirical usage in productivity context unverified. | User speech capture testing & interview audit. | Users state they strictly compartmentalize and only use pure English for planning tasks. |
| **A-BEH-03** | Behavioral | Users strongly prefer an interactive approval step ("AI proposes, user decides") over fully autonomous auto-scheduling. | 4 | 2 | **8 (Med)** | **Supported by Motion/Reclaim teardowns** (user backlash against autonomous calendar shifts). | Synthetic user testing & interview responses. | Users demand zero-click auto-scheduling and find reviewing proposals tedious. |
| **A-BEH-04** | Behavioral | Users struggle to distinguish between casual ideas, conditional intentions, and hard commitments in their daily notes. | 4 | 2 | **8 (Med)** | **Hypothesis**; GTD literature supports this distinction. | Task classification audit of user notes. | Users rarely write down casual ideas alongside tasks, or easily distinguish them manually. |
| **A-TECH-01** | Technical | Gnani Prisma ASR is readily accessible, cost-effective, and capable of transcribing conversational Tanglish with low word error rate (WER). | 5 | 4 | **20 (HIGH)** | **UNVERIFIED & HIGH RISK** (Gnani has no public self-serve pricing; requires enterprise sales or challenge account). | Technical integration trial & benchmark test (Task 0.2.4). | Gnani API requires prohibitive enterprise commitments ($> \$1,000/\text{mo}$) or challenge credits fail/expire; or WER on Tanglish $> 25\%$. |
| **A-TECH-02** | Technical | Modern LLMs (e.g. Gemini 2.0 Flash / GPT-4o-mini) can accurately extract structured JSON (tasks, dates, dependencies, negations) from messy code-mixed transcripts. | 5 | 2 | **10 (Med)** | **Benchmarked on English**; multilingual Indic benchmarks show higher syntax variance. | Synthetic scenario evaluation (Task 0.2.5 & Task 0.3.4). | LLM hallucinates deadlines, fails to parse Tamil temporal idioms (*"naalaiki marunaal"*), or drops dependencies $> 15\%$ of the time. |
| **A-TECH-03** | Technical | Pure LLM reasoning is insufficient for schedule generation; a hybrid deterministic algorithm (DAG / CSP) is mandatory for realistic planning. | 4 | 1 | **4 (Low)** | **Verified Fact** (LLMs suffer from arithmetic drift and non-deterministic temporal overlap errors). | Algorithmic scheduling design (Task 0.2.4). | An LLM can flawlessly solve 20-variable calendar bin-packing without mathematical drift (historically disproven). |
| **A-TECH-04** | Technical | A web application (Next.js) is an acceptable form factor for a voice-first mobile-heavy planning assistant. | 4 | 4 | **16 (HIGH)** | **QUESTIONABLE** (Voice capture on mobile web has Safari/Chrome microphone background audio limitations vs. native app). | UX feasibility analysis & user platform survey. | Users insist on instant lock-screen / widget voice capture, which mobile web cannot natively deliver. |
| **A-MKT-01** | Market | Users are willing to pay for or actively use a dedicated planning tool rather than sticking to free substitutes (WhatsApp self-chat, Apple Notes). | 5 | 4 | **20 (HIGH)** | **UNPROVEN**; consumer productivity has notorious churn and low willingness-to-pay (WTP). | Willingness-to-pay probe in interviews. | Users refuse to pay even nominal subscription fees ($\approx ₹199–₹499/\text{mo}$) or switch from free WhatsApp. |
| **A-MKT-02** | Market | Big tech (Google Gemini, Microsoft Copilot, Apple Intelligence) will not trivially commoditize this workflow in the next 12–18 months. | 4 | 4 | **16 (HIGH)** | **HIGH RISK** (Gemini already links to Google Tasks/Calendar; Todoist launched Ramble). | Competitive moat teardown (Task 0.2.1). | Gemini/Apple Intelligence natively supports colloquial Indian code-mixing for task scheduling directly on OS lock screens. |
| **A-UX-01** | UX | Users will tolerate a conversational clarification dialogue when an ambiguous task is detected, rather than abandoning the app. | 3 | 3 | **9 (Med)** | **Hypothesis**; conversational friction often degrades task entry speed. | Synthetic user journey testing. | Users abandon capture when prompted with $> 1$ clarification question. |
| **A-UX-02** | UX | Presenting a proposed schedule with conflict explanations reduces user cognitive anxiety rather than increasing cognitive burden. | 4 | 2 | **8 (Med)** | **Psychology literature supports visual clarity**, but complex UI can overwhelm. | User testing of visual proposal mockups. | Users feel more stressed looking at conflict lists than simple linear checklists. |

---

## 3. High-Priority Risk Mitigation Directives

### 3.1 Critical Technical Risk: Gnani Prisma Accessibility (A-TECH-01)
- **Risk Score:** 20 (High)
- **Action Required:** Immediate exploration of commercial-grade fallbacks with self-serve pay-as-you-go APIs. Specifically, **Sarvam AI (Saaras model)**, which provides public self-serve pricing (₹0.49/minute) and specialized Indic code-mixing support, must be architected as an active parallel integration target alongside OpenAI Whisper and Bhashini.

### 3.2 Critical Market Risk: Willingness-to-Pay & Substitute Stickiness (A-MKT-01)
- **Risk Score:** 20 (High)
- **Action Required:** Phase 0.1 interviews must explicitly probe actual past financial spending on productivity tools, not hypothetical willingness ("Have you paid for any software in the past 12 months?"). If WTP is zero, consumer B2C monetization is invalid, forcing an ad-supported, freemium, or B2B/freelancer professional pivot.

### 3.3 Critical UX/Platform Risk: Web App Form Factor vs. Native Mobile Friction (A-TECH-04)
- **Risk Score:** 16 (High)
- **Action Required:** A web application cannot provide lock-screen audio capture, instant OS widgets, or background listening on mobile OS. If users capture thoughts primarily on-the-go (driving, walking), a pure web app MVP will experience high friction compared to a Progressive Web App (PWA) with Web Audio API or a cross-platform mobile wrapper (React Native / Flutter).

