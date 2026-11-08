from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, date, timedelta
from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction, ClarificationQuestion, PriorityEnum
from backend.app.schemas.proposal import (
    ProposalResponse,
    ProposalItemResponse,
    ProposalApproveRequest,
    ProposalApproveResponse,
    ProposalItemPatch,
    ProposalClarificationRequest,
    ProposalItemUpdate,
)
from backend.app.schemas.capture import CaptureResponse, CaptureCreate
from backend.app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent, PlanResponse
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
)
from backend.app.db.repositories.base import BaseRepository

def get_utc_now():
    return datetime.now(timezone.utc)

class InMemoryStore(BaseRepository):
    """
    Self-contained store matching the 14-table schema for local execution and test suites.
    """
    def __init__(self):
        self.users: Dict[UUID, dict] = {}
        self.captures: Dict[UUID, dict] = {}
        self.proposals: Dict[UUID, dict] = {}
        self.proposal_items: Dict[UUID, dict] = {}
        self.tasks: Dict[UUID, dict] = {}
        self.task_dependencies: List[dict] = []
        self.availability_windows: Dict[UUID, List[AvailabilityWindow]] = {}
        self.busy_events: Dict[UUID, List[BusyEvent]] = {}
        self.idempotency_keys: Dict[str, dict] = {}
        self.memory_preferences: Dict[UUID, dict] = {}

        # Seed default test user
        self.default_user_id = UUID("00000000-0000-0000-0000-000000000001")
        self.users[self.default_user_id] = {
            "id": self.default_user_id,
            "email": "test@thozhi.ai",
            "full_name": "Test User",
            "locale": "ta-IN",
            "timezone": "Asia/Kolkata"
        }
        self._seed_default_memory()

    def _seed_default_memory(self):
        now = get_utc_now()
        seed_prefs = [
            {
                "id": uuid4(),
                "user_id": self.default_user_id,
                "category": MemoryCategoryEnum.PLANNING_STYLE,
                "preference_key": "morning_deep_work_window",
                "preference_value": {"start": "09:30", "end": "12:30", "preferred_priority": "P1"},
                "description": "User prefers scheduling P1 analytical and coding tasks between 09:30 AM and 12:30 PM.",
                "is_active": True,
                "consent_level": "EXPLICIT_CONSENT",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": uuid4(),
                "user_id": self.default_user_id,
                "category": MemoryCategoryEnum.WORKING_HOURS,
                "preference_key": "protected_lunch_break",
                "preference_value": {"start": "13:00", "end": "14:00", "blocking": True},
                "description": "Protected lunch break: never schedule focus blocks or calls between 13:00 and 14:00.",
                "is_active": True,
                "consent_level": "EXPLICIT_CONSENT",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": uuid4(),
                "user_id": self.default_user_id,
                "category": MemoryCategoryEnum.DURATION_PRIOR,
                "preference_key": "technical_report_duration_prior",
                "preference_value": {"baseline_multiplier": 1.4, "suggested_min": 75},
                "description": "Technical reports and architecture documentation typically require +45 mins buffer.",
                "is_active": True,
                "consent_level": "USER_APPROVED",
                "created_at": now,
                "updated_at": now
            }
        ]
        for p in seed_prefs:
            self.memory_preferences[p["id"]] = p

    # ---------------- USER PROFILE ----------------
    def get_user_profile(self, user_id: UUID, user_token: Optional[str] = None) -> dict:
        user = self.users.get(user_id)
        if not user:
            user = {
                "id": user_id,
                "email": "user@thozhi.ai",
                "full_name": "Karthi P.",
                "locale": "ta-IN",
                "timezone": "Asia/Kolkata"
            }
            self.users[user_id] = user
        return user

    def update_user_profile(self, user_id: UUID, updates: dict, user_token: Optional[str] = None) -> dict:
        user = self.get_user_profile(user_id)
        for k, v in updates.items():
            if v is not None:
                user[k] = v
        if "full_name" in updates and updates["full_name"]:
            now = get_utc_now()
            self.set_memory_preference(
                user_id=user_id,
                create_req=MemoryPreferenceCreate(
                    preference_key="user_profile",
                    category=MemoryCategoryEnum.USER_PROFILE,
                    preference_value={"full_name": updates["full_name"]},
                    description=f"User display name is {updates['full_name']}."
                )
            )
        return user

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
        capture_id = uuid4()
        now = get_utc_now()
        cap_dict = {
            "id": capture_id,
            "user_id": user_id,
            "input_type": input_type.upper(),
            "transcript_text": transcript_text,
            "original_transcript": original_transcript or transcript_text,
            "translated_transcript": translated_transcript,
            "detected_language": detected_language,
            "processing_status": processing_status,
            "lifecycle_status": "PENDING_REVIEW",
            "created_at": now,
            "proposal_ids": [],
            "provider_metadata": provider_metadata or {},
            "error_message": None
        }
        self.captures[capture_id] = cap_dict
        return CaptureResponse(**cap_dict, proposals=[], proposal_count=0)

    def _compute_capture_lifecycle_status(self, proposals: List[ProposalResponse]) -> str:
        if not proposals:
            return "COMPLETED"
        statuses = [p.status for p in proposals]
        if all(s in ("COMMITTED", "RESOLVED") for s in statuses):
            return "COMMITTED"
        if all(s == "REJECTED" for s in statuses):
            return "REJECTED"
        if any(s == "APPROVED" for s in statuses):
            return "APPROVED"
        if any(s in ("PENDING", "PENDING_REVIEW") for s in statuses):
            return "PENDING_REVIEW"
        return statuses[0]

    def get_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[CaptureResponse]:
        cap = self.captures.get(capture_id)
        if not cap:
            return None
        if user_id and cap["user_id"] != user_id:
            return None

        props: List[ProposalResponse] = []
        for pid in cap.get("proposal_ids", []):
            prop = self.get_proposal(pid)
            if prop:
                props.append(prop)

        lifecycle = self._compute_capture_lifecycle_status(props)
        cap["lifecycle_status"] = lifecycle
        return CaptureResponse(
            **cap,
            proposals=props,
            proposal_count=len(props)
        )

    def list_captures(self, user_id: Optional[UUID] = None, limit: int = 20, user_token: Optional[str] = None) -> List[CaptureResponse]:
        target_user = user_id or self.default_user_id
        caps = [
            c for c in self.captures.values()
            if not user_id or c["user_id"] == target_user
        ]
        caps.sort(key=lambda c: c["created_at"], reverse=True)
        if limit:
            caps = caps[:limit]

        res: List[CaptureResponse] = []
        for cap in caps:
            props: List[ProposalResponse] = []
            for pid in cap.get("proposal_ids", []):
                p = self.get_proposal(pid)
                if p:
                    props.append(p)
            lifecycle = self._compute_capture_lifecycle_status(props)
            cap["lifecycle_status"] = lifecycle
            res.append(
                CaptureResponse(
                    **cap,
                    proposals=props,
                    proposal_count=len(props)
                )
            )
        return res

    def delete_capture(self, capture_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        cap = self.captures.get(capture_id)
        if not cap:
            return False
        if user_id and cap["user_id"] != user_id:
            return False
        del self.captures[capture_id]
        return True

    def clear_captures(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> int:
        target_user = user_id or self.default_user_id
        to_del = [cid for cid, c in self.captures.items() if not user_id or c["user_id"] == target_user]
        for cid in to_del:
            del self.captures[cid]
        return len(to_del)

    # ---------------- PROPOSALS & EXTRACTIONS ----------------
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
        expires_at = now + timedelta(hours=24)

        item_responses: List[ProposalItemResponse] = []

        active_priors = [
            p for p in self.memory_preferences.values()
            if p["user_id"] == user_id and p["is_active"] and p["category"] == MemoryCategoryEnum.DURATION_PRIOR
        ]

        for item in extraction.extracted_items:
            est_dur = item.estimated_duration_min
            dur_source = item.duration_source or ("USER_EXPLICIT" if est_dur is not None else "UNSPECIFIED")

            # Stage 6 Contextual Memory: calibrate duration from learned priors if unspecified or default heuristic
            if (est_dur is None or dur_source == "DEFAULT_HEURISTIC") and active_priors:
                title_lower = item.proposed_title.lower()
                for prior in active_priors:
                    val = prior.get("preference_value", {})
                    key_lower = prior.get("preference_key", "").lower()
                    desc_lower = (prior.get("description") or "").lower()
                    if any(kw in title_lower for kw in ["report", "presentation", "assignment", "meeting", "review"] if kw in key_lower or kw in desc_lower):
                        if "suggested_min" in val:
                            est_dur = int(val["suggested_min"])
                            dur_source = "LEARNED_PRIOR"
                            break
                        elif "baseline_multiplier" in val:
                            base = est_dur if est_dur is not None else 30
                            est_dur = int(base * float(val["baseline_multiplier"]))
                            dur_source = "LEARNED_PRIOR"
                            break

            uncertainty_flags = list(item.uncertainty_flags or [])
            if est_dur is None and "UNSPECIFIED_DURATION" not in uncertainty_flags:
                uncertainty_flags.append("UNSPECIFIED_DURATION")
            if (item.priority is None or item.priority == PriorityEnum.UNSPECIFIED) and "UNSPECIFIED_PRIORITY" not in uncertainty_flags:
                uncertainty_flags.append("UNSPECIFIED_PRIORITY")

            item_id = uuid4()
            item_dict = {
                "id": item_id,
                "proposal_id": prop_id,
                "temp_id": item.temp_id,
                "item_type": item.item_type,
                "action": getattr(item, "action", None),
                "object": getattr(item, "object", None),
                "proposed_title": item.proposed_title,
                "description": item.description,
                "original_title": item.proposed_title,
                "original_description": item.description,
                "translated_title": None,
                "translated_description": None,
                "source_expression": item.source_expression,
                "deadline_expression": item.deadline_expression,
                "normalized_deadline": datetime.fromisoformat(item.normalized_deadline_iso) if item.normalized_deadline_iso else None,
                "estimated_duration_min": est_dur,
                "duration_source": dur_source,
                "priority": item.priority,
                "confidence_score": item.confidence,
                "intent_confidence": getattr(item, "intent_confidence", None),
                "action_confidence": getattr(item, "action_confidence", None),
                "object_confidence": getattr(item, "object_confidence", None),
                "deadline_confidence": getattr(item, "deadline_confidence", None),
                "uncertainty_flags": uncertainty_flags,
                "condition_trigger": item.condition_trigger,
                "decision_state": "PENDING",
                "rejection_reason": None,
                "created_at": now
            }
            self.proposal_items[item_id] = item_dict
            item_responses.append(ProposalItemResponse(**item_dict))

        # Preserve original questions and options for clarifications
        clar_list = []
        for q in (extraction.clarifications or []):
            q_dict = q.model_dump() if hasattr(q, "model_dump") else dict(q)
            if not q_dict.get("original_question_text"):
                q_dict["original_question_text"] = q_dict.get("question_text")
            if not q_dict.get("original_suggested_options"):
                q_dict["original_suggested_options"] = list(q_dict.get("suggested_options", []))
            clar_list.append(ClarificationQuestion(**q_dict))

        prop_dict = {
            "id": prop_id,
            "user_id": user_id,
            "capture_id": capture_id,
            "transcript_text": extraction.transcript_text,
            "original_transcript": extraction.transcript_text,
            "translated_transcript": None,
            "display_language": "original",
            "translation_status": "ORIGINAL",
            "intent_summary": extraction.intent_summary,
            "original_intent_summary": extraction.intent_summary,
            "translated_intent_summary": None,
            "detected_language": extraction.detected_language,
            "status": "PENDING_REVIEW",
            "created_at": now,
            "expires_at": expires_at,
            "clarifications": clar_list
        }
        self.proposals[prop_id] = prop_dict
        if capture_id and capture_id in self.captures:
            if prop_id not in self.captures[capture_id]["proposal_ids"]:
                self.captures[capture_id]["proposal_ids"].append(prop_id)

        return ProposalResponse(
            **prop_dict,
            items=item_responses
        )

    def get_proposal(self, proposal_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[ProposalResponse]:
        prop = self.proposals.get(proposal_id)
        if not prop:
            return None
        if user_id is not None and prop.get("user_id") != user_id:
            return None

        items = [
            ProposalItemResponse(**item)
            for item in self.proposal_items.values()
            if item["proposal_id"] == proposal_id
        ]
        return ProposalResponse(
            **prop,
            items=items
        )

    def list_proposals(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        capture_id: Optional[UUID] = None,
        limit: int = 50,
        user_token: Optional[str] = None
    ) -> List[ProposalResponse]:
        target_user = user_id or self.default_user_id
        matching: List[ProposalResponse] = []
        for pid, prop in self.proposals.items():
            if user_id and prop["user_id"] != target_user:
                continue
            if capture_id and prop.get("capture_id") != capture_id:
                continue
            if status:
                prop_status = prop.get("status", "").upper()
                filter_status = status.upper()
                if filter_status == "PENDING" and prop_status not in ("PENDING", "PENDING_REVIEW"):
                    continue
                elif filter_status != "PENDING" and prop_status != filter_status:
                    continue

            p_obj = self.get_proposal(pid)
            if p_obj:
                matching.append(p_obj)

        matching.sort(key=lambda p: p.created_at, reverse=True)
        if limit:
            matching = matching[:limit]
        return matching

    def reject_proposal(
        self,
        proposal_id: UUID,
        user_id: Optional[UUID] = None,
        reason: Optional[str] = "User rejected proposal",
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        prop = self.proposals.get(proposal_id)
        if not prop:
            raise KeyError(f"Proposal {proposal_id} not found")
        if user_id and prop["user_id"] != user_id:
            raise KeyError(f"Proposal {proposal_id} not found for this user")

        prop["status"] = "REJECTED"
        for item in self.proposal_items.values():
            if item["proposal_id"] == proposal_id:
                item["decision_state"] = "REJECTED"
                item["rejection_reason"] = reason

        if prop.get("capture_id") and prop["capture_id"] in self.captures:
            cap_props = [self.get_proposal(pid) for pid in self.captures[prop["capture_id"]].get("proposal_ids", [])]
            self.captures[prop["capture_id"]]["lifecycle_status"] = self._compute_capture_lifecycle_status([p for p in cap_props if p])

        return self.get_proposal(proposal_id)

    def batch_approve_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> dict:
        uid = user_id or self.default_user_id
        created_task_ids: List[UUID] = []
        affected_count = 0
        for pid in proposal_ids:
            prop = self.proposals.get(pid)
            if not prop or prop.get("status") in ("COMMITTED", "REJECTED"):
                continue
            items = [item for item in self.proposal_items.values() if item["proposal_id"] == pid]
            decisions = [
                ProposalItemUpdate(
                    id=item["id"],
                    proposed_title=item["proposed_title"],
                    estimated_duration_min=item["estimated_duration_min"],
                    priority=item["priority"],
                    is_approved=True
                )
                for item in items
            ]
            key = f"{idempotency_key}_{pid}" if idempotency_key else str(uuid4())
            res = self.approve_proposal(
                proposal_id=pid,
                user_id=uid,
                request=ProposalApproveRequest(idempotency_key=key, items=decisions),
                user_token=user_token
            )
            created_task_ids.extend(res.created_task_ids)
            affected_count += 1
        return {
            "affected_count": affected_count,
            "created_task_ids": created_task_ids,
            "proposal_ids": proposal_ids,
            "message": f"Successfully batch approved and committed {affected_count} proposals."
        }

    def batch_reject_proposals(
        self,
        proposal_ids: List[UUID],
        user_id: Optional[UUID] = None,
        reason: Optional[str] = "Batch rejected by user",
        user_token: Optional[str] = None
    ) -> dict:
        uid = user_id or self.default_user_id
        affected_count = 0
        for pid in proposal_ids:
            prop = self.proposals.get(pid)
            if not prop or prop.get("status") in ("COMMITTED", "REJECTED"):
                continue
            self.reject_proposal(proposal_id=pid, user_id=uid, reason=reason, user_token=user_token)
            affected_count += 1
        return {
            "affected_count": affected_count,
            "proposal_ids": proposal_ids,
            "message": f"Successfully batch rejected {affected_count} proposals."
        }

    def update_proposal_item(
        self,
        proposal_id: UUID,
        item_id: UUID,
        patch: ProposalItemPatch,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalItemResponse:
        item = self.proposal_items.get(item_id)
        if not item or item["proposal_id"] != proposal_id:
            raise ResourceNotFoundException(
                detail=f"Proposal item {item_id} not found in proposal {proposal_id}",
                resource_type="proposal_item",
                resource_id=str(item_id)
            )
        patch_dict = patch.model_dump(exclude_unset=True)
        for k, v in patch_dict.items():
            item[k] = v
        return ProposalItemResponse(**item)

    def apply_clarifications(
        self,
        proposal_id: UUID,
        request: ProposalClarificationRequest,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        prop = self.proposals.get(proposal_id)
        if not prop:
            raise ResourceNotFoundException(
                detail=f"Proposal {proposal_id} not found",
                resource_type="proposal",
                resource_id=str(proposal_id)
            )

        for ans in request.answers:
            for q in prop.get("clarifications", []):
                q_id = q.id if hasattr(q, "id") else (q.get("id") if isinstance(q, dict) else "")
                if q_id == ans.question_id:
                    rel_id = (
                        getattr(q, "target_item_temp_id", None)
                        or getattr(q, "related_item_temp_id", None)
                        or (q.get("target_item_temp_id") if isinstance(q, dict) else None)
                        or (q.get("related_item_temp_id") if isinstance(q, dict) else None)
                    )
                    if rel_id:
                        for it in self.proposal_items.values():
                            if it["proposal_id"] == proposal_id and it["temp_id"] == rel_id:
                                if ans.resolved_deadline_iso:
                                    it["normalized_deadline"] = datetime.fromisoformat(ans.resolved_deadline_iso)
                                if ans.resolved_duration_min:
                                    it["estimated_duration_min"] = ans.resolved_duration_min
                                if ans.resolved_item_type:
                                    it["item_type"] = ans.resolved_item_type
                                it["uncertainty_flags"] = [f for f in it.get("uncertainty_flags", []) if "UNCERTAIN" not in f]

        return self.get_proposal(proposal_id)

    async def translate_proposal(
        self,
        proposal_id: UUID,
        target_language: str,
        translator = None,
        user_id: Optional[UUID] = None,
        user_token: Optional[str] = None
    ) -> ProposalResponse:
        """
        Translates proposal transcript, intent summary, item titles, descriptions,
        and clarification questions to target_language ('en', 'ta', or 'original').
        Invariants:
        1. original_transcript, original_title, and original_description are NEVER overwritten.
        2. Normalized deadlines, estimated durations, priorities, and dependency graphs are NEVER altered.
        3. Switching to 'original' is instant and fully reversible.
        """
        prop = self.proposals.get(proposal_id)
        if not prop:
            raise ResourceNotFoundException(
                detail=f"Proposal {proposal_id} not found",
                resource_type="proposal",
                resource_id=str(proposal_id)
            )

        target = target_language.lower().strip()
        items = [
            it for it in self.proposal_items.values()
            if it["proposal_id"] == proposal_id
        ]

        # Case 1: Revert to Original Language
        if target in ["original", "auto", "none"]:
            prop["transcript_text"] = prop.get("original_transcript") or prop.get("transcript_text")
            prop["intent_summary"] = prop.get("original_intent_summary") or prop.get("intent_summary")
            prop["display_language"] = "original"
            prop["translation_status"] = "ORIGINAL"
            prop["translated_transcript"] = None
            prop["translated_intent_summary"] = None

            for item in items:
                item["proposed_title"] = item.get("original_title") or item["proposed_title"]
                item["description"] = item.get("original_description")
                item["translated_title"] = None
                item["translated_description"] = None

            for q in prop.get("clarifications", []):
                if hasattr(q, "original_question_text") and q.original_question_text:
                    q.question_text = q.original_question_text
                elif isinstance(q, dict) and q.get("original_question_text"):
                    q["question_text"] = q["original_question_text"]
                if hasattr(q, "original_suggested_options") and q.original_suggested_options:
                    q.suggested_options = list(q.original_suggested_options)
                elif isinstance(q, dict) and q.get("original_suggested_options"):
                    q["suggested_options"] = list(q["original_suggested_options"])

            return self.get_proposal(proposal_id)

        # Case 2: Translate to English ('en') or Tamil ('ta')
        from backend.app.providers.translation.sarvam import SarvamTranslationProvider
        active_translator = translator or SarvamTranslationProvider()

        src_transcript = prop.get("original_transcript") or prop.get("transcript_text") or ""
        src_intent = prop.get("original_intent_summary") or prop.get("intent_summary") or ""
        src_lang = prop.get("detected_language") or "auto"

        texts_to_translate = [src_transcript, src_intent]

        # Items
        for item in items:
            src_item_title = item.get("original_title") or item["proposed_title"]
            texts_to_translate.append(src_item_title)
            if item.get("original_description"):
                texts_to_translate.append(item["original_description"])

        # Clarifications
        clar_questions = prop.get("clarifications", [])
        for q in clar_questions:
            q_text = getattr(q, "original_question_text", None) or (q.get("original_question_text") if isinstance(q, dict) else None) or (getattr(q, "question_text", None) or (q.get("question_text") if isinstance(q, dict) else ""))
            texts_to_translate.append(q_text)
            options = getattr(q, "original_suggested_options", None) or (q.get("original_suggested_options") if isinstance(q, dict) else None) or (getattr(q, "suggested_options", []) or (q.get("suggested_options") if isinstance(q, dict) else []))
            for opt in options:
                texts_to_translate.append(opt)

        translated_results = await active_translator.translate_batch(
            texts=texts_to_translate,
            source_language=src_lang,
            target_language=target
        )

        res_idx = 0
        trans_transcript = translated_results[res_idx].translated_text
        res_idx += 1
        trans_intent = translated_results[res_idx].translated_text
        res_idx += 1

        for item in items:
            trans_title = translated_results[res_idx].translated_text
            res_idx += 1
            item["proposed_title"] = trans_title
            item["translated_title"] = trans_title
            if item.get("original_description"):
                trans_desc = translated_results[res_idx].translated_text
                res_idx += 1
                item["description"] = trans_desc
                item["translated_description"] = trans_desc

        for q in clar_questions:
            trans_q_text = translated_results[res_idx].translated_text
            res_idx += 1
            if hasattr(q, "question_text"):
                q.question_text = trans_q_text
            elif isinstance(q, dict):
                q["question_text"] = trans_q_text

            options = getattr(q, "original_suggested_options", None) or (q.get("original_suggested_options") if isinstance(q, dict) else None) or (getattr(q, "suggested_options", []) or (q.get("suggested_options") if isinstance(q, dict) else []))
            new_opts = []
            for _ in options:
                new_opts.append(translated_results[res_idx].translated_text)
                res_idx += 1
            if hasattr(q, "suggested_options"):
                q.suggested_options = new_opts
            elif isinstance(q, dict):
                q["suggested_options"] = new_opts

        prop["transcript_text"] = trans_transcript
        prop["translated_transcript"] = trans_transcript
        prop["intent_summary"] = trans_intent
        prop["translated_intent_summary"] = trans_intent
        prop["display_language"] = target
        prop["translation_status"] = "TRANSLATED"

        return self.get_proposal(proposal_id)

    def approve_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        request: ProposalApproveRequest,
        user_token: Optional[str] = None
    ) -> ProposalApproveResponse:
        # Idempotency check
        if request.idempotency_key in self.idempotency_keys:
            prev = self.idempotency_keys[request.idempotency_key]
            return ProposalApproveResponse(**prev)

        prop = self.proposals.get(proposal_id)
        if not prop:
            raise KeyError(f"Proposal {proposal_id} not found")
        if prop["expires_at"] < get_utc_now():
            raise ProposalExpiredException(str(proposal_id))

        approved_task_ids: List[UUID] = []
        rejected_count = 0
        now = get_utc_now()

        for decision in request.items:
            item = self.proposal_items.get(decision.id)
            if not item or item["proposal_id"] != proposal_id:
                continue

            if decision.is_approved:
                item["decision_state"] = "APPROVED"
                task_id = uuid4()
                resolved_deadline = datetime.fromisoformat(decision.normalized_deadline_iso) if decision.normalized_deadline_iso else item.get("normalized_deadline")
                if decision.scheduled_date:
                    sched_date = date.fromisoformat(decision.scheduled_date)
                elif resolved_deadline:
                    sched_date = resolved_deadline.date()
                else:
                    sched_date = date.today()

                dur_min = decision.estimated_duration_min if decision.estimated_duration_min is not None else item.get("estimated_duration_min")
                dur_source = "USER_EXPLICIT" if decision.estimated_duration_min is not None else item.get("duration_source", "UNSPECIFIED")

                new_task = {
                    "id": task_id,
                    "user_id": user_id,
                    "title": decision.proposed_title or item["proposed_title"],
                    "description": item["description"],
                    "priority": decision.priority or item["priority"],
                    "estimated_duration_min": dur_min,
                    "duration_source": dur_source,
                    "actual_duration_min": None,
                    "deadline": resolved_deadline,
                    "scheduled_date": sched_date,
                    "scheduled_start": None,
                    "scheduled_end": None,
                    "status": "PENDING",
                    "origin_proposal_item_id": item["id"],
                    "source_language": prop["detected_language"],
                    "completed_at": None,
                    "created_at": now,
                    "updated_at": now
                }
                self.tasks[task_id] = new_task
                approved_task_ids.append(task_id)
            else:
                item["decision_state"] = "REJECTED"
                item["rejection_reason"] = decision.rejection_reason or "User dismissed item"
                rejected_count += 1

        prop["status"] = "COMMITTED" if approved_task_ids else "REJECTED"
        if prop.get("capture_id") and prop["capture_id"] in self.captures:
            cap_props = [self.get_proposal(pid) for pid in self.captures[prop["capture_id"]].get("proposal_ids", [])]
            self.captures[prop["capture_id"]]["lifecycle_status"] = self._compute_capture_lifecycle_status([p for p in cap_props if p])

        resp = {
            "proposal_id": proposal_id,
            "approved_tasks_count": len(approved_task_ids),
            "rejected_items_count": rejected_count,
            "created_task_ids": approved_task_ids,
            "message": "Human decision recorded. Tasks explicitly committed to schedule."
        }
        self.idempotency_keys[request.idempotency_key] = resp
        return ProposalApproveResponse(**resp)

    # ---------------- TASKS ----------------
    def create_task(self, user_id: UUID, task_create: TaskCreate, user_token: Optional[str] = None) -> TaskResponse:
        now = get_utc_now()
        target_sched_date = task_create.scheduled_date or now.date()

        # Duplicate prevention check
        norm_title = task_create.title.strip().lower()
        for t in self.tasks.values():
            if t["user_id"] == user_id and t["status"] != "COMPLETED":
                if t["title"].strip().lower() == norm_title and t["scheduled_date"] == target_sched_date:
                    raise DuplicateTaskException(title=task_create.title, scheduled_date=str(target_sched_date))

        task_id = uuid4()
        dur_src = getattr(task_create, "duration_source", "USER_EXPLICIT" if task_create.estimated_duration_min else "UNSPECIFIED")
        task_dict = {
            "id": task_id,
            "user_id": user_id,
            "title": task_create.title.strip(),
            "description": task_create.description,
            "priority": task_create.priority,
            "estimated_duration_min": task_create.estimated_duration_min,
            "duration_source": dur_src,
            "actual_duration_min": None,
            "deadline": task_create.deadline,
            "scheduled_date": target_sched_date,
            "scheduled_start": None,
            "scheduled_end": None,
            "status": "PENDING",
            "origin_proposal_item_id": task_create.origin_proposal_item_id,
            "source_language": "en",
            "completed_at": None,
            "created_at": now,
            "updated_at": now
        }
        self.tasks[task_id] = task_dict
        return TaskResponse(**task_dict, dependencies=[])

    def list_tasks(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        target_date: Optional[date] = None,
        deadline_date: Optional[date] = None,
        user_token: Optional[str] = None
    ) -> List[TaskResponse]:
        target_user = user_id or self.default_user_id
        result = []
        for t in self.tasks.values():
            if not user_id or t["user_id"] == target_user:
                if status and t["status"].upper() != status.upper():
                    continue
                if target_date is not None and t["scheduled_date"] != target_date:
                    continue
                if deadline_date is not None and (not t["deadline"] or t["deadline"].date() != deadline_date):
                    continue
                deps = [
                    d["depends_on_task_id"]
                    for d in self.task_dependencies
                    if d["task_id"] == t["id"]
                ]
                result.append(TaskResponse(**t, dependencies=deps))
        return result

    def get_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> Optional[TaskResponse]:
        t = self.tasks.get(task_id)
        if not t:
            return None
        if user_id is not None and t.get("user_id") != user_id:
            return None
        deps = [
            d["depends_on_task_id"]
            for d in self.task_dependencies
            if d["task_id"] == t["id"]
        ]
        return TaskResponse(**t, dependencies=deps)

    def update_task(self, task_id: UUID, task_update: TaskUpdate, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        t = self.tasks.get(task_id)
        if not t:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        if user_id is not None and t.get("user_id") != user_id:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        update_data = task_update.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            t[k] = v
        t["updated_at"] = get_utc_now()
        deps = [d["depends_on_task_id"] for d in self.task_dependencies if d["task_id"] == t["id"]]
        return TaskResponse(**t, dependencies=deps)

    def delete_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        if task_id not in self.tasks:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        if user_id is not None and self.tasks[task_id].get("user_id") != user_id:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        del self.tasks[task_id]
        self.task_dependencies = [
            d for d in self.task_dependencies
            if d["task_id"] != task_id and d["depends_on_task_id"] != task_id
        ]
        return True

    def complete_task(self, task_id: UUID, user_id: Optional[UUID] = None, actual_duration_min: Optional[int] = None, user_token: Optional[str] = None) -> TaskResponse:
        task = self.tasks.get(task_id)
        if not task:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        if user_id is not None and task.get("user_id") != user_id:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        now = get_utc_now()
        task["status"] = "COMPLETED"
        task["actual_duration_min"] = actual_duration_min or task.get("estimated_duration_min", 30)
        task["completed_at"] = now
        task["updated_at"] = now
        deps = [d["depends_on_task_id"] for d in self.task_dependencies if d["task_id"] == task_id]
        return TaskResponse(**task, dependencies=deps)

    def reopen_task(self, task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> TaskResponse:
        task = self.tasks.get(task_id)
        if not task:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        if user_id is not None and task.get("user_id") != user_id:
            raise ResourceNotFoundException(
                detail=f"Task {task_id} not found",
                resource_type="task",
                resource_id=str(task_id)
            )
        now = get_utc_now()
        task["status"] = "PENDING"
        task["completed_at"] = None
        task["updated_at"] = now
        deps = [d["depends_on_task_id"] for d in self.task_dependencies if d["task_id"] == task_id]
        return TaskResponse(**task, dependencies=deps)

    def add_task_dependency(self, task_id: UUID, depends_on_task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> dict:
        if task_id not in self.tasks:
            raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
        if depends_on_task_id not in self.tasks:
            raise ResourceNotFoundException(detail=f"Prerequisite task {depends_on_task_id} not found", resource_type="task", resource_id=str(depends_on_task_id))
        if task_id == depends_on_task_id:
            raise SchedulingCycleException("Task cannot depend on itself.")

        if any(d["task_id"] == task_id and d["depends_on_task_id"] == depends_on_task_id for d in self.task_dependencies):
            return {"task_id": task_id, "depends_on_task_id": depends_on_task_id}

        from backend.app.modules.planning.engine import PlanningEngine
        test_deps = [(d["depends_on_task_id"], d["task_id"]) for d in self.task_dependencies]
        test_deps.append((depends_on_task_id, task_id))

        all_tasks = [TaskResponse(**t, dependencies=[]) for t in self.tasks.values()]
        PlanningEngine.topological_sort(all_tasks, test_deps)

        dep_record = {
            "id": uuid4(),
            "user_id": user_id or self.tasks[task_id].get("user_id", self.default_user_id),
            "task_id": task_id,
            "depends_on_task_id": depends_on_task_id
        }
        self.task_dependencies.append(dep_record)
        return dep_record

    def delete_task_dependency(self, task_id: UUID, depends_on_task_id: UUID, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> bool:
        initial_len = len(self.task_dependencies)
        self.task_dependencies = [
            d for d in self.task_dependencies
            if not (d["task_id"] == task_id and d["depends_on_task_id"] == depends_on_task_id)
        ]
        return len(self.task_dependencies) < initial_len

    def get_task_dependencies(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[dict]:
        if user_id is None:
            return list(self.task_dependencies)
        user_tasks = {t_id for t_id, t in self.tasks.items() if t.get("user_id") == user_id}
        return [
            d for d in self.task_dependencies
            if d.get("user_id") == user_id or d["task_id"] in user_tasks
        ]

    # ---------------- PLANNING & AVAILABILITY ----------------
    def get_user_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        uid = user_id or self.default_user_id
        if uid in self.availability_windows:
            return self.availability_windows[uid]
        from datetime import time

        # Stage 6: Check if user configured working hours preference in personal memory
        for p in self.memory_preferences.values():
            if p["user_id"] == uid and p["is_active"] and p["preference_key"] == "user_working_hours":
                val = p.get("preference_value", {})
                start_str = val.get("startTime") or val.get("start")
                end_str = val.get("endTime") or val.get("end")
                if start_str and end_str:
                    try:
                        s_h, s_m = map(int, str(start_str).split(":"))
                        e_h, e_m = map(int, str(end_str).split(":"))
                        return [
                            AvailabilityWindow(day_of_week=i, start_time=time(s_h, s_m), end_time=time(e_h, e_m))
                            for i in range(5)
                        ]
                    except Exception:
                        pass

        return [
            AvailabilityWindow(day_of_week=i, start_time=time(9, 0), end_time=time(18, 0))
            for i in range(5)
        ]

    def get_user_busy_events(self, user_id: Optional[UUID] = None, target_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        uid = user_id or self.default_user_id
        events = list(self.busy_events.get(uid, []))
        from datetime import time
        t_date = target_date or get_utc_now().date()
        # Stage 6: Automatically respect active blocking memory preferences (e.g. protected lunch break)
        for p in self.memory_preferences.values():
            if p["user_id"] == uid and p["is_active"] and p.get("preference_value", {}).get("blocking"):
                val = p["preference_value"]
                start_str = val.get("start")
                end_str = val.get("end")
                if start_str and end_str:
                    try:
                        s_h, s_m = map(int, str(start_str).split(":"))
                        e_h, e_m = map(int, str(end_str).split(":"))
                        b_start = datetime.combine(t_date, time(s_h, s_m))
                        b_end = datetime.combine(t_date, time(e_h, e_m))
                        title = p.get("description") or p["preference_key"]
                        if not any(e.title == title for e in events):
                            events.append(
                                BusyEvent(
                                    id=p["id"],
                                    user_id=uid,
                                    title=title,
                                    start_time=b_start,
                                    end_time=b_end,
                                    is_blocking=True
                                )
                            )
                    except Exception:
                        pass
        return events

    # ---------------- STAGE 6: PERSONAL MEMORY & PRIVACY ----------------
    def list_memory_preferences(
        self,
        user_id: Optional[UUID] = None,
        category: Optional[MemoryCategoryEnum] = None,
        active_only: bool = False,
        user_token: Optional[str] = None
    ) -> List[MemoryPreferenceResponse]:
        uid = user_id or self.default_user_id
        results = []
        for p in self.memory_preferences.values():
            if p["user_id"] == uid:
                if active_only and not p.get("is_active", True):
                    continue
                if category and p.get("category") != category:
                    continue
                p_copy = dict(p)
                if "created_at" not in p_copy:
                    p_copy["created_at"] = get_utc_now()
                if "updated_at" not in p_copy:
                    p_copy["updated_at"] = get_utc_now()
                results.append(MemoryPreferenceResponse(**p_copy))
        return results

    def get_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> MemoryPreferenceResponse:
        p = self.memory_preferences.get(pref_id)
        if not p or p.get("user_id") != user_id:
            raise ResourceNotFoundException(
                detail=f"Preference with ID {pref_id} not found",
                resource_type="memory_preference",
                resource_id=str(pref_id)
            )
        p_copy = dict(p)
        if "created_at" not in p_copy:
            p_copy["created_at"] = get_utc_now()
        if "updated_at" not in p_copy:
            p_copy["updated_at"] = get_utc_now()
        return MemoryPreferenceResponse(**p_copy)

    def set_memory_preference(
        self,
        user_id: UUID,
        create_req: MemoryPreferenceCreate,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        now = get_utc_now()
        # Check if preference_key already exists for this user (upsert)
        for p in self.memory_preferences.values():
            if p["user_id"] == user_id and p["preference_key"] == create_req.preference_key:
                p["category"] = create_req.category
                p["preference_value"] = create_req.preference_value
                p["description"] = create_req.description or p.get("description")
                p["consent_level"] = create_req.consent_level
                p["is_active"] = True
                p["updated_at"] = now
                return MemoryPreferenceResponse(**p)

        pref_id = uuid4()
        new_pref = {
            "id": pref_id,
            "user_id": user_id,
            "category": create_req.category,
            "preference_key": create_req.preference_key,
            "preference_value": create_req.preference_value,
            "description": create_req.description or f"User preference for {create_req.preference_key}",
            "is_active": True,
            "consent_level": create_req.consent_level,
            "created_at": now,
            "updated_at": now
        }
        self.memory_preferences[pref_id] = new_pref
        return MemoryPreferenceResponse(**new_pref)

    def patch_memory_preference(
        self,
        user_id: UUID,
        pref_id: UUID,
        patch: MemoryPreferencePatch,
        user_token: Optional[str] = None
    ) -> MemoryPreferenceResponse:
        p = self.memory_preferences.get(pref_id)
        if not p or p["user_id"] != user_id:
            raise ResourceNotFoundException(
                detail=f"Preference {pref_id} not found",
                resource_type="memory_preference",
                resource_id=str(pref_id)
            )
        patch_dict = patch.model_dump(exclude_unset=True)
        for k, v in patch_dict.items():
            p[k] = v
        p["updated_at"] = get_utc_now()
        return MemoryPreferenceResponse(**p)

    def delete_memory_preference(self, user_id: UUID, identifier: str, user_token: Optional[str] = None) -> bool:
        target_id = None
        try:
            u_id = UUID(identifier)
            if u_id in self.memory_preferences and self.memory_preferences[u_id]["user_id"] == user_id:
                target_id = u_id
        except ValueError:
            pass

        if not target_id:
            for p in self.memory_preferences.values():
                if p["user_id"] == user_id and p["preference_key"] == identifier:
                    target_id = p["id"]
                    break

        if not target_id:
            raise ResourceNotFoundException(
                detail=f"Preference '{identifier}' not found for deletion",
                resource_type="memory_preference",
                resource_id=identifier
            )
        del self.memory_preferences[target_id]
        return True

    def toggle_memory_preference(self, user_id: UUID, pref_id: UUID, user_token: Optional[str] = None) -> MemoryPreferenceResponse:
        p = self.memory_preferences.get(pref_id)
        if not p or p["user_id"] != user_id:
            raise ResourceNotFoundException(
                detail=f"Preference {pref_id} not found",
                resource_type="memory_preference",
                resource_id=str(pref_id)
            )
        p["is_active"] = not p["is_active"]
        p["updated_at"] = get_utc_now()
        return MemoryPreferenceResponse(**p)

    def analyze_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        uid = user_id or self.default_user_id
        completed = [
            t for t in self.tasks.values()
            if t["user_id"] == uid and t["status"] == "COMPLETED" and t.get("actual_duration_min")
        ]

        clusters: Dict[str, List[tuple[int, int]]] = {}
        for t in completed:
            title_lower = t["title"].lower()
            keyword = "general"
            for kw in ["report", "presentation", "assignment", "meeting", "call", "review", "audit", "study"]:
                if kw in title_lower:
                    keyword = kw
                    break
            if keyword not in clusters:
                clusters[keyword] = []
            clusters[keyword].append((t.get("estimated_duration_min", 30), t["actual_duration_min"]))

        suggestions: List[DurationPriorSuggestion] = []
        for kw, samples in clusters.items():
            if len(samples) >= 1:
                avg_actual = sum(s[1] for s in samples) // len(samples)
                avg_est = sum(s[0] for s in samples) // len(samples)
                ratio = round(avg_actual / avg_est, 2) if avg_est > 0 else 1.0
                if abs(ratio - 1.0) >= 0.15 or avg_actual != avg_est:
                    suggestions.append(
                        DurationPriorSuggestion(
                            task_pattern=kw,
                            suggested_duration_min=avg_actual,
                            historical_samples=len(samples),
                            confidence=min(0.5 + 0.1 * len(samples), 0.95),
                            rationale=f"Historical data across {len(samples)} '{kw}' task(s) shows actual duration averages {avg_actual}m vs estimated {avg_est}m ({ratio}x)."
                        )
                    )
        return suggestions

    def export_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> UserDataExportResponse:
        user_tasks = [t for t in self.tasks.values() if t["user_id"] == user_id]
        user_props = [p for p in self.proposals.values() if p["user_id"] == user_id]
        user_prefs = [p for p in self.memory_preferences.values() if p["user_id"] == user_id]

        now = get_utc_now()
        data_bundle = {
            "user": self.users.get(user_id, {}),
            "tasks": user_tasks,
            "proposals": user_props,
            "memory_preferences": user_prefs,
            "availability_windows": [w.model_dump() for w in self.get_user_windows(user_id)],
            "export_metadata": {
                "generated_at": now.isoformat(),
                "export_format": "THOZHI_SOVEREIGN_ARCHIVE_V1",
                "zero_audio_retention_verified": True
            }
        }
        return UserDataExportResponse(
            user_id=user_id,
            exported_at=now,
            tasks_count=len(user_tasks),
            proposals_count=len(user_props),
            preferences_count=len(user_prefs),
            data=data_bundle
        )

    def purge_user_data(self, user_id: UUID, user_token: Optional[str] = None) -> DataPurgeResponse:
        task_ids_to_del = [t_id for t_id, t in self.tasks.items() if t["user_id"] == user_id]
        for t_id in task_ids_to_del:
            del self.tasks[t_id]
        self.task_dependencies = [
            d for d in self.task_dependencies
            if d["task_id"] not in task_ids_to_del and d["depends_on_task_id"] not in task_ids_to_del
        ]

        prop_ids_to_del = [p_id for p_id, p in self.proposals.items() if p["user_id"] == user_id]
        for p_id in prop_ids_to_del:
            del self.proposals[p_id]
        item_ids_to_del = [i_id for i_id, i in self.proposal_items.items() if i["proposal_id"] in prop_ids_to_del]
        for i_id in item_ids_to_del:
            del self.proposal_items[i_id]

        pref_ids_to_del = [p_id for p_id, p in self.memory_preferences.items() if p["user_id"] == user_id]
        for p_id in pref_ids_to_del:
            del self.memory_preferences[p_id]

        return DataPurgeResponse(
            user_id=user_id,
            purged_at=get_utc_now(),
            records_deleted={
                "tasks": len(task_ids_to_del),
                "proposals": len(prop_ids_to_del),
                "proposal_items": len(item_ids_to_del),
                "memory_preferences": len(pref_ids_to_del)
            },
            status="PURGED_SOVEREIGN"
        )

    # ---------------- ALIASES & INTERFACE HARMONIZATION ----------------
    def commit_proposal(self, proposal_id: UUID, approve_req: ProposalApproveRequest, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> ProposalApproveResponse:
        return self.approve_proposal(proposal_id=proposal_id, user_id=user_id or self.default_user_id, request=approve_req, user_token=user_token)

    def answer_clarification(self, proposal_id: UUID, req: ProposalClarificationRequest, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> ProposalResponse:
        return self.apply_clarifications(proposal_id=proposal_id, request=req, user_id=user_id, user_token=user_token)

    def get_duration_priors(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[DurationPriorSuggestion]:
        return self.analyze_duration_priors(user_id=user_id or self.default_user_id, user_token=user_token)

    def get_availability_windows(self, user_id: Optional[UUID] = None, user_token: Optional[str] = None) -> List[AvailabilityWindow]:
        return self.get_user_windows(user_id=user_id or self.default_user_id, user_token=user_token)

    def get_busy_events(self, user_id: Optional[UUID] = None, plan_date: Optional[date] = None, user_token: Optional[str] = None) -> List[BusyEvent]:
        return self.get_user_busy_events(user_id=user_id or self.default_user_id, target_date=plan_date or get_utc_now().date(), user_token=user_token)

    def list_pending_proposals(self, user_id: Optional[UUID] = None, limit: int = 50, user_token: Optional[str] = None) -> List[ProposalResponse]:
        return self.list_proposals(user_id=user_id, status="PENDING_REVIEW", limit=limit, user_token=user_token)

    def save_plan(self, user_id: UUID, plan_response: PlanResponse, user_token: Optional[str] = None) -> PlanResponse:
        if not hasattr(self, "saved_plans"):
            self.saved_plans = {}
        self.saved_plans[(user_id, plan_response.plan_date)] = plan_response
        return plan_response

    def get_plan_for_date(self, user_id: UUID, plan_date: date, user_token: Optional[str] = None) -> Optional[PlanResponse]:
        if not hasattr(self, "saved_plans"):
            self.saved_plans = {}
        return self.saved_plans.get((user_id, plan_date))

# Singleton instance & class aliases
store = InMemoryStore()
InMemoryRepository = InMemoryStore
