# 13 — Evidence Gap & Uncertainty Register

## 1. Document Overview
This register catalogs all **known unknowns**, unverified hypotheses, missing empirical data, and technical uncertainties that cannot be resolved via secondary desk research alone.

Prior to authorizing **Stage 1 (Architecture & Implementation)**, the project owner must review these evidence gaps and ensure that critical blocking gaps are systematically addressed.

---

## 2. Epistemological Classification Framework

To maintain scientific integrity throughout Stage 0, every finding across our research artifacts is strictly categorized into one of five evidentiary levels:
1. **[FACT]:** Objectively verified via primary documentation, active testing, or physical law.
2. **[SECONDARY]:** Corroborated by external industry research, published benchmarks, or competitive teardowns.
3. **[SYNTHETIC]:** Evaluated against simulated research prompts and algorithmic models (not human users).
4. **[HYPOTHESIS]:** A logical deduction that appears plausible but lacks empirical proof.
5. **[EVIDENCE GAP]:** Critical data that is currently missing and requires physical field investigation.

---

## 3. Master Evidence Gap Inventory

| Gap ID | Category | Description of Unknown / Missing Evidence | Current Status | Required Closure Action | Dependency / Blocker | Criticality |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-01** | User Behavior | **Actual Willingness-to-Pay (WTP) in Target Cohort:** We know freelancers experience planning pain, but we do not have empirical proof that bilingual Indian freelancers will pay ₹299–₹499/month for a dedicated planning webapp when WhatsApp and paper are free. | **HYPOTHESIS** | Conduct 6–8 field interviews using [`05-interview-guide.md`](./05-interview-guide.md). Audit past software purchase receipts. | Human Project Owner Field Action | **BLOCKING (Fatal if 0% WTP)** |
| **GAP-02** | User Behavior | **Tanglish Usage in Professional Task Capture:** While people speak Tanglish informally, do bilingual professionals actually use Tanglish when writing down or vocalizing serious business commitments, or do they naturally revert to English? | **HYPOTHESIS** | Inspect actual user notes/WhatsApp self-chats during user interviews. | Human Project Owner Field Action | **CRITICAL (Drives Opportunity D)** |
| **GAP-03** | Technical | **Gnani Prisma Production API Credentials & Quotas:** Public documentation confirms Prisma’s existence, but exact production rate limits, challenge credit caps, and commercial pay-as-you-go pricing remain unverified. | **EVIDENCE GAP** | Project Owner to inspect Gnani challenge dashboard or contact `speechstack@gnani.ai`. | Project Owner / Gnani Sales | **CRITICAL (Drives ASR selection)** |
| **GAP-04** | Technical | **Acoustic Robustness on Low-End Microphones:** How does Indic ASR (Gnani/Sarvam) perform when audio is recorded via low-cost mobile phone headsets or laptop built-in microphones in noisy Chennai/Bengaluru street or cafe environments? | **SYNTHETIC ONLY** | Record 10 real audio samples in noisy ambient environments and benchmark Word/Concept Error Rate. | Technical Feasibility Team | **MEDIUM (UX Resilience)** |
| **GAP-05** | Product / UX | **Tolerance for Clarification Questions:** How many clarifying questions will a user tolerate when an ambiguous task is detected before they perceive the app as annoying and abandon it? | **HYPOTHESIS** | Test interactive prototypes in Stage 1 with 1 vs. 2 vs. 3 clarification prompts. | UX Research Team | **MEDIUM (UX Flow)** |
| **GAP-06** | Product / UX | **Web App vs. Mobile App Friction:** Will target freelancers adopt a browser-based web application (Next.js) for quick planning, or will they churn immediately due to the lack of an iOS/Android lock-screen voice widget? | **SECONDARY ONLY** | Survey interview participants on their device habits: Where do you plan your day—laptop or phone? | Human Project Owner Field Action | **CRITICAL (Drives platform choice)** |
| **GAP-07** | Technical | **LLM Temporal Parsing of Non-Standard Idioms:** Can Gemini 2.0 Flash reliably parse colloquial Tamil temporal phrases like *"naalaiki marunaal"* (day after tomorrow), *"inniku sayanthiram"* (this evening), and *"vara vellikilamai"* (coming Friday) without off-by-one errors? | **SYNTHETIC ONLY** | Run the 18 synthetic test scenarios through live Gemini 2.0 Flash API with structured JSON output. | Technical Feasibility Team | **HIGH (Core Planning Logic)** |

---

## 4. Pre-Stage 1 Action Plan to Close Gaps

```
┌────────────────────────────────────────────────────────┐
│ Pre-Stage 1 Gap Closure Protocol                       │
├────────────────────────────────────────────────────────┤
│ 1. Project Owner conducts 6–8 user interviews using     │
│    05-interview-guide.md (Closes GAP-01, GAP-02, GAP-06).│
│                                                        │
│ 2. Project Owner verifies Gnani challenge account      │
│    status and credit limits (Closes GAP-03).           │
│                                                        │
│ 3. Engineering team runs benchmark script on Gemini    │
│    Flash using the 18 synthetic test scenarios         │
│    (Closes GAP-07).                                    │
│                                                        │
│ 4. If GAP-01 reveals zero WTP, review Section 18 of    │
│    16-final-validation-report.md for Pivot options.    │
└────────────────────────────────────────────────────────┘
```

---

## 5. Formal Certification of Research Limitations
The Product Research team hereby certifies that:
- **No field interview findings have been fabricated.**
- **No API capabilities have been assumed without documentation.**
- All items in this register represent genuine empirical uncertainties that must be treated with intellectual honesty prior to capital investment or code development.
