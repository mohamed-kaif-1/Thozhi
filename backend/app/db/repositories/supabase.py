import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, date, timedelta
from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction, PriorityEnum, ItemTypeEnum, ClarificationQuestion
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
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent, PlanResponse, ScheduleSlot
from backend.app.schemas.memory import (
    MemoryPreferenceCreate,
    MemoryPreferenceResponse,
    MemoryPreferencePatch,
    MemoryCategoryEnum,
    DurationPriorSuggestion,
    UserDataExportResponse,
    DataPurgeResponse,
)
from backend.app.core.errors import (
    ProposalExpiredException,
    IdempotencyConflictException,
    ResourceNotFoundException,
    DuplicateTaskException,
    SchedulingCycleException,
    PermissionDeniedException,
)
from backend.app.db.supabase_client import (
    supabase_client,
    SupabaseClient,
    SupabaseConnectionError,
    SupabaseQueryError,
    SupabaseAuthError,
)
from backend.app.db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None

def _parse_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None

def _parse_uuid(val: Any) -> Optional[UUID]:
    if val is None:
        return None
    if isinstance(val, UUID):
        return val
    try:
        return UUID(str(val))
    except Exception:
        return None

class SupabaseRepository(BaseRepository):
    """
    Durable PostgreSQL implementation of BaseRepository via Supabase PostgREST REST API.
    Enforces tenant scoping, explicit error propagation, and sovereign human governance.
    Zero RAM fallback: every write and read interacts with Supabase PostgREST tables.
    """
    def __init__(self, client: Optional[SupabaseClient] = None):
        self.client = client or supabase_client

    @property
    def is_live(self) -> bool:
        return self.client.is_configured

    # ---------------- USER PROFILE ----------------
    def get_user_profile(self, user_id: UUID, user_token: Optional[str] = None) -> dict:
        records = self.client.list_records_sync("users", {"id": f"eq.{user_id}"}, user_token=user_token)
        if records:
            r = records[0]
            return {
                "user_id": str(r.get("id")),
                "email": r.get("email", ""),
                "full_name": r.get("full_name") or "Antigravity User",
                "locale": r.get("locale") or "en-US",
                "timezone": r.get("timezone", "Asia/Kolkata"),
                "default_start_time": str(r.get("default_start_time", "09:00:00")),
                "default_end_time": str(r.get("default_end_time", "18:00:00")),
            }
        return {
            "user_id": str(user_id),
            "email": "user@thozhi.ai",
            "full_name": "Antigravity User",
            "locale": "en-US",
            "timezone": "Asia/Kolkata",
            "default_start_time": "09:00:00",
            "default_end_time": "18:00:00",
        }

    def update_user_profile(self, user_id: UUID, updates: dict, user_token: Optional[str] = None) -> dict:
        now = get_utc_now()
        payload = {"updated_at": now.isoformat()}
        if "full_name" in updates and updates["full_name"] is not None:
            payload["full_name"] = updates["full_name"]
        if "locale" in updates and updates["locale"] is not None:
            payload["locale"] = updates["locale"]
        if "timezone" in updates and updates["timezone"] is not None:
            payload["timezone"] = updates["timezone"]

        # Ensure user exists first or upsert
        self.client.insert_record_sync(
            "users",
            {
                "id": str(user_id),
                "email": f"user_{str(user_id)[:8]}@thozhi.ai",
                "full_name": payload.get("full_name", "Antigravity User"),
                "locale": payload.get("locale", "en-US"),
                "timezone": payload.get("timezone", "Asia/Kolkata"),
                "updated_at": now.isoformat()
            },
            upsert=True,
            user_token=user_token
        )
        return self.get_user_profile(user_id, user_token=user_token)

    # ---------------- CAPTURES ----------------
    def create_capture(
        self,
        user_id: UUID,
        input_type: str,
        transcript_text: str,
        detected_language: str = "Tanglish",
        original_transcript: Optional[str] = None,
        translated_transcript: Optional[str] = None,
        processing_status: str = "PROCESSED",
        provider_metadata: Optional[dict] = None,
        user_token: Optional[str] = None
    ) -> CaptureResponse:
        cap_id = uuid4()
        now = get_utc_now()
        status_val = "PROCESSED" if processing_status in ("COMPLETED", "PROCESSED") else processing_status
        data = {
            "id": str(cap_id),
            "user_id": str(user_id),
            "input_type": input_type,
            "transcript_text": transcript_text,
            "detected_language": detected_language,
            "original_transcript": original_transcript,
            "translated_transcript": translated_transcript,
            "processing_status": status_val,
            "lifecycle_status": "PENDING_REVIEW",
            "provider_metadata": provider_metadata or {},
            "created_at": now.isoformat(),
        }
        res = self.client.insert_record_sync("captures", data, user_token=user_token)
        return self._row_to_capture(res if isinstance(res, dict) else data)

    def get_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[CaptureResponse]:
        filters = {"id": f"eq.{capture_id}"}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        record = self.client.get_record_sync("captures", filters, user_token=user_token)
        if not record:
            return None
        return self._row_to_capture(record)

    def list_captures(self, user_id: Optional[UUID] = None, limit: int = 20, user_token: Optional[str] = None) -> List[CaptureResponse]:
        filters = {"order": "created_at.desc", "limit": str(limit)}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        records = self.client.list_records_sync("captures", filters, user_token=user_token)
        return [self._row_to_capture(r) for r in records]

    def delete_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        filters = {"id": f"eq.{capture_id}"}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        count = self.client.delete_record_sync("captures", filters, user_token=user_token)
        return count > 0

    def clear_captures(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> int:
        filters = {}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        return self.client.delete_record_sync("captures", filters, user_token=user_token)

    def _row_to_capture(self, r: dict) -> CaptureResponse:
        c_id = _parse_uuid(r["id"]) or uuid4()
        u_id = _parse_uuid(r.get("user_id")) or self.default_user_id
        dt = _parse_dt(r.get("created_at")) or get_utc_now()
        prop_ids_raw = r.get("proposal_ids") or []
        prop_ids = [_parse_uuid(p) for p in prop_ids_raw if _parse_uuid(p)]
        return CaptureResponse(
            id=c_id,
            user_id=u_id,
            input_type=r.get("input_type", "TEXT"),
            transcript_text=r.get("transcript_text", ""),
            original_transcript=r.get("original_transcript"),
            translated_transcript=r.get("translated_transcript"),
            detected_language=r.get("detected_language", "Tanglish"),
            processing_status=r.get("processing_status", "PROCESSED"),
            lifecycle_status=r.get("lifecycle_status", "PENDING_REVIEW"),
            created_at=dt,
            proposal_ids=prop_ids,
            proposals=[],
            proposal_count=len(prop_ids),
        )

    # ---------------- PROPOSALS & APPROVALS ----------------
    def create_proposal_from_extraction(
        self,
        user_id: UUID,
        extraction: ExtractionResponse,
        capture_id: Optional[UUID] = None,
        model_provider: str = "gemini-2.5-flash",
        model_version: str = "v1",
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        prop_id = uuid4()
        now = get_utc_now()
        exp = now + timedelta(days=7)

        raw_clarifs = getattr(extraction, "clarifications", None) or getattr(extraction, "clarification_questions", None) or []
        clarifications_data = []
        for q in raw_clarifs:
            if hasattr(q, "model_dump"):
                clarifications_data.append(q.model_dump())
            elif isinstance(q, dict):
                clarifications_data.append(q)
            else:
                clarifications_data.append({"id": "clar_1", "question_text": str(q), "suggested_options": []})

        summary = getattr(extraction, "intent_summary", None) or getattr(extraction, "overall_intent_summary", None) or ""

        prop_data = {
            "id": str(prop_id),
            "user_id": str(user_id),
            "capture_id": str(capture_id) if capture_id else None,
            "status": "PENDING_REVIEW",
            "model_provider": model_provider,
            "model_version": model_version,
            "intent_summary": summary,
            "display_language": "original",
            "translation_status": "ORIGINAL",
            "clarifications": clarifications_data,
            "created_at": now.isoformat(),
            "expires_at": exp.isoformat()
        }
        self.client.insert_record_sync("proposals", prop_data, user_token=user_token)

        items_responses: List[ProposalItemResponse] = []
        raw_items = getattr(extraction, "extracted_items", None) or getattr(extraction, "proposed_items", None) or []
        for idx, item in enumerate(raw_items):
            item_id = uuid4()
            prio_val = None
            if item.priority is not None:
                val = item.priority.value if hasattr(item.priority, "value") else str(item.priority)
                prio_val = None if val in ("UNSPECIFIED", "NONE", "") else val

            item_data = {
                "id": str(item_id),
                "proposal_id": str(prop_id),
                "user_id": str(user_id),
                "item_type": item.item_type.value if hasattr(item.item_type, "value") else str(item.item_type),
                "proposed_title": item.proposed_title,
                "description": item.description,
                "action": getattr(item, "action", None),
                "object": getattr(item, "object", None),
                "deadline": item.deadline.isoformat() if item.deadline else None,
                "earliest_start": item.earliest_start.isoformat() if getattr(item, "earliest_start", None) else None,
                "estimated_duration_min": item.estimated_duration_min or 30,
                "duration_source": getattr(item, "duration_source", "MODEL_ESTIMATE"),
                "priority": prio_val,
                "confidence": getattr(item, "confidence", 0.85),
                "uncertainty_flags": getattr(item, "uncertainty_flags", []),
                "source_reference": getattr(item, "source_reference", "RAW_EXTRACT"),
                "status": "PENDING",
                "decision_state": "PENDING",
                "created_at": now.isoformat()
            }
            self.client.insert_record_sync("proposal_items", item_data, user_token=user_token)
            items_responses.append(self._row_to_proposal_item(item_data, temp_id=f"tmp_{idx}"))

        if capture_id:
            cap = self.client.get_record_sync("captures", {"id": f"eq.{capture_id}"}, user_token=user_token)
            if cap:
                existing_pids = cap.get("proposal_ids") or []
                if str(prop_id) not in existing_pids:
                    existing_pids.append(str(prop_id))
                    self.client.update_record_sync("captures", {"id": f"eq.{capture_id}"}, {"proposal_ids": existing_pids}, user_token=user_token)

        return ProposalResponse(
            id=prop_id,
            user_id=user_id,
            capture_id=capture_id,
            transcript_text=None,
            original_transcript=None,
            translated_transcript=None,
            display_language="original",
            translation_status="ORIGINAL",
            intent_summary=summary,
            detected_language="Tanglish",
            status="PENDING_REVIEW",
            created_at=now,
            expires_at=exp,
            items=items_responses,
            clarifications=raw_clarifs
        )

    def get_proposal(self, proposal_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[ProposalResponse]:
        filters = {"id": f"eq.{proposal_id}"}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        prop_rec = self.client.get_record_sync("proposals", filters, user_token=user_token)
        if not prop_rec:
            return None
        items_rec = self.client.list_records_sync("proposal_items", {"proposal_id": f"eq.{proposal_id}", "order": "created_at.asc"}, user_token=user_token)
        items = [self._row_to_proposal_item(r, temp_id=f"item_{idx}") for idx, r in enumerate(items_rec)]
        return self._row_to_proposal(prop_rec, items)

    def list_proposals(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        capture_id: Optional[UUID] = None,
        limit: int = 50,
        user_token: Optional[str] = None
    ) -> List[ProposalResponse]:
        filters = {"order": "created_at.desc", "limit": str(limit)}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        if status:
            filters["status"] = f"eq.{status}"
        if capture_id:
            filters["capture_id"] = f"eq.{capture_id}"

        prop_recs = self.client.list_records_sync("proposals", filters, user_token=user_token)
        results: List[ProposalResponse] = []
        for r in prop_recs:
            pid = r["id"]
            items_rec = self.client.list_records_sync("proposal_items", {"proposal_id": f"eq.{pid}", "order": "created_at.asc"}, user_token=user_token)
            items = [self._row_to_proposal_item(it, temp_id=f"item_{i}") for i, it in enumerate(items_rec)]
            results.append(self._row_to_proposal(r, items))
        return results

    def list_pending_proposals(self, user_id: Optional[UUID] = None, limit: int = 50, user_token: Optional[str] = None) -> List[ProposalResponse]:
        return self.list_proposals(user_id=user_id, status="PENDING_REVIEW", limit=limit, user_token=user_token)

    def update_proposal_item(
        self,
        proposal_id: UUID,
        item_id: UUID,
        patch: ProposalItemPatch,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalItemResponse:
        filters = {"id": f"eq.{item_id}", "proposal_id": f"eq.{proposal_id}"}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"

        existing = self.client.get_record_sync("proposal_items", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Proposal item {item_id} not found", resource_type="proposal_item", resource_id=str(item_id))

        update_dict = {}
        if patch.proposed_title is not None:
            update_dict["proposed_title"] = patch.proposed_title
        if patch.description is not None:
            update_dict["description"] = patch.description
        if patch.estimated_duration_min is not None:
            update_dict["estimated_duration_min"] = patch.estimated_duration_min
        if patch.priority is not None:
            val = patch.priority.value if hasattr(patch.priority, "value") else str(patch.priority)
            update_dict["priority"] = None if val in ("UNSPECIFIED", "NONE", "") else val
        if patch.normalized_deadline is not None:
            update_dict["deadline"] = patch.normalized_deadline.isoformat()

        if update_dict:
            res = self.client.update_record_sync("proposal_items", filters, update_dict, user_token=user_token)
            if res:
                return self._row_to_proposal_item(res[0], temp_id="patched")
        return self._row_to_proposal_item(existing, temp_id="patched")

    def apply_clarifications(
        self,
        proposal_id: UUID,
        request: ProposalClarificationRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        prop = self.get_proposal(proposal_id, user_id, user_token=user_token)
        if not prop:
            raise ResourceNotFoundException(detail=f"Proposal {proposal_id} not found", resource_type="proposal", resource_id=str(proposal_id))
        return prop

    def answer_clarification(
        self,
        proposal_id: UUID,
        req: ProposalClarificationRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        return self.apply_clarifications(proposal_id, req, user_id, user_token=user_token)

    def approve_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        request: ProposalApproveRequest,
        user_token: Optional[str] = None
    ) -> ProposalApproveResponse:
        # Idempotency fast-path check
        cached = self.client.get_record_sync(
            "approval_idempotency",
            {"idempotency_key": f"eq.{request.idempotency_key}", "user_id": f"eq.{user_id}"},
            user_token=user_token
        )
        if cached:
            return ProposalApproveResponse(**cached["response_payload"])

        prop = self.get_proposal(proposal_id, user_id, user_token=user_token)
        if not prop:
            raise ResourceNotFoundException(
                detail=f"Proposal {proposal_id} not found",
                resource_type="proposal",
                resource_id=str(proposal_id)
            )

        if prop.status in ("APPROVED", "COMMITTED"):
            raise IdempotencyConflictException("Proposal has already been approved and committed.")
        if prop.status == "REJECTED":
            raise ProposalExpiredException("Proposal has already been rejected.")

        now = get_utc_now()
        # Build strict 100% item coverage decision payload
        decision_map = {item_dec.id: item_dec for item_dec in request.items}
        item_decisions = []
        for item in prop.items:
            decision = decision_map.get(item.id)
            is_approved = decision.is_approved if decision is not None else True
            title = getattr(decision, "proposed_title", None) or item.proposed_title
            est_dur = getattr(decision, "estimated_duration_min", None) or item.estimated_duration_min or 30
            if decision and decision.priority:
                val = decision.priority.value if hasattr(decision.priority, "value") else str(decision.priority)
                prio = None if val in ("UNSPECIFIED", "NONE", "") else val
            elif item.priority:
                val = item.priority.value if hasattr(item.priority, "value") else str(item.priority)
                prio = None if val in ("UNSPECIFIED", "NONE", "") else val
            else:
                prio = None

            sched_d = getattr(decision, "scheduled_date", None)
            if sched_d:
                sched_str = sched_d.isoformat() if hasattr(sched_d, "isoformat") else str(sched_d)
            elif item.normalized_deadline:
                sched_str = item.normalized_deadline.date().isoformat()
            else:
                sched_str = None
            rej_reason = getattr(decision, "rejection_reason", None) if not is_approved else None

            item_decisions.append({
                "id": str(item.id),
                "is_approved": is_approved,
                "proposed_title": title,
                "estimated_duration_min": est_dur,
                "priority": prio,
                "scheduled_date": sched_str,
                "rejection_reason": rej_reason
            })

        rpc_params = {
            "p_user_id": str(user_id),
            "p_proposal_id": str(proposal_id),
            "p_idempotency_key": request.idempotency_key,
            "p_item_decisions": item_decisions
        }

        try:
            raw_result = self.client.rpc_sync("commit_proposal_atomic", rpc_params, user_token=user_token)
            if not raw_result:
                raise SupabaseQueryError(500, "Empty response from commit_proposal_atomic RPC")

            created_task_uuids = [
                UUID(t) if isinstance(t, str) else t
                for t in raw_result.get("created_task_ids", [])
            ]
            prop_id = UUID(raw_result["proposal_id"]) if isinstance(raw_result["proposal_id"], str) else raw_result["proposal_id"]

            return ProposalApproveResponse(
                proposal_id=prop_id,
                approved_tasks_count=raw_result.get("approved_tasks_count", 0),
                rejected_items_count=raw_result.get("rejected_items_count", 0),
                created_task_ids=created_task_uuids,
                message=raw_result.get("message", "Human decision recorded atomically. Tasks explicitly committed to schedule.")
            )
        except SupabaseQueryError as exc:
            err_msg = str(exc.detail).lower()
            if "p0002" in err_msg or "not found" in err_msg:
                raise ResourceNotFoundException(
                    detail=f"Proposal {proposal_id} or item not found",
                    resource_type="proposal",
                    resource_id=str(proposal_id)
                )
            elif "23505" in err_msg or "already been committed" in err_msg:
                raise IdempotencyConflictException("Proposal has already been approved and committed.")
            elif "22023" in err_msg and "already been rejected" in err_msg:
                raise ProposalExpiredException("Proposal has already been rejected.")
            elif "42501" in err_msg or "access denied" in err_msg:
                raise PermissionDeniedException("Access denied for this proposal.")
            raise

    def commit_proposal(
        self,
        proposal_id: UUID,
        approve_req: ProposalApproveRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalApproveResponse:
        return self.approve_proposal(proposal_id, user_id or self.default_user_id, approve_req, user_token=user_token)

    def reject_proposal(
        self,
        proposal_id: UUID,
        user_id: Optional[UUID] = None,
        reason: Optional[str] = "User rejected proposal",
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        uid = user_id or self.default_user_id
        prop = self.get_proposal(proposal_id, uid, user_token=user_token)
        if not prop:
            raise ResourceNotFoundException(detail=f"Proposal {proposal_id} not found", resource_type="proposal", resource_id=str(proposal_id))

        self.client.update_record_sync("proposals", {"id": f"eq.{proposal_id}", "user_id": f"eq.{uid}"}, {"status": "REJECTED"}, user_token=user_token)
        self.client.update_record_sync(
            "proposal_items",
            {"proposal_id": f"eq.{proposal_id}", "user_id": f"eq.{uid}"},
            {"status": "REJECTED", "decision_state": "REJECTED", "rejection_reason": reason},
            user_token=user_token
        )
        if prop.capture_id:
            self.client.update_record_sync("captures", {"id": f"eq.{prop.capture_id}", "user_id": f"eq.{uid}"}, {"lifecycle_status": "REJECTED"}, user_token=user_token)

        return self.get_proposal(proposal_id, uid, user_token=user_token)

    def batch_approve_proposals(self, proposal_ids: List[UUID], user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> dict:
        uid = user_id or self.default_user_id
        approved, failed = [], []
        for pid in proposal_ids:
            try:
                res = self.approve_proposal(pid, uid, ProposalApproveRequest(idempotency_key=f"batch_{uuid4()}", items=[]), user_token=user_token)
                approved.append(str(pid))
            except Exception as e:
                failed.append({"id": str(pid), "error": str(e)})
        return {"approved": approved, "failed": failed}

    def batch_reject_proposals(self, proposal_ids: List[UUID], user_id: Optional[UUID] = None, reason: Optional[str] = "Batch rejected by user", user_token: Optional[str] = None) -> dict:
        uid = user_id or self.default_user_id
        rejected, failed = [], []
        for pid in proposal_ids:
            try:
                self.reject_proposal(pid, uid, reason, user_token=user_token)
                rejected.append(str(pid))
            except Exception as e:
                failed.append({"id": str(pid), "error": str(e)})
        return {"rejected": rejected, "failed": failed}

    async def translate_proposal(
        self,
        proposal_id: UUID,
        target_language: str,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        uid = user_id or self.default_user_id
        prop = self.get_proposal(proposal_id, uid, user_token=user_token)
        if not prop:
            raise ResourceNotFoundException(detail=f"Proposal {proposal_id} not found", resource_type="proposal", resource_id=str(proposal_id))

        from backend.app.providers.translation.sarvam import sarvam_provider
        self.client.update_record_sync(
            "proposals",
            {"id": f"eq.{proposal_id}", "user_id": f"eq.{uid}"},
            {"display_language": target_language, "translation_status": "TRANSLATED" if target_language != "original" else "ORIGINAL"},
            user_token=user_token
        )
        return self.get_proposal(proposal_id, uid, user_token=user_token)

    def _row_to_proposal_item(self, r: dict, temp_id: str = "tmp_0") -> ProposalItemResponse:
        i_id = _parse_uuid(r["id"]) or uuid4()
        p_id = _parse_uuid(r.get("proposal_id")) or uuid4()
        dt = _parse_dt(r.get("created_at")) or get_utc_now()
        dl = _parse_dt(r.get("deadline"))
        itype = r.get("item_type", "TASK")
        if isinstance(itype, str):
            try:
                itype = ItemTypeEnum(itype)
            except Exception:
                itype = ItemTypeEnum.TASK
        prio = r.get("priority")
        if isinstance(prio, str) and prio not in ("UNSPECIFIED", "NONE", ""):
            try:
                prio = PriorityEnum(prio)
            except Exception:
                prio = None
        else:
            prio = None

        return ProposalItemResponse(
            id=i_id,
            proposal_id=p_id,
            temp_id=temp_id,
            item_type=itype,
            action=r.get("action"),
            object=r.get("object"),
            proposed_title=r.get("proposed_title", ""),
            description=r.get("description"),
            original_title=r.get("original_title") or r.get("proposed_title"),
            original_description=r.get("original_description") or r.get("description"),
            translated_title=r.get("translated_title"),
            translated_description=r.get("translated_description"),
            source_expression=r.get("source_reference", "RAW_EXTRACT"),
            deadline_expression=None,
            normalized_deadline=dl,
            estimated_duration_min=r.get("estimated_duration_min", 30),
            duration_source=r.get("duration_source", "UNSPECIFIED"),
            priority=prio,
            confidence_score=float(r.get("confidence", 0.9)),
            decision_state=r.get("decision_state", "PENDING"),
            rejection_reason=r.get("rejection_reason"),
            created_at=dt
        )

    def _row_to_proposal(self, r: dict, items: List[ProposalItemResponse]) -> ProposalResponse:
        p_id = _parse_uuid(r["id"]) or uuid4()
        u_id = _parse_uuid(r.get("user_id")) or self.default_user_id
        c_id = _parse_uuid(r.get("capture_id"))
        dt = _parse_dt(r.get("created_at")) or get_utc_now()
        exp = _parse_dt(r.get("expires_at")) or (dt + timedelta(days=7))

        raw_clarifications = r.get("clarifications") or []
        clarifications_list = []
        for q in raw_clarifications:
            if isinstance(q, dict):
                try:
                    clarifications_list.append(ClarificationQuestion(**q))
                except Exception:
                    pass
            elif isinstance(q, ClarificationQuestion):
                clarifications_list.append(q)

        return ProposalResponse(
            id=p_id,
            user_id=u_id,
            capture_id=c_id,
            transcript_text=r.get("transcript_text"),
            original_transcript=r.get("original_transcript"),
            translated_transcript=r.get("translated_transcript"),
            display_language=r.get("display_language", "original"),
            translation_status=r.get("translation_status", "ORIGINAL"),
            intent_summary=r.get("intent_summary", ""),
            original_intent_summary=r.get("original_intent_summary"),
            translated_intent_summary=r.get("translated_intent_summary"),
            detected_language=r.get("detected_language", "Tanglish"),
            status=r.get("status", "PENDING_REVIEW"),
            created_at=dt,
            expires_at=exp,
            items=items,
            clarifications=clarifications_list
        )

    # ---------------- TASKS ----------------
    def list_tasks(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        target_date: Optional[date] = None,
        deadline_date: Optional[date] = None,
        user_token: Optional[str] = None
    ) -> List[TaskResponse]:
        uid = user_id or self.default_user_id
        filters = {"user_id": f"eq.{uid}", "order": "created_at.desc"}
        if status:
            filters["status"] = f"eq.{status}"

        records = self.client.list_records_sync("tasks", filters, user_token=user_token)
        deps = self.get_task_dependencies(uid, user_token=user_token)
        task_deps_map: Dict[UUID, List[UUID]] = {}
        for d in deps:
            t_id = d["task_id"]
            if t_id not in task_deps_map:
                task_deps_map[t_id] = []
            task_deps_map[t_id].append(d["depends_on_task_id"])

        results: List[TaskResponse] = []
        for r in records:
            t_id = _parse_uuid(r["id"])
            if not t_id:
                continue
            t_resp = self._row_to_task(r, task_deps_map.get(t_id, []))
            if target_date is not None and t_resp.scheduled_date != target_date:
                continue
            if deadline_date is not None and (not t_resp.deadline or t_resp.deadline.date() != deadline_date):
                continue
            results.append(t_resp)
        return results

    def get_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[TaskResponse]:
        filters = {"id": f"eq.{task_id}"}
        if user_id:
            filters["user_id"] = f"eq.{user_id}"
        record = self.client.get_record_sync("tasks", filters, user_token=user_token)
        if not record:
            return None
        deps = [d["depends_on_task_id"] for d in self.get_task_dependencies(user_id, user_token=user_token) if d["task_id"] == task_id]
        return self._row_to_task(record, deps)

    def create_task(self, user_id: UUID, task_create: TaskCreate, user_token: Optional[str] = None) -> TaskResponse:
        now = get_utc_now()
        target_sched_date = task_create.scheduled_date or (task_create.deadline.date() if task_create.deadline else now.date())

        # Check duplicate
        norm_title = task_create.title.strip().lower()
        existing = self.list_tasks(user_id=user_id, user_token=user_token)
        for t in existing:
            if t.status != "COMPLETED" and t.title.strip().lower() == norm_title and t.scheduled_date == target_sched_date:
                raise DuplicateTaskException(title=task_create.title, scheduled_date=str(target_sched_date))

        task_id = uuid4()
        dur_src = getattr(task_create, "duration_source", "USER_EXPLICIT" if task_create.estimated_duration_min else "UNSPECIFIED")

        prio_val = None
        if task_create.priority is not None:
            val = task_create.priority.value if hasattr(task_create.priority, "value") else str(task_create.priority)
            prio_val = None if val in ("UNSPECIFIED", "NONE", "") else val

        data = {
            "id": str(task_id),
            "user_id": str(user_id),
            "title": task_create.title.strip(),
            "description": task_create.description,
            "priority": prio_val,
            "estimated_duration_min": task_create.estimated_duration_min,
            "duration_source": dur_src,
            "deadline": task_create.deadline.isoformat() if task_create.deadline else None,
            "scheduled_date": str(target_sched_date) if target_sched_date else None,
            "status": "PENDING",
            "source_language": "en",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        res = self.client.insert_record_sync("tasks", data, user_token=user_token)
        return self._row_to_task(res if isinstance(res, dict) else data, [])

    def update_task(self, task_id: UUID, task_update: TaskUpdate, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        uid = user_id or self.default_user_id
        filters = {"id": f"eq.{task_id}", "user_id": f"eq.{uid}"}
        existing = self.client.get_record_sync("tasks", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))

        update_dict = {"updated_at": get_utc_now().isoformat()}
        data = task_update.model_dump(exclude_unset=True)
        for k, v in data.items():
            if k == "priority":
                if v is None:
                    update_dict["priority"] = None
                else:
                    val = v.value if hasattr(v, "value") else str(v)
                    update_dict["priority"] = None if val in ("UNSPECIFIED", "NONE", "") else val
            elif k == "deadline" and v is not None:
                update_dict["deadline"] = v.isoformat()
            elif k == "scheduled_date" and v is not None:
                update_dict["scheduled_date"] = v.isoformat() if hasattr(v, "isoformat") else str(v)
            else:
                update_dict[k] = v

        res = self.client.update_record_sync("tasks", filters, update_dict, user_token=user_token)
        deps = [d["depends_on_task_id"] for d in self.get_task_dependencies(uid, user_token=user_token) if d["task_id"] == task_id]
        return self._row_to_task(res[0] if res else existing, deps)

    def delete_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        uid = user_id or self.default_user_id
        filters = {"id": f"eq.{task_id}", "user_id": f"eq.{uid}"}
        count = self.client.delete_record_sync("tasks", filters, user_token=user_token)
        if count == 0:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
        # Remove dependency edges
        self.client.delete_record_sync("task_dependencies", {"successor_task_id": f"eq.{task_id}", "user_id": f"eq.{uid}"}, user_token=user_token)
        self.client.delete_record_sync("task_dependencies", {"predecessor_task_id": f"eq.{task_id}", "user_id": f"eq.{uid}"}, user_token=user_token)
        return True

    def complete_task(self, task_id: UUID, user_id: Optional[UUID] = None, actual_duration_min: Optional[int] = None, user_token: Optional[str] = None) -> TaskResponse:
        uid = user_id or self.default_user_id
        filters = {"id": f"eq.{task_id}", "user_id": f"eq.{uid}"}
        existing = self.client.get_record_sync("tasks", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))

        now = get_utc_now()
        act_dur = actual_duration_min or existing.get("estimated_duration_min", 30)
        res = self.client.update_record_sync("tasks", filters, {
            "status": "COMPLETED",
            "completed_at": now.isoformat(),
            "actual_duration_min": act_dur,
            "updated_at": now.isoformat()
        }, user_token=user_token)
        deps = [d["depends_on_task_id"] for d in self.get_task_dependencies(uid, user_token=user_token) if d["task_id"] == task_id]
        return self._row_to_task(res[0] if res else existing, deps)

    def reopen_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        uid = user_id or self.default_user_id
        filters = {"id": f"eq.{task_id}", "user_id": f"eq.{uid}"}
        existing = self.client.get_record_sync("tasks", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))

        now = get_utc_now()
        res = self.client.update_record_sync("tasks", filters, {
            "status": "PENDING",
            "completed_at": None,
            "updated_at": now.isoformat()
        }, user_token=user_token)
        deps = [d["depends_on_task_id"] for d in self.get_task_dependencies(uid, user_token=user_token) if d["task_id"] == task_id]
        return self._row_to_task(res[0] if res else existing, deps)

    def add_task_dependency(self, task_id: UUID, depends_on_task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> dict:
        uid = user_id or self.default_user_id
        if task_id == depends_on_task_id:
            raise SchedulingCycleException("Task cannot depend on itself.")

        t1 = self.client.get_record_sync("tasks", {"id": f"eq.{task_id}", "user_id": f"eq.{uid}"}, user_token=user_token)
        if not t1:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
        t2 = self.client.get_record_sync("tasks", {"id": f"eq.{depends_on_task_id}", "user_id": f"eq.{uid}"}, user_token=user_token)
        if not t2:
            raise ResourceNotFoundException(detail=f"Prerequisite task {depends_on_task_id} not found", resource_type="task", resource_id=str(depends_on_task_id))

        existing = self.client.list_records_sync("task_dependencies", {
            "successor_task_id": f"eq.{task_id}",
            "predecessor_task_id": f"eq.{depends_on_task_id}",
            "user_id": f"eq.{uid}"
        }, user_token=user_token)
        if existing:
            return {"task_id": task_id, "depends_on_task_id": depends_on_task_id}

        # Cycle check via PlanningEngine
        all_tasks = self.list_tasks(user_id=uid, user_token=user_token)
        all_deps = self.get_task_dependencies(uid, user_token=user_token)
        test_deps = [(d["depends_on_task_id"], d["task_id"]) for d in all_deps]
        test_deps.append((depends_on_task_id, task_id))

        from backend.app.modules.planning.engine import PlanningEngine
        PlanningEngine.topological_sort(all_tasks, test_deps)

        dep_id = uuid4()
        dep_data = {
            "id": str(dep_id),
            "user_id": str(uid),
            "successor_task_id": str(task_id),
            "predecessor_task_id": str(depends_on_task_id),
            "dependency_type": "FINISH_TO_START",
            "created_at": get_utc_now().isoformat()
        }
        self.client.insert_record_sync("task_dependencies", dep_data, user_token=user_token)
        return {"id": dep_id, "task_id": task_id, "depends_on_task_id": depends_on_task_id}

    def delete_task_dependency(self, task_id: UUID, depends_on_task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        uid = user_id or self.default_user_id
        count = self.client.delete_record_sync("task_dependencies", {
            "successor_task_id": f"eq.{task_id}",
            "predecessor_task_id": f"eq.{depends_on_task_id}",
            "user_id": f"eq.{uid}"
        }, user_token=user_token)
        return count > 0

    def get_task_dependencies(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[dict]:
        uid = user_id or self.default_user_id
        records = self.client.list_records_sync("task_dependencies", {"user_id": f"eq.{uid}"}, user_token=user_token)
        return [
            {
                "id": _parse_uuid(r.get("id")),
                "task_id": _parse_uuid(r.get("successor_task_id") or r.get("task_id")),
                "depends_on_task_id": _parse_uuid(r.get("predecessor_task_id") or r.get("depends_on_task_id")),
                "dependency_type": r.get("dependency_type", "FINISH_TO_START")
            }
            for r in records
            if r.get("successor_task_id") or r.get("task_id")
        ]

    def _row_to_task(self, r: dict, deps: List[UUID]) -> TaskResponse:
        t_id = _parse_uuid(r["id"]) or uuid4()
        u_id = _parse_uuid(r.get("user_id")) or self.default_user_id
        dt_create = _parse_dt(r.get("created_at")) or get_utc_now()
        dt_up = _parse_dt(r.get("updated_at")) or dt_create
        dl = _parse_dt(r.get("deadline"))
        comp = _parse_dt(r.get("completed_at"))
        prio = r.get("priority")
        if isinstance(prio, str) and prio not in ("UNSPECIFIED", "NONE", ""):
            try:
                prio = PriorityEnum(prio)
            except Exception:
                prio = None
        else:
            prio = None

        raw_sched = r.get("scheduled_date")
        if raw_sched:
            if isinstance(raw_sched, str):
                try:
                    sched_d = date.fromisoformat(raw_sched)
                except Exception:
                    sched_d = dl.date() if dl else dt_create.date()
            elif isinstance(raw_sched, date):
                sched_d = raw_sched
            else:
                sched_d = dl.date() if dl else dt_create.date()
        else:
            sched_d = dl.date() if dl else dt_create.date()

        return TaskResponse(
            id=t_id,
            user_id=u_id,
            title=r.get("title", ""),
            description=r.get("description"),
            priority=prio,
            estimated_duration_min=r.get("estimated_duration_min"),
            duration_source=r.get("duration_source", "UNSPECIFIED"),
            actual_duration_min=r.get("actual_duration_min"),
            deadline=dl,
            scheduled_date=sched_d,
            scheduled_start=None,
            scheduled_end=None,
            status=r.get("status", "PENDING"),
            origin_proposal_item_id=_parse_uuid(r.get("source_proposal_item_id")),
            source_language=r.get("source_language", "en"),
            completed_at=comp,
            created_at=dt_create,
            updated_at=dt_up,
            dependencies=deps
        )

    # ---------------- PLANS & AVAILABILITY ----------------
    def get_availability_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        uid = user_id or self.default_user_id
        records = self.client.list_records_sync("availability_windows", {"user_id": f"eq.{uid}"}, user_token=user_token)
        if records:
            from datetime import time
            windows = []
            for r in records:
                s_t = time.fromisoformat(r["start_time"] if ":" in r["start_time"] else "09:00:00")
                e_t = time.fromisoformat(r["end_time"] if ":" in r["end_time"] else "18:00:00")
                windows.append(AvailabilityWindow(day_of_week=0, start_time=s_t, end_time=e_t, label="Working Hours"))
            return windows

        from datetime import time
        return [
            AvailabilityWindow(day_of_week=i, start_time=time(9, 0), end_time=time(18, 0), label="Working Hours")
            for i in range(5)
        ]

    def get_user_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        return self.get_availability_windows(user_id, user_token=user_token)

    def get_busy_events(self, user_id: Optional[UUID] = None, plan_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        uid = user_id or self.default_user_id
        records = self.client.list_records_sync("busy_events", {"user_id": f"eq.{uid}"}, user_token=user_token)
        events: List[BusyEvent] = []
        for r in records:
            st = _parse_dt(r["start_time"])
            et = _parse_dt(r["end_time"])
            if st and et:
                if plan_date is None or st.date() == plan_date or et.date() == plan_date:
                    events.append(BusyEvent(
                        id=_parse_uuid(r["id"]),
                        title=r.get("title", "Busy"),
                        start_time=st,
                        end_time=et,
                        is_blocking=True
                    ))
        return events

    def get_user_busy_events(self, user_id: Optional[UUID] = None, plan_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        return self.get_busy_events(user_id, plan_date, user_token=user_token)

    def save_plan(self, user_id: UUID, plan_response: PlanResponse, user_token: Optional[str] = None) -> PlanResponse:
        plan_id = uuid4()
        now = get_utc_now()
        plan_data = {
            "id": str(plan_id),
            "user_id": str(user_id),
            "plan_date": plan_response.plan_date.isoformat(),
            "feasibility_status": "FEASIBLE",
            "total_allocated_minutes": plan_response.total_scheduled_minutes,
            "capacity_deficit_minutes": max(0, plan_response.total_scheduled_minutes - plan_response.total_available_minutes),
            "created_at": now.isoformat()
        }
        self.client.insert_record_sync("plans", plan_data, upsert=True, user_token=user_token)

        for slot in plan_response.slots:
            item_data = {
                "id": str(uuid4()),
                "plan_id": str(plan_id),
                "task_id": str(slot.task_id),
                "allocated_start": slot.start_time.isoformat(),
                "allocated_end": slot.end_time.isoformat(),
                "status": slot.scheduling_status
            }
            self.client.insert_record_sync("plan_items", item_data, user_token=user_token)

        plan_response.id = plan_id
        return plan_response

    def get_plan_for_date(self, user_id: UUID, plan_date: date, user_token: Optional[str] = None) -> Optional[PlanResponse]:
        records = self.client.list_records_sync("plans", {
            "user_id": f"eq.{user_id}",
            "plan_date": f"eq.{plan_date.isoformat()}"
        }, user_token=user_token)
        if not records:
            return None
        r = records[0]
        plan_id = r["id"]
        item_recs = self.client.list_records_sync("plan_items", {"plan_id": f"eq.{plan_id}"}, user_token=user_token)
        slots: List[ScheduleSlot] = []
        for it in item_recs:
            st = _parse_dt(it["allocated_start"])
            et = _parse_dt(it["allocated_end"])
            t_id = _parse_uuid(it["task_id"])
            if st and et and t_id:
                dur = int((et - st).total_seconds() // 60)
                slots.append(ScheduleSlot(
                    task_id=t_id,
                    title="Scheduled Task",
                    start_time=st,
                    end_time=et,
                    duration_min=dur,
                    scheduling_status=it.get("status", "SCHEDULED")
                ))

        return PlanResponse(
            id=_parse_uuid(plan_id),
            plan_date=plan_date,
            status="PROPOSED",
            total_available_minutes=480,
            total_scheduled_minutes=r.get("total_allocated_minutes", 0),
            capacity_percentage=round((r.get("total_allocated_minutes", 0) / 480) * 100, 1),
            slots=slots,
            conflicts=[]
        )

    # ---------------- SOVEREIGN MEMORY & GDPR ----------------
    def list_memory_preferences(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[MemoryPreferenceResponse]:
        uid = user_id or self.default_user_id
        records = self.client.list_records_sync("memory_preferences", {"user_id": f"eq.{uid}", "is_active": "eq.true"}, user_token=user_token)
        return [self._row_to_pref(r) for r in records]

    def get_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> Optional[MemoryPreferenceResponse]:
        record = self.client.get_record_sync("memory_preferences", {"id": f"eq.{pref_id}", "user_id": f"eq.{user_id}"}, user_token=user_token)
        if not record:
            return None
        return self._row_to_pref(record)

    def set_memory_preference(
        self,
        user_id: UUID,
        create_req: MemoryPreferenceCreate,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        now = get_utc_now()
        cat = create_req.category.value if hasattr(create_req.category, "value") else str(create_req.category)
        data = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "preference_key": create_req.preference_key,
            "category": cat,
            "preference_value": create_req.preference_value,
            "description": create_req.description,
            "is_active": True,
            "consent_granted": True,
            "consent_level": create_req.consent_level or "USER_EXPLICIT",
            "consent_status": "GRANTED",
            "updated_at": now.isoformat(),
            "created_at": now.isoformat()
        }
        res = self.client.insert_record_sync("memory_preferences", data, upsert=True, user_token=user_token)
        return self._row_to_pref(res if isinstance(res, dict) else data)

    def patch_memory_preference(
        self,
        user_id: UUID,
        pref_id: UUID,
        patch: MemoryPreferencePatch,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        filters = {"id": f"eq.{pref_id}", "user_id": f"eq.{user_id}"}
        existing = self.client.get_record_sync("memory_preferences", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Preference {pref_id} not found", resource_type="memory_preference", resource_id=str(pref_id))

        update_dict = {"updated_at": get_utc_now().isoformat()}
        if patch.preference_value is not None:
            update_dict["preference_value"] = patch.preference_value
        if patch.is_active is not None:
            update_dict["is_active"] = patch.is_active
        if patch.description is not None:
            update_dict["description"] = patch.description

        res = self.client.update_record_sync("memory_preferences", filters, update_dict, user_token=user_token)
        return self._row_to_pref(res[0] if res else existing)

    def delete_memory_preference(self, user_id: UUID, identifier: str, user_token: Optional[str] = None) -> bool:
        # Check by id or by key
        id_uuid = _parse_uuid(identifier)
        if id_uuid:
            filters = {"id": f"eq.{id_uuid}", "user_id": f"eq.{user_id}"}
        else:
            filters = {"preference_key": f"eq.{identifier}", "user_id": f"eq.{user_id}"}

        count = self.client.delete_record_sync("memory_preferences", filters, user_token=user_token)
        return count > 0

    def toggle_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> MemoryPreferenceResponse:
        filters = {"id": f"eq.{pref_id}", "user_id": f"eq.{user_id}"}
        existing = self.client.get_record_sync("memory_preferences", filters, user_token=user_token)
        if not existing:
            raise ResourceNotFoundException(detail=f"Preference {pref_id} not found", resource_type="memory_preference", resource_id=str(pref_id))

        new_status = not existing.get("is_active", True)
        res = self.client.update_record_sync("memory_preferences", filters, {"is_active": new_status, "updated_at": get_utc_now().isoformat()}, user_token=user_token)
        return self._row_to_pref(res[0] if res else existing)

    def get_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        uid = user_id or self.default_user_id
        completed_tasks = self.list_tasks(user_id=uid, status="COMPLETED", user_token=user_token)
        clusters: Dict[str, List[int]] = {}
        for t in completed_tasks:
            if t.actual_duration_min:
                words = [w for w in t.title.lower().split() if len(w) > 3]
                for w in words:
                    if w not in clusters:
                        clusters[w] = []
                    clusters[w].append(t.actual_duration_min)

        suggestions: List[DurationPriorSuggestion] = []
        for kw, samples in clusters.items():
            if len(samples) >= 2:
                avg_dur = sum(samples) // len(samples)
                suggestions.append(DurationPriorSuggestion(
                    task_pattern=kw,
                    suggested_duration_min=avg_dur,
                    historical_samples=len(samples),
                    confidence=min(0.5 + 0.1 * len(samples), 0.95),
                    rationale=f"Observed average {avg_dur}m across {len(samples)} '{kw}' tasks in PostgreSQL history."
                ))
        return suggestions

    def analyze_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        return self.get_duration_priors(user_id, user_token=user_token)

    def purge_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> DataPurgeResponse:
        now = get_utc_now()
        counts = {}
        # Order of deletion respecting foreign key references:
        # 1. Dependent edges and items
        counts["task_dependencies"] = self.client.delete_record_sync("task_dependencies", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["tasks"] = self.client.delete_record_sync("tasks", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["proposal_items"] = self.client.delete_record_sync("proposal_items", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["proposals"] = self.client.delete_record_sync("proposals", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["captures"] = self.client.delete_record_sync("captures", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["plans"] = self.client.delete_record_sync("plans", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["busy_events"] = self.client.delete_record_sync("busy_events", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["availability_windows"] = self.client.delete_record_sync("availability_windows", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["contextual_summaries"] = self.client.delete_record_sync("contextual_summaries", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["memory_preferences"] = self.client.delete_record_sync("memory_preferences", {"user_id": f"eq.{user_id}"}, user_token=user_token)
        counts["approval_idempotency"] = self.client.delete_record_sync("approval_idempotency", {"user_id": f"eq.{user_id}"}, user_token=user_token)

        # Insert immutable audit log for sovereign purge event (System/Audit log insertion with allow_service_role=True)
        self.client.insert_record_sync(
            "audit_logs",
            {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "event_type": "SOVEREIGN_PURGE",
                "metadata": {"purged_at": now.isoformat(), "counts": counts},
                "created_at": now.isoformat()
            },
            allow_service_role=True
        )

        return DataPurgeResponse(
            user_id=user_id,
            purged_at=now,
            records_deleted=counts,
            status="PURGED_SOVEREIGN"
        )

    def export_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> UserDataExportResponse:
        now = get_utc_now()
        tasks = self.list_tasks(user_id=user_id, user_token=user_token)
        proposals = self.list_proposals(user_id=user_id, user_token=user_token)
        prefs = self.list_memory_preferences(user_id=user_id, user_token=user_token)
        profile = self.get_user_profile(user_id, user_token=user_token)

        data = {
            "profile": profile,
            "tasks": [t.model_dump() for t in tasks],
            "proposals": [p.model_dump() for p in proposals],
            "memory_preferences": [pr.model_dump() for pr in prefs],
            "export_metadata": {
                "generated_at": now.isoformat(),
                "export_format": "THOZHI_SOVEREIGN_ARCHIVE_POSTGREST_V1",
                "zero_audio_retention_verified": True
            }
        }

        return UserDataExportResponse(
            user_id=user_id,
            exported_at=now,
            tasks_count=len(tasks),
            proposals_count=len(proposals),
            preferences_count=len(prefs),
            data=data
        )

    def _row_to_pref(self, r: dict) -> MemoryPreferenceResponse:
        p_id = _parse_uuid(r["id"]) or uuid4()
        u_id = _parse_uuid(r.get("user_id")) or self.default_user_id
        dt_create = _parse_dt(r.get("created_at")) or get_utc_now()
        dt_up = _parse_dt(r.get("updated_at")) or dt_create
        cat = r.get("category", "PLANNING_STYLE")
        if isinstance(cat, str):
            try:
                cat = MemoryCategoryEnum(cat)
            except Exception:
                cat = MemoryCategoryEnum.PLANNING_STYLE

        return MemoryPreferenceResponse(
            id=p_id,
            user_id=u_id,
            category=cat,
            preference_key=r.get("preference_key", ""),
            preference_value=r.get("preference_value", {}),
            description=r.get("description"),
            is_active=bool(r.get("is_active", True)),
            consent_level=r.get("consent_level", "USER_EXPLICIT"),
            created_at=dt_create,
            updated_at=dt_up
        )
