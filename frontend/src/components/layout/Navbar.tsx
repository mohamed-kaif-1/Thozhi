import React from "react";
import Link from "next/link";
import { Calendar, Mic } from "lucide-react";

export const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 bg-white border-b-2 border-black">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-lg bg-neo-blue border-2 border-black shadow-[2px_2px_0px_0px_#000] flex items-center justify-center text-black font-black text-xl">
            தோ
          </div>
          <div>
            <span className="font-black text-xl tracking-tight text-black">
              THOZHI
            </span>
            <span className="text-[10px] block -mt-1 text-black font-bold uppercase tracking-wider">
              AI Personal Planning
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-2">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-black bg-neo-blue border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0px_0px_#000] transition"
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Today</span>
          </Link>

          <Link
            href="/#capture"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-black bg-white border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:bg-neo-blue-light hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0px_0px_#000] transition"
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Capture</span>
          </Link>
        </nav>
      </div>
    </header>
  );
};
