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
  UNSPECIFIED: "UNSPECIFIED",
} as const;
export type Priority = (typeof Priority)[keyof typeof Priority];

export type DisplayLanguage = "original" | "en" | "ta";

export interface ProposalItem {
  id: string;
  proposal_id: string;
  temp_id: string;
  item_type: ItemType;
  action?: string | null;
  object?: string | null;
  proposed_title: string;
  description?: string | null;
  original_title?: string | null;
  original_description?: string | null;
  translated_title?: string | null;
  translated_description?: string | null;
  source_expression: string;
  deadline_expression?: string | null;
  normalized_deadline?: string | null;
  estimated_duration_min?: number | null;
  duration_source: string;
  priority?: Priority | null;
  confidence_score: number;
  intent_confidence?: number | null;
  action_confidence?: number | null;
  object_confidence?: number | null;
  deadline_confidence?: number | null;
  uncertainty_flags: string[];
  decision_state: "PENDING" | "APPROVED" | "REJECTED";
  rejection_reason?: string | null;
}

export interface ClarificationQuestion {
  id: string;
  target_item_temp_id?: string;
  related_item_temp_id?: string;
  question_text: string;
  original_question_text?: string;
  suggested_options?: string[];
  original_suggested_options?: string[];
  field_to_update?: string;
}

export interface Proposal {
  id: string;
  user_id: string;
  capture_id?: string | null;
  transcript_text?: string | null;
  original_transcript?: string | null;
  translated_transcript?: string | null;
  display_language: DisplayLanguage | string;
  translation_status?: "ORIGINAL" | "TRANSLATED" | "FALLBACK" | string;
  intent_summary: string;
  original_intent_summary?: string | null;
  translated_intent_summary?: string | null;
  detected_language: string;
  status:
    | "PROCESSING"
    | "PENDING_REVIEW"
    | "APPROVED"
    | "REJECTED"
    | "COMMITTED"
    | "RESOLVED"
    | "FAILED"
    | "EXPIRED"
    | string;
  created_at: string;
  expires_at: string;
  items: ProposalItem[];
  clarifications?: ClarificationQuestion[];
}

export interface CaptureRecord {
  id: string;
  user_id: string;
  input_type: "VOICE" | "TEXT" | "voice" | "text" | string;
  transcript_text: string;
  original_transcript?: string | null;
  translated_transcript?: string | null;
  detected_language: string;
  processing_status: "PROCESSING" | "COMPLETED" | "FAILED" | string;
  lifecycle_status:
    | "PENDING_REVIEW"
    | "APPROVED"
    | "COMMITTED"
    | "REJECTED"
    | "COMPLETED"
    | string;
  created_at: string;
  proposal_ids: string[];
  proposals?: Proposal[];
  proposal_count?: number;
  error_message?: string | null;
}

export interface ProposalItemDecision {
  id: string;
  proposed_title?: string;
  estimated_duration_min?: number | null;
  priority?: Priority | null;
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
  priority?: Priority | null;
  estimated_duration_min?: number | null;
  actual_duration_min?: number | null;
  duration_source?: string | null;
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
  duration_source?: string;
  deadline?: string | null;
  priority?: Priority | string | null;
  scheduling_status?: string;
  explanation?: string | null;
}

export interface UserProfile {
  id: string;
  display_name: string;
  email?: string | null;
  timezone?: string;
  created_at?: string;
  updated_at?: string;
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

