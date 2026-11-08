"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Mic, Bell, Sun, Moon, LogOut, LogIn } from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { useUserProfile } from "@/lib/useUserProfile";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";

export const TopNav: React.FC = () => {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");
  const { displayName, initials } = useUserProfile();
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout, isConfigured } = useAuth();

  const getPageTitle = (path: string) => {
    switch (path) {
      case "/": return "Today's Agenda & Focus";
      case "/capture": return "Thought Capture Studio";
      case "/tasks": return "Task Management";
      case "/planner": return "Intelligent Planner";
      case "/calendar": return "Calendar & Schedules";
      case "/projects": return "Projects & Milestones";
      case "/goals": return "Strategic Goals";
      case "/insights": return "Productivity Insights";
      case "/assistant": return "Conversational Assistant";
      case "/notifications": return "Notification Center";
      case "/settings": return "Settings & Preferences";
      default: return "Personal Planning Workspace";
    }
  };

  return (
    <header className="h-16 bg-white/85 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/80 dark:border-sky-500/15 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 transition-colors duration-200">
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link href="/" className="md:hidden flex items-center gap-2" aria-label="THOZHI Home">
          <BrandLogo variant="icon" className="w-9 h-9" alt="THOZHI Mascot" priority />
        </Link>
        <div>
          <h1 className="text-base md:text-lg font-bold text-slate-900 dark:text-white tracking-tight">
            {getPageTitle(pathname)}
          </h1>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
            <BrandLogo variant="icon" className="w-3.5 h-3.5 inline-block opacity-80" />
            <span className="text-sky-600 dark:text-sky-400 font-semibold">THOZHI</span>
            <span>•</span>
            <span className="capitalize">{pathname === "/" ? "Home" : pathname.replace("/", "")}</span>
          </div>
        </div>
      </div>

      {/* Global Actions */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {pathname !== "/login" && (
          <>
            {/* Search Bar */}
            <div className="relative hidden sm:block w-48 md:w-64">
              <Search className="w-4 h-4 text-slate-400 dark:text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks, commitments..."
                className="w-full h-9 pl-9 pr-3 rounded-lg bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-700/60 focus:border-sky-500 dark:focus:border-sky-400 focus:outline-none text-xs text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 transition shadow-inner"
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
          </>
        )}

        {/* Theme Toggle Button (Light / Dark) */}
        <button
          onClick={toggleTheme}
          type="button"
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          className="w-9 h-9 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 dark:hover:bg-slate-700/80 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-amber-300 flex items-center justify-center transition shadow-sm"
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {theme === "dark" ? (
            <Sun className="w-4 h-4 text-amber-300 animate-fade-in" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700 animate-fade-in" />
          )}
        </button>

        {pathname !== "/login" && (
          <>
            {/* Notifications Icon with Badge */}
            <Link
              href="/notifications"
              className="relative w-9 h-9 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 dark:hover:bg-slate-700/80 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white flex items-center justify-center transition shadow-sm"
              aria-label="View notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyber-amber-500 animate-pulse" />
            </Link>

            {/* Authentication State & Profile Trigger */}
            {isAuthenticated ? (
              <div className="flex items-center gap-1.5">
                <Link
                  href="/settings"
                  className="w-9 h-9 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-300 border border-amber-400/40 text-slate-950 font-black text-xs flex items-center justify-center shadow uppercase hover:ring-2 hover:ring-amber-400/50 transition"
                  aria-label="Profile settings"
                  title={`Signed in as ${user?.email || displayName}`}
                >
                  {initials}
                </Link>
                <button
                  onClick={() => logout()}
                  type="button"
                  className="w-9 h-9 rounded-lg bg-slate-100 hover:bg-red-500/10 dark:bg-slate-800/80 dark:hover:bg-red-500/20 border border-slate-200 dark:border-slate-700/60 text-slate-600 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 flex items-center justify-center transition shadow-sm"
                  title="Sign Out"
                  aria-label="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : isConfigured ? (
              <Link
                href="/login"
                className="h-9 px-3 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-600 dark:text-sky-300 font-semibold text-xs flex items-center gap-1.5 transition shadow-sm"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
            ) : null}
          </>
        )}
      </div>
    </header>
  );
};
