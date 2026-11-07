"use client";

import React, { useState } from "react";
import { MicButton } from "@/components/capture/MicButton";
import { ProposalReviewCard } from "@/components/proposal/ProposalReviewCard";
import { useProposalStore } from "@/store/proposalStore";
import { captureText, captureAudio, submitProposalApproval } from "@/lib/api";
import {
  Sparkles,
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
} from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";

export default function CapturePage() {
  const [inputText, setInputText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState<"ta" | "tanglish" | "en">("tanglish");
  const [isProcessing, setIsProcessing] = useState(false);
  const [recentCaptures, setRecentCaptures] = useState<
    Array<{ id: string; text: string; time: string; type: "voice" | "text" }>
  >([
    {
      id: "1",
      text: "Naalaiku kaalaila 10 manikku project review irukku, adhellam prepare panni slide mudikanum.",
      time: "10 mins ago",
      type: "voice",
    },
    {
      id: "2",
      text: "Submit lab record by Friday 4 PM, otherwise penalty marks.",
      time: "2 hours ago",
      type: "text",
    },
  ]);
  const [notification, setNotification] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { activeProposal, setProposal, clearProposal, itemDecisions } = useProposalStore();

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    try {
      setIsProcessing(true);
      const textToCapture = inputText.trim();
      const proposal = await captureText(textToCapture);
      setProposal(proposal);
      setRecentCaptures((prev) => [
        {
          id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          text: proposal.transcript_text || textToCapture,
          time: "Just now",
          type: "text",
        },
        ...prev,
      ]);
      setInputText("");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Capture failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAudioRecorded = async (audioBlob: Blob) => {
    if (isProcessing) return;
    try {
      setIsProcessing(true);
      const proposal = await captureAudio(audioBlob, selectedLanguage);
      setProposal(proposal);
      const displayedText = proposal.transcript_text || proposal.intent_summary || "Audio capture session";
      setRecentCaptures((prev) => [
        {
          id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          text: displayedText,
          time: "Just now",
          type: "voice",
        },
        ...prev,
      ]);
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
      const decisions = Object.values(itemDecisions);
      const res = await submitProposalApproval(activeProposal.id, decisions);
      setNotification(res.message);
      clearProposal();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Approval submission failed: ${message}`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsProcessing(false);
    }
  };

  const applyTemplate = (template: string) => {
    setInputText(template);
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div className="flex items-center gap-3.5">
          <BrandLogo variant="icon" className="w-12 h-12 flex-shrink-0 hidden sm:block" alt="THOZHI Mascot" priority />
          <div>
            <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
              <span>Thought Capture Studio</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold uppercase tracking-wider">
                Multilingual Voice & Text
              </span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Express yourself freely in Tamil, Tanglish, or English. THOZHI extracts tasks and commitments for your approval.
            </p>
          </div>
        </div>

        {/* Gnani Engine Telemetry Badge */}
        <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-canvas-card border border-sky-500/20 text-xs text-slate-300 shadow-sm">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-semibold text-slate-200">ASR: Gnani Prisma v3</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono">
            ta-IN
          </span>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-3 shadow-lg shadow-emerald-950/40 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span className="font-medium text-sm">{notification}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-200 flex items-center gap-2.5 font-bold shadow-lg shadow-rose-500/10 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Studio Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Voice & Text Capture (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Audio Capture Card */}
          <div className="surface-card p-6 relative overflow-hidden border-sky-500/20">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-sky-400 animate-pulse" />
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  Voice Thought Stream
                </h2>
              </div>
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Info className="w-3.5 h-3.5 text-sky-400" /> Zero Raw Audio Retained
              </span>
            </div>

            <div className="p-6 rounded-2xl bg-canvas-subtle/80 border border-sky-500/10 flex flex-col items-center justify-center text-center">
              <MicButton
                onAudioRecorded={handleAudioRecorded}
                isProcessing={isProcessing}
                size="lg"
              />
              <p className="mt-4 text-xs text-slate-400 max-w-sm">
                Tap to speak freely in Tamil or Tanglish. Our streaming adapter processes audio in transient memory.
              </p>
            </div>
          </div>

          {/* Text Capture Form */}
          <div className="surface-card p-6 border-sky-500/20">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-sky-400" />
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  Type Unstructured Thoughts
                </h2>
              </div>

              {/* Language Selector */}
              <div className="flex items-center gap-1 bg-canvas-subtle p-1 rounded-lg border border-slate-700/60">
                <Languages className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
                <button
                  type="button"
                  onClick={() => setSelectedLanguage("tanglish")}
                  className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                    selectedLanguage === "tanglish"
                      ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Tanglish
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedLanguage("ta")}
                  className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                    selectedLanguage === "ta"
                      ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  தமிழ்
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedLanguage("en")}
                  className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                    selectedLanguage === "en"
                      ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  English
                </button>
              </div>
            </div>

            <form onSubmit={handleTextSubmit} className="space-y-4">
              <div className="relative">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={
                    selectedLanguage === "tanglish"
                      ? "E.g. Inaiki evening 5 manikku client call irukku, adhe mudichitu report submit pannanum..."
                      : selectedLanguage === "ta"
                      ? "எ.கா. இன்று மாலை 5 மணிக்கு வாடிக்கையாளர் அழைப்பு உள்ளது, அறிக்கை சமர்ப்பிக்க வேண்டும்..."
                      : "E.g. Need to finalize budget report before 3pm and coordinate with engineering lead..."
                  }
                  rows={4}
                  className="w-full rounded-xl bg-canvas-subtle border border-sky-500/20 p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400 transition resize-none"
                  disabled={isProcessing}
                />
              </div>

              {/* Quick Prompt Starters */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-cyber-amber-400" /> Templates:
                </span>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "Inaiki evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-subtle hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
                >
                  Tanglish Review
                </button>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "Tomorrow morning 9:30 AM team sprint planning meeting. Need 45 mins to review backlog tickets before that."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-subtle hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
                >
                  Sprint Meeting
                </button>
                <button
                  type="button"
                  onClick={() =>
                    applyTemplate(
                      "College assignment deadline is Friday 11:59 PM. Must finish chapters 4 and 5."
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-subtle hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
                >
                  College Deadline
                </button>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isProcessing || !inputText.trim()}
                  className="btn-primary px-6 py-2.5 rounded-xl font-bold flex items-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
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
          <div className="surface-card p-5 border-sky-500/20 bg-gradient-to-br from-canvas-card to-slate-900/60">
            <div className="flex items-center gap-3 mb-3">
              <BrandLogo variant="icon" className="w-9 h-9 flex-shrink-0" alt="THOZHI Mascot" />
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Sovereign Intent Pipeline</span>
                </h3>
                <span className="text-[10px] text-sky-400 font-semibold">Gnani AI Prisma v3 Engine</span>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-3">
              1. <strong>Capture:</strong> Streams raw audio to Gnani Prisma v3.<br />
              2. <strong>Extraction:</strong> LLM classifies Tasks, Deadlines, and Conditions.<br />
              3. <strong>Approval:</strong> Zero silent task creation. You approve every item.
            </p>
            <div className="p-3 rounded-lg bg-cyber-amber-500/10 border border-cyber-amber-500/30 text-cyber-amber-300 text-xs flex items-center gap-2">
              <Clock className="w-4 h-4 flex-shrink-0" />
              <span>The AI proposes. The user decides.</span>
            </div>
          </div>

          {/* Recent Captures */}
          <div className="surface-card p-5 border-sky-500/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <History className="w-4 h-4 text-sky-400" />
                <span>Recent Capture Stream</span>
              </h3>
              <button
                type="button"
                onClick={() => setRecentCaptures([])}
                className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1 transition"
              >
                <Trash2 className="w-3 h-3" /> Clear
              </button>
            </div>

            <div className="space-y-3">
              {recentCaptures.map((c) => (
                <div
                  key={c.id}
                  className="p-3.5 rounded-xl bg-canvas-subtle/80 border border-slate-800 hover:border-sky-500/30 transition text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-semibold text-sky-400 uppercase tracking-wider">
                      {c.type === "voice" ? "🎙️ Voice" : "⌨️ Text"}
                    </span>
                    <span>{c.time}</span>
                  </div>
                  <p className="text-slate-200 line-clamp-2 leading-relaxed">
                    {c.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Proposal Deck Overlay / Section */}
      {activeProposal && (
        <div className="pt-6 border-t border-sky-500/20 animate-slideUp">
          <ProposalReviewCard
            onCommit={handleCommitProposal}
            isSubmitting={isProcessing}
          />
        </div>
      )}
    </div>
  );
}
