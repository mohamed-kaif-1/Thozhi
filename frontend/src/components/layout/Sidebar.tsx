"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Mic,
  CheckSquare,
  CalendarDays,
  Calendar,
  FolderGit2,
  Target,
  Brain,
  BarChart3,
  Bot,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string | number;
}

const PRIMARY_NAV: NavItem[] = [
  { name: "Home", href: "/", icon: Home },
  { name: "Capture", href: "/capture", icon: Mic },
  { name: "My Tasks", href: "/tasks", icon: CheckSquare, badge: 3 },
  { name: "Planner", href: "/planner", icon: CalendarDays },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Projects", href: "/projects", icon: FolderGit2 },
  { name: "Goals", href: "/goals", icon: Target },
  { name: "Memory", href: "/memory", icon: Brain },
  { name: "Insights", href: "/insights", icon: BarChart3 },
  { name: "Assistant", href: "/assistant", icon: Bot },
  { name: "Notifications", href: "/notifications", icon: Bell, badge: "2" },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col bg-canvas-card border-r border-sky-500/15 transition-all duration-300 z-40 relative flex-shrink-0 min-h-screen",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-sky-500/15">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-sky-400 border border-sky-300/40 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-sky-500/20 flex-shrink-0">
            தோ
          </div>
          {!isCollapsed && (
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-black text-lg tracking-tight text-white">
                  THOZHI
                </span>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-cyber-amber-500/20 text-cyber-amber-400 border border-cyber-amber-500/30">
                  AI
                </span>
              </div>
              <span className="text-[10px] block text-sky-400 font-semibold tracking-wide">
                Personal Planner
              </span>
            </div>
          )}
        </Link>

        {/* Collapse Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-7 h-7 rounded-lg bg-canvas-subtle hover:bg-slate-800 border border-slate-700/60 text-slate-400 hover:text-white flex items-center justify-center transition"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav Items List */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {PRIMARY_NAV.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all group relative",
                isActive
                  ? "bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm shadow-sky-500/10"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
            >
              <Icon
                className={cn(
                  "w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-110",
                  isActive ? "text-sky-400" : "text-slate-400 group-hover:text-sky-300"
                )}
              />
              {!isCollapsed && <span className="truncate">{item.name}</span>}

              {/* Notification / Count Badge */}
              {item.badge && !isCollapsed && (
                <span className="ml-auto px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyber-blue-500/20 text-sky-300 border border-sky-400/30">
                  {item.badge}
                </span>
              )}

              {/* Tooltip for collapsed view */}
              {isCollapsed && (
                <div className="absolute left-full ml-3 px-2.5 py-1 bg-slate-900 border border-sky-500/30 text-white text-xs font-bold rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition whitespace-nowrap z-50">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </div>

      {/* Bottom Footer Actions */}
      <div className="p-3 border-t border-sky-500/15 space-y-1 bg-canvas-subtle/50">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold transition",
            pathname === "/settings"
              ? "bg-sky-500/15 text-sky-400 border border-sky-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0 text-slate-400" />
          {!isCollapsed && <span>Settings</span>}
        </Link>

        {/* User Profile Mini */}
        {!isCollapsed && (
          <div className="mt-2 pt-2 border-t border-slate-800 flex items-center gap-3 px-2 py-1">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-amber-300 border border-amber-400/40 flex items-center justify-center text-slate-950 font-black text-xs">
              KP
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-white truncate">Karthi P.</p>
              <p className="text-[10px] text-sky-400 font-medium truncate">Pro Free Plan</p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
