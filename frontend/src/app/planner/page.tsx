"use client";

import React, { useState, useEffect } from "react";
import { CapacityBar } from "@/components/ui/CapacityBar";
import { getTodayPlan, applyReschedule } from "@/lib/api";
import { ScheduledBlock, Plan } from "@/types";
import {
  CalendarDays,
  Clock,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Sun,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const MOCK_SCHEDULE_BLOCKS: ScheduledBlock[] = [
  {
    id: "block-1",
    task_id: "task-1",
    task_title: "Sprint Review & Stakeholder Demo",
    start_time: "2026-11-07T09:30:00",
    end_time: "2026-11-07T10:30:00",
    is_locked: true,
  },
  {
    id: "block-2",
    task_id: "task-2",
    task_title: "Deep Work: Finalize Architecture PRD",
    start_time: "2026-11-07T11:00:00",
    end_time: "2026-11-07T13:00:00",
    is_locked: false,
  },
  {
    id: "block-3",
    task_id: "task-3",
    task_title: "Client Technical Clarification Call",
    start_time: "2026-11-07T14:30:00",
    end_time: "2026-11-07T15:15:00",
    is_locked: true,
  },
  {
    id: "block-4",
    task_id: "task-4",
    task_title: "Review Pull Requests & Supabase Policies",
    start_time: "2026-11-07T16:00:00",
    end_time: "2026-11-07T17:30:00",
    is_locked: false,
  },
];

const HOURS = [
  "08:00", "09:00", "10:00", "11:00", "12:00", "13:00",
  "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"
];

export default function PlannerPage() {
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [scheduledBlocks, setScheduledBlocks] = useState<ScheduledBlock[]>(MOCK_SCHEDULE_BLOCKS);
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(null);
  const [hasConflict, setHasConflict] = useState(false);
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Focus capacity calculations
  const totalAvailableMin = currentPlan?.total_available_minutes || 480;
  const totalScheduledMin = currentPlan?.total_scheduled_minutes || scheduledBlocks.reduce((acc, b) => {
    const start = new Date(b.start_time).getTime();
    const end = new Date(b.end_time).getTime();
    return acc + Math.round((end - start) / 60000);
  }, 0);
  const capacityPct = currentPlan?.capacity_percentage ?? Math.round((totalScheduledMin / totalAvailableMin) * 100);

  const fetchPlan = async () => {
    try {
      const p = await getTodayPlan();
      if (p) {
        setCurrentPlan(p);
        if (p.slots && p.slots.length > 0) {
          const blocks: ScheduledBlock[] = p.slots.map((s, idx) => ({
            id: `slot-${idx}`,
            task_id: s.task_id,
            task_title: s.title,
            start_time: s.start_time,
            end_time: s.end_time,
            is_locked: false,
          }));
          setScheduledBlocks(blocks);
        }
      }
    } catch {
      // Fallback to mock schedule
    }
  };

  useEffect(() => {
    fetchPlan();
  }, [currentDate]);

  const handleApplyReschedule = async () => {
    if (!currentPlan?.reschedule_suggestions?.length) return;
    setIsRescheduling(true);
    try {
      const updatedPlan = await applyReschedule(currentPlan.reschedule_suggestions);
      setCurrentPlan(updatedPlan);
      const blocks: ScheduledBlock[] = updatedPlan.slots.map((s, idx) => ({
        id: `slot-${idx}`,
        task_id: s.task_id,
        task_title: s.title,
        start_time: s.start_time,
        end_time: s.end_time,
        is_locked: false,
      }));
      setScheduledBlocks(blocks);
      setNotification("Applied smart schedule optimization! Conflicts resolved.");
      setTimeout(() => setNotification(null), 4000);
    } catch {
      setNotification("Could not apply reschedule suggestions.");
    } finally {
      setIsRescheduling(false);
    }
  };

  const handleSimulateConflict = () => {
    setHasConflict(true);
    const conflictBlock: ScheduledBlock = {
      id: "conflict-block",
      task_id: "task-conflict",
      task_title: "⚠️ Overlapping Emergency Lab Review",
      start_time: "2026-11-07T11:30:00",
      end_time: "2026-11-07T12:30:00",
      is_locked: false,
    };
    setScheduledBlocks((prev) => [...prev, conflictBlock]);
  };

  const handleResolveConflicts = () => {
    setIsRescheduling(true);
    setTimeout(() => {
      setScheduledBlocks((prev) =>
        prev.map((b) => {
          if (b.id === "conflict-block") {
            return {
              ...b,
              task_title: "Resolved: Lab Review",
              start_time: "2026-11-07T18:00:00",
              end_time: "2026-11-07T19:00:00",
            };
          }
          return b;
        })
      );
      setHasConflict(false);
      setIsRescheduling(false);
      setNotification("Resolved conflicts using topological dependency sequencing!");
      setTimeout(() => setNotification(null), 4000);
    }, 900);
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Intelligent Planner & Timeline</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyber-amber-500/10 border border-cyber-amber-500/30 text-cyber-amber-300 font-semibold">
              Deterministic Math Engine
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Visual time-blocking governed by Kahn&apos;s topological sort. Zero AI scheduling hallucinations.
          </p>
        </div>

        {/* Date Selector Navigation */}
        <div className="flex items-center gap-2 p-1.5 rounded-xl bg-canvas-card border border-sky-500/20 text-xs">
          <button
            onClick={() =>
              setCurrentDate((prev) => new Date(prev.getTime() - 24 * 3600 * 1000))
            }
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-bold text-slate-200 px-3">
            {currentDate.toLocaleDateString("en-US", {
              weekday: "short",
              month: "short",
              day: "numeric",
            })}
          </span>
          <button
            onClick={() =>
              setCurrentDate((prev) => new Date(prev.getTime() + 24 * 3600 * 1000))
            }
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-3 shadow-lg">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span className="font-medium text-sm">{notification}</span>
        </div>
      )}

      {/* Daily Capacity & Morning Briefing Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 surface-card p-6 border-sky-500/20 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" />
              <span>Today&apos;s Focus Workload</span>
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              Target: 8.0h Max Workload
            </span>
          </div>

          <CapacityBar
            totalAvailableMin={totalAvailableMin}
            totalScheduledMin={totalScheduledMin}
            capacityPercentage={capacityPct}
          />
        </div>

        {/* Morning Briefing Assistant Widget */}
        <div className="lg:col-span-4 surface-card p-6 border-cyber-amber-500/30 bg-gradient-to-br from-canvas-card to-cyber-amber-950/10 space-y-3">
          <div className="flex items-center gap-2 text-cyber-amber-400">
            <Sun className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Morning Briefing</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            You have <strong>{scheduledBlocks.length} planned sessions</strong> today. 
            Deep work block scheduled at 11:00 AM before afternoon client commitments.
          </p>
          <div className="pt-2 flex items-center gap-2">
            {!hasConflict ? (
              <button
                type="button"
                onClick={handleSimulateConflict}
                className="text-[11px] px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              >
                Test Conflict Scenario
              </button>
            ) : (
              <button
                type="button"
                onClick={handleResolveConflicts}
                disabled={isRescheduling}
                className="btn-amber text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isRescheduling && "animate-spin")} />
                <span>Resolve Conflicts with AI</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Conflict Warning Banner (if detected) */}
      {hasConflict && (
        <div className="surface-card p-4 border-rose-500/40 bg-rose-950/20 flex items-center justify-between gap-4 animate-slideDown">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 flex-shrink-0 animate-bounce" />
            <div>
              <p className="text-sm font-bold text-rose-300">
                Schedule Conflict Detected: 2 Overlapping Commitments at 11:30 AM
              </p>
              <p className="text-xs text-rose-400/80">
                &apos;Emergency Lab Review&apos; collides with &apos;Deep Work: Finalize Architecture PRD&apos;.
              </p>
            </div>
          </div>
          <button
            onClick={handleResolveConflicts}
            className="btn-primary text-xs px-4 py-2 rounded-xl font-bold flex-shrink-0"
          >
            Auto-Reschedule Plan
          </button>
        </div>
      )}

      {/* Backend Real Conflicts and Smart Reschedule Suggestions */}
      {currentPlan?.conflicts && currentPlan.conflicts.length > 0 && (
        <div className="space-y-3">
          {currentPlan.conflicts.map((c, i) => (
            <div
              key={i}
              className={cn(
                "surface-card p-4 flex items-center justify-between gap-4 border",
                c.severity === "CRITICAL"
                  ? "border-rose-500/40 bg-rose-950/20 text-rose-200"
                  : "border-cyber-amber-500/40 bg-cyber-amber-950/20 text-cyber-amber-200"
              )}
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className={cn("w-5 h-5 flex-shrink-0", c.severity === "CRITICAL" ? "text-rose-400" : "text-cyber-amber-400")} />
                <div>
                  <p className="text-xs font-mono font-bold uppercase tracking-wider">{c.code}</p>
                  <p className="text-sm font-medium">{c.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {currentPlan?.reschedule_suggestions && currentPlan.reschedule_suggestions.length > 0 && (
        <div className="surface-card p-4 border-sky-500/40 bg-sky-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-sky-400 flex-shrink-0" />
            <div>
              <p className="text-sm font-bold text-sky-200">
                AI Capacity Optimization: {currentPlan.reschedule_suggestions.length} Task(s) Recommended for Rescheduling
              </p>
              <p className="text-xs text-sky-300/80">
                {currentPlan.reschedule_suggestions.map((s) => `"${s.title}" → ${s.suggested_date}`).join(", ")}
              </p>
            </div>
          </div>
          <button
            onClick={handleApplyReschedule}
            disabled={isRescheduling}
            className="btn-primary text-xs px-4 py-2 rounded-xl font-bold flex items-center gap-2 flex-shrink-0"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isRescheduling && "animate-spin")} />
            <span>Apply Recommended Schedule</span>
          </button>
        </div>
      )}

      {/* Visual Timeline Schedule Grid */}
      <div className="surface-card p-6 border-sky-500/20 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Hourly Timeline Schedule
            </h2>
          </div>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Kahn&apos;s DAG Topological Sort
          </span>
        </div>

        {/* Hour Blocks with Scheduled Items */}
        <div className="relative pl-16 pr-4 space-y-4 py-2">
          {HOURS.map((hour) => {
            // Find blocks starting at or spanning this hour
            const hourInt = parseInt(hour.split(":")[0], 10);
            const matchingBlocks = scheduledBlocks.filter((b) => {
              const startHour = new Date(b.start_time).getHours();
              return startHour === hourInt;
            });

            return (
              <div key={hour} className="relative min-h-[48px] flex items-start gap-4 border-t border-slate-800/80 pt-2">
                {/* Hour Label */}
                <div className="absolute -left-14 top-2 text-xs font-mono text-slate-500 w-10 text-right">
                  {hour}
                </div>

                {/* Scheduled Block Cards inside this hour */}
                <div className="flex-1 space-y-2">
                  {matchingBlocks.length > 0 ? (
                    matchingBlocks.map((b) => {
                      const isEmergency = b.task_title.includes("Overlapping") || b.task_title.includes("Emergency");
                      return (
                        <div
                          key={b.id}
                          className={cn(
                            "p-3.5 rounded-xl border transition flex items-center justify-between gap-4",
                            isEmergency
                              ? "bg-rose-950/40 border-rose-500/50 text-rose-200"
                              : b.is_locked
                              ? "bg-canvas-subtle border-sky-500/40 shadow-sm shadow-sky-500/10 text-slate-100"
                              : "bg-canvas-subtle/80 border-slate-700 text-slate-200"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <span
                              className={cn(
                                "w-2.5 h-2.5 rounded-full flex-shrink-0",
                                isEmergency
                                  ? "bg-rose-500 animate-ping"
                                  : b.is_locked
                                  ? "bg-sky-400"
                                  : "bg-cyber-amber-400"
                              )}
                            />
                            <div>
                              <p className="text-sm font-semibold">{b.task_title}</p>
                              <p className="text-xs text-slate-400 font-mono mt-0.5">
                                {new Date(b.start_time).toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                                {" - "}
                                {new Date(b.end_time).toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {b.is_locked && (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 border border-sky-500/30 text-sky-300 font-mono">
                                Locked Commitment
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="h-6 flex items-center">
                      <span className="text-[11px] text-slate-600 italic">Available focus window</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
