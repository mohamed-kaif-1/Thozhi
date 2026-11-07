"use client";

import React, { useState } from "react";
import {
  Send,
  Sparkles,
  Volume2,
  VolumeX,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/brand/BrandLogo";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  actionProposal?: {
    type: "reschedule" | "clarify";
    details: string;
  };
}

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "m-1",
    sender: "assistant",
    text: "Vanakkam! I am THOZHI (தோழி), your multilingual sovereign planning partner. How can I assist with your commitments or daily workload today?",
    timestamp: "10:00 AM",
  },
  {
    id: "m-2",
    sender: "user",
    text: "Why did you schedule the Architecture PRD deep work block before lunch?",
    timestamp: "10:02 AM",
  },
  {
    id: "m-3",
    sender: "assistant",
    text: "I scheduled it from 11:00 AM to 1:00 PM based on two deterministic constraints:\n1. Your learned preference indicates your highest cognitive stamina is before 12:30 PM.\n2. The 2:30 PM client call depends on having the technical PRD finalized first.\n\nRemember: 'The AI proposes. The user decides.' If you prefer moving it to late afternoon, let me know!",
    timestamp: "10:02 AM",
  },
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);

  const handleSendMessage = (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage("");
    setIsTyping(true);

    setTimeout(() => {
      let replyText = "";
      if (text.toLowerCase().includes("overwhelmed") || text.toLowerCase().includes("drop")) {
        replyText = "Looking at your schedule, you have 6.5 hours of commitments against an 8-hour target. You can safely defer 'Review Pull Requests' (P3 Routine) to tomorrow morning to create a 90-minute buffer.";
      } else if (text.toLowerCase().includes("tanglish") || text.toLowerCase().includes("tamil")) {
        replyText = "Kandippa! Neenga Tamil la pesinaalum sari, Tanglish la type panninaalum sari, Gnani Prisma v3 engine accurate-aa interpret pannum. Enna task plan pannanum?";
      } else {
        replyText = "Understood. I will cross-reference your available calendar capacity and topological dependencies before proposing any schedule adjustments.";
      }

      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: "assistant",
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 700);
  };

  const handleQuickPrompt = (prompt: string) => {
    handleSendMessage(prompt);
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-sky-500/20 flex-shrink-0">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Conversational Assistant</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold">
              Schedule & Intent Dialogue
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Ask questions about why decisions were proposed, manage overload, or triage tasks.
          </p>
        </div>

        {/* TTS Toggle */}
        <button
          onClick={() => setTtsEnabled(!ttsEnabled)}
          className={cn(
            "p-2 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition",
            ttsEnabled
              ? "bg-sky-500/20 text-sky-300 border-sky-500/40"
              : "bg-canvas-card border-slate-700 text-slate-400 hover:text-white"
          )}
          title="Toggle Text-to-Speech audio output"
        >
          {ttsEnabled ? <Volume2 className="w-4 h-4 text-sky-400" /> : <VolumeX className="w-4 h-4" />}
          <span className="hidden sm:inline">Audio Readout</span>
        </button>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((m) => {
          const isAssistant = m.sender === "assistant";
          return (
            <div
              key={m.id}
              className={cn(
                "flex items-start gap-3",
                isAssistant ? "justify-start" : "justify-end"
              )}
            >
              {isAssistant && (
                <BrandLogo variant="icon" className="w-8 h-8 flex-shrink-0" alt="THOZHI Assistant" />
              )}

              <div
                className={cn(
                  "p-4 rounded-2xl max-w-lg text-sm leading-relaxed space-y-1.5 shadow-sm",
                  isAssistant
                    ? "bg-canvas-card border border-sky-500/20 text-slate-200"
                    : "bg-gradient-to-br from-sky-600 to-sky-700 text-white font-medium"
                )}
              >
                <p className="whitespace-pre-line">{m.text}</p>
                <div
                  className={cn(
                    "text-[10px] text-right font-mono",
                    isAssistant ? "text-slate-500" : "text-sky-200"
                  )}
                >
                  {m.timestamp}
                </div>
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center gap-3">
            <BrandLogo variant="icon" className="w-8 h-8 flex-shrink-0 animate-pulse" alt="THOZHI Thinking" />
            <div className="p-3.5 rounded-2xl bg-canvas-card border border-sky-500/20 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]" />
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      {/* Suggested Quick Prompts */}
      <div className="flex flex-wrap items-center gap-2 pt-2 flex-shrink-0">
        <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-cyber-amber-400" /> Suggested:
        </span>
        <button
          type="button"
          onClick={() => handleQuickPrompt("I feel overwhelmed today, what can I drop or reschedule?")}
          className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-card hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
        >
          Overloaded today?
        </button>
        <button
          type="button"
          onClick={() => handleQuickPrompt("Explain why the design review task has high priority.")}
          className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-card hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
        >
          Why is design review P1?
        </button>
        <button
          type="button"
          onClick={() => handleQuickPrompt("Tamil/Tanglish la task epdi add panradhu?")}
          className="text-[11px] px-2.5 py-1 rounded-md bg-canvas-card hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition"
        >
          Tanglish guide
        </button>
      </div>

      {/* Input Field Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="flex items-center gap-2 p-2 rounded-2xl bg-canvas-card border border-sky-500/20 flex-shrink-0"
      >
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask THOZHI about your schedule or priorities..."
          className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={!inputMessage.trim()}
          className="btn-primary p-2.5 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
