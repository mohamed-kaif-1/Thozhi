"use client";

import React from "react";
import { Priority } from "@/types";
import { useProposalStore } from "@/store/proposalStore";
import { Check, X, Clock, AlertCircle, Quote, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProposalReviewCardProps {
  onCommit: () => void;
  isSubmitting?: boolean;
}

export const ProposalReviewCard: React.FC<ProposalReviewCardProps> = ({
  onCommit,
  isSubmitting = false,
}) => {
  const {
    activeProposal,
    itemDecisions,
    updateDecision,
    toggleApproval,
    approveAll,
    rejectAll,
  } = useProposalStore();

  if (!activeProposal) return null;

  const approvedCount = Object.values(itemDecisions).filter((d) => d.is_approved).length;
  const rejectedCount = Object.values(itemDecisions).length - approvedCount;

  return (
    <div className="surface-card border border-amber-500/30 p-6 shadow-2xl shadow-amber-950/20 rounded-xl transition-all">
      {/* Header Banner */}
      <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/20 border border-amber-500/40 text-amber-300">
              AI Proposed Plan
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/20 border border-sky-500/40 text-sky-300">
              Gnani AI Prisma v3
            </span>
            <span className="text-xs text-slate-400 font-medium">
              Language: {activeProposal.detected_language}
            </span>
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            {activeProposal.intent_summary}
          </h2>
          <p className="text-xs text-amber-400/90 mt-1 flex items-center gap-1.5 font-medium">
            <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0 text-amber-400" />
            Core Invariant: The AI proposes. The user decides. Only approved items enter your schedule.
          </p>
        </div>

        {/* Bulk Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={approveAll}
            className="text-xs font-bold px-3 py-1.5 rounded-lg bg-sky-500/20 border border-sky-500/40 text-sky-300 hover:bg-sky-500/30 transition"
          >
            Approve All
          </button>
          <button
            onClick={rejectAll}
            className="text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition"
          >
            Reject All
          </button>
        </div>
      </div>

      {/* Items List */}
      <div className="space-y-4">
        {activeProposal.items.map((item) => {
          const decision = itemDecisions[item.id] || { is_approved: true };
          const isApproved = decision.is_approved;

          return (
            <div
              key={item.id}
              className={cn(
                "p-4 rounded-xl border transition-all duration-200",
                isApproved
                  ? "bg-slate-900/90 border-sky-500/25 shadow-md"
                  : "bg-slate-950/60 border-slate-800 opacity-60"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 border border-slate-700 text-slate-200">
                      {item.item_type}
                    </span>
                    <span className="text-[11px] font-semibold text-sky-400">
                      Confidence: {Math.round(item.confidence_score * 100)}%
                    </span>
                    {item.uncertainty_flags.map((flag) => (
                      <span
                        key={flag}
                        className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 flex items-center gap-1"
                      >
                        <AlertCircle className="w-2.5 h-2.5" />
                        {flag}
                      </span>
                    ))}
                  </div>

                  {/* Editable Proposed Title */}
                  <input
                    type="text"
                    value={decision.proposed_title ?? item.proposed_title}
                    disabled={!isApproved}
                    onChange={(e) =>
                      updateDecision(item.id, { proposed_title: e.target.value })
                    }
                    className="w-full text-base font-semibold text-white bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 focus:border-sky-400 focus:outline-none transition"
                  />

                  {/* Extracted Original Substring */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 italic">
                    <Quote className="w-3 h-3 flex-shrink-0 text-slate-500" />
                    <span>&quot;{item.source_expression}&quot;</span>
                  </div>

                  {/* Controls: Duration & Priority */}
                  <div className="flex items-center gap-4 pt-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-300">
                      <Clock className="w-3.5 h-3.5 text-sky-400" />
                      <select
                        value={decision.estimated_duration_min ?? item.estimated_duration_min}
                        disabled={!isApproved}
                        onChange={(e) =>
                          updateDecision(item.id, {
                            estimated_duration_min: Number(e.target.value),
                          })
                        }
                        className="text-xs bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 font-medium text-white focus:outline-none focus:border-sky-400"
                      >
                        <option value={15}>15 mins</option>
                        <option value={30}>30 mins</option>
                        <option value={45}>45 mins</option>
                        <option value={60}>60 mins</option>
                        <option value={90}>90 mins</option>
                        <option value={120}>2 hours</option>
                      </select>
                    </div>

                    <select
                      value={decision.priority ?? item.priority}
                      disabled={!isApproved}
                      onChange={(e) =>
                        updateDecision(item.id, {
                          priority: e.target.value as Priority,
                        })
                      }
                      className="text-xs bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 font-medium text-white focus:outline-none focus:border-sky-400"
                    >
                      <option value="P1_CRITICAL">P1 - Critical</option>
                      <option value="P2_MEDIUM">P2 - Medium</option>
                      <option value="P3_LOW">P3 - Low</option>
                      <option value="BACKBURNER">Backburner</option>
                    </select>
                  </div>
                </div>

                {/* Approve / Reject Toggle Button */}
                <button
                  type="button"
                  onClick={() => toggleApproval(item.id)}
                  aria-label={isApproved ? "Dismiss item" : "Approve item"}
                  className={cn(
                    "p-2.5 rounded-xl border flex items-center justify-center transition-all",
                    isApproved
                      ? "bg-sky-500/20 border-sky-500/40 text-sky-400 hover:bg-sky-500/30"
                      : "bg-slate-800 border-slate-700 text-slate-400 hover:text-white"
                  )}
                >
                  {isApproved ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Confirmation Footer */}
      <div className="flex items-center justify-between border-t border-slate-800 pt-5 mt-6">
        <p className="text-sm font-medium text-slate-300">
          Decisions: <strong className="text-sky-400 font-bold">{approvedCount} approved</strong>,{" "}
          <strong className="text-slate-400">{rejectedCount} dismissed</strong>
        </p>

        <button
          onClick={onCommit}
          disabled={isSubmitting || approvedCount === 0}
          className={cn(
            "px-6 py-2.5 rounded-xl font-bold text-sm text-white shadow-lg transition-all flex items-center gap-2",
            approvedCount > 0
              ? "btn-primary"
              : "bg-slate-800 border border-slate-700 text-slate-500 cursor-not-allowed opacity-50",
            isSubmitting && "opacity-75 cursor-wait"
          )}
        >
          {isSubmitting ? "Committing Tasks..." : `Commit ${approvedCount} Tasks to Schedule`}
        </button>
      </div>
    </div>
  );
};
