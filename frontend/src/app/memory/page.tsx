"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Trash2,
  Lock,
  Clock,
  Eye,
  CheckCircle2,
  Search,
  Download,
  ToggleLeft,
  ToggleRight,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/brand/BrandLogo";
import {
  listMemoryPreferences,
  deleteMemoryPreference,
  toggleMemoryPreference,
  getDurationPriorSuggestions,
  exportPersonalData,
  purgeAllPersonalData,
  MemoryPreference,
  DurationPrior,
} from "@/lib/api";

const SEED_FALLBACK: MemoryPreference[] = [
  {
    id: "mem-1",
    user_id: "default",
    category: "DURATION_PRIOR",
    preference_key: "technical_report_duration_prior",
    preference_value: { baseline_multiplier: 1.4, suggested_min: 75 },
    description: "User consistently underestimates report documentation by +45 mins. THOZHI applies a 1.4x buffer.",
    is_active: true,
    consent_level: "USER_APPROVED",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "mem-2",
    user_id: "default",
    category: "PLANNING_STYLE",
    preference_key: "morning_deep_work_window",
    preference_value: { start: "09:30", end: "12:30", preferred_priority: "P1" },
    description: "User prefers scheduling P1 analytical and coding tasks between 09:30 AM and 12:30 PM.",
    is_active: true,
    consent_level: "EXPLICIT_CONSENT",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "mem-3",
    user_id: "default",
    category: "WORKING_HOURS",
    preference_key: "protected_lunch_break",
    preference_value: { start: "13:00", end: "14:00", blocking: true },
    description: "Protected lunch break: never schedule focus blocks or calls between 13:00 and 14:00.",
    is_active: true,
    consent_level: "EXPLICIT_CONSENT",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export default function MemoryPage() {
  const [preferences, setPreferences] = useState<MemoryPreference[]>([]);
  const [durationSuggestions, setDurationSuggestions] = useState<DurationPrior[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [notification, setNotification] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const prefs = await listMemoryPreferences();
      if (prefs && prefs.length > 0) {
        setPreferences(prefs);
      } else {
        setPreferences(SEED_FALLBACK);
      }
    } catch {
      setPreferences(SEED_FALLBACK);
    }

    try {
      const suggs = await getDurationPriorSuggestions();
      if (suggs) {
        setDurationSuggestions(suggs);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: string) => {
    setPreferences((prev) => prev.filter((p) => p.id !== id));
    try {
      await deleteMemoryPreference(id);
      setNotification("Memory record permanently removed from local store.");
    } catch {
      setNotification("Memory record deleted locally.");
    }
    setTimeout(() => setNotification(null), 3500);
  };

  const handleToggle = async (id: string) => {
    setPreferences((prev) =>
      prev.map((p) => (p.id === id ? { ...p, is_active: !p.is_active } : p))
    );
    try {
      await toggleMemoryPreference(id);
    } catch {
      // ignore
    }
  };

  const handleExport = async () => {
    try {
      const blob = await exportPersonalData();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `thozhi_sovereign_export_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setNotification("Downloaded sovereign personal data bundle!");
      setTimeout(() => setNotification(null), 4000);
    } catch {
      setNotification("Failed to export personal data.");
    }
  };

  const handlePurgeAll = async () => {
    if (
      confirm(
        "Are you sure? This triggers your sovereign 'Right to be Forgotten' and permanently purges all learned preferences, tasks, and history."
      )
    ) {
      try {
        await purgeAllPersonalData();
        setPreferences([]);
        setDurationSuggestions([]);
        setNotification("All personal memories purged permanently (Right to be Forgotten).");
      } catch {
        setPreferences([]);
        setNotification("All local memories purged.");
      }
      setTimeout(() => setNotification(null), 4000);
    }
  };

  const filteredPreferences = preferences.filter((p) => {
    if (selectedCategory !== "all" && p.category.toLowerCase() !== selectedCategory.toLowerCase()) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        p.preference_key.toLowerCase().includes(q) ||
        (p.description && p.description.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Hybrid Personal Memory & Privacy</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
              Sovereign & Local-First
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            THOZHI learns personal duration priors and preferences only with your consent. You hold the sovereign right to inspect, disable, and purge anything.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="text-xs px-3.5 py-2 rounded-xl bg-canvas-card hover:bg-slate-800 border border-sky-500/30 text-sky-300 font-bold flex items-center gap-2 transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Data</span>
          </button>
          <button
            onClick={handlePurgeAll}
            className="text-xs px-3.5 py-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/40 text-rose-300 font-bold flex items-center gap-2 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Purge All</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-3 shadow-lg">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span className="font-medium text-sm">{notification}</span>
        </div>
      )}

      {/* Sovereign Guarantee Badges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="surface-card p-4 border-sky-500/20 space-y-2">
          <div className="flex items-center gap-2 text-sky-400">
            <Lock className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Zero Audio Retention</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            All voice streams are held strictly in ephemeral RAM buffers and destroyed immediately post-ASR.
          </p>
        </div>

        <div className="surface-card p-4 border-cyber-amber-500/20 space-y-2">
          <div className="flex items-center gap-2 text-cyber-amber-400">
            <ShieldCheck className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Consent-Gated Priors</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Duration adjustments are proposed transparently and never silently manipulated in your calendar.
          </p>
        </div>

        <div className="surface-card p-4 border-emerald-500/20 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400">
            <Eye className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Right to be Forgotten</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Full compliance with sovereign data governance. One click to erase all embeddings and weights.
          </p>
        </div>
      </div>

      {/* Duration Prior Learning Suggestions */}
      {durationSuggestions.length > 0 && (
        <div className="surface-card p-5 border-cyber-amber-500/40 bg-cyber-amber-950/10 space-y-3">
          <div className="flex items-center gap-2 text-cyber-amber-400">
            <Sparkles className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">
              AI Duration Prior Discovery ({durationSuggestions.length} Pattern Detected)
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {durationSuggestions.map((s, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-black/40 border border-cyber-amber-500/20 flex items-center justify-between gap-4 text-xs"
              >
                <div>
                  <span className="font-bold text-cyber-amber-200 uppercase tracking-wide">
                    Pattern: {s.task_pattern}
                  </span>
                  <p className="text-slate-300 mt-0.5">{s.rationale}</p>
                </div>
                <span className="px-2 py-1 rounded bg-cyber-amber-500/20 text-cyber-amber-300 font-mono text-[10px]">
                  Suggested: {s.suggested_duration_min}m
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-canvas-card border border-sky-500/20">
        <div className="relative flex-1 w-full sm:max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search learned memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-canvas-subtle border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-400"
          />
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-canvas-subtle border border-slate-700 text-xs self-stretch sm:self-auto justify-center">
          {[
            { id: "all", label: "All Memories" },
            { id: "duration_prior", label: "Duration Priors" },
            { id: "planning_style", label: "Planning Style" },
            { id: "working_hours", label: "Working Hours" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "px-3 py-1 rounded-md font-medium transition",
                selectedCategory === cat.id
                  ? "bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Memories List */}
      <div className="space-y-4">
        {filteredPreferences.length === 0 ? (
          <div className="surface-card p-12 text-center text-slate-400 space-y-3">
            <BrandLogo variant="icon" className="w-14 h-14 mx-auto opacity-70 mb-1" alt="THOZHI Mascot" />
            <p className="text-base font-bold text-slate-200">No memory entries found</p>
            <p className="text-xs text-slate-400">
              As you use THOZHI, observed duration multipliers and working preferences will appear here for your review.
            </p>
          </div>
        ) : (
          filteredPreferences.map((pref) => {
            const isPrior = pref.category.includes("DURATION");
            return (
              <div
                key={pref.id}
                className={cn(
                  "surface-card surface-card-hover p-5 border-sky-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition",
                  !pref.is_active && "opacity-50"
                )}
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span
                      className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider",
                        isPrior
                          ? "bg-cyber-amber-950/60 text-cyber-amber-300 border border-cyber-amber-500/40"
                          : "bg-sky-950/60 text-sky-300 border border-sky-500/40"
                      )}
                    >
                      {pref.category.replace("_", " ")}
                    </span>
                    <h3 className="text-sm font-bold text-white font-mono">{pref.preference_key}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/30 text-emerald-300 font-mono">
                      {pref.consent_level}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                    {pref.description || JSON.stringify(pref.preference_value)}
                  </p>

                  <div className="text-[11px] text-slate-500 flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" /> Updated: {new Date(pref.updated_at || Date.now()).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => handleToggle(pref.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white transition"
                    title={pref.is_active ? "Disable preference" : "Enable preference"}
                  >
                    {pref.is_active ? (
                      <ToggleRight className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-slate-600" />
                    )}
                  </button>

                  <button
                    onClick={() => handleDelete(pref.id)}
                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition"
                    title="Purge this preference"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
