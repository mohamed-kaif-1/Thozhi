"use client";

import React, { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  source: "thozhi" | "google_calendar";
  priority?: "p1" | "p2" | "p3";
  is_all_day?: boolean;
}

const MOCK_EVENTS: CalendarEvent[] = [
  {
    id: "e-1",
    title: "Stakeholder Sprint Review",
    start: "2026-11-07T09:30:00",
    end: "2026-11-07T10:30:00",
    source: "google_calendar",
  },
  {
    id: "e-2",
    title: "Deep Work: Architecture PRD",
    start: "2026-11-07T11:00:00",
    end: "2026-11-07T13:00:00",
    source: "thozhi",
    priority: "p1",
  },
  {
    id: "e-3",
    title: "Client Technical Clarification Call",
    start: "2026-11-07T14:30:00",
    end: "2026-11-07T15:15:00",
    source: "google_calendar",
  },
  {
    id: "e-4",
    title: "Supabase RLS & Audit Verification",
    start: "2026-11-07T16:00:00",
    end: "2026-11-07T17:30:00",
    source: "thozhi",
    priority: "p2",
  },
  {
    id: "e-5",
    title: "Math 401 Assignment Submission",
    start: "2026-11-08T18:00:00",
    end: "2026-11-08T19:00:00",
    source: "thozhi",
    priority: "p1",
  },
  {
    id: "e-6",
    title: "Weekly Product Strategy Sync",
    start: "2026-11-09T10:00:00",
    end: "2026-11-09T11:00:00",
    source: "google_calendar",
  },
];

type CalendarView = "month" | "week" | "day";

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [view, setView] = useState<CalendarView>("week");
  const [events] = useState<CalendarEvent[]>(MOCK_EVENTS);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string>("Synced 2 mins ago");

  const handleSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      setSyncStatus("Synced just now");
    }, 1000);
  };

  // Week days generation
  const startOfWeek = new Date(currentDate);
  startOfWeek.setDate(currentDate.getDate() - currentDate.getDay() + 1); // Monday

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    return d;
  });

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Calendar Integration</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-semibold">
              Bi-Directional View
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Overlay THOZHI sovereign focus sessions with external Google and Outlook calendars.
          </p>
        </div>

        {/* External Sync Status & Sync Button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-canvas-card border border-sky-500/20 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400">Google Calendar:</span>
            <span className="font-semibold text-slate-200">{syncStatus}</span>
          </div>

          <button
            onClick={handleSync}
            disabled={isSyncing}
            className="p-2 rounded-xl bg-canvas-card border border-sky-500/30 text-sky-400 hover:text-white hover:bg-slate-800 transition"
            title="Sync external calendars"
          >
            <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Control Bar: Navigation & View Switchers */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 rounded-xl bg-canvas-card border border-sky-500/20">
        <div className="flex items-center gap-3">
          <button
            onClick={() =>
              setCurrentDate(
                new Date(
                  currentDate.getTime() -
                    (view === "week" ? 7 : 1) * 24 * 3600 * 1000
                )
              )
            }
            className="p-1.5 rounded-lg bg-canvas-subtle hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm font-bold text-white min-w-[140px] text-center">
            {currentDate.toLocaleDateString("en-US", {
              month: "long",
              year: "numeric",
            })}
          </span>
          <button
            onClick={() =>
              setCurrentDate(
                new Date(
                  currentDate.getTime() +
                    (view === "week" ? 7 : 1) * 24 * 3600 * 1000
                )
              )
            }
            className="p-1.5 rounded-lg bg-canvas-subtle hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => setCurrentDate(new Date())}
            className="text-xs px-2.5 py-1 rounded-md bg-canvas-subtle hover:bg-slate-800 text-sky-400 border border-slate-700 font-semibold transition"
          >
            Today
          </button>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-canvas-subtle border border-slate-700 text-xs self-end sm:self-auto">
          {(["day", "week", "month"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={cn(
                "px-3 py-1 rounded-md capitalize font-semibold transition",
                view === v
                  ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              )}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* WEEK VIEW GRID */}
      {view === "week" && (
        <div className="surface-card border-sky-500/20 overflow-hidden">
          {/* Days of week header */}
          <div className="grid grid-cols-7 border-b border-slate-800 bg-canvas-subtle/50 text-center text-xs font-semibold py-3">
            {weekDays.map((day, i) => {
              const isToday = day.toDateString() === new Date().toDateString();
              return (
                <div key={i} className="space-y-1">
                  <span className="text-slate-400 block uppercase text-[10px]">
                    {day.toLocaleDateString("en-US", { weekday: "short" })}
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold",
                      isToday
                        ? "bg-sky-500 text-white shadow-md shadow-sky-500/30"
                        : "text-slate-200"
                    )}
                  >
                    {day.getDate()}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Week Days Schedule Content Columns */}
          <div className="grid grid-cols-7 divide-x divide-slate-800 min-h-[500px]">
            {weekDays.map((day, i) => {
              const dateStr = day.toISOString().split("T")[0];
              const dayEvents = events.filter((e) => e.start.startsWith(dateStr));

              return (
                <div key={i} className="p-2 space-y-2 bg-canvas/30 hover:bg-slate-900/30 transition">
                  {dayEvents.map((evt) => {
                    const isGoogle = evt.source === "google_calendar";
                    return (
                      <div
                        key={evt.id}
                        className={cn(
                          "p-2 rounded-lg border text-left text-xs space-y-1 transition hover:scale-[1.02]",
                          isGoogle
                            ? "bg-slate-900/80 border-slate-700/80 text-slate-300"
                            : evt.priority === "p1"
                            ? "bg-rose-950/40 border-rose-500/40 text-rose-200"
                            : "bg-sky-950/40 border-sky-500/40 text-sky-200"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-slate-400">
                            {new Date(evt.start).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          <span
                            className={cn(
                              "text-[9px] px-1 rounded font-bold uppercase",
                              isGoogle
                                ? "bg-slate-800 text-slate-400"
                                : "bg-sky-500/30 text-sky-300"
                            )}
                          >
                            {isGoogle ? "GCal" : "THOZHI"}
                          </span>
                        </div>
                        <p className="font-semibold line-clamp-2 leading-tight">
                          {evt.title}
                        </p>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* MONTH VIEW GRID */}
      {view === "month" && (
        <div className="surface-card p-6 border-sky-500/20 text-center space-y-4">
          <p className="text-sm font-bold text-slate-300">
            Month Overview for {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </p>
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: 31 }, (_, i) => {
              const dayNum = i + 1;
              const hasEvents = dayNum === 7 || dayNum === 8 || dayNum === 9;
              return (
                <div
                  key={i}
                  className={cn(
                    "h-24 p-2 rounded-xl bg-canvas-subtle border border-slate-800 text-left flex flex-col justify-between transition",
                    dayNum === 7 && "border-sky-500/50 bg-sky-950/20"
                  )}
                >
                  <span className="text-xs font-bold text-slate-400">{dayNum}</span>
                  {hasEvents && (
                    <div className="space-y-1">
                      <span className="block text-[10px] px-1 py-0.5 rounded bg-sky-500/20 text-sky-300 truncate">
                        {dayNum === 7 ? "3 sessions" : "1 commitment"}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* DAY VIEW */}
      {view === "day" && (
        <div className="surface-card p-6 border-sky-500/20 space-y-4">
          <h3 className="text-base font-bold text-white">
            Daily Detailed Schedule — {currentDate.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </h3>
          <div className="space-y-3">
            {events.slice(0, 4).map((evt) => (
              <div
                key={evt.id}
                className="p-4 rounded-xl bg-canvas-subtle border border-slate-800 flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-200">{evt.title}</p>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    {new Date(evt.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                    {new Date(evt.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
                <span className="text-xs font-bold text-sky-400 uppercase">
                  {evt.source}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
