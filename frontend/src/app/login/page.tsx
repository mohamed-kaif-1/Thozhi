"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, Mail, AlertCircle, CheckCircle2, ArrowRight, Loader2 } from "lucide-react";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/";

  const { login, signUp, isAuthenticated, isLoading: authLoading, isConfigured, error: authError, clearError } = useAuth();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  // If already authenticated, redirect immediately
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, authLoading, router, redirectTo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setInfoMessage(null);
    clearError();

    if (!email.trim() || !password) {
      setLocalError("Please provide both email and password.");
      return;
    }

    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters long.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === "login") {
        const res = await login(email, password);
        if (res.error) {
          setLocalError(res.error);
        } else {
          router.push(redirectTo);
        }
      } else {
        const res = await signUp(email, password);
        if (res.error) {
          setLocalError(res.error);
        } else if (res.message) {
          setInfoMessage(res.message);
        } else {
          router.push(redirectTo);
        }
      }
    } catch (err: unknown) {
      setLocalError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="min-h-[80vh] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-sky-500/20 shadow-xl backdrop-blur-sm">
        {/* Header / Brand */}
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <BrandLogo variant="icon" className="w-16 h-16 drop-shadow-md" alt="THOZHI Mascot" priority />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {mode === "login" ? "Welcome back to THOZHI" : "Create your THOZHI account"}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {mode === "login"
              ? "Sign in to access your personal planning workspace"
              : "Experience sovereign AI intent-to-action planning"}
          </p>
        </div>

        {/* Configuration Warning Notice */}
        {!isConfigured && (
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-500" />
            <div>
              <p className="font-semibold">Supabase Auth Configuration Needed</p>
              <p className="text-[11px] mt-0.5 text-amber-600/90 dark:text-amber-400/90">
                To connect to live Supabase Auth, specify <code className="bg-amber-500/20 px-1 py-0.5 rounded font-mono">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in <code className="bg-amber-500/20 px-1 py-0.5 rounded font-mono">frontend/.env.local</code>.
              </p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {activeError && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs flex items-start gap-2.5 animate-fade-in">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
            <div className="flex-1 font-medium">{activeError}</div>
          </div>
        )}

        {/* Information Message */}
        {infoMessage && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs flex items-start gap-2.5 animate-fade-in">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-500" />
            <div className="flex-1 font-medium">{infoMessage}</div>
          </div>
        )}

        {/* Form */}
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={isSubmitting}
                className="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition disabled:opacity-50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isSubmitting}
                className="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition disabled:opacity-50"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || authLoading}
            className="w-full h-10 mt-2 rounded-xl bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-400 hover:to-sky-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{mode === "login" ? "Signing In..." : "Creating Account..."}</span>
              </>
            ) : (
              <>
                <span>{mode === "login" ? "Sign In" : "Create Account"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Toggle Mode Footer */}
        <div className="pt-4 border-t border-slate-200 dark:border-slate-800 text-center">
          {mode === "login" ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Don&apos;t have an account yet?{" "}
              <button
                type="button"
                onClick={() => {
                  setMode("signup");
                  setLocalError(null);
                  setInfoMessage(null);
                }}
                className="text-sky-600 dark:text-sky-400 font-bold hover:underline"
              >
                Sign up
              </button>
            </p>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setLocalError(null);
                  setInfoMessage(null);
                }}
                className="text-sky-600 dark:text-sky-400 font-bold hover:underline"
              >
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
