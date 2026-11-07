export type ItemType =
  | "TASK"
  | "COMMITMENT"
  | "IDEA"
  | "WISH"
  | "CONDITIONAL_INTENTION"
  | "QUESTION"
  | "REMINDER"
  | "COMPLETED"
  | "CANCELLED"
  | "INFORMATIONAL";

export const Priority = {
  P1: "P1_CRITICAL",
  P2: "P2_MEDIUM",
  P3: "P3_LOW",
  BACKBURNER: "BACKBURNER",
} as const;
export type Priority = (typeof Priority)[keyof typeof Priority];

export interface ProposalItem {
  id: string;
  proposal_id: string;
  temp_id: string;
  item_type: ItemType;
  proposed_title: string;
  description?: string | null;
  source_expression: string;
  deadline_expression?: string | null;
  normalized_deadline?: string | null;
  estimated_duration_min: number;
  duration_source: string;
  priority: Priority;
  confidence_score: number;
  uncertainty_flags: string[];
  decision_state: "PENDING" | "APPROVED" | "REJECTED";
  rejection_reason?: string | null;
}

export interface Proposal {
  id: string;
  user_id: string;
  capture_id?: string | null;
  intent_summary: string;
  detected_language: string;
  status: "PENDING_REVIEW" | "RESOLVED" | "EXPIRED";
  created_at: string;
  expires_at: string;
  items: ProposalItem[];
}

export interface ProposalItemDecision {
  id: string;
  proposed_title?: string;
  estimated_duration_min?: number;
  priority?: Priority;
  normalized_deadline_iso?: string;
  scheduled_date?: string;
  is_approved: boolean;
  rejection_reason?: string;
}

export interface ProposalApproveRequest {
  idempotency_key: string;
  items: ProposalItemDecision[];
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  priority: Priority;
  estimated_duration_min: number;
  actual_duration_min?: number | null;
  deadline?: string | null;
  scheduled_date?: string | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  status:
    | "PENDING"
    | "IN_PROGRESS"
    | "COMPLETED"
    | "CANCELLED"
    | "todo"
    | "in_progress"
    | "completed";
  origin_proposal_item_id?: string | null;
  source_language?: string | null;
  dependencies?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ScheduleSlot {
  task_id: string;
  title: string;
  start_time: string;
  end_time: string;
  duration_min: number;
}

export interface ScheduledBlock {
  id: string;
  task_id: string;
  task_title: string;
  start_time: string;
  end_time: string;
  is_locked?: boolean;
}

export interface ConflictWarning {
  code: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  message: string;
  task_ids: string[];
}

export interface RescheduleSuggestion {
  task_id: string;
  title: string;
  current_date: string;
  suggested_date: string;
  reason: string;
}

export interface Plan {
  id?: string | null;
  plan_date: string;
  status: string;
  total_available_minutes: number;
  total_scheduled_minutes: number;
  capacity_percentage: number;
  summary_explanation?: string;
  slots: ScheduleSlot[];
  conflicts: ConflictWarning[];
  unassigned_task_ids: string[];
  reschedule_suggestions?: RescheduleSuggestion[];
}

