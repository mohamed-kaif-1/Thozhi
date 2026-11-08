"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Loader2, ShieldAlert } from "lucide-react";
import Link from "next/link";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, isConfigured } = useAuth();

  useEffect(() => {
    // If auth is configured and user is not authenticated and not currently on login page
    if (!isLoading && !isAuthenticated && isConfigured && pathname !== "/login") {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isAuthenticated, isLoading, isConfigured, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-sky-500 animate-spin" />
        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          Verifying session credentials...
        </p>
      </div>
    );
  }

  // If unauthenticated and auth is configured, show a guard notice while redirecting
  if (!isAuthenticated && isConfigured && pathname !== "/login") {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto">
        <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mb-4 text-amber-500">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
          Authentication Required
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
          You must be signed in to access your personal planning workspace.
        </p>
        <Link
          href={`/login?redirect=${encodeURIComponent(pathname)}`}
          className="btn-primary text-xs px-4 py-2 rounded-xl"
        >
          Sign In
        </Link>
      </div>
    );
  }

  return <>{children}</>;
};
