"use client";

import React, { useState } from "react";
import {
  Target,
  Plus,
  Trophy,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface KeyResult {
  id: string;
  metric: string;
  target: number;
  current: number;
  unit: string;
}

interface StrategicGoal {
  id: string;
  title: string;
  timeframe: string; // e.g., "Q4 2026"
  category: "career" | "academic" | "health";
  progress: number;
  key_results: KeyResult[];
  status: "on_track" | "at_risk" | "achieved";
}

const MOCK_GOALS: StrategicGoal[] = [
  {
    id: "g-1",
    title: "Ship THOZHI Sovereign Planning Engine MVP",
    timeframe: "Q4 2026",
    category: "career",
    progress: 80,
    status: "on_track",
    key_results: [
      { id: "kr-1", metric: "Verified Stage 0 to Stage 3 Architecture", target: 4, current: 3, unit: "stages" },
      { id: "kr-2", metric: "Prisma v3 Indic Speech Benchmarks (<15% WER)", target: 15, current: 12.8, unit: "% WER" },
      { id: "kr-3", metric: "Zero Silent Task Creation Tests Passing", target: 100, current: 100, unit: "% tests" },
    ],
  },
  {
    id: "g-2",
    title: "Graduate with Engineering Distinction (CGPA > 8.5)",
    timeframe: "Academic Year 2026-27",
    category: "academic",
    progress: 65,
    status: "on_track",
    key_results: [
      { id: "kr-4", metric: "Major Project Capstone Review Score", target: 90, current: 85, unit: "marks" },
      { id: "kr-5", metric: "Semester 7 & 8 Coursework Submissions on Time", target: 10, current: 7, unit: "courses" },
    ],
  },
  {
    id: "g-3",
    title: "Establish 3 Recurring Freelance Engineering Retainers",
    timeframe: "Q1 2027",
    category: "career",
    progress: 40,
    status: "at_risk",
    key_results: [
      { id: "kr-6", metric: "Active Client Contract Retainers", target: 3, current: 1, unit: "clients" },
      { id: "kr-7", metric: "Monthly Recurring Revenue", target: 50000, current: 20000, unit: "INR" },
    ],
  },
];

export default function GoalsPage() {
  const [goals, setGoals] = useState<StrategicGoal[]>(MOCK_GOALS);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Goal Form State
  const [newTitle, setNewTitle] = useState("");
  const [newTimeframe, setNewTimeframe] = useState("Q4 2026");
  const [newCategory, setNewCategory] = useState<"career" | "academic" | "health">("career");

  const handleCreateGoal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const created: StrategicGoal = {
      id: `g-${Date.now()}`,
      title: newTitle.trim(),
      timeframe: newTimeframe,
      category: newCategory,
      progress: 0,
      status: "on_track",
      key_results: [
        { id: `kr-${Date.now()}`, metric: "Initial Milestone Execution", target: 100, current: 10, unit: "%" },
      ],
    };

    setGoals([created, ...goals]);
    setIsModalOpen(false);
    setNewTitle("");
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Strategic Goals & OKRs</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyber-amber-500/10 border border-cyber-amber-500/30 text-cyber-amber-300 font-semibold">
              Long-term Alignment
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Connect high-level aspirations to day-to-day focus sessions. Protect time for what truly matters.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-amber px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Goal</span>
        </button>
      </div>

      {/* Goal Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {goals.map((goal) => {
          const isAtRisk = goal.status === "at_risk";
          return (
            <div
              key={goal.id}
              className={cn(
                "surface-card surface-card-hover p-6 flex flex-col justify-between space-y-6 relative border-sky-500/20",
                isAtRisk && "border-rose-500/30"
              )}
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-mono font-bold text-sky-400 bg-sky-950/40 px-2 py-0.5 rounded border border-sky-500/20">
                    {goal.timeframe}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] uppercase font-bold px-2 py-0.5 rounded",
                      goal.status === "on_track"
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-500/30"
                        : "bg-rose-950/60 text-rose-300 border border-rose-500/30"
                    )}
                  >
                    {goal.status.replace("_", " ")}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white leading-snug">
                  {goal.title}
                </h3>

                {/* Progress Meter */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Overall Progress</span>
                    <span className="font-bold text-cyber-amber-400 font-mono">
                      {goal.progress}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-canvas-subtle overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        isAtRisk ? "bg-rose-500" : "bg-gradient-to-r from-sky-400 to-cyber-amber-400"
                      )}
                      style={{ width: `${goal.progress}%` }}
                    />
                  </div>
                </div>

                {/* Key Results Checklist */}
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                    Key Results (OKRs)
                  </span>
                  {goal.key_results.map((kr) => (
                    <div
                      key={kr.id}
                      className="p-2.5 rounded-lg bg-canvas-subtle/80 border border-slate-800 text-xs space-y-1"
                    >
                      <p className="text-slate-300 leading-tight">{kr.metric}</p>
                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                        <span>Current: {kr.current} {kr.unit}</span>
                        <span className="text-sky-400 font-bold">Goal: {kr.target} {kr.unit}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-sky-400" />
                  <span>{goal.key_results.length} Metrics Tracked</span>
                </span>
                <span className="font-semibold text-sky-400 hover:text-sky-300 cursor-pointer">
                  View Tasks →
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* CREATE GOAL MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="surface-card w-full max-w-lg p-6 border-cyber-amber-500/30 shadow-2xl relative animate-scaleUp">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-cyber-amber-400" />
              <span>Create Strategic Goal</span>
            </h2>

            <form onSubmit={handleCreateGoal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Goal Objective *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="E.g. Achieve 100 daily active users for personal planning engine"
                  className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyber-amber-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Timeframe
                  </label>
                  <input
                    type="text"
                    value={newTimeframe}
                    onChange={(e) => setNewTimeframe(e.target.value)}
                    placeholder="Q4 2026 or Annual"
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-cyber-amber-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) =>
                      setNewCategory(e.target.value as "career" | "academic" | "health")
                    }
                    className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-cyber-amber-400"
                  >
                    <option value="career">Career & Engineering</option>
                    <option value="academic">Academic & Degree</option>
                    <option value="health">Personal & Health</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-amber px-5 py-2 rounded-xl text-xs font-bold"
                >
                  Save Strategic Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
