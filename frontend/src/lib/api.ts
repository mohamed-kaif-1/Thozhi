import { Proposal, ProposalApproveRequest, ProposalItemDecision, Plan, Task, RescheduleSuggestion } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApprovalResponse {
  proposal_id: string;
  approved_tasks_count: number;
  rejected_items_count: number;
  created_task_ids: string[];
  message: string;
}

export interface MemoryPreference {
  id: string;
  user_id: string;
  category: string;
  preference_key: string;
  preference_value: Record<string, unknown> | null;
  description?: string;
  confidence_score?: number;
  consent_granted?: boolean;
  consent_level?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DurationPrior {
  task_pattern: string;
  suggested_duration_min: number;
  historical_samples: number;
  confidence: number;
  rationale: string;
}

export async function captureText(text: string): Promise<Proposal> {
  const res = await fetch(`${API_BASE}/captures/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, user_timezone: "Asia/Kolkata" }),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: "Failed to parse text" }))) as { detail?: string };
    throw new Error(err.detail || "Capture failed");
  }
  return res.json();
}

export async function captureAudio(audioBlob: Blob): Promise<Proposal> {
  const formData = new FormData();
  const ext = audioBlob.type.includes("mp4")
    ? "mp4"
    : audioBlob.type.includes("webm")
    ? "webm"
    : audioBlob.type.includes("ogg")
    ? "ogg"
    : "wav";
  formData.append("file", audioBlob, `recording.${ext}`);
  formData.append("user_timezone", "Asia/Kolkata");

  const res = await fetch(`${API_BASE}/captures/audio`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: "Audio processing failed" }))) as { detail?: string };
    throw new Error(err.detail || "Audio capture failed");
  }
  return res.json();
}

export async function submitProposalApproval(
  proposalId: string,
  decisions: ProposalItemDecision[]
): Promise<ApprovalResponse> {
  const payload: ProposalApproveRequest = {
    idempotency_key: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `idemp_${Date.now()}`,
    items: decisions,
  };

  const res = await fetch(`${API_BASE}/proposals/${proposalId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: "Approval submission failed" }))) as { detail?: string };
    throw new Error(err.detail || "Approval failed");
  }
  return res.json();
}

export async function getTodayPlan(): Promise<Plan> {
  const res = await fetch(`${API_BASE}/plans/today`);
  if (!res.ok) {
    throw new Error("Failed to load today's plan");
  }
  return res.json();
}

export async function listTasks(targetDate?: string): Promise<Task[]> {
  const url = targetDate ? `${API_BASE}/tasks?target_date=${targetDate}` : `${API_BASE}/tasks`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to load tasks");
  }
  return res.json();
}

export async function completeTask(taskId: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/complete`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to complete task");
  }
  return res.json();
}

export async function reopenTask(taskId: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/reopen`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to reopen task");
  }
  return res.json();
}

export async function deleteTask(taskId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to delete task");
  }
}

export async function createTask(taskData: Partial<Task>): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taskData),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: "Failed to create task" }))) as { detail?: string };
    throw new Error(err.detail || "Task creation failed");
  }
  return res.json();
}

export async function applyReschedule(reschedules: RescheduleSuggestion[]): Promise<{ message: string; applied_count: number }> {
  const res = await fetch(`${API_BASE}/plans/reschedule/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reschedules }),
  });
  if (!res.ok) {
    throw new Error("Failed to apply reschedule");
  }
  return res.json();
}

export async function listMemoryPreferences(): Promise<MemoryPreference[]> {
  const res = await fetch(`${API_BASE}/memory/preferences`);
  if (!res.ok) {
    throw new Error("Failed to load memory preferences");
  }
  return res.json();
}

export async function createMemoryPreference(pref: Partial<MemoryPreference>): Promise<MemoryPreference> {
  const res = await fetch(`${API_BASE}/memory/preferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pref),
  });
  if (!res.ok) {
    throw new Error("Failed to create memory preference");
  }
  return res.json();
}

export async function toggleMemoryPreference(prefId: string, isActive?: boolean): Promise<MemoryPreference> {
  const endpoint = `${API_BASE}/memory/preferences/${prefId}/toggle`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: isActive !== undefined ? JSON.stringify({ is_active: isActive }) : undefined,
  });
  if (!res.ok) {
    // fallback to PATCH if toggle endpoint returns 404/405
    const patchRes = await fetch(`${API_BASE}/memory/preferences/${prefId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: isActive ?? false }),
    });
    if (!patchRes.ok) throw new Error("Failed to toggle preference");
    return patchRes.json();
  }
  return res.json();
}

export async function deleteMemoryPreference(prefId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/memory/preferences/${prefId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to delete preference");
  }
}

export async function getDurationPriorSuggestions(): Promise<DurationPrior[]> {
  const res = await fetch(`${API_BASE}/memory/duration-priors/suggestions`);
  if (!res.ok) {
    throw new Error("Failed to load duration suggestions");
  }
  return res.json();
}

export async function exportPersonalData(): Promise<Blob> {
  const res = await fetch(`${API_BASE}/memory/export`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to export personal data");
  }
  return res.blob();
}

export async function purgeAllPersonalData(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/memory/purge`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to purge personal data");
  }
  return res.json();
}
