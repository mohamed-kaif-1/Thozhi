# 13 — Assumptions & Open Product Decisions Register

## 1. Document Control & Objective
- **Document Stage:** Stage 1 — Architecture & Strategy
- **Product:** THOZHI
- **Status:** Architecture Specification (Implementation Prohibited)
- **Objective:** Track all architectural assumptions, differentiate validated choices from hypotheses, and present unresolved product decisions requiring explicit human project owner determination.

---

## 2. Active Technical & Behavioral Assumptions

| Assumption ID | Domain | Assumption Statement | Risk Rating | Evidence Status | Falsification / Failure Impact |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **ASSUMP-01** | Technical | Selected benchmarked NLU model (e.g. Gemini 1.5 Flash / GPT-4o-mini) reliably maintains $<10\%$ Concept Error Rate on Tanglish text across all regional dialects. | Medium | **Synthetic Verified** (Requires live acoustic validation). | System prompts must be tuned with dialect-specific few-shot exemplars. |
| **ASSUMP-02** | Behavioral | Bilingual professionals are willing to review a structured Proposal Card before tasks are saved. | High | **Secondary Supported** (Motion backlash validates agency preference). | If users find reviewing tedious, system must support "Quick Auto-Approve" for non-conflicting tasks. |
| **ASSUMP-03** | Technical | Gnani Prisma v3 challenge credits will remain active throughout development and testing. | Critical | **Unverified Operational Dependency**. | System immediately fails over to Sarvam AI Saaras API without downtime. |
| **ASSUMP-04** | UX | Mobile Web Audio API captures adequate acoustic quality on budget Android headsets in noisy environments. | Medium | **Pending Field Audio Benchmark**. | Frontend must implement client-side audio level meters and noise warning alerts. |
| **ASSUMP-05** | Market | Bilingual Indian freelancers possess a non-zero willingness to pay ($\ge ₹299/\text{mo}$) for time-saving software. | High | **Unverified Hypothesis** (Pending Field Interviews). | Business model must pivot to B2B team licensing or ad-supported freemium. |

---

## 3. Unresolved Product Decisions Requiring Project Owner Sign-Off

### Decision 1: Final Beachhead Target Persona
- **Context:** Stage 0 research identified Freelancers & Solo Consultants as the most commercially viable beachhead, while early exploratory notes considered ASHA healthcare workers and College Students.
- **Option 1A: Bilingual Freelancers & Solo Consultants (Recommended)**  
  *Pros:* Direct financial ROI for time saved; validated software expense habits; no enterprise SSO blockers.  
  *Cons:* High capture friction; entrenched WhatsApp self-chat habits.
- **Option 1B: Final-Year College Students & Aspirants**  
  *Pros:* Very easy to recruit; high campus virality; rapid feedback loops.  
  *Cons:* Near-zero willingness to pay; seasonal churn upon graduation.
- **Option 1C: ASHA Healthcare / Community Field Workers**  
  *Pros:* Exceptional social impact; clear voice-first utility.  
  *Cons:* Completely unvalidated in field research; constrained by government reporting systems and state health ministry IT mandates.
- **Owner Action Required:** Select primary beachhead persona prior to Stage 2 UI screen design.

---

### Decision 2: Web Application (PWA) vs. Native Mobile Wrapper (React Native)
- **Context:** The current technical constraint specifies a Next.js web application. However, voice capture often occurs while commuting or walking, where opening a browser tab introduces friction compared to a lock-screen widget.
- **Option 2A: Progressive Web App (Next.js PWA) (Recommended for Stage 1)**  
  *Pros:* Single codebase; fastest development velocity; zero app store friction; runs on low-spec developer hardware.  
  *Cons:* No iOS lock-screen recording widget; background audio recording sandboxed by mobile browsers.
- **Option 2B: Native Mobile Wrapper (Capacitor / Expo) in Stage 2**  
  *Pros:* Direct home-screen audio widget; push notifications.  
  *Cons:* Doubles frontend build complexity; requires Android/iOS development toolchains.
- **Owner Action Required:** Confirm whether Stage 1 MVP remains strictly Web PWA, with mobile wrappers deferred to Stage 2.

---

### Decision 3: Transcript Retention Baseline Policy
- **Context:** While raw audio is destroyed immediately post-ASR (Zero-Retention), text transcripts can either be retained for user review or purged to maximize privacy under the DPDP Act.
- **Option 3A: 30-Day Rolling Window (Recommended)**  
  *Pros:* Allows users to search past thoughts; balance between utility and privacy.
- **Option 3B: Immediate Purge on Approval**  
  *Pros:* Maximum privacy; zero sensitive client text retained in database.  
  *Cons:* User cannot review raw thoughts once tasks are approved.
- **Owner Action Required:** Specify default transcript retention duration.

---

### Decision 4: Gnani Challenge Account Verification & Quota Caps
- **Context:** Gnani Prisma v3 REST endpoint requires `X-API-Key-ID`. Challenge account rate limits and total allocated audio hours have not been inspected by the engineering team.
- **Owner Action Required:** Log into the Gnani developer portal or inspect challenge onboarding email to confirm:
  1. Exact monthly audio hour quota.
  2. Concurrency limit (requests per second).
  3. Quota expiration date.

