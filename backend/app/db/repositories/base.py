from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import date
from backend.app.schemas.intent import ExtractionResponse
from backend.app.schemas.proposal import (
    ProposalResponse,
    ProposalItemResponse,
    ProposalApproveRequest,
    ProposalApproveResponse,
    ProposalItemPatch,
    ProposalClarificationRequest,
)
from backend.app.schemas.capture import CaptureResponse, CaptureCreate
from backend.app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent, PlanResponse
from backend.app.schemas.memory import (
    MemoryPreferenceCreate,
    MemoryPreferenceResponse,
    MemoryPreferencePatch,
    DurationPriorSuggestion,
    UserDataExportResponse,
    DataPurgeResponse,
)

class BaseRepository(ABC):
    """
    Abstract Base Repository interface defining sovereign data operations.
    Enforces strict tenant scoping, explicit lifecycle states, and non-destructive operations.
    """
    default_user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")

    # ---------------- USER PROFILE ----------------
    @abstractmethod
    def get_user_profile(self, user_id: UUID, user_token: Optional[str] = None) -> dict:
        """Retrieves user profile dictionary."""
        pass

    @abstractmethod
    def update_user_profile(self, user_id: UUID, updates: dict, user_token: Optional[str] = None) -> dict:
        """Updates user profile and synchronizes relevant memory preferences."""
        pass

    # ---------------- CAPTURES ----------------
    @abstractmethod
    def create_capture(
        self,
        user_id: UUID,
        input_type: str,
        transcript_text: str,
        detected_language: str = "Tanglish",
        original_transcript: Optional[str] = None,
        translated_transcript: Optional[str] = None,
        processing_status: str = "COMPLETED",
        provider_metadata: Optional[dict] = None,
        user_token: Optional[str] = None
    ) -> CaptureResponse:
        """Persists a new capture record."""
        pass

    @abstractmethod
    def get_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[CaptureResponse]:
        """Retrieves a single capture record scoped to user."""
        pass

    @abstractmethod
    def list_captures(self, user_id: Optional[UUID] = None, limit: int = 20, user_token: Optional[str] = None) -> List[CaptureResponse]:
        """Lists recent capture records ordered by creation timestamp."""
        pass

    @abstractmethod
    def delete_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        """Deletes a capture record without deleting downstream approved tasks."""
        pass

    @abstractmethod
    def clear_captures(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> int:
        """Clears all capture history for user."""
        pass

    # ---------------- PROPOSALS & APPROVALS ----------------
    @abstractmethod
    def create_proposal_from_extraction(
        self,
        user_id: UUID,
        extraction: ExtractionResponse,
        capture_id: Optional[UUID] = None,
        model_provider: str = "gemini-2.5-flash",
        model_version: str = "v1",
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """Creates an independent, pending task proposal draft from structured NLU extraction."""
        pass

    @abstractmethod
    def get_proposal(self, proposal_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[ProposalResponse]:
        """Retrieves proposal with its constituent proposed items."""
        pass

    @abstractmethod
    def list_proposals(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        capture_id: Optional[UUID] = None,
        limit: int = 50,
        user_token: Optional[str] = None
    ) -> List[ProposalResponse]:
        """Lists proposals with optional status and capture filters."""
        pass

    @abstractmethod
    def list_pending_proposals(self, user_id: Optional[UUID] = None, limit: int = 50, user_token: Optional[str] = None) -> List[ProposalResponse]:
        """Lists all uncommitted proposals awaiting human approval."""
        pass

    @abstractmethod
    def update_proposal_item(
        self,
        proposal_id: UUID,
        item_id: UUID,
        patch: ProposalItemPatch,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalItemResponse:
        """Updates an individual proposed item before approval."""
        pass

    @abstractmethod
    def apply_clarifications(
        self,
        proposal_id: UUID,
        request: ProposalClarificationRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """Resolves missing or ambiguous information on a proposal."""
        pass

    @abstractmethod
    def answer_clarification(
        self,
        proposal_id: UUID,
        req: ProposalClarificationRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """Alias for apply_clarifications."""
        pass

    @abstractmethod
    def approve_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        request: ProposalApproveRequest,
        user_token: Optional[str] = None
    ) -> ProposalApproveResponse:
        """Commits approved proposal items into active tasks with idempotency protection."""
        pass

    @abstractmethod
    def commit_proposal(
        self,
        proposal_id: UUID,
        approve_req: ProposalApproveRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalApproveResponse:
        """Alias for approve_proposal."""
        pass

    @abstractmethod
    def reject_proposal(
        self,
        proposal_id: UUID,
        user_id: Optional[UUID] = None,
        reason: Optional[str] = "User rejected proposal",
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """Marks proposal as REJECTED without creating tasks."""
        pass

    @abstractmethod
    def batch_approve_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> dict:
        """Batch approves multiple proposals."""
        pass

    @abstractmethod
    def batch_reject_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: Optional[UUID] = None,
        reason: Optional[str] = "Batch rejected by user",
        user_token: Optional[str] = None
    ) -> dict:
        """Batch rejects multiple proposals."""
        pass

    @abstractmethod
    async def translate_proposal(
        self,
        proposal_id: UUID,
        target_language: str,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """Translates proposal text preserving original invariants."""
        pass

    # ---------------- TASKS ----------------
    @abstractmethod
    def list_tasks(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        target_date: Optional[date] = None,
        deadline_date: Optional[date] = None,
        user_token: Optional[str] = None
    ) -> List[TaskResponse]:
        """Lists active, approved user tasks."""
        pass

    @abstractmethod
    def get_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[TaskResponse]:
        """Retrieves an individual task."""
        pass

    @abstractmethod
    def create_task(self, user_id: UUID, task_create: TaskCreate, user_token: Optional[str] = None) -> TaskResponse:
        """Creates an explicit user task."""
        pass

    @abstractmethod
    def update_task(self, task_id: UUID, task_update: TaskUpdate, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        """Updates an existing task."""
        pass

    @abstractmethod
    def delete_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        """Deletes a task and cascading dependency edges."""
        pass

    @abstractmethod
    def complete_task(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None,
        actual_duration_min: Optional[int] = None,
        user_token: Optional[str] = None
    ) -> TaskResponse:
        """Marks a task as completed."""
        pass

    @abstractmethod
    def reopen_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        """Reopens a completed or postponed task."""
        pass

    @abstractmethod
    def add_task_dependency(
        self,
        task_id: UUID,
        depends_on_task_id: UUID,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> dict:
        """Adds a directed acyclic dependency edge between two tasks."""
        pass

    @abstractmethod
    def delete_task_dependency(
        self,
        task_id: UUID,
        depends_on_task_id: UUID,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> bool:
        """Removes a dependency edge between tasks."""
        pass

    @abstractmethod
    def get_task_dependencies(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[dict]:
        """Lists all active task dependency edges for the user."""
        pass

    # ---------------- PLANS & AVAILABILITY ----------------
    @abstractmethod
    def get_availability_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        """Retrieves user availability intervals."""
        pass

    @abstractmethod
    def get_user_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        """Alias for get_availability_windows."""
        pass

    @abstractmethod
    def get_busy_events(self, user_id: Optional[UUID] = None, plan_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        """Retrieves calendar blocking intervals for a given date."""
        pass

    @abstractmethod
    def get_user_busy_events(self, user_id: Optional[UUID] = None, plan_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        """Alias for get_busy_events."""
        pass

    @abstractmethod
    def save_plan(self, user_id: UUID, plan_response: PlanResponse, user_token: Optional[str] = None) -> PlanResponse:
        """Persists a computed daily focus plan."""
        pass

    @abstractmethod
    def get_plan_for_date(self, user_id: UUID, plan_date: date, user_token: Optional[str] = None) -> Optional[PlanResponse]:
        """Retrieves saved daily plan."""
        pass

    # ---------------- SOVEREIGN MEMORY & GDPR ----------------
    @abstractmethod
    def list_memory_preferences(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[MemoryPreferenceResponse]:
        """Lists sovereign user preferences."""
        pass

    @abstractmethod
    def get_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> Optional[MemoryPreferenceResponse]:
        """Retrieves a specific memory preference."""
        pass

    @abstractmethod
    def set_memory_preference(
        self,
        user_id: UUID,
        create_req: MemoryPreferenceCreate,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        """Sets or upserts a user preference with explicit consent."""
        pass

    @abstractmethod
    def patch_memory_preference(
        self,
        user_id: UUID,
        pref_id: UUID,
        patch: MemoryPreferencePatch,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        """Modifies an existing memory preference."""
        pass

    @abstractmethod
    def delete_memory_preference(self, user_id: UUID, identifier: str, user_token: Optional[str] = None) -> bool:
        """Deletes a specific memory preference by ID or key."""
        pass

    @abstractmethod
    def toggle_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> MemoryPreferenceResponse:
        """Toggles active state of a memory preference."""
        pass

    @abstractmethod
    def get_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        """Retrieves learned duration prior suggestions."""
        pass

    @abstractmethod
    def analyze_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        """Alias for get_duration_priors."""
        pass

    @abstractmethod
    def purge_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> DataPurgeResponse:
        """Right-to-be-forgotten permanent purge across all personal data tables."""
        pass

    @abstractmethod
    def export_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> UserDataExportResponse:
        """GDPR sovereign data portability export in structured JSON."""
        pass
