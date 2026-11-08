from datetime import datetime, date, time, timedelta
from typing import List, Dict, Set, Optional, Tuple
from uuid import UUID
import copy

from backend.app.schemas.plan import ScheduleSlot, ConflictWarning, PlanResponse, BusyEvent, AvailabilityWindow, RescheduleSuggestion
from backend.app.schemas.task import TaskResponse
from backend.app.schemas.intent import PriorityEnum
from backend.app.core.errors import SchedulingCycleException

PRIORITY_WEIGHTS = {
    PriorityEnum.P1_CRITICAL: 1,
    PriorityEnum.P2_MEDIUM: 2,
    PriorityEnum.P3_LOW: 3,
    PriorityEnum.BACKBURNER: 4
}

class PlanningEngine:
    """
    Deterministic DAG topological scheduler with interval capacity math.
    Zero non-deterministic hallucinations in scheduling.
    """

    @staticmethod
    def topological_sort(tasks: List[TaskResponse], dependencies: List[Tuple[UUID, UUID]]) -> List[TaskResponse]:
        """
        Kahn's algorithm for topological sorting of tasks.
        dependencies: list of (prerequisite_id, dependent_id) -> prereq must finish before dependent.
        """
        task_map: Dict[UUID, TaskResponse] = {t.id: t for t in tasks}
        task_ids = set(task_map.keys())

        in_degree: Dict[UUID, int] = {t_id: 0 for t_id in task_ids}
        adj: Dict[UUID, List[UUID]] = {t_id: [] for t_id in task_ids}

        for prereq_id, dep_id in dependencies:
            if prereq_id in task_ids and dep_id in task_ids:
                adj[prereq_id].append(dep_id)
                in_degree[dep_id] += 1

        # Priority queue / sorted list by priority and deadline
        def sort_key(t_id: UUID):
            task = task_map[t_id]
            deadline_val = task.deadline.timestamp() if task.deadline else float('inf')
            priority_val = PRIORITY_WEIGHTS.get(task.priority, 3)
            return (priority_val, deadline_val)

        zero_in_degree = [t_id for t_id, deg in in_degree.items() if deg == 0]
        zero_in_degree.sort(key=sort_key)

        sorted_tasks: List[TaskResponse] = []

        while zero_in_degree:
            curr_id = zero_in_degree.pop(0)
            sorted_tasks.append(task_map[curr_id])

            for neighbor_id in adj[curr_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    zero_in_degree.append(neighbor_id)

            zero_in_degree.sort(key=sort_key)

        if len(sorted_tasks) < len(tasks):
            cycle_tasks = [task_map[t_id].title for t_id, deg in in_degree.items() if deg > 0]
            raise SchedulingCycleException(f"Cyclic dependency detected among tasks: {', '.join(cycle_tasks)}")

        return sorted_tasks

    @staticmethod
    def calculate_free_intervals(
        target_date: date,
        windows: List[AvailabilityWindow],
        busy_events: List[BusyEvent]
    ) -> List[Tuple[datetime, datetime]]:
        """
        Subtracts busy blocks from work availability windows to find contiguous free slots.
        """
        # Convert windows for this day of week into concrete datetime ranges
        day_of_week = target_date.weekday()
        day_windows: List[Tuple[datetime, datetime]] = []

        for w in windows:
            if w.day_of_week == day_of_week:
                start_dt = datetime.combine(target_date, w.start_time)
                end_dt = datetime.combine(target_date, w.end_time)
                if end_dt > start_dt:
                    day_windows.append((start_dt, end_dt))

        if not day_windows:
            # Default window 09:00 to 18:00 if no specific window defined
            start_dt = datetime.combine(target_date, time(9, 0))
            end_dt = datetime.combine(target_date, time(18, 0))
            day_windows.append((start_dt, end_dt))

        # Sort and merge busy events
        blocking_events = [
            (max(e.start_time, day_windows[0][0]), min(e.end_time, day_windows[-1][1]))
            for e in busy_events if e.is_blocking and e.end_time > day_windows[0][0] and e.start_time < day_windows[-1][1]
        ]
        blocking_events.sort(key=lambda x: x[0])

        merged_busy: List[Tuple[datetime, datetime]] = []
        for start, end in blocking_events:
            if not merged_busy:
                merged_busy.append((start, end))
            else:
                last_start, last_end = merged_busy[-1]
                if start <= last_end:
                    merged_busy[-1] = (last_start, max(last_end, end))
                else:
                    merged_busy.append((start, end))

        # Compute free intervals across each window
        free_intervals: List[Tuple[datetime, datetime]] = []
        for win_start, win_end in day_windows:
            curr_start = win_start
            for b_start, b_end in merged_busy:
                if b_end <= curr_start or b_start >= win_end:
                    continue
                if b_start > curr_start:
                    free_intervals.append((curr_start, min(b_start, win_end)))
                curr_start = max(curr_start, b_end)
                if curr_start >= win_end:
                    break
            if curr_start < win_end:
                free_intervals.append((curr_start, win_end))

        return [slot for slot in free_intervals if (slot[1] - slot[0]).total_seconds() >= 300] # min 5 min

    @staticmethod
    def infer_task_duration(task: TaskResponse) -> Tuple[int, str, bool]:
        """
        Determines the task duration and duration source.
        Returns: (duration_min, duration_source, is_estimate)
        - If task.estimated_duration_min is explicit from user: returns (duration, USER_EXPLICIT, False)
        - If unstated, infers a defensible AI estimate based on complexity and keywords:
          * project/raven/build/deploy/architecture -> 180 min (3h) AI_ESTIMATE
          * study/research/assignment/exam/paper -> 120 min (2h) AI_ESTIMATE
          * presentation/report/documentation/lab record -> 90 min (1.5h) AI_ESTIMATE
          * email/slack/quick/ping/message/check -> 15 min AI_ESTIMATE
          * meeting/sync/call/standup -> 30 min AI_ESTIMATE
        - If unstated and no keyword matches: returns (30, UNSPECIFIED, True).
        """
        src = getattr(task, "duration_source", None)
        if task.estimated_duration_min is not None and src in ("USER_EXPLICIT", "LEARNED_PRIOR"):
            return task.estimated_duration_min, src, False

        if task.estimated_duration_min is not None and src == "AI_ESTIMATE":
            return task.estimated_duration_min, "AI_ESTIMATE", True

        title_lower = task.title.lower()
        if any(kw in title_lower for kw in ["project", "raven", "build", "deploy", "architecture", "system", "app"]):
            return 180, "AI_ESTIMATE", True
        elif any(kw in title_lower for kw in ["study", "exam", "coursework", "assignment", "paper", "research", "audit"]):
            return 120, "AI_ESTIMATE", True
        elif any(kw in title_lower for kw in ["presentation", "report", "documentation", "lab record"]):
            return 90, "AI_ESTIMATE", True
        elif any(kw in title_lower for kw in ["email", "slack", "quick", "ping", "message", "check"]):
            return 15, "AI_ESTIMATE", True
        elif any(kw in title_lower for kw in ["meeting", "sync", "call", "standup"]):
            return 30, "AI_ESTIMATE", True
        elif task.estimated_duration_min is not None:
            return task.estimated_duration_min, src or "USER_EXPLICIT", False
        else:
            return 30, "UNSPECIFIED", True

    @classmethod
    def schedule_day(
        cls,
        target_date: date,
        tasks: List[TaskResponse],
        dependencies: List[Tuple[UUID, UUID]],
        windows: List[AvailabilityWindow],
        busy_events: List[BusyEvent]
    ) -> PlanResponse:
        """
        Executes full deterministic scheduling for a given day.
        Respects hard deadlines, user availability, topological dependencies, and explicit durations.
        """
        conflicts: List[ConflictWarning] = []

        # Check for overlapping busy commitments (Case 5)
        for i in range(len(busy_events)):
            for j in range(i + 1, len(busy_events)):
                e1, e2 = busy_events[i], busy_events[j]
                if max(e1.start_time, e2.start_time) < min(e1.end_time, e2.end_time):
                    conflicts.append(
                        ConflictWarning(
                            code="OVERLAPPING_COMMITMENT",
                            severity="CRITICAL",
                            message=f"Overlapping commitments detected: '{e1.title}' ({e1.start_time.strftime('%H:%M')}–{e1.end_time.strftime('%H:%M')}) collides with '{e2.title}' ({e2.start_time.strftime('%H:%M')}–{e2.end_time.strftime('%H:%M')}).",
                            task_ids=[]
                        )
                    )

        sorted_tasks = cls.topological_sort(tasks, dependencies)
        free_slots = cls.calculate_free_intervals(target_date, windows, busy_events)

        total_available_minutes = sum(int((s[1] - s[0]).total_seconds() // 60) for s in free_slots)

        scheduled_slots: List[ScheduleSlot] = []
        unassigned_ids: List[UUID] = []

        task_end_times: Dict[UUID, datetime] = {}

        # Track remaining intervals dynamically: list of [start, end]
        current_intervals = [[s[0], s[1]] for s in free_slots]

        # Build dependency map: task_id -> list of prereqs
        prereq_map: Dict[UUID, List[UUID]] = {t.id: [] for t in tasks}
        for prereq_id, dep_id in dependencies:
            if dep_id in prereq_map:
                prereq_map[dep_id].append(prereq_id)

        for task in sorted_tasks:
            duration_min, dur_source, is_est = cls.infer_task_duration(task)
            duration = timedelta(minutes=duration_min)

            # Check if deadline has already passed on or before target date (Case 7)
            if task.deadline:
                dl_cmp = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                now_cmp = datetime.now()
                is_past = False
                if target_date < date.today() or dl_cmp < datetime.combine(target_date, time.min):
                    is_past = True
                elif target_date == date.today() and dl_cmp <= (now_cmp - timedelta(hours=2)):
                    is_past = True

                if is_past:
                    conflicts.append(
                        ConflictWarning(
                            code="DEADLINE_ALREADY_PASSED",
                            severity="CRITICAL",
                            message=f"Deadline for '{task.title}' ({dl_cmp.strftime('%Y-%m-%d %H:%M')}) has already passed. Please revise deadline to schedule.",
                            task_ids=[task.id]
                        )
                    )
                    unassigned_ids.append(task.id)
                    continue

            # Feasibility check before deadline on target_date (Case 4)
            if task.deadline:
                dl_cmp = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                if dl_cmp.date() == target_date:
                    avail_before_dl = 0
                    for s_start, s_end in free_slots:
                        eff_start = s_start
                        eff_end = min(s_end, dl_cmp)
                        if eff_end > eff_start:
                            avail_before_dl += int((eff_end - eff_start).total_seconds() // 60)

                    if duration_min > avail_before_dl:
                        conflicts.append(
                            ConflictWarning(
                                code="OVERCAPACITY",
                                severity="CRITICAL",
                                message=f"Task '{task.title}' is infeasible on {target_date}: Requires {duration_min} minutes, but only {avail_before_dl} minutes are available before deadline ({dl_cmp.strftime('%H:%M')}). Deficit: {duration_min - avail_before_dl} minutes.",
                                task_ids=[task.id]
                            )
                        )
                        unassigned_ids.append(task.id)
                        continue

            # Earliest start must be after all prereqs finish (Case 6)
            earliest_start = datetime.combine(target_date, time.min)
            for prereq_id in prereq_map[task.id]:
                if prereq_id in task_end_times:
                    earliest_start = max(earliest_start, task_end_times[prereq_id])
                elif any(t.id == prereq_id for t in tasks):
                    # Prerequisite was not scheduled!
                    earliest_start = datetime.max

            placed = False
            for idx, interval in enumerate(current_intervals):
                slot_start, slot_end = interval
                candidate_start = max(slot_start, earliest_start)
                candidate_end = candidate_start + duration

                if candidate_end <= slot_end:
                    # Check deadline constraint
                    dl_exceeded = False
                    if task.deadline:
                        dl_cmp = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                        if dl_cmp.date() == target_date and candidate_end > dl_cmp:
                            dl_exceeded = True

                    # Generate explainable narrative
                    dur_label = f"{duration_min}m"
                    if dur_source == "AI_ESTIMATE":
                        dur_label = f"{duration_min}m AI estimate"
                    elif dur_source == "UNSPECIFIED":
                        dur_label = f"{duration_min}m unconfirmed"

                    dl_note = f" before {task.deadline.strftime('%I:%M %p')}" if task.deadline else ""
                    explanation = f"Scheduled at {candidate_start.strftime('%I:%M %p')} – {candidate_end.strftime('%I:%M %p')} ({dur_label}) in earliest available focus window{dl_note}."

                    sched_status = "SCHEDULED" if not dl_exceeded else "CONFLICT"
                    if dur_source == "UNSPECIFIED":
                        sched_status = "TENTATIVE"

                    scheduled_slots.append(
                        ScheduleSlot(
                            task_id=task.id,
                            title=task.title,
                            start_time=candidate_start,
                            end_time=candidate_end,
                            duration_min=duration_min,
                            duration_source=dur_source,
                            deadline=task.deadline,
                            priority=task.priority,
                            scheduling_status=sched_status,
                            explanation=explanation
                        )
                    )
                    task_end_times[task.id] = candidate_end
                    placed = True

                    if dl_exceeded:
                        conflicts.append(
                            ConflictWarning(
                                code="DEADLINE_EXCEEDED",
                                severity="CRITICAL",
                                message=f"Task '{task.title}' finishes at {candidate_end.strftime('%H:%M')}, which exceeds deadline {dl_cmp.strftime('%H:%M')}.",
                                task_ids=[task.id]
                            )
                        )

                    # Update interval
                    if candidate_start > slot_start and candidate_end < slot_end:
                        current_intervals[idx] = [slot_start, candidate_start]
                        current_intervals.insert(idx + 1, [candidate_end, slot_end])
                    elif candidate_start == slot_start and candidate_end < slot_end:
                        current_intervals[idx] = [candidate_end, slot_end]
                    elif candidate_start > slot_start and candidate_end == slot_end:
                        current_intervals[idx] = [slot_start, candidate_start]
                    else:
                        current_intervals.pop(idx)
                    break

            if not placed:
                unassigned_ids.append(task.id)
                conflicts.append(
                    ConflictWarning(
                        code="OVERCAPACITY",
                        severity="WARNING",
                        message=f"Insufficient free time slot to schedule '{task.title}' ({duration_min}m) on {target_date}.",
                        task_ids=[task.id]
                    )
                )

        total_scheduled_minutes = sum(s.duration_min for s in scheduled_slots)
        capacity_pct = (
            round((total_scheduled_minutes / total_available_minutes) * 100, 1)
            if total_available_minutes > 0 else 100.0
        )

        if capacity_pct > 100.0:
            conflicts.append(
                ConflictWarning(
                    code="CAPACITY_EXCEEDED",
                    severity="CRITICAL",
                    message=f"Scheduled load ({total_scheduled_minutes}m) exceeds available focus capacity ({total_available_minutes}m).",
                    task_ids=unassigned_ids
                )
            )

        # Smart reschedule suggestions for unassigned tasks or deadline conflicts
        reschedule_suggestions: List[RescheduleSuggestion] = []
        next_day = target_date + timedelta(days=1)
        for task in tasks:
            if task.id in unassigned_ids:
                reschedule_suggestions.append(
                    RescheduleSuggestion(
                        task_id=task.id,
                        title=task.title,
                        current_date=target_date,
                        suggested_date=next_day,
                        reason=f"Shifted to {next_day} due to focus capacity deficit on {target_date}."
                    )
                )

        summary_parts = [
            f"Deterministic plan for {target_date}: {len(scheduled_slots)}/{len(tasks)} tasks scheduled ({total_scheduled_minutes}m of {total_available_minutes}m capacity, {capacity_pct}% load)."
        ]
        if conflicts:
            summary_parts.append(f"Identified {len(conflicts)} conflict warning(s) requiring attention.")
        else:
            summary_parts.append("Zero temporal or capacity conflicts detected.")
        if reschedule_suggestions:
            summary_parts.append(f"Proposed {len(reschedule_suggestions)} smart rescheduling alternative(s).")

        return PlanResponse(
            plan_date=target_date,
            status="PROPOSED",
            total_available_minutes=total_available_minutes,
            total_scheduled_minutes=total_scheduled_minutes,
            capacity_percentage=capacity_pct,
            summary_explanation=" ".join(summary_parts),
            slots=scheduled_slots,
            conflicts=conflicts,
            unassigned_task_ids=unassigned_ids,
            reschedule_suggestions=reschedule_suggestions
        )
