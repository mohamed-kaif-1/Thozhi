from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, date, timedelta
from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction
from backend.app.schemas.proposal import (
    ProposalResponse,
    ProposalItemResponse,
    ProposalApproveRequest,
    ProposalApproveResponse,
    ProposalItemPatch,
    ProposalClarificationRequest,
)
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

def get_utc_now():
    return datetime.now(timezone.utc)

class InMemoryStore:
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

    # ---------------- PROPOSALS & EXTRACTIONS ----------------
    def create_proposal_from_extraction(
        self,
        user_id: UUID,
        extraction: ExtractionResponse,
        capture_id: Optional[UUID] = None
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
            est_dur = item.estimated_duration_min or 30
            dur_source = item.duration_source or "DEFAULT_HEURISTIC"

            # Stage 6 Contextual Memory: calibrate duration from learned priors
            if dur_source == "DEFAULT_HEURISTIC" and active_priors:
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
                            est_dur = int(est_dur * float(val["baseline_multiplier"]))
                            dur_source = "LEARNED_PRIOR"
                            break

            item_id = uuid4()
            item_dict = {
                "id": item_id,
                "proposal_id": prop_id,
                "temp_id": item.temp_id,
                "item_type": item.item_type,
                "proposed_title": item.proposed_title,
                "description": item.description,
                "source_expression": item.source_expression,
                "deadline_expression": item.deadline_expression,
                "normalized_deadline": datetime.fromisoformat(item.normalized_deadline_iso) if item.normalized_deadline_iso else None,
                "estimated_duration_min": est_dur,
                "duration_source": dur_source,
                "priority": item.priority,
                "confidence_score": item.confidence,
                "uncertainty_flags": item.uncertainty_flags,
                "condition_trigger": item.condition_trigger,
                "decision_state": "PENDING",
                "rejection_reason": None,
                "created_at": now
            }
            self.proposal_items[item_id] = item_dict
            item_responses.append(ProposalItemResponse(**item_dict))

        prop_dict = {
            "id": prop_id,
            "user_id": user_id,
            "capture_id": capture_id,
            "intent_summary": extraction.intent_summary,
            "detected_language": extraction.detected_language,
            "status": "PENDING_REVIEW",
            "created_at": now,
            "expires_at": expires_at,
            "clarifications": extraction.clarifications
        }
        self.proposals[prop_id] = prop_dict

        return ProposalResponse(
            **prop_dict,
            items=item_responses
        )

    def get_proposal(self, proposal_id: UUID) -> Optional[ProposalResponse]:
        prop = self.proposals.get(proposal_id)
        if not prop:
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

    def update_proposal_item(
        self,
        proposal_id: UUID,
        item_id: UUID,
        patch: ProposalItemPatch
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
        request: ProposalClarificationRequest
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

    def approve_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        request: ProposalApproveRequest
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
                new_task = {
                    "id": task_id,
                    "user_id": user_id,
                    "title": decision.proposed_title or item["proposed_title"],
                    "description": item["description"],
                    "priority": decision.priority or item["priority"],
                    "estimated_duration_min": decision.estimated_duration_min or item["estimated_duration_min"],
                    "actual_duration_min": None,
                    "deadline": datetime.fromisoformat(decision.normalized_deadline_iso) if decision.normalized_deadline_iso else item["normalized_deadline"],
                    "scheduled_date": date.fromisoformat(decision.scheduled_date) if decision.scheduled_date else date.today(),
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

        prop["status"] = "RESOLVED"

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
    def create_task(self, user_id: UUID, task_create: TaskCreate) -> TaskResponse:
        now = get_utc_now()
        target_sched_date = task_create.scheduled_date or now.date()
        
        # Duplicate prevention check
        norm_title = task_create.title.strip().lower()
        for t in self.tasks.values():
            if t["user_id"] == user_id and t["status"] != "COMPLETED":
                if t["title"].strip().lower() == norm_title and t["scheduled_date"] == target_sched_date:
                    raise DuplicateTaskException(title=task_create.title, scheduled_date=str(target_sched_date))
                    
        task_id = uuid4()
        task_dict = {
            "id": task_id,
            "user_id": user_id,
            "title": task_create.title.strip(),
            "description": task_create.description,
            "priority": task_create.priority,
            "estimated_duration_min": task_create.estimated_duration_min,
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

    def list_tasks(self, user_id: UUID, target_date: Optional[date] = None) -> List[TaskResponse]:
        result = []
        for t in self.tasks.values():
            if t["user_id"] == user_id:
                if target_date is None or t["scheduled_date"] == target_date:
                    deps = [
                        d["depends_on_task_id"]
                        for d in self.task_dependencies
                        if d["task_id"] == t["id"]
                    ]
                    result.append(TaskResponse(**t, dependencies=deps))
        return result

    def delete_task(self, task_id: UUID) -> bool:
        if task_id not in self.tasks:
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

    def complete_task(self, task_id: UUID, actual_duration_min: Optional[int] = None) -> TaskResponse:
        task = self.tasks.get(task_id)
        if not task:
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

    def reopen_task(self, task_id: UUID) -> TaskResponse:
        task = self.tasks.get(task_id)
        if not task:
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

    def add_task_dependency(self, task_id: UUID, depends_on_task_id: UUID) -> dict:
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
            "task_id": task_id,
            "depends_on_task_id": depends_on_task_id
        }
        self.task_dependencies.append(dep_record)
        return dep_record

    def delete_task_dependency(self, task_id: UUID, depends_on_task_id: UUID) -> bool:
        initial_len = len(self.task_dependencies)
        self.task_dependencies = [
            d for d in self.task_dependencies
            if not (d["task_id"] == task_id and d["depends_on_task_id"] == depends_on_task_id)
        ]
        return len(self.task_dependencies) < initial_len

    # ---------------- PLANNING & AVAILABILITY ----------------
    def get_user_windows(self, user_id: UUID) -> List[AvailabilityWindow]:
        if user_id in self.availability_windows:
            return self.availability_windows[user_id]
        from datetime import time

        # Stage 6: Check if user configured working hours preference in personal memory
        for p in self.memory_preferences.values():
            if p["user_id"] == user_id and p["is_active"] and p["preference_key"] == "user_working_hours":
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

    def get_user_busy_events(self, user_id: UUID, target_date: date) -> List[BusyEvent]:
        events = list(self.busy_events.get(user_id, []))
        from datetime import time
        # Stage 6: Automatically respect active blocking memory preferences (e.g. protected lunch break)
        for p in self.memory_preferences.values():
            if p["user_id"] == user_id and p["is_active"] and p.get("preference_value", {}).get("blocking"):
                val = p["preference_value"]
                start_str = val.get("start")
                end_str = val.get("end")
                if start_str and end_str:
                    try:
                        s_h, s_m = map(int, str(start_str).split(":"))
                        e_h, e_m = map(int, str(end_str).split(":"))
                        b_start = datetime.combine(target_date, time(s_h, s_m))
                        b_end = datetime.combine(target_date, time(e_h, e_m))
                        title = p.get("description") or p["preference_key"]
                        if not any(e.title == title for e in events):
                            events.append(
                                BusyEvent(
                                    id=p["id"],
                                    user_id=user_id,
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
        user_id: UUID,
        category: Optional[MemoryCategoryEnum] = None,
        active_only: bool = False
    ) -> List[MemoryPreferenceResponse]:
        results = []
        for p in self.memory_preferences.values():
            if p["user_id"] == user_id:
                if active_only and not p["is_active"]:
                    continue
                if category and p["category"] != category:
                    continue
                results.append(MemoryPreferenceResponse(**p))
        return results

    def get_memory_preference(self, user_id: UUID, pref_id: UUID) -> MemoryPreferenceResponse:
        p = self.memory_preferences.get(pref_id)
        if not p or p["user_id"] != user_id:
            raise ResourceNotFoundException(
                detail=f"Preference with ID {pref_id} not found",
                resource_type="memory_preference",
                resource_id=str(pref_id)
            )
        return MemoryPreferenceResponse(**p)

    def set_memory_preference(
        self,
        user_id: UUID,
        create_req: MemoryPreferenceCreate
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
        patch: MemoryPreferencePatch
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

    def delete_memory_preference(self, user_id: UUID, identifier: str) -> bool:
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

    def toggle_memory_preference(self, user_id: UUID, pref_id: UUID) -> MemoryPreferenceResponse:
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

    def analyze_duration_priors(self, user_id: UUID) -> List[DurationPriorSuggestion]:
        completed = [
            t for t in self.tasks.values()
            if t["user_id"] == user_id and t["status"] == "COMPLETED" and t.get("actual_duration_min")
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

    def export_user_data(self, user_id: UUID) -> UserDataExportResponse:
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

    def purge_user_data(self, user_id: UUID) -> DataPurgeResponse:
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

# Singleton instance
store = InMemoryStore()
