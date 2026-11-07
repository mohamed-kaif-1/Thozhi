"use client";

import React, { useState, useEffect } from "react";
import { Task, Priority } from "@/types";
import {
  listTasks,
  createTask,
  deleteTask as apiDeleteTask,
  completeTask as apiCompleteTask,
  reopenTask as apiReopenTask,
} from "@/lib/api";
import {
  CheckSquare,
  Plus,
  Search,
  Filter,
  LayoutList,
  Kanban,
  Grid,
  Clock,
  Calendar,
  CheckCircle2,
  Circle,
  Trash2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Mock seed tasks if backend store is currently empty
const SEED_TASKS: Task[] = [
  {
    id: "seed-1",
    user_id: "user-1",
    title: "Client Architecture Sync & Prototype Demo",
    description: "Present Gnani Prisma v3 STT pipeline integration & proposal review card workflow to stakeholders.",
    estimated_duration_min: 45,
    priority: Priority.P1,
    deadline: new Date(Date.now() + 4 * 3600 * 1000).toISOString(),
    status: "in_progress",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "seed-2",
    user_id: "user-1",
    title: "Review Math 401 Assignment & Submit Lab Report",
    description: "Verify all calculated derivatives and ensure PDF submission to college portal before deadline.",
    estimated_duration_min: 60,
    priority: Priority.P2,
    deadline: new Date(Date.now() + 12 * 3600 * 1000).toISOString(),
    status: "todo",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "seed-3",
    user_id: "user-1",
    title: "Configure Supabase RLS Policies for Sovereign Audit Trail",
    description: "Verify that row level security policies block tenant leaks on proposals and personal memory table.",
    estimated_duration_min: 90,
    priority: Priority.P1,
    deadline: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
    status: "todo",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "seed-4",
    user_id: "user-1",
    title: "Daily Morning Standup & Priority Clarification",
    description: "Align with design team on dark obsidian grid styling and amber proposal card colors.",
    estimated_duration_min: 30,
    priority: Priority.P3,
    status: "completed",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "seed-5",
    user_id: "user-1",
    title: "Clean Temporary Audio Buffers & Transient Memory",
    description: "Ensure zero raw audio retention guarantee by flushing system cache.",
    estimated_duration_min: 20,
    priority: Priority.P3,
    status: "completed",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

type ViewMode = "list" | "kanban" | "matrix";
type StatusFilter = "all" | "today" | "todo" | "in_progress" | "completed";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPriority, setSelectedPriority] = useState<string>("all");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // New task form state
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newDuration, setNewDuration] = useState(45);
  const [newPriority, setNewPriority] = useState<Priority>(Priority.P2);
  const [newDeadline, setNewDeadline] = useState("");

  const loadTasks = async () => {
    try {
      const fetched = await listTasks();
      if (fetched && fetched.length > 0) {
        setTasks(fetched);
      } else {
        setTasks(SEED_TASKS);
      }
    } catch {
      setTasks(SEED_TASKS);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const toggleTaskStatus = async (id: string) => {
    const target = tasks.find((t) => t.id === id);
    if (!target) return;
    const isNowCompleted = target.status !== "completed" && target.status !== "COMPLETED";

    setTasks((prev) =>
      prev.map((t) => {
        if (t.id === id) {
          return { ...t, status: isNowCompleted ? "completed" : "todo" };
        }
        return t;
      })
    );

    try {
      if (isNowCompleted) {
        await apiCompleteTask(id);
      } else {
        await apiReopenTask(id);
      }
    } catch {
      // optimistic update maintained
    }
  };

  const deleteTask = async (id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
    try {
      await apiDeleteTask(id);
    } catch {
      // ignore
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const created = await createTask({
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        estimated_duration_min: Number(newDuration),
        priority: newPriority,
        deadline: newDeadline ? new Date(newDeadline).toISOString() : undefined,
        scheduled_date: new Date().toISOString().split("T")[0],
      });
      setTasks((prev) => [created, ...prev]);
    } catch {
      const fallback: Task = {
        id: `task-${Date.now()}`,
        user_id: "user-1",
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        estimated_duration_min: Number(newDuration),
        priority: newPriority,
        deadline: newDeadline ? new Date(newDeadline).toISOString() : undefined,
        status: "todo",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setTasks((prev) => [fallback, ...prev]);
    }

    setIsCreateModalOpen(false);
    setNewTitle("");
    setNewDescription("");
    setNewDuration(45);
    setNewPriority(Priority.P2);
    setNewDeadline("");
  };

  // Filter tasks
  const filteredTasks = tasks.filter((task) => {
    if (searchQuery.trim()) {
      const matchesSearch =
        task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.description?.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;
    }

    if (selectedPriority !== "all" && task.priority !== selectedPriority) {
      return false;
    }

    if (statusFilter === "completed") return task.status === "completed";
    if (statusFilter === "todo") return task.status === "todo";
    if (statusFilter === "in_progress") return task.status === "in_progress";
    if (statusFilter === "today") {
      return task.status !== "completed";
    }

    return true;
  });

  const getPriorityBadge = (p: Priority) => {
    switch (p) {
      case Priority.P1:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            P1 Urgent
          </span>
        );
      case Priority.P2:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyber-amber-500/20 text-cyber-amber-300 border border-cyber-amber-500/30">
            P2 Important
          </span>
        );
      case Priority.P3:
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
            P3 Routine
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>My Tasks Workspace</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold">
              {filteredTasks.length} tasks
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Organize, schedule, and track approved commitments. Zero silent additions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn-primary px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Task</span>
          </button>
        </div>
      </div>

      {/* Control Bar: Filters & View Switchers */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 p-4 rounded-xl bg-canvas-card border border-sky-500/20">
        {/* Search & Status Filters */}
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          {/* Search Input */}
          <div className="relative min-w-[200px] flex-1 max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-canvas-subtle border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-400"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center p-1 rounded-lg bg-canvas-subtle border border-slate-700/80 text-xs">
            {(
              [
                { id: "all", label: "All" },
                { id: "today", label: "Today" },
                { id: "todo", label: "To Do" },
                { id: "in_progress", label: "In Progress" },
                { id: "completed", label: "Completed" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={cn(
                  "px-3 py-1 rounded-md font-medium transition",
                  statusFilter === tab.id
                    ? "bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40"
                    : "text-slate-400 hover:text-white"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Priority Dropdown */}
          <div className="flex items-center gap-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-canvas-subtle border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-sky-400"
            >
              <option value="all">All Priorities</option>
              <option value={Priority.P1}>P1 Urgent</option>
              <option value={Priority.P2}>P2 Important</option>
              <option value={Priority.P3}>P3 Routine</option>
            </select>
          </div>
        </div>

        {/* View Mode Toggle Buttons */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-canvas-subtle border border-slate-700/80 self-end lg:self-auto">
          <button
            onClick={() => setViewMode("list")}
            className={cn(
              "p-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition",
              viewMode === "list"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                : "text-slate-400 hover:text-white"
            )}
            title="List View"
          >
            <LayoutList className="w-4 h-4" />
            <span className="hidden sm:inline">List</span>
          </button>

          <button
            onClick={() => setViewMode("kanban")}
            className={cn(
              "p-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition",
              viewMode === "kanban"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                : "text-slate-400 hover:text-white"
            )}
            title="Kanban Board"
          >
            <Kanban className="w-4 h-4" />
            <span className="hidden sm:inline">Kanban</span>
          </button>

          <button
            onClick={() => setViewMode("matrix")}
            className={cn(
              "p-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition",
              viewMode === "matrix"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                : "text-slate-400 hover:text-white"
            )}
            title="Eisenhower Matrix"
          >
            <Grid className="w-4 h-4" />
            <span className="hidden sm:inline">Matrix</span>
          </button>
        </div>
      </div>

      {/* VIEW MODE 1: LIST VIEW */}
      {viewMode === "list" && (
        <div className="space-y-3">
          {filteredTasks.length === 0 ? (
            <div className="surface-card p-12 text-center text-slate-400 space-y-3">
              <CheckSquare className="w-12 h-12 text-slate-600 mx-auto" />
              <p className="text-base font-bold text-slate-300">No tasks match your filters</p>
              <p className="text-xs text-slate-500">
                Capture thoughts via voice or click &apos;New Task&apos; to create one manually.
              </p>
            </div>
          ) : (
            filteredTasks.map((task) => {
              const isDone = task.status === "completed";
              return (
                <div
                  key={task.id}
                  className={cn(
                    "surface-card surface-card-hover p-4 flex items-center justify-between gap-4 transition",
                    isDone && "opacity-60 bg-canvas-card/40 border-slate-800"
                  )}
                >
                  <div className="flex items-center gap-3.5 flex-1 min-w-0">
                    <button
                      onClick={() => toggleTaskStatus(task.id)}
                      className="flex-shrink-0 text-slate-400 hover:text-emerald-400 transition"
                      aria-label="Toggle task status"
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 fill-emerald-950" />
                      ) : (
                        <Circle className="w-5 h-5 hover:text-sky-400" />
                      )}
                    </button>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span
                          className={cn(
                            "text-sm font-semibold text-slate-100 truncate",
                            isDone && "line-through text-slate-500"
                          )}
                        >
                          {task.title}
                        </span>
                        {getPriorityBadge(task.priority)}
                        {task.status === "in_progress" && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                            In Progress
                          </span>
                        )}
                      </div>

                      {task.description && (
                        <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                          {task.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Metadata and Actions */}
                  <div className="flex items-center gap-4 text-xs text-slate-400 flex-shrink-0">
                    <div className="flex items-center gap-1.5 bg-canvas-subtle px-2.5 py-1 rounded-md border border-slate-800">
                      <Clock className="w-3.5 h-3.5 text-sky-400" />
                      <span>{task.estimated_duration_min}m</span>
                    </div>

                    {task.deadline && (
                      <div className="hidden sm:flex items-center gap-1.5 text-cyber-amber-400 bg-cyber-amber-950/30 px-2.5 py-1 rounded-md border border-cyber-amber-500/20">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{new Date(task.deadline).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
                      </div>
                    )}

                    <button
                      onClick={() => deleteTask(task.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition"
                      title="Delete Task"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* VIEW MODE 2: KANBAN BOARD */}
      {viewMode === "kanban" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* TO DO COLUMN */}
          <div className="surface-card p-4 border-sky-500/20 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">To Do</h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-bold">
                {tasks.filter((t) => t.status === "todo").length}
              </span>
            </div>

            <div className="space-y-3 min-h-[300px]">
              {tasks
                .filter((t) => t.status === "todo")
                .map((task) => (
                  <div
                    key={task.id}
                    className="p-3.5 rounded-xl bg-canvas-subtle border border-slate-800 hover:border-sky-500/40 transition space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-slate-200">{task.title}</p>
                      {getPriorityBadge(task.priority)}
                    </div>
                    {task.description && (
                      <p className="text-[11px] text-slate-400 line-clamp-2">{task.description}</p>
                    )}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-sky-400" /> {task.estimated_duration_min}m
                      </span>
                      <button
                        onClick={() =>
                          setTasks((prev) =>
                            prev.map((t) => (t.id === task.id ? { ...t, status: "in_progress" } : t))
                          )
                        }
                        className="text-[11px] text-sky-400 hover:text-sky-300 font-semibold"
                      >
                        Start →
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* IN PROGRESS COLUMN */}
          <div className="surface-card p-4 border-sky-500/20 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400 animate-pulse" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">In Progress</h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-950 text-sky-300 font-bold border border-sky-500/30">
                {tasks.filter((t) => t.status === "in_progress").length}
              </span>
            </div>

            <div className="space-y-3 min-h-[300px]">
              {tasks
                .filter((t) => t.status === "in_progress")
                .map((task) => (
                  <div
                    key={task.id}
                    className="p-3.5 rounded-xl bg-canvas-subtle border border-sky-500/40 shadow-sm shadow-sky-500/10 space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-slate-100">{task.title}</p>
                      {getPriorityBadge(task.priority)}
                    </div>
                    {task.description && (
                      <p className="text-[11px] text-slate-400 line-clamp-2">{task.description}</p>
                    )}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-sky-400" /> {task.estimated_duration_min}m
                      </span>
                      <button
                        onClick={() => toggleTaskStatus(task.id)}
                        className="text-[11px] text-emerald-400 hover:text-emerald-300 font-bold"
                      >
                        Complete ✓
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* COMPLETED COLUMN */}
          <div className="surface-card p-4 border-sky-500/20 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Completed</h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 font-bold border border-emerald-500/30">
                {tasks.filter((t) => t.status === "completed").length}
              </span>
            </div>

            <div className="space-y-3 min-h-[300px]">
              {tasks
                .filter((t) => t.status === "completed")
                .map((task) => (
                  <div
                    key={task.id}
                    className="p-3.5 rounded-xl bg-canvas-subtle/50 border border-slate-800/80 space-y-2 opacity-60"
                  >
                    <p className="text-xs font-semibold text-slate-300 line-through">{task.title}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>Done</span>
                      <button
                        onClick={() => toggleTaskStatus(task.id)}
                        className="text-[11px] text-slate-400 hover:text-white"
                      >
                        Reopen
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 3: EISENHOWER PRIORITY MATRIX */}
      {viewMode === "matrix" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* QUADRANT 1: URGENT & IMPORTANT (P1) */}
          <div className="surface-card p-5 border-rose-500/30 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-rose-500/20">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-md bg-rose-500" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Q1: Urgent & Critical (P1)
                </h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-300 font-mono">
                Do Immediately
              </span>
            </div>
            <div className="space-y-2">
              {tasks
                .filter((t) => t.priority === Priority.P1 && t.status !== "completed")
                .map((t) => (
                  <div
                    key={t.id}
                    className="p-3 rounded-lg bg-canvas-subtle border border-slate-800 flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-slate-200">{t.title}</span>
                    <span className="text-[11px] text-rose-400 font-mono">{t.estimated_duration_min}m</span>
                  </div>
                ))}
            </div>
          </div>

          {/* QUADRANT 2: IMPORTANT & NOT URGENT (P2) */}
          <div className="surface-card p-5 border-cyber-amber-500/30 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-cyber-amber-500/20">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-md bg-cyber-amber-500" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Q2: Strategic Focus (P2)
                </h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-cyber-amber-950 text-cyber-amber-300 font-mono">
                Schedule in Planner
              </span>
            </div>
            <div className="space-y-2">
              {tasks
                .filter((t) => t.priority === Priority.P2 && t.status !== "completed")
                .map((t) => (
                  <div
                    key={t.id}
                    className="p-3 rounded-lg bg-canvas-subtle border border-slate-800 flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-slate-200">{t.title}</span>
                    <span className="text-[11px] text-cyber-amber-400 font-mono">
                      {t.estimated_duration_min}m
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* QUADRANT 3: ROUTINE & DELEGATION (P3) */}
          <div className="surface-card p-5 border-sky-500/30 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-sky-500/20">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-md bg-sky-500" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Q3: Operational & Routine (P3)
                </h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-sky-950 text-sky-300 font-mono">
                Batch Process
              </span>
            </div>
            <div className="space-y-2">
              {tasks
                .filter((t) => t.priority === Priority.P3 && t.status !== "completed")
                .map((t) => (
                  <div
                    key={t.id}
                    className="p-3 rounded-lg bg-canvas-subtle border border-slate-800 flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-slate-200">{t.title}</span>
                    <span className="text-[11px] text-sky-400 font-mono">{t.estimated_duration_min}m</span>
                  </div>
                ))}
            </div>
          </div>

          {/* QUADRANT 4: COMPLETED / ARCHIVED */}
          <div className="surface-card p-5 border-emerald-500/30 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-emerald-500/20">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-md bg-emerald-500" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Archived / Completed
                </h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 font-mono">
                Resolved
              </span>
            </div>
            <div className="space-y-2">
              {tasks
                .filter((t) => t.status === "completed")
                .slice(0, 4)
                .map((t) => (
                  <div
                    key={t.id}
                    className="p-3 rounded-lg bg-canvas-subtle/50 border border-slate-800/80 flex items-center justify-between opacity-60"
                  >
                    <span className="text-xs font-semibold text-slate-300 line-through">{t.title}</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* CREATE TASK MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="surface-card w-full max-w-lg p-6 border-sky-500/30 shadow-2xl relative animate-scaleUp">
            <button
              onClick={() => setIsCreateModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5 text-sky-400" />
              <span>Create New Task</span>
            </h2>

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Task Title *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="E.g. Finalize engineering specification document"
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description / Notes
                </label>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Optional context, links, or dependencies..."
                  rows={3}
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="480"
                    step="5"
                    value={newDuration}
                    onChange={(e) => setNewDuration(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Priority
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as Priority)}
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
                  >
                    <option value={Priority.P1}>P1 Urgent & Critical</option>
                    <option value={Priority.P2}>P2 Important Focus</option>
                    <option value={Priority.P3}>P3 Operational Routine</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Target Deadline (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={newDeadline}
                  onChange={(e) => setNewDeadline(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-bold"
                >
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
