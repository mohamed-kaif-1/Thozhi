"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Mic, Bell } from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { useUserProfile } from "@/lib/useUserProfile";

export const TopNav: React.FC = () => {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");
  const { displayName, initials } = useUserProfile();

  const getPageTitle = (path: string) => {
    switch (path) {
      case "/": return "Today's Agenda & Focus";
      case "/capture": return "Thought Capture Studio";
      case "/tasks": return "Task Management";
      case "/planner": return "Intelligent Planner";
      case "/calendar": return "Calendar & Schedules";
      case "/projects": return "Projects & Milestones";
      case "/goals": return "Strategic Goals";
      case "/memory": return "Personal Memory & Privacy";
      case "/insights": return "Productivity Insights";
      case "/assistant": return "Conversational Assistant";
      case "/notifications": return "Notification Center";
      case "/settings": return "Settings & Preferences";
      default: return "Personal Planning Workspace";
    }
  };

  return (
    <header className="h-16 bg-canvas-card/80 backdrop-blur-md border-b border-sky-500/15 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link href="/" className="md:hidden flex items-center gap-2" aria-label="THOZHI Home">
          <BrandLogo variant="icon" className="w-9 h-9" alt="THOZHI Mascot" priority />
        </Link>
        <div>
          <h1 className="text-base md:text-lg font-bold text-white tracking-tight">
            {getPageTitle(pathname)}
          </h1>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-medium">
            <BrandLogo variant="icon" className="w-3.5 h-3.5 inline-block opacity-80" />
            <span className="text-sky-400 font-semibold">THOZHI</span>
            <span>•</span>
            <span className="capitalize">{pathname === "/" ? "Home" : pathname.replace("/", "")}</span>
          </div>
        </div>
      </div>

      {/* Global Actions */}
      <div className="flex items-center gap-3">
        {/* Search Bar */}
        <div className="relative hidden sm:block w-48 md:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tasks, commitments..."
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-slate-900/90 border border-slate-700/60 focus:border-sky-400 focus:outline-none text-xs text-white placeholder:text-slate-500 transition shadow-inner"
          />
        </div>

        {/* Quick Voice / Text Capture Button */}
        <Link
          href="/capture"
          className="h-9 px-3.5 rounded-lg btn-primary flex items-center gap-2 text-xs"
        >
          <Mic className="w-4 h-4 text-white" />
          <span className="hidden sm:inline">Quick Capture</span>
        </Link>

        {/* Notifications Icon with Badge */}
        <Link
          href="/notifications"
          className="relative w-9 h-9 rounded-lg bg-canvas-subtle hover:bg-slate-800 border border-slate-700/60 text-slate-300 hover:text-white flex items-center justify-center transition"
          aria-label="View notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyber-amber-500 animate-pulse" />
        </Link>

        {/* User Profile Mini Trigger */}
        <Link
          href="/settings"
          className="w-9 h-9 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-300 border border-amber-400/40 text-slate-950 font-black text-xs flex items-center justify-center shadow uppercase hover:ring-2 hover:ring-amber-400/50 transition"
          aria-label="Profile settings"
          title={`Signed in as ${displayName}`}
        >
          {initials}
        </Link>
      </div>
    </header>
  );
};
