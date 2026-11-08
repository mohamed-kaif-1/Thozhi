"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, CheckSquare, CalendarDays, Settings, Mic } from "lucide-react";
import { cn } from "@/lib/utils";

export const BottomNav: React.FC = () => {
  const pathname = usePathname();

  if (pathname === "/login") {
    return null;
  }

  const navItems = [
    { name: "Today", href: "/", icon: Home },
    { name: "Tasks", href: "/tasks", icon: CheckSquare },
    { name: "Capture", href: "/capture", icon: Mic, isVoice: true },
    { name: "Planner", href: "/planner", icon: CalendarDays },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <nav
      aria-label="Mobile Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-t border-slate-200/80 dark:border-sky-500/20 px-3 py-1.5 flex items-center justify-around shadow-2xl transition-colors duration-200"
    >
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        if (item.isVoice) {
          return (
            <Link
              key={item.name}
              href={item.href}
              className="relative -top-4 flex flex-col items-center group"
              aria-label="Open Voice Capture"
            >
              <div
                className={cn(
                  "w-13 h-13 rounded-full p-3 flex items-center justify-center transition-all duration-300 shadow-lg",
                  "bg-gradient-to-tr from-sky-600 via-sky-500 to-cyan-400 text-white shadow-sky-500/30",
                  "hover:scale-105 active:scale-95 border-2 border-white dark:border-slate-800"
                )}
              >
                <Icon className="w-6 h-6 animate-pulse" />
              </div>
              <span className="text-[10px] font-bold text-sky-600 dark:text-sky-400 mt-0.5">
                Capture
              </span>
            </Link>
          );
        }

        return (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex flex-col items-center py-1 px-2.5 rounded-xl transition-all",
              isActive
                ? "text-sky-600 dark:text-sky-400 font-bold"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            )}
          >
            <Icon className={cn("w-5 h-5 transition-transform", isActive && "scale-110")} />
            <span className="text-[10px] mt-0.5 tracking-tight">{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );
};
