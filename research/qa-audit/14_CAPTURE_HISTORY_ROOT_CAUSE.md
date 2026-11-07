# THOZHI — Root Cause Analysis: Capture History, Multiple Proposals & Approval Queue Lifecycle

## 1. Executive Summary & Problem Classification

- **Component:** Thought Capture Studio & AI Proposal Review Lifecycle
- **Severity:** P1 (Core Product Workflow & Human-in-the-Loop Integrity)
- **Status:** Identified, Root Causes Isolated, Architectural Repairs Completed & Verified

### Observed Issue
When a user recorded or submitted sequential voice or text captures without immediately approving or committing the resulting proposal:
1. Capture 1 was processed and Proposal 1 was generated.
2. When Capture 2 was submitted before Proposal 1 was committed, Proposal 1 was completely overwritten and disappeared from the UI.
3. The "Recent Capture Stream" in the frontend maintained mock dummy cards (`useState` with hardcoded text) that were non-interactive.
4. Users had no means to review previous captures, inspect their associated proposals, or execute independent decisions (e.g. approve Capture 1, reject Capture 2, leave Capture 3 pending).

This violated the core THOZHI architectural invariant:
> *"The AI proposes. The user decides. Every capture is an independent record. Every proposal is an independent decision. Nothing disappears unless the user explicitly chooses an action that resolves or deletes it."*

---

## 2. Root Cause Analysis

### Root Cause 1 (Backend): Absence of First-Class `Capture` Entity & Endpoints
- **Defect:** Prior to this overhaul, the backend router `/captures/text` and `/captures/audio` ran ASR and NLU extraction directly into a `Proposal` object, completely skipping persistence of a parent `Capture` domain record.
- **Impact:**
  - No database collection for `Capture` records existed (`self.captures = {}` was absent).
  - No `GET /captures`, `GET /captures/{id}`, `DELETE /captures/{id}`, or `POST /captures/clear` endpoints existed.
  - No queue listing endpoint (`GET /proposals?status=...`) existed to query proposals awaiting user review.
  - Historical captures could neither be queried, filtered, nor hydrated on page refresh.

### Root Cause 2 (State Management): Singular Ephemeral Proposal Store
- **Defect:** `frontend/src/store/proposalStore.ts` was implemented around a singular state variable:
  ```typescript
  interface ProposalState {
    activeProposal: Proposal | null;
    itemDecisions: Record<string, ProposalItemDecision>;
    setProposal: (proposal: Proposal) => void;
  }
  ```
- **Impact:**
  - Calling `setProposal(newProposal)` completely replaced `activeProposal` with the new capture and wiped `itemDecisions` for the previous proposal.
  - Previous proposals were instantly dropped into JavaScript garbage collection.
  - Decisions could not be made independently or out of order.

### Root Cause 3 (Frontend): Mock Capture Stream & Non-Interactive UI
- **Defect:** `frontend/src/app/capture/page.tsx` maintained `recentCaptures` as a local component state initialized with hardcoded dummy strings:
  ```typescript
  const [recentCaptures, setRecentCaptures] = useState([
    { id: "1", text: "Naalaiku kaalaila 10 manikku project review...", ... },
    { id: "2", text: "Submit lab record by Friday 4 PM...", ... }
  ]);
  ```
- **Impact:**
  - The stream was cosmetic and decoupled from backend data.
  - Capture stream cards were non-clickable `<div>` elements without `onClick` handlers.
  - Clicking a previous capture did not reload its transcript or proposal into the review deck.
  - The "Clear" button merely wiped local array state without respecting backend persistence.

---

## 3. Core Architectural Fixes

### 1. Persistent Domain Model (`Capture` & `ProposalQueue`)
- Added Pydantic schemas `CaptureCreate` and `CaptureResponse` in `backend/app/schemas/capture.py` featuring:
  - `id: UUID`, `user_id: UUID`, `input_type: AUDIO | TEXT`
  - `transcript_text`, `original_transcript`, `translated_transcript`
  - `detected_language`, `processing_status`, `lifecycle_status`
  - `proposal_ids`, `proposals: List[ProposalResponse]`, `proposal_count: int`
- Added repository methods in `backend/app/db/repository.py`:
  - `create_capture(...)`
  - `get_capture(...)` with linked proposals and computed lifecycle status
  - `list_captures(...)`
  - `delete_capture(...)`
  - `clear_captures(...)` (clears stream logs while preserving tasks and proposals)
  - `list_proposals(status, capture_id, user_id)`
  - `reject_proposal(proposal_id, reason)`

### 2. Upgraded Multi-Capture & Multi-Proposal Store
- Overhauled `frontend/src/store/proposalStore.ts` to manage:
  - `captures: CaptureRecord[]`
  - `proposals: Proposal[]`
  - `activeProposalId`, `activeCaptureId`, `activeProposal`
  - `itemDecisions: Record<string, ProposalItemDecision>` (persisting decisions by item ID)
  - Actions: `loadInitialQueue()`, `selectCapture(id)`, `selectProposal(id)`, `commitActiveProposal()`, `rejectActiveProposal(reason)`, and `clearHistory()`.

### 3. Interactive Capture Stream & Decision Management
- `frontend/src/app/capture/page.tsx` now fetches real capture records from the backend.
- Every capture card is an interactive element displaying:
  - Capture type (Voice / Text)
  - Detected language
  - Lifecycle badge (`PENDING`, `COMMITTED`, `REJECTED`)
  - Relative timestamp
  - Spoken transcript & translation preview
- Filter tabs enable switching between `All`, `Pending`, `Committed`, and `Rejected`.
- Selecting any card instantly loads its transcript and associated proposal into `ProposalReviewCard`.
- `ProposalReviewCard` includes both "Commit Tasks to Schedule" and "Reject Entire Proposal", with status banners when inspecting committed or rejected proposals.
