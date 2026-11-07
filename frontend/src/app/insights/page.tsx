"use client";

import React from "react";
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  Flame,
  Award,
  Sparkles,
  PieChart,
  ArrowUpRight
} from "lucide-react";

export default function InsightsPage() {
  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Productivity Insights</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
              Weekly Analysis
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical insights into your focus velocity, duration estimation calibration, and schedule adherence.
          </p>
        </div>

        {/* Focus Score Hero Stat */}
        <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-canvas-card border border-sky-500/30 shadow-md">
          <Award className="w-5 h-5 text-cyber-amber-400" />
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Focus Calibration</span>
            <span className="text-base font-black text-white font-mono">88 / 100</span>
          </div>
          <span className="text-xs text-emerald-400 font-bold flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5" /> +6%
          </span>
        </div>
      </div>

      {/* Top Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="surface-card p-5 border-sky-500/20 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Total Focus Time</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-2xl font-black text-white font-mono">34.5 hrs</p>
          <span className="text-xs text-emerald-400 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> +2.4h vs last week
          </span>
        </div>

        <div className="surface-card p-5 border-cyber-amber-500/20 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">P1 Tasks Completed</span>
            <CheckCircle2 className="w-4 h-4 text-cyber-amber-400" />
          </div>
          <p className="text-2xl font-black text-white font-mono">18 / 19</p>
          <span className="text-xs text-cyber-amber-400 font-medium">
            94.7% critical completion
          </span>
        </div>

        <div className="surface-card p-5 border-emerald-500/20 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Estimation Accuracy</span>
            <PieChart className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-black text-white font-mono">84.2%</p>
          <span className="text-xs text-slate-400">
            Buffer priors calibrated
          </span>
        </div>

        <div className="surface-card p-5 border-rose-500/20 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Daily Planning Streak</span>
            <Flame className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-black text-white font-mono">12 Days</p>
          <span className="text-xs text-rose-400">
            Consecutive mornings planned
          </span>
        </div>
      </div>

      {/* Main Analytics: Planned vs Actual & Workload Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Planned vs Actual Duration Bar Comparison (7 cols) */}
        <div className="lg:col-span-7 surface-card p-6 border-sky-500/20 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white uppercase tracking-wider">
                Planned vs Actual Hours
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Weekly calibration across Monday through Friday
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-sky-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-sky-400" /> Planned
              </span>
              <span className="flex items-center gap-1.5 text-cyber-amber-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-cyber-amber-400" /> Actual
              </span>
            </div>
          </div>

          {/* Bar Chart Representation */}
          <div className="space-y-4 pt-2">
            {[
              { day: "Mon", planned: 6.5, actual: 6.0 },
              { day: "Tue", planned: 7.0, actual: 7.5 },
              { day: "Wed", planned: 8.0, actual: 7.8 },
              { day: "Thu", planned: 6.0, actual: 6.2 },
              { day: "Fri", planned: 7.0, actual: 7.0 },
            ].map((d) => (
              <div key={d.day} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-300">{d.day}</span>
                  <span className="font-mono text-slate-400 text-[11px]">
                    {d.actual}h actual / {d.planned}h planned
                  </span>
                </div>
                <div className="space-y-1">
                  <div className="w-full h-2 rounded-full bg-canvas-subtle overflow-hidden">
                    <div
                      className="h-full rounded-full bg-sky-400"
                      style={{ width: `${(d.planned / 9) * 100}%` }}
                    />
                  </div>
                  <div className="w-full h-2 rounded-full bg-canvas-subtle overflow-hidden">
                    <div
                      className="h-full rounded-full bg-cyber-amber-400"
                      style={{ width: `${(d.actual / 9) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Workload Distribution Breakdown (5 cols) */}
        <div className="lg:col-span-5 surface-card p-6 border-sky-500/20 space-y-6">
          <div>
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Time Distribution
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Category allocation of your 34.5 hours
            </p>
          </div>

          <div className="space-y-3">
            {[
              { label: "Deep Engineering & Problem Solving", pct: 55, color: "#38BDF8" },
              { label: "Client Clarification & Meetings", pct: 25, color: "#F59E0B" },
              { label: "Academic / College Capstone", pct: 15, color: "#10B981" },
              { label: "Administrative / Email & Buffer", pct: 5, color: "#94A3B8" },
            ].map((cat) => (
              <div key={cat.label} className="p-3 rounded-xl bg-canvas-subtle/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-200 font-semibold">{cat.label}</span>
                  <span className="font-bold font-mono text-white">{cat.pct}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${cat.pct}%`, backgroundColor: cat.color }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* AI Optimization Tip */}
          <div className="p-4 rounded-xl bg-cyber-amber-950/20 border border-cyber-amber-500/30 text-xs space-y-1.5 text-cyber-amber-200">
            <div className="flex items-center gap-1.5 font-bold text-cyber-amber-400">
              <Sparkles className="w-4 h-4" />
              <span>AI Planning Tip</span>
            </div>
            <p className="leading-relaxed">
              Applying the +15% automatic duration buffer to Thursday afternoon tasks prevented 2 schedule overruns this week.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
