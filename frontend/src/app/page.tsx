"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { VoiceAgentOrb, CaptureLanguage } from "@/components/capture/VoiceAgentOrb";
import { ProposalReviewCard } from "@/components/proposal/ProposalReviewCard";
import { CapacityBar } from "@/components/ui/CapacityBar";
import { useProposalStore } from "@/store/proposalStore";
import {
  captureText,
  captureAudio,
  getTodayPlan,
  listTasks,
  completeTask,
  reopenTask,
} from "@/lib/api";
import { Task, Plan } from "@/types";
import {
  Sparkles,
  Send,
  CheckCircle2,
  Circle,
  Calendar,
  ArrowRight,
  Bot,
  AlertCircle,
  Play,
  Clock,
  ChevronRight,
  CalendarDays,
} from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { useUserProfile } from "@/lib/useUserProfile";
import { cn } from "@/lib/utils";

export default function Home() {
  const { displayName } = useUserProfile();
  const [inputText, setInputText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());
  const [selectedDayIdx, setSelectedDayIdx] = useState(0); // Today is 0

  const {
    activeProposal,
    setProposal,
    commitActiveProposal,
    rejectActiveProposal,
    loadInitialQueue,
  } = useProposalStore();

  const loadData = async () => {
    try {
      const [fetchedTasks, fetchedPlan] = await Promise.all([
        listTasks(),
        getTodayPlan().catch(() => null),
      ]);
      setTasks(fetchedTasks);
      if (fetchedPlan) setPlan(fetchedPlan);
    } catch (e) {
      console.error("Error loading dashboard data:", e);
    }
  };

  useEffect(() => {
    loadData();
    loadInitialQueue();
  }, [loadInitialQueue]);

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    try {
      setIsProcessing(true);
      const proposal = await captureText(inputText);
      setProposal(proposal);
      setInputText("");
      setNotification("Thought captured and added to pending queue.");
      setTimeout(() => setNotification(null), 4000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Capture failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAudioRecorded = async (audioBlob: Blob, language: CaptureLanguage = "tanglish") => {
    if (isProcessing) return;
    try {
      setIsProcessing(true);
      const proposal = await captureAudio(audioBlob, language);
      setProposal(proposal);
      setNotification("Audio transcribed with Gnani AI Prisma v3 and plan extracted.");
      setTimeout(() => setNotification(null), 4000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Audio capture failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCommitProposal = async () => {
    if (!activeProposal) return;
    try {
      setIsProcessing(true);
      const res = await commitActiveProposal();
      if (res) {
        setNotification(res.message);
      }
      await loadData();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Approval submission failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!activeProposal) return;
    try {
      setIsProcessing(true);
      await rejectActiveProposal("Rejected by user from dashboard");
      setNotification("Proposal marked as rejected.");
      setTimeout(() => setNotification(null), 4000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Rejection failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleTaskCompletion = async (taskId: string) => {
    const isNowCompleted = !completedTaskIds.has(taskId);
    setCompletedTaskIds((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });

    try {
      if (isNowCompleted) {
        await completeTask(taskId);
      } else {
        await reopenTask(taskId);
      }
    } catch {
      // optimistic update maintained
    }
  };

  // Derived progress statistics
  const totalTasksCount = tasks.length;
  const completedCount = completedTaskIds.size;
  const pendingCount = Math.max(0, totalTasksCount - completedCount);
  const progressPercentage =
    totalTasksCount > 0 ? Math.round((completedCount / totalTasksCount) * 100) : 65;

  // Identify Today's Focus task (Highest priority pending task)
  const focusTask = useMemo(() => {
    const pendingTasks = tasks.filter((t) => !completedTaskIds.has(t.id));
    const p1 = pendingTasks.find((t) => t.priority === "P1_CRITICAL");
    if (p1) return p1;
    const p2 = pendingTasks.find((t) => t.priority === "P2_MEDIUM");
    if (p2) return p2;
    return pendingTasks[0] || null;
  }, [tasks, completedTaskIds]);

  // Identify Next Up task (second pending task)
  const nextUpTask = useMemo(() => {
    const remaining = tasks.filter(
      (t) => !completedTaskIds.has(t.id) && t.id !== focusTask?.id
    );
    return remaining[0] || null;
  }, [tasks, completedTaskIds, focusTask]);

  // Generate 7-day weekly calendar window (Monday through Sunday)
  const weekDays = useMemo(() => {
    const now = new Date();
    const currentDay = now.getDay(); // 0 is Sunday
    const distanceToMonday = (currentDay + 6) % 7;
    const monday = new Date(now);
    monday.setDate(now.getDate() - distanceToMonday);

    return Array.from({ length: 7 }).map((_, i) => {
      const d = new Date(monday);
      d.setDate(monday.getDate() + i);
      const isToday = d.toDateString() === now.toDateString();
      return {
        date: d,
        dayName: d.toLocaleDateString("en-US", { weekday: "narrow" }), // M, T, W...
        dayShort: d.toLocaleDateString("en-US", { weekday: "short" }), // Mon, Tue...
        dayNum: d.getDate(),
        isToday,
      };
    });
  }, []);

  const todayDateFormatted = useMemo(() => {
    return new Date().toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
  }, []);

  return (
    <div className="space-y-8 pb-12 transition-colors duration-200">
      {/* 1. Header & Greeting — Apple/Samsung Typographic Minimalism */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-sky-500/15 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-sky-500/10 dark:bg-sky-500/15 border border-sky-500/30 text-sky-600 dark:text-sky-400">
              வணக்கம் · {displayName.trim().split(" ")[0]}
            </span>
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              {todayDateFormatted}
            </span>
          </div>
          <h1 className="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
            Today.
          </h1>
          <p className="text-sm md:text-base text-slate-500 dark:text-slate-400 mt-1 font-medium">
            Your day, your direction.
          </p>
        </div>

        {/* Quick Progress Metrics */}
        <div className="flex items-center gap-3">
          <div className="surface-card px-4 py-2 text-center border-slate-200/80 dark:border-sky-500/20">
            <span className="block text-xl font-black text-sky-600 dark:text-sky-400">
              {totalTasksCount}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
              Total
            </span>
          </div>
          <div className="surface-card px-4 py-2 text-center border-emerald-500/20">
            <span className="block text-xl font-black text-emerald-600 dark:text-emerald-400">
              {completedCount}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
              Done
            </span>
          </div>
          <div className="surface-card px-4 py-2 text-center border-amber-500/20">
            <span className="block text-xl font-black text-amber-600 dark:text-amber-400">
              {pendingCount}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
              Pending
            </span>
          </div>
        </div>
      </div>

      {/* Notifications / Error Toasts */}
      {notification && (
        <div className="p-4 rounded-xl bg-sky-500/15 border border-sky-500/40 text-sky-700 dark:text-sky-200 flex items-center gap-2.5 font-bold shadow-lg shadow-sky-500/10 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-sky-500 dark:text-sky-400 flex-shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-700 dark:text-rose-200 flex items-center gap-2.5 font-bold shadow-lg shadow-rose-500/10 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-500 dark:text-rose-400 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 2. Today's Focus Card & Weekly Calendar Strip (Reference Layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Today's Focus Card (Matches the uploaded reference screenshot) */}
        <div className="lg:col-span-7 surface-card p-6 md:p-7 flex flex-col justify-between border-slate-200/90 dark:border-sky-500/20 shadow-xl relative overflow-hidden group">
          {/* Subtle ambient light gradient backdrop */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-sky-400/10 dark:bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-black tracking-widest uppercase text-slate-400 dark:text-slate-400">
                TODAY&apos;S FOCUS
              </span>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/25">
                Priority Flow
              </span>
            </div>

            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {focusTask ? focusTask.title : "Complete your priorities"}
              </h2>
              <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
                {focusTask
                  ? `${focusTask.estimated_duration_min} minutes allocated • ${focusTask.priority}`
                  : "All key tasks are in flight. Capture new thoughts below or start your scheduled block."}
              </p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            {/* Daily Progress Bar */}
            <div className="space-y-1.5">
              <div className="w-full h-3 bg-slate-200/80 dark:bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-300/50 dark:border-slate-700/50">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-500 via-sky-400 to-cyan-300 transition-all duration-500 shadow-sm"
                  style={{ width: `${Math.min(100, Math.max(5, progressPercentage))}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 pt-0.5">
                <span>Daily progress · {progressPercentage}%</span>
                <span>{completedCount} of {totalTasksCount} completed</span>
              </div>
            </div>

            {/* Start Task Action */}
            {focusTask && (
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => toggleTaskCompletion(focusTask.id)}
                  className="px-5 py-2.5 rounded-xl btn-primary text-xs font-bold flex items-center gap-2 shadow-md hover:scale-[1.02] active:scale-95 transition"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Focus Task</span>
                </button>
                <Link
                  href="/planner"
                  className="px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700/80 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-200 text-xs font-bold transition flex items-center gap-1.5"
                >
                  <span>Open Planner</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Weekly Calendar & Next Up Column */}
        <div className="lg:col-span-5 flex flex-col justify-between gap-6">
          {/* Weekly Calendar Strip */}
          <div className="surface-card p-5 border-slate-200/90 dark:border-sky-500/20 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CalendarDays className="w-4 h-4 text-sky-500 dark:text-sky-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Weekly Schedule
                </h3>
              </div>
              <Link
                href="/calendar"
                className="text-[11px] font-bold text-sky-600 dark:text-sky-400 hover:underline flex items-center gap-1"
              >
                <span>Full View</span>
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>

            {/* 7-Day Horizontal Strip */}
            <div className="grid grid-cols-7 gap-2 text-center">
              {weekDays.map((d, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedDayIdx(idx)}
                  className={cn(
                    "py-2 px-1 rounded-xl flex flex-col items-center transition-all",
                    d.isToday
                      ? "bg-sky-500 text-white font-bold shadow-md shadow-sky-500/30 scale-105"
                      : selectedDayIdx === idx
                      ? "bg-sky-500/15 border border-sky-500/40 text-sky-600 dark:text-sky-300 font-semibold"
                      : "bg-slate-100/80 dark:bg-slate-800/50 hover:bg-slate-200/80 dark:hover:bg-slate-700/50 text-slate-600 dark:text-slate-400"
                  )}
                >
                  <span className="text-[10px] uppercase font-bold tracking-tight opacity-75">
                    {d.dayName}
                  </span>
                  <span className="text-sm font-extrabold mt-0.5">{d.dayNum}</span>
                  {d.isToday && (
                    <span className="w-1 h-1 rounded-full bg-white mt-1" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Next Up Card */}
          <div className="surface-card p-5 border-slate-200/90 dark:border-sky-500/20 shadow-xl flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                  NEXT UP
                </span>
                {nextUpTask && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/25">
                    {nextUpTask.priority}
                  </span>
                )}
              </div>

              {nextUpTask ? (
                <div className="space-y-1">
                  <h4 className="text-base font-bold text-slate-900 dark:text-white line-clamp-1">
                    {nextUpTask.title}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-sky-500" />
                    <span>Est. {nextUpTask.estimated_duration_min} mins</span>
                  </p>
                </div>
              ) : (
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300">
                    No immediate upcoming task
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Your immediate schedule is clear. Speak to THOZHI below to schedule new priorities.
                  </p>
                </div>
              )}
            </div>

            {nextUpTask && (
              <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => toggleTaskCompletion(nextUpTask.id)}
                  className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Mark Complete</span>
                </button>
                <Link
                  href="/tasks"
                  className="text-xs font-bold text-sky-600 dark:text-sky-400 hover:underline flex items-center gap-1"
                >
                  <span>View in Tasks</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. Daily Focus Capacity Bar */}
      <section>
        <CapacityBar
          totalAvailableMin={plan?.total_available_minutes || 480}
          totalScheduledMin={plan?.total_scheduled_minutes || 0}
          capacityPercentage={plan?.capacity_percentage || 0}
        />
      </section>

      {/* 4. Human-in-the-Loop Proposal Review Card (The AI proposes. The user decides.) */}
      {activeProposal && (
        <section className="animate-fade-in">
          <ProposalReviewCard
            onCommit={handleCommitProposal}
            onReject={handleRejectProposal}
            isSubmitting={isProcessing}
          />
        </section>
      )}

      {/* 5. AI Voice Agent — Priority Interactive Studio */}
      <section
        id="capture"
        className="surface-card p-6 md:p-8 border-slate-200/90 dark:border-sky-500/25 shadow-2xl relative overflow-hidden space-y-6"
      >
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sky-500/15 border border-sky-500/40 flex items-center justify-center text-sky-600 dark:text-sky-400 shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                AI Voice Interaction Studio
              </h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Spoken brain dump • Multilingual Tamil, Tanglish & English • Automated Action Extraction
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-xs font-bold text-sky-600 dark:text-sky-400">
            <span className="w-2 h-2 rounded-full bg-sky-500 animate-pulse" />
            <span>Primary ASR: Gnani AI Prisma v3</span>
          </div>
        </div>

        {/* Central Voice Agent Experience & Text Input */}
        <div className="flex flex-col lg:flex-row items-center justify-around gap-8 pt-4 pb-2">
          {/* Expressive AI Voice Agent Orb */}
          <div className="flex flex-col items-center w-full lg:w-1/2">
            <VoiceAgentOrb
              onAudioRecorded={handleAudioRecorded}
              isProcessing={isProcessing}
              variant="hero"
            />
          </div>

          <div className="hidden lg:block w-px h-64 bg-slate-200 dark:bg-slate-800" />

          {/* Fallback Text Capture */}
          <form onSubmit={handleTextSubmit} className="w-full lg:w-5/12 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
              <span>Or type thoughts directly:</span>
              <span className="text-[11px] text-slate-400">Press Return to extract</span>
            </div>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="E.g. Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum..."
              rows={4}
              className="w-full text-sm font-medium p-3.5 rounded-xl border border-slate-300 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-950/80 focus:border-sky-500 dark:focus:border-sky-400 focus:outline-none text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputText.trim()}
              className="w-full py-2.5 rounded-xl btn-primary flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider disabled:opacity-50 shadow-md"
            >
              <Send className="w-4 h-4" />
              <span>Extract Plan Proposals</span>
            </button>
          </form>
        </div>
      </section>

      {/* 6. AI Planning Recommendations Card */}
      <section className="surface-card p-5 border-amber-500/25 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/40 flex items-center justify-center text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>AI Planning Recommendation</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-700 dark:text-amber-300 font-bold">
                Active Suggestion
              </span>
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 font-medium">
              You have an open focus block this afternoon. Would you like to schedule your high-priority commitments into deterministic hourly slots?
            </p>
          </div>
        </div>
        <Link
          href="/planner"
          className="px-4 py-2 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber-700 dark:text-amber-300 text-xs font-bold flex items-center gap-1.5 flex-shrink-0 transition shadow-sm"
        >
          <span>Open Planner</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </section>

      {/* 7. Confirmed Schedule & Tasks */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-sky-500 dark:text-sky-400" />
            <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
              Today&apos;s Confirmed Tasks & Schedule
            </h2>
          </div>
          <Link
            href="/tasks"
            className="text-xs font-bold text-sky-600 dark:text-sky-400 hover:text-sky-500 flex items-center gap-1 transition"
          >
            <span>View All ({tasks.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {tasks.length === 0 ? (
          <div className="p-8 text-center surface-card border-slate-200/80 dark:border-slate-800 rounded-2xl space-y-2">
            <BrandLogo variant="icon" className="w-14 h-14 mx-auto opacity-75 mb-1" alt="THOZHI Mascot" />
            <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
              No confirmed tasks for today yet.
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto font-medium">
              Speak or enter thoughts in the AI Voice Interaction Studio above. Once you review and approve the proposal, your tasks will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => {
              const isDone = completedTaskIds.has(task.id);

              return (
                <div
                  key={task.id}
                  onClick={() => toggleTaskCompletion(task.id)}
                  className="surface-card surface-card-hover p-4 border-slate-200/80 dark:border-sky-500/15 flex items-center justify-between cursor-pointer group shadow-sm"
                >
                  <div className="flex items-center gap-3.5">
                    <button
                      type="button"
                      aria-label={isDone ? "Mark incomplete" : "Mark complete"}
                      className="text-slate-400 group-hover:text-sky-500 transition"
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400 stroke-[2.5]" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                      )}
                    </button>
                    <div>
                      <h3
                        className={cn(
                          "text-sm font-semibold transition",
                          isDone
                            ? "line-through text-slate-400 dark:text-slate-500"
                            : "text-slate-900 dark:text-white"
                        )}
                      >
                        {task.title}
                      </h3>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-medium">
                        <span className="text-sky-600 dark:text-sky-400 font-semibold">{task.estimated_duration_min} mins</span>
                        <span>•</span>
                        <span className="font-bold text-amber-600 dark:text-amber-400">{task.priority}</span>
                      </div>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                    APPROVED
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
