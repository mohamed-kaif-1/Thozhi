"use client";

import React, { useState, useEffect } from "react";
import { VoiceAgentOrb, CaptureLanguage } from "@/components/capture/VoiceAgentOrb";
import { ProposalReviewCard } from "@/components/proposal/ProposalReviewCard";
import { useProposalStore } from "@/store/proposalStore";
import { captureText, captureAudio } from "@/lib/api";
import {
  Send,
  Languages,
  Radio,
  FileText,
  Clock,
  History,
  Info,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Inbox,
} from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { cn } from "@/lib/utils";

function formatCaptureTime(isoString?: string): string {
  if (!isoString) return "Just now";
  const date = new Date(isoString);
  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diffSec < 60) return "Just now";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function CapturePage() {
  const [inputText, setInputText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState<CaptureLanguage>("tanglish");
  const [isProcessing, setIsProcessing] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    captures,
    proposals,
    activeProposal,
    activeCaptureId,
    filterStatus,
    setFilterStatus,
    loadInitialQueue,
    setProposal,
    selectCapture,
    commitActiveProposal,
    rejectActiveProposal,
    clearHistory,
    isSubmitting,
  } = useProposalStore();

  useEffect(() => {
    loadInitialQueue();
  }, [loadInitialQueue]);

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    try {
      setIsProcessing(true);
      const textToCapture = inputText.trim();
      const proposal = await captureText(textToCapture);
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

  const handleAudioRecorded = async (audioBlob: Blob, language: CaptureLanguage = selectedLanguage) => {
    if (isProcessing) return;
    try {
      setIsProcessing(true);
      const proposal = await captureAudio(audioBlob, language);
      setProposal(proposal);
      setNotification("Audio transcribed with Gnani AI Prisma v3 and added to pending queue.");
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
      const res = await commitActiveProposal();
      if (res) {
        setNotification(res.message);
        setTimeout(() => setNotification(null), 5000);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Approval submission failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    }
  };

  const handleRejectProposal = async () => {
    if (!activeProposal) return;
    try {
      await rejectActiveProposal("Rejected by user from queue review");
      setNotification("Proposal marked as rejected. No tasks were added.");
      setTimeout(() => setNotification(null), 4000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Rejection failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    }
  };

  const handleClearHistory = async () => {
    if (confirm("Clear visible capture stream history? (Committed tasks and pending proposals will remain safely preserved)")) {
      await clearHistory();
      setNotification("Capture stream history cleared. Tasks and proposals remain preserved.");
      setTimeout(() => setNotification(null), 4000);
    }
  };

  const applyTemplate = (template: string) => {
    setInputText(template);
  };

  // Filter captures according to filterStatus
  const filteredCaptures = captures.filter((c) => {
    if (filterStatus === "ALL") return true;
    if (filterStatus === "PENDING_REVIEW") return c.lifecycle_status === "PENDING_REVIEW";
    if (filterStatus === "COMMITTED") return c.lifecycle_status === "COMMITTED";
    if (filterStatus === "REJECTED") return c.lifecycle_status === "REJECTED";
    return true;
  });

  const pendingProposalsCount = proposals.filter((p) => p.status === "PENDING_REVIEW").length;
  const committedCount = captures.filter((c) => c.lifecycle_status === "COMMITTED").length;
  const rejectedCount = captures.filter((c) => c.lifecycle_status === "REJECTED").length;

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto transition-colors duration-200">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-sky-500/20">
        <div className="flex items-center gap-3.5">
          <BrandLogo variant="icon" className="w-12 h-12 flex-shrink-0 hidden sm:block" alt="THOZHI Mascot" priority />
          <div>
            <h1 className="text-2xl md:text-3xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-3">
              <span>Thought Capture Studio</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-600 dark:text-sky-400 font-semibold uppercase tracking-wider">
                Voice & Text
              </span>
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Express yourself freely in Tamil, Tanglish, or English. THOZHI extracts tasks and commitments for your approval.
            </p>
          </div>
        </div>

        {/* Gnani Engine Telemetry Badge */}
        <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-canvas-card border border-slate-200 dark:border-sky-500/20 text-xs text-slate-700 dark:text-slate-300 shadow-sm">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">ASR: Gnani Prisma v3</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-700 dark:text-sky-300 font-mono font-bold">
            ta-IN
          </span>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300 flex items-center gap-3 shadow-lg shadow-emerald-500/5 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span className="font-medium text-sm">{notification}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-500/15 border border-rose-300 dark:border-rose-500/40 text-rose-800 dark:text-rose-200 flex items-center gap-2.5 font-bold shadow-lg shadow-rose-500/10 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Studio Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Voice & Text Capture (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Audio Capture Card with VoiceAgentOrb */}
          <div className="surface-card p-6 relative overflow-hidden border-slate-200/90 dark:border-sky-500/20 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-sky-500 animate-pulse" />
                <h2 className="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Voice Thought Stream
                </h2>
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 font-medium">
                <Info className="w-3.5 h-3.5 text-sky-500" /> Zero Raw Audio Retained
              </span>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-canvas-subtle/80 border border-slate-200 dark:border-sky-500/10 flex flex-col items-center justify-center text-center">
              <VoiceAgentOrb
                onAudioRecorded={handleAudioRecorded}
                isProcessing={isProcessing}
                initialLanguage={selectedLanguage}
                onLanguageChange={setSelectedLanguage}
                variant="hero"
              />
              <p className="mt-4 text-xs text-slate-500 dark:text-slate-400 max-w-sm">
                Tap to speak freely in Tamil, Tanglish, or English. Our streaming adapter processes audio in transient memory.
              </p>
            </div>
          </div>

          {/* Text Capture Form */}
          <div className="surface-card p-6 border-slate-200/90 dark:border-sky-500/20 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-sky-500" />
                <h2 className="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Type Unstructured Thoughts
                </h2>
              </div>

              {/* Language Selector */}
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-canvas-subtle p-1 rounded-lg border border-slate-200 dark:border-slate-700/60">
                <Languages className="w-3.5 h-3.5 text-slate-500 ml-1.5" />
                {(["tanglish", "ta", "en"] as CaptureLanguage[]).map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => setSelectedLanguage(lang)}
                    className={cn(
                      "px-2 py-0.5 rounded text-xs font-semibold transition",
                      selectedLanguage === lang
                        ? "bg-sky-500/20 text-sky-600 dark:text-sky-300 border border-sky-500/40 font-bold"
                        : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                    )}
                  >
                    {lang === "tanglish" ? "Tanglish" : lang === "ta" ? "தமிழ்" : "English"}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleTextSubmit} className="space-y-4">
              <div className="relative">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="e.g. நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்..."
                  rows={4}
                  className="w-full bg-slate-50 dark:bg-slate-950/80 border border-slate-300 dark:border-slate-800 rounded-xl p-3.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-600 focus:outline-none focus:border-sky-500 transition resize-none shadow-inner"
                />
              </div>

              {/* Quick Template Chips */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-[11px] text-slate-500 font-medium">Quick examples:</span>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 dark:bg-canvas-subtle dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-sky-600 dark:hover:text-sky-300 border border-slate-200 dark:border-slate-800 transition"
                >
                  Tamil Deadline
                </button>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "Review project pull requests tomorrow morning at 10 AM, need 45 minutes."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 dark:bg-canvas-subtle dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-sky-600 dark:hover:text-sky-300 border border-slate-200 dark:border-slate-800 transition"
                >
                  English Sprint
                </button>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "Friday evening 4 PM kulla lab manual record submission pannanum, romba mukkiyam."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 dark:bg-canvas-subtle dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-sky-600 dark:hover:text-sky-300 border border-slate-200 dark:border-slate-800 transition"
                >
                  Tanglish Lab
                </button>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isProcessing || !inputText.trim()}
                  className="btn-primary px-6 py-2.5 rounded-xl font-bold flex items-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                >
                  {isProcessing ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Extracting Intent...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Extract Plan Proposals</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Recent Captures & Architecture Notice (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Pipeline Information Card */}
          <div className="surface-card p-5 border-slate-200/90 dark:border-sky-500/20 shadow-xl">
            <div className="flex items-center gap-3 mb-3">
              <BrandLogo variant="icon" className="w-9 h-9 flex-shrink-0" alt="THOZHI Mascot" />
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>Sovereign Intent Pipeline</span>
                </h3>
                <span className="text-[10px] text-sky-600 dark:text-sky-400 font-semibold">Gnani AI Prisma v3 Engine</span>
              </div>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-3">
              1. <strong>Capture:</strong> Streams raw audio to Gnani Prisma v3.<br />
              2. <strong>Extraction:</strong> LLM classifies Tasks, Deadlines, and Conditions.<br />
              3. <strong>Approval:</strong> Zero silent task creation. You approve every item.
            </p>
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2 font-semibold">
              <Clock className="w-4 h-4 flex-shrink-0 text-amber-500" />
              <span>The AI proposes. The user decides.</span>
            </div>
          </div>

          {/* Recent Captures Stream */}
          <div className="surface-card p-5 border-slate-200/90 dark:border-sky-500/20 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <History className="w-4 h-4 text-sky-500" />
                <span>Recent Capture Stream</span>
              </h3>
              {captures.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="text-xs text-slate-500 hover:text-rose-500 flex items-center gap-1 transition"
                  title="Clear visible stream (committed tasks remain intact)"
                >
                  <Trash2 className="w-3 h-3" /> Clear History
                </button>
              )}
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1.5 mb-4 border-b border-slate-200 dark:border-slate-800 pb-2 text-[11px]">
              <button
                type="button"
                onClick={() => setFilterStatus("ALL")}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition",
                  filterStatus === "ALL"
                    ? "bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-500/40 font-bold"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                )}
              >
                All ({captures.length})
              </button>
              <button
                type="button"
                onClick={() => setFilterStatus("PENDING_REVIEW")}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1",
                  filterStatus === "PENDING_REVIEW"
                    ? "bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/40 font-bold"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                )}
              >
                Pending ({pendingProposalsCount})
              </button>
              <button
                type="button"
                onClick={() => setFilterStatus("COMMITTED")}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition",
                  filterStatus === "COMMITTED"
                    ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40 font-bold"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                )}
              >
                Committed ({committedCount})
              </button>
              <button
                type="button"
                onClick={() => setFilterStatus("REJECTED")}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition",
                  filterStatus === "REJECTED"
                    ? "bg-rose-500/20 text-rose-700 dark:text-rose-300 border border-rose-500/40 font-bold"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                )}
              >
                Rejected ({rejectedCount})
              </button>
            </div>

            {/* Capture Cards List */}
            {filteredCaptures.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                <Inbox className="w-8 h-8 mx-auto mb-2 text-slate-400 dark:text-slate-600 opacity-60" />
                <p className="font-semibold text-slate-600 dark:text-slate-400">No captures found in this view.</p>
                <p className="text-[11px] mt-1 text-slate-400 dark:text-slate-500">Speak or type your thoughts to create a capture.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                {filteredCaptures.map((c) => {
                  const isSelected = activeCaptureId === c.id;
                  const isVoice = c.input_type === "AUDIO";
                  const status = c.lifecycle_status;

                  return (
                    <div
                      key={c.id}
                      onClick={() => selectCapture(c.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          selectCapture(c.id);
                        }
                      }}
                      className={cn(
                        "p-3 rounded-xl border text-xs space-y-1.5 transition text-left cursor-pointer",
                        isSelected
                          ? "bg-sky-50 dark:bg-sky-950/40 border-sky-500/60 shadow-md shadow-sky-500/10"
                          : "bg-slate-50 dark:bg-canvas-subtle/80 border-slate-200 dark:border-slate-800 hover:border-sky-500/40 hover:bg-slate-100 dark:hover:bg-slate-900/60"
                      )}
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-sky-600 dark:text-sky-400 flex items-center gap-1 uppercase tracking-wider">
                          {isVoice ? "🎙️ Voice" : "⌨️ Text"}
                          <span className="text-slate-400 font-normal">({c.detected_language})</span>
                        </span>
                        <div className="flex items-center gap-1.5">
                          {status === "COMMITTED" && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
                              COMMITTED
                            </span>
                          )}
                          {status === "REJECTED" && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30">
                              REJECTED
                            </span>
                          )}
                          {status === "PENDING_REVIEW" && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                              PENDING
                            </span>
                          )}
                          <span className="text-slate-400">{formatCaptureTime(c.created_at)}</span>
                        </div>
                      </div>

                      <p className="text-slate-800 dark:text-slate-200 line-clamp-2 leading-relaxed">
                        {c.original_transcript || c.transcript_text}
                      </p>

                      {c.translated_transcript && c.translated_transcript !== c.original_transcript && (
                        <p className="text-[11px] text-sky-600 dark:text-sky-300/80 line-clamp-1 italic font-medium">
                          ↳ {c.translated_transcript}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Extracted Proposal Deck Overlay / Section */}
      {activeProposal && (
        <div className="pt-6 border-t border-slate-200/80 dark:border-sky-500/20 animate-slideUp">
          <ProposalReviewCard
            onCommit={handleCommitProposal}
            onReject={handleRejectProposal}
            isSubmitting={isProcessing || isSubmitting}
          />
        </div>
      )}
    </div>
  );
}
