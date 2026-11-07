"use client";

import React, { useState } from "react";
import { Priority } from "@/types";
import { useProposalStore } from "@/store/proposalStore";
import { Check, X, Clock, AlertCircle, Quote, ShieldAlert, HelpCircle, Globe, Mic } from "lucide-react";
import { cn } from "@/lib/utils";
import { submitProposalClarifications, translateProposal } from "@/lib/api";

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
    setProposal,
    setProposalLanguage,
  } = useProposalStore();

  const [isTranslating, setIsTranslating] = useState(false);

  const handleLanguageChange = async (targetLang: string) => {
    if (!activeProposal) return;
    setIsTranslating(true);
    try {
      const updated = await translateProposal(activeProposal.id, targetLang);
      setProposalLanguage(updated);
    } catch (err) {
      console.error("Language translation failed:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleAnswerClarification = async (questionId: string, option: string) => {
    if (!activeProposal) return;
    try {
      const now = new Date();
      let resolvedIso: string | undefined = undefined;
      if (option.toLowerCase().includes("5 pm") || option.toLowerCase().includes("evening")) {
        now.setHours(17, 0, 0, 0);
        resolvedIso = now.toISOString();
      } else if (option.toLowerCase().includes("tomorrow") || option.toLowerCase().includes("9 am")) {
        const tomorrow = new Date(Date.now() + 86400000);
        tomorrow.setHours(9, 0, 0, 0);
        resolvedIso = tomorrow.toISOString();
      }
      
      const durationMin = option.includes("min") ? parseInt(option, 10) : undefined;
      
      const updated = await submitProposalClarifications(activeProposal.id, [
        {
          question_id: questionId,
          answer: option,
          selected_option: option,
          resolved_deadline_iso: resolvedIso,
          resolved_duration_min: isNaN(Number(durationMin)) ? undefined : durationMin,
        },
      ]);
      setProposal(updated);
    } catch (e) {
      console.error("Clarification failed:", e);
    }
  };

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
            <span className="text-xs text-slate-400 font-semibold tracking-wider uppercase">
              DETECTED: {activeProposal.detected_language}
            </span>
            {activeProposal.translation_status === "TRANSLATED" && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 border border-emerald-500/40 text-emerald-300">
                Sarvam AI Translated
              </span>
            )}
          </div>

          <h2 className="text-lg font-bold text-white tracking-tight">
            {activeProposal.intent_summary}
          </h2>

          {/* Display Language Selector */}
          <div className="flex items-center gap-2.5 mt-2.5 mb-1.5 flex-wrap">
            <label htmlFor="display-language-select" className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-sky-400" />
              <span>Display language:</span>
            </label>
            <div className="relative inline-flex items-center">
              <select
                id="display-language-select"
                value={activeProposal.display_language || "original"}
                disabled={isTranslating}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="text-xs bg-slate-900 border border-sky-500/50 hover:border-sky-400 text-sky-200 font-semibold rounded-lg px-3 py-1 focus:outline-none focus:ring-1 focus:ring-sky-400 cursor-pointer transition shadow-inner"
              >
                <option value="en">English</option>
                <option value="ta">தமிழ் (Tamil)</option>
                <option value="original">Original language</option>
              </select>
              {isTranslating && (
                <span className="ml-2 text-xs text-sky-400 animate-pulse font-semibold">
                  Translating...
                </span>
              )}
            </div>
          </div>

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

      {/* Spoken Transcript Preview */}
      {activeProposal.transcript_text && (
        <div className="mb-5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5 font-medium flex-wrap gap-2">
            <span className="flex items-center gap-1.5 text-sky-300 font-semibold">
              <Mic className="w-3.5 h-3.5 text-sky-400" />
              Recognized Speech ({activeProposal.display_language === "original" ? "Original" : activeProposal.display_language === "ta" ? "Tamil Display" : "English Display"}):
            </span>
            {activeProposal.display_language !== "original" && activeProposal.original_transcript && activeProposal.original_transcript !== activeProposal.transcript_text && (
              <span className="text-[11px] text-slate-500 italic">
                Original Spoken: &quot;{activeProposal.original_transcript}&quot;
              </span>
            )}
          </div>
          <p className="text-slate-200 font-medium italic">
            &quot;{activeProposal.transcript_text}&quot;
          </p>
        </div>
      )}

      {/* Clarification Q&A Loop (Phase 5.3) */}
      {activeProposal.clarifications && activeProposal.clarifications.length > 0 && (
        <div className="mb-6 p-4 rounded-xl bg-cyber-amber-950/30 border border-cyber-amber-500/40 space-y-3">
          <div className="flex items-center gap-2 text-cyber-amber-300">
            <HelpCircle className="w-4 h-4 flex-shrink-0 text-cyber-amber-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider">
              Clarification Required Before Schedule Finalization
            </h3>
          </div>
          <div className="space-y-3">
            {activeProposal.clarifications.map((q) => (
              <div key={q.id} className="p-3 rounded-lg bg-slate-900/90 border border-slate-700/80 space-y-2">
                <p className="text-xs font-semibold text-slate-200">{q.question_text}</p>
                {q.suggested_options && q.suggested_options.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {q.suggested_options.map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => handleAnswerClarification(q.id, opt)}
                        className="text-xs px-3 py-1 rounded-md bg-cyber-amber-500/20 hover:bg-cyber-amber-500/30 text-cyber-amber-200 border border-cyber-amber-500/40 font-semibold transition cursor-pointer"
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

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
