# THOZHI — Stage 0 Research & Validation Documentation Repository

## Stage Overview

- **Project:** THOZHI (Proposed Multilingual AI-Powered Personal Planning Assistant)
- **Stage:** 0 — Product Validation, Competitive Research & Problem Approval
- **Status:** Complete (Research & Technical Feasibility) / PENDING (Human Field Interviews)
- **Mode:** Research, Analysis, and Documentation Only
- **Implementation Status:** STRICTLY PROHIBITED (Zero application code, zero DB migrations, zero component prototyping)
- **Decision Authority:** Human Project Owner Exclusively

---

## Purpose of this Repository

This repository hosts the complete independent product research, competitive benchmarking, technical feasibility, and problem validation artifacts for Project **THOZHI**. 

The investigation was conducted by an independent senior research and product validation team acting across six disciplines:
1. **Product Research Lead:** Hypothesis formulation, user problem definition, and scoping boundaries.
2. **Market and Competitor Research Analyst:** Primary competitor teardown, substitute workflow analysis, and feature differentiation matrix.
3. **UX Researcher:** Behavioral research protocols, Mom-Test interview guides, screening criteria, and privacy ethics.
4. **AI Product Architect:** Natural language understanding, intent extraction architectures, temporal reasoning, and LLM evaluation.
5. **Technical Feasibility Analyst:** Gnani Prisma ASR analysis, Sarvam/Whisper fallbacks, deterministic scheduling math, and API cost modeling.
6. **Critical Product Reviewer:** Red-teaming assumptions, identifying product weaknesses, stress-testing failure modes, and establishing falsification criteria.

---

## Directory Index

| File | Document Title | Primary Objective & Description |
| :--- | :--- | :--- |
| [`00-stage-overview.md`](./00-stage-overview.md) | **Stage 0 Master Execution Tracker** | Comprehensive phase/task progress tracker, execution governance, and strict rule compliance audit. |
| [`01-problem-hypothesis.md`](./01-problem-hypothesis.md) | **Problem Hypothesis & Definition** | Investigation of core cognitive overload hypothesis, situational breakdowns, consequences, and disconfirming criteria. |
| [`02-assumption-register.md`](./02-assumption-register.md) | **Comprehensive Assumption Register** | Exhaustive catalog of product, technical, behavioral, and market assumptions with risk ratings and falsification triggers. |
| [`03-opportunity-analysis.md`](./03-opportunity-analysis.md) | **Four Opportunity Hypotheses Analysis** | Independent evaluations of Commitment Understanding (A), Realistic Planning (B), Conflict Detection (C), and Multilingual Context (D). |
| [`04-target-user-analysis.md`](./04-target-user-analysis.md) | **Target User Segment Comparison** | Comparative scoring of 5 demographic segments; beachhead market selection and rationale. |
| [`05-interview-guide.md`](./05-interview-guide.md) | **User Research & Interview Protocol** | Structured 10–15 minute behavioral interview guide (Mom-Test compliant), recruitment criteria, notes template, and consent framework *(Status: PENDING HUMAN EXECUTION)*. |
| [`06-competitor-analysis.md`](./06-competitor-analysis.md) | **Direct Competitor Deep-Dive** | 18-dimension breakdown of Todoist/Ramble, Gemini+Tasks, Microsoft To Do, Motion, Reclaim, AudioPen, Saner.ai, and Goblin Tools. |
| [`07-substitute-analysis.md`](./07-substitute-analysis.md) | **Substitute Solutions & Friction Analysis** | Why users default to WhatsApp self-chat, paper notebooks, voice memos, calendar blocks, and general LLMs; switching cost barriers. |
| [`08-technical-feasibility.md`](./08-technical-feasibility.md) | **Technical Feasibility & Pipeline Architecture** | System pipeline feasibility, deterministic scheduling math (DAG / CSP) vs. LLM probabilistic hallucination, and hybrid planning logic. |
| [`09-gnani-integration-research.md`](./09-gnani-integration-research.md) | **Gnani Prisma STT Integration Analysis** | In-depth analysis of Prisma v2.5/v3.0, account access barriers, pricing realities, latency, and contingency fallbacks (Sarvam AI / Whisper). |
| [`10-llm-comparison.md`](./10-llm-comparison.md) | **LLM Comparative Evaluation** | Benchmark comparison of Gemini 2.0/1.5 Flash, Claude 3.5 Haiku, GPT-4o-mini, and Llama 3.3 for structured JSON extraction and code-mixed Tamil. |
| [`11-synthetic-test-scenarios.md`](./11-synthetic-test-scenarios.md) | **18 Synthetic Research Scenarios** | Test-bed scenarios covering edge cases: negations, mid-stream corrections, conditional commitments, Tanglish rambles, and schedule churn. |
| [`12-risk-register.md`](./12-risk-register.md) | **Product & Technical Risk Register** | Matrix of technical, market, adoption, UX, and operational risks with probability, severity, and mitigation playbooks. |
| [`13-evidence-gap-register.md`](./13-evidence-gap-register.md) | **Evidence Gap & Uncertainty Register** | Itemized inventory of unverified claims, missing data, and human field dependencies required prior to Stage 1. |
| [`14-provisional-mvp-scope.md`](./14-provisional-mvp-scope.md) | **Provisional MVP Scope & Boundaries** | Strict P0 Must-Have vs. P1 Nice-to-Have vs. P2 Out-of-Scope boundaries; explicit definition of what NOT to build. |
| [`15-validation-scorecard.md`](./15-validation-scorecard.md) | **Opportunity Validation Scorecard** | Weighted empirical scoring of Opportunity Hypotheses A, B, C, and D across 9 objective criteria. |
| [`16-final-validation-report.md`](./16-final-validation-report.md) | **Stage 0 Final Validation Report & Gate Decision** | Master executive synthesis, key findings, counter-arguments, supporting evidence, and definitive **Pivot & Proceed Conditionally** recommendation. |
| [`17-independent-evidence-audit.md`](./17-independent-evidence-audit.md) | **Independent Evidence Audit** | Line-by-line verification of factual, competitive, technical, pricing, and capability claims across all documents. |
| [`18-corrected-opportunity-scorecard.md`](./18-corrected-opportunity-scorecard.md) | **Corrected Opportunity Scorecard** | Recalculated opportunity scores with decoupled desk-research vs. field-validation confidence intervals. |
| [`19-stage-0-final-decision.md`](./19-stage-0-final-decision.md) | **Stage 0 Final Decision & Governance Gateway** | Three distinct assessments (Desk Research, Problem Validation, Stage 1 Readiness) and human approval gateway. |

---

## Strict Execution Governance

In strict accordance with Stage 0 execution guidelines:
- **No application code, components, or services** were created or initialized.
- **No API keys** were configured, and **no paid APIs** were invoked.
- **No user interviews were fabricated**; all interview protocols are formally flagged as **PENDING HUMAN EXECUTION** awaiting the project owner.
- **Competitor features and pricing** were cross-verified via primary product documentation and live web research; unverified claims are explicitly noted.
- **Final approval authority** rests solely with the human project owner. Stage 1 cannot proceed until explicit sign-off is granted.
