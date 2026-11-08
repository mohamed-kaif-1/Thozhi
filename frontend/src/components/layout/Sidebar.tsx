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
  BarChart3,
  Bot,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { useUserProfile } from "@/lib/useUserProfile";

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
  { name: "Insights", href: "/insights", icon: BarChart3 },
  { name: "Assistant", href: "/assistant", icon: Bot },
  { name: "Notifications", href: "/notifications", icon: Bell, badge: "2" },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { displayName, initials } = useUserProfile();

  if (pathname === "/login") {
    return null;
  }

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col bg-white/85 dark:bg-slate-900/85 backdrop-blur-md border-r border-slate-200/80 dark:border-sky-500/15 transition-all duration-300 z-40 relative flex-shrink-0 min-h-screen",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-200/80 dark:border-sky-500/15">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          {isCollapsed ? (
            <BrandLogo variant="icon" className="w-10 h-10 flex-shrink-0" alt="THOZHI Mascot" priority />
          ) : (
            <BrandLogo variant="horizontal" className="h-9 w-auto flex-shrink-0" alt="THOZHI — Daily Planner" priority />
          )}
        </Link>

        {/* Collapse Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-canvas-subtle dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/60 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center transition shadow-sm"
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
                  ? "bg-sky-500/10 dark:bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/30 shadow-sm shadow-sky-500/10"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
              )}
            >
              <Icon
                className={cn(
                  "w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-110",
                  isActive ? "text-sky-600 dark:text-sky-400" : "text-slate-500 dark:text-slate-400 group-hover:text-sky-500 dark:group-hover:text-sky-300"
                )}
              />
              {!isCollapsed && <span className="truncate">{item.name}</span>}

              {/* Notification / Count Badge */}
              {item.badge && !isCollapsed && (
                <span className="ml-auto px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/15 text-sky-600 dark:text-sky-300 border border-sky-400/30">
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
      <div className="p-3 border-t border-slate-200/80 dark:border-sky-500/15 space-y-1 bg-slate-50/50 dark:bg-canvas-subtle/50">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold transition",
            pathname === "/settings"
              ? "bg-sky-500/10 dark:bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/30"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0 text-slate-500 dark:text-slate-400" />
          {!isCollapsed && <span>Settings</span>}
        </Link>

        {/* User Profile Mini */}
        {!isCollapsed && (
          <div className="mt-2 pt-2 border-t border-slate-200/80 dark:border-slate-800 flex items-center gap-3 px-2 py-1">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-amber-300 border border-amber-400/40 flex items-center justify-center text-slate-950 font-black text-xs uppercase shadow-sm">
              {initials}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-slate-900 dark:text-white truncate" title={displayName}>{displayName}</p>
              <p className="text-[10px] text-sky-600 dark:text-sky-400 font-medium truncate">Pro Free Plan</p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
