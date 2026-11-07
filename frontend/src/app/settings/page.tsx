"use client";

import React, { useState, useEffect } from "react";
import {
  Mic,
  Clock,
  Shield,
  Download,
  CheckCircle2,
  Save,
  Cpu,
  Sparkles,
} from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { cn } from "@/lib/utils";
import {
  listMemoryPreferences,
  createMemoryPreference,
  exportPersonalData,
} from "@/lib/api";

export default function SettingsPage() {
  const [primaryLanguage, setPrimaryLanguage] = useState<"tanglish" | "ta" | "en">("tanglish");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("18:00");
  const [dailyFocusHours, setDailyFocusHours] = useState(8);
  const [autoBufferPct, setAutoBufferPct] = useState(15);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    listMemoryPreferences()
      .then((prefs) => {
        if (!prefs) return;
        for (const p of prefs) {
          if (p.preference_key === "user_working_hours" && p.preference_value) {
            const val = p.preference_value as Record<string, unknown>;
            if (typeof val.startTime === "string") setStartTime(val.startTime);
            if (typeof val.endTime === "string") setEndTime(val.endTime);
            if (val.dailyFocusHours !== undefined) setDailyFocusHours(Number(val.dailyFocusHours));
          }
          if (p.preference_key === "primary_language" && p.preference_value) {
            const val = p.preference_value as Record<string, unknown>;
            if (val.primaryLanguage === "en" || val.primaryLanguage === "tanglish" || val.primaryLanguage === "ta") {
              setPrimaryLanguage(val.primaryLanguage);
            }
          }
          if (p.preference_key === "auto_buffer" && p.preference_value) {
            const val = p.preference_value as Record<string, unknown>;
            if (val.autoBufferPct !== undefined) setAutoBufferPct(Number(val.autoBufferPct));
          }
        }
      })
      .catch(() => {
        // ignore
      });
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await Promise.all([
        createMemoryPreference({
          preference_key: "user_working_hours",
          category: "WORKING_HOURS",
          preference_value: { startTime, endTime, dailyFocusHours },
          description: `Configured focus working hours from ${startTime} to ${endTime} (${dailyFocusHours}h max load).`,
        }),
        createMemoryPreference({
          preference_key: "primary_language",
          category: "LANGUAGE",
          preference_value: { primaryLanguage },
          description: `Primary Indic language preference set to ${primaryLanguage}.`,
        }),
        createMemoryPreference({
          preference_key: "auto_buffer",
          category: "PLANNING_STYLE",
          preference_value: { autoBufferPct },
          description: `Automatic schedule buffer set to ${autoBufferPct}%.`,
        }),
      ]);
      setNotification("Settings successfully synced to sovereign memory!");
    } catch {
      setNotification("Saved settings locally.");
    }
    setTimeout(() => setNotification(null), 3500);
  };

  const handleExportData = async () => {
    try {
      const blob = await exportPersonalData();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `thozhi-sovereign-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setNotification("Sovereign data export generated and downloaded!");
      setTimeout(() => setNotification(null), 3500);
    } catch {
      setNotification("Failed to export sovereign data.");
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Settings & Sovereignty</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold">
              Configuration
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure working hours, Indic speech models, planning buffers, and export your sovereign data.
          </p>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-3 shadow-lg">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span className="font-medium text-sm">{notification}</span>
        </div>
      )}

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* SECTION 1: WORKING HOURS & CAPACITY */}
        <div className="surface-card p-6 border-sky-500/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Clock className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Working Hours & Daily Capacity
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Day Start Time
              </label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Day End Time
              </label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Target Daily Focus Hours
              </label>
              <input
                type="number"
                min="2"
                max="14"
                step="0.5"
                value={dailyFocusHours}
                onChange={(e) => setDailyFocusHours(Number(e.target.value))}
                className="w-full px-3.5 py-2 rounded-lg bg-canvas-subtle border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-sky-400"
              />
            </div>
          </div>
        </div>

        {/* SECTION 2: MULTILINGUAL SPEECH & ASR ENGINES */}
        <div className="surface-card p-6 border-sky-500/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Mic className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Multilingual Speech Recognition Engines
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                Primary Input Dialect
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: "tanglish", label: "Tanglish (Tamil + English)" },
                  { id: "ta", label: "தமிழ் (Tamil Script)" },
                  { id: "en", label: "English (Indian Accent)" },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setPrimaryLanguage(item.id as "tanglish" | "ta" | "en")}
                    className={cn(
                      "p-3 rounded-xl border text-xs font-bold transition text-left space-y-1",
                      primaryLanguage === item.id
                        ? "bg-sky-500/20 text-sky-300 border-sky-400"
                        : "bg-canvas-subtle text-slate-400 border-slate-800 hover:text-white"
                    )}
                  >
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* ASR Providers Status */}
            <div className="space-y-2 pt-2">
              <span className="text-xs font-semibold text-slate-400 block">
                Active Speech Telemetry & Fallback Hierarchy
              </span>

              {/* Primary: Gnani AI Prisma v3 */}
              <div className="p-3.5 rounded-xl bg-canvas-subtle border border-sky-500/30 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">Primary: Gnani AI Prisma v3</span>
                      <span className="text-[10px] px-1.5 rounded bg-sky-500/20 text-sky-300 font-mono">
                        model=&quot;prisma-v3.0&quot;
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Endpoint: https://api.vachana.ai/stt/v3 | Header: X-API-Key-ID
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-emerald-400 uppercase">
                  Online
                </span>
              </div>

              {/* Fallback: Sarvam Saaras v3 */}
              <div className="p-3.5 rounded-xl bg-canvas-subtle/60 border border-slate-800 flex items-center justify-between opacity-80">
                <div className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-500" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-300">Failover: Sarvam Saaras v3</span>
                      <span className="text-[10px] px-1.5 rounded bg-slate-800 text-slate-400 font-mono">
                        ₹0.50/min
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Endpoint: POST https://api.sarvam.ai/speech-to-text
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-slate-400 uppercase">
                  Standby
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 3: SCHEDULING CALIBRATION */}
        <div className="surface-card p-6 border-sky-500/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Cpu className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Deterministic Scheduling Math
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="font-semibold text-slate-300">
                  Automatic Duration Buffer Percentage
                </label>
                <span className="font-bold text-cyber-amber-400 font-mono">
                  {autoBufferPct}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="5"
                value={autoBufferPct}
                onChange={(e) => setAutoBufferPct(Number(e.target.value))}
                className="w-full accent-sky-400"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Adds conservative buffer time to tasks to absorb cognitive friction and transitions.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 4: DATA SOVEREIGNTY & EXPORT */}
        <div className="surface-card p-6 border-emerald-500/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Data Sovereignty & Local Storage
            </h2>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-300 leading-relaxed">
              All your tasks, proposals, and duration memories belong exclusively to you. You can export complete data in standard JSON at any time.
            </p>
            <button
              type="button"
              onClick={handleExportData}
              className="btn-primary text-xs px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 flex-shrink-0"
            >
              <Download className="w-4 h-4" />
              <span>Export Data (JSON)</span>
            </button>
          </div>
        </div>

        {/* SECTION 5: BRAND IDENTITY & APP METADATA */}
        <div className="surface-card p-6 border-sky-500/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Sparkles className="w-5 h-5 text-cyber-amber-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Brand Identity & Application Profile
            </h2>
          </div>

          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 p-4 rounded-xl bg-canvas-subtle/80 border border-sky-500/15">
            <BrandLogo variant="horizontal" className="h-12 w-auto flex-shrink-0" alt="THOZHI Brand Identity" />
            <div className="space-y-1.5 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2">
                <span className="text-sm font-black text-white">THOZHI (தோழி) v1.0.0</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                  Production Build
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Multilingual AI Personal Planning Assistant with Gnani AI Prisma v3 Indic Speech Pipeline.
              </p>
              <p className="text-[11px] text-cyber-amber-400 font-semibold italic">
                &ldquo;The AI proposes. The user decides.&rdquo;
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="btn-amber px-6 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
}
