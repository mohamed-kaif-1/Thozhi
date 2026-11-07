"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { MicButton } from "@/components/capture/MicButton";
import { ProposalReviewCard } from "@/components/proposal/ProposalReviewCard";
import { CapacityBar } from "@/components/ui/CapacityBar";
import { useProposalStore } from "@/store/proposalStore";
import {
  captureText,
  captureAudio,
  submitProposalApproval,
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
  Clock,
  Calendar,
  ArrowRight,
  Bot
} from "lucide-react";

export default function Home() {
  const [inputText, setInputText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());

  const { activeProposal, setProposal, clearProposal, itemDecisions } = useProposalStore();

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
  }, []);

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    try {
      setIsProcessing(true);
      const proposal = await captureText(inputText);
      setProposal(proposal);
      setInputText("");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      alert(`Capture failed: ${message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAudioRecorded = async (audioBlob: Blob) => {
    try {
      setIsProcessing(true);
      const proposal = await captureAudio(audioBlob);
      setProposal(proposal);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      alert(`Audio capture failed: ${message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCommitProposal = async () => {
    if (!activeProposal) return;
    try {
      setIsProcessing(true);
      const decisions = Object.values(itemDecisions);
      const res = await submitProposalApproval(activeProposal.id, decisions);
      setNotification(res.message);
      clearProposal();
      await loadData();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      alert(`Approval submission failed: ${message}`);
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

  return (
    <div className="space-y-8 pb-12">
      {/* Welcome & Daily Overview Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-sky-500/15 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400">
              வணக்கம் · Good morning
            </span>
            <span className="text-xs text-slate-400">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">
            Ready to plan your day, Karthi?
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Speak or type thoughts in Tamil, Tanglish, or English. The AI proposes. You decide.
          </p>
        </div>

        {/* Quick Stats Badges */}
        <div className="flex items-center gap-3">
          <div className="surface-card px-4 py-2 border border-sky-500/20 text-center">
            <span className="block text-xl font-black text-sky-400">{tasks.length}</span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase">Today Tasks</span>
          </div>
          <div className="surface-card px-4 py-2 border border-emerald-500/20 text-center">
            <span className="block text-xl font-black text-emerald-400">{completedTaskIds.size}</span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase">Completed</span>
          </div>
          <div className="surface-card px-4 py-2 border border-amber-500/20 text-center">
            <span className="block text-xl font-black text-amber-400">
              {tasks.length - completedTaskIds.size}
            </span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase">Pending</span>
          </div>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className="p-4 rounded-xl bg-sky-500/15 border border-sky-500/40 text-sky-200 flex items-center gap-2.5 font-bold shadow-lg shadow-sky-500/10 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-sky-400 flex-shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* Daily Focus Capacity Bar */}
      <section>
        <CapacityBar
          totalAvailableMin={plan?.total_available_minutes || 480}
          totalScheduledMin={plan?.total_scheduled_minutes || 0}
          capacityPercentage={plan?.capacity_percentage || 0}
        />
      </section>

      {/* Human-in-the-Loop Proposal Review Card Deck */}
      {activeProposal && (
        <section className="animate-fade-in">
          <ProposalReviewCard
            onCommit={handleCommitProposal}
            isSubmitting={isProcessing}
          />
        </section>
      )}

      {/* Thought Capture Studio Section */}
      <section id="capture" className="surface-card p-6 border border-sky-500/25 shadow-xl space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Capture Thoughts & Unstructured Intentions
              </h2>
              <span className="text-[11px] text-slate-400">
                Spoken or typed brain dump • Auto-categorized into commitments
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-xs font-bold text-sky-400">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
            <span>Primary ASR: Gnani AI Prisma v3</span>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-8 justify-around pt-2">
          {/* Audio Recorder Button */}
          <div className="flex flex-col items-center">
            <MicButton
              onAudioRecorded={handleAudioRecorded}
              isProcessing={isProcessing}
            />
          </div>

          <div className="hidden md:block w-px h-36 bg-slate-800" />

          {/* Text Input Fallback */}
          <form onSubmit={handleTextSubmit} className="w-full md:w-1/2 space-y-3">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="E.g. Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum..."
              rows={3}
              className="w-full text-sm font-medium p-3.5 rounded-xl border border-slate-700/80 bg-slate-950/80 focus:border-sky-400 focus:outline-none text-white placeholder:text-slate-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputText.trim()}
              className="w-full py-2.5 rounded-xl btn-primary flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>Extract Plan Proposals</span>
            </button>
          </form>
        </div>
      </section>

      {/* AI Planning Recommendations Card */}
      <section className="surface-card p-5 border border-amber-500/25 bg-gradient-to-r from-canvas-card via-canvas-elevated to-canvas-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 flex-shrink-0 mt-0.5">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>AI Planning Recommendation</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300">
                Active Suggestion
              </span>
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              You have a 2-hour open focus block between 02:00 PM and 04:00 PM. Would you like to schedule your high-priority coding task here?
            </p>
          </div>
        </div>
        <Link
          href="/planner"
          className="px-4 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center gap-1.5 flex-shrink-0 transition"
        >
          <span>Open Planner</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </section>

      {/* Confirmed Schedule & Tasks */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Today&apos;s Confirmed Tasks & Schedule
            </h2>
          </div>
          <Link
            href="/tasks"
            className="text-xs font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1 transition"
          >
            <span>View All ({tasks.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {tasks.length === 0 ? (
          <div className="p-8 text-center surface-card border border-slate-800 rounded-xl space-y-2">
            <Clock className="w-8 h-8 text-slate-500 mx-auto mb-1" />
            <p className="text-sm font-bold text-slate-300">
              No confirmed tasks for today yet.
            </p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Speak or enter thoughts in the capture section above. Once you review and approve the proposal, your tasks will appear here.
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
                  className="surface-card surface-card-hover p-4 border border-sky-500/15 flex items-center justify-between cursor-pointer group"
                >
                  <div className="flex items-center gap-3.5">
                    <button
                      type="button"
                      aria-label={isDone ? "Mark incomplete" : "Mark complete"}
                      className="text-slate-400 group-hover:text-sky-400 transition"
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-500" />
                      )}
                    </button>
                    <div>
                      <h3
                        className={`text-sm font-semibold transition ${
                          isDone ? "line-through text-slate-500" : "text-white"
                        }`}
                      >
                        {task.title}
                      </h3>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1">
                        <span className="font-medium text-sky-400">{task.estimated_duration_min} mins</span>
                        <span>•</span>
                        <span className="font-semibold text-amber-400">{task.priority}</span>
                      </div>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
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
