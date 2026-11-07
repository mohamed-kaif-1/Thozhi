import React from "react";
import Link from "next/link";
import { Calendar, Mic } from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";

export const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 bg-canvas-card border-b border-sky-500/20 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <BrandLogo variant="horizontal" className="h-9 w-auto" alt="THOZHI — Daily Planner" priority />
        </Link>

        <nav className="flex items-center gap-2">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-sky-400 bg-sky-500/10 border border-sky-500/30 hover:bg-sky-500/20 transition"
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Today</span>
          </Link>

          <Link
            href="/#capture"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-200 bg-canvas-subtle border border-slate-700/60 hover:border-sky-500/30 hover:text-white transition"
          >
            <Mic className="w-3.5 h-3.5 text-cyber-amber-400" />
            <span>Capture</span>
          </Link>
        </nav>
      </div>
    </header>
  );
};
