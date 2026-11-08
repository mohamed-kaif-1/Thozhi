"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User, Session } from "@supabase/supabase-js";
import { getSupabaseClient } from "@/lib/supabase";
import { setAuthToken } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isConfigured: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string; message?: string }>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const supabase = getSupabaseClient();
  const isConfigured = supabase !== null;

  const clearError = useCallback(() => setError(null), []);

  // Sync token to API client and internal state
  const syncSession = useCallback((newSession: Session | null) => {
    setSession(newSession);
    setUser(newSession?.user || null);
    const accessToken = newSession?.access_token || null;
    setToken(accessToken);
    setAuthToken(accessToken);
  }, []);

  // Initial session restoration
  useEffect(() => {
    let isMounted = true;

    if (!supabase) {
      setIsLoading(false);
      return;
    }

    const restoreSession = async () => {
      try {
        const { data, error: sessionError } = await supabase.auth.getSession();
        if (sessionError) {
          console.warn("[THOZHI Auth] Session restoration warning:", sessionError.message);
        }
        if (isMounted) {
          syncSession(data.session);
        }
      } catch (err) {
        console.error("[THOZHI Auth] Failed to restore session:", err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    restoreSession();

    // Listen to real-time auth events (token refresh, sign-in, sign-out)
    const { data: authListener } = supabase.auth.onAuthStateChange((event, newSession) => {
      if (isMounted) {
        if (event === "SIGNED_OUT") {
          syncSession(null);
        } else if (newSession) {
          syncSession(newSession);
        }
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  }, [supabase, syncSession]);

  // Refresh access token
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (!supabase) return false;
    try {
      const { data, error: refreshErr } = await supabase.auth.refreshSession();
      if (refreshErr || !data.session) {
        syncSession(null);
        return false;
      }
      syncSession(data.session);
      return true;
    } catch {
      syncSession(null);
      return false;
    }
  }, [supabase, syncSession]);

  // Handle 401 Unauthorized API responses
  useEffect(() => {
    const handleUnauthorized = async () => {
      if (!token && !session) return;
      console.warn("[THOZHI Auth] 401 Unauthorized received. Attempting session refresh...");
      const refreshed = await refreshToken();
      if (!refreshed) {
        setError("Your session has expired. Please sign in again.");
      }
    };

    window.addEventListener("thozhi:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("thozhi:unauthorized", handleUnauthorized);
    };
  }, [refreshToken, token, session]);

  // Log In with Email & Password
  const login = useCallback(
    async (email: string, password: string): Promise<{ error?: string }> => {
      setError(null);
      if (!supabase) {
        const msg = "Supabase Auth is not configured. Missing NEXT_PUBLIC_SUPABASE_ANON_KEY.";
        setError(msg);
        return { error: msg };
      }

      try {
        const { data, error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

        if (signInError) {
          setError(signInError.message);
          return { error: signInError.message };
        }

        syncSession(data.session);
        return {};
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Authentication failed";
        setError(msg);
        return { error: msg };
      }
    },
    [supabase, syncSession]
  );

  // Sign Up with Email & Password
  const signUp = useCallback(
    async (email: string, password: string): Promise<{ error?: string; message?: string }> => {
      setError(null);
      if (!supabase) {
        const msg = "Supabase Auth is not configured. Missing NEXT_PUBLIC_SUPABASE_ANON_KEY.";
        setError(msg);
        return { error: msg };
      }

      try {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
        });

        if (signUpError) {
          setError(signUpError.message);
          return { error: signUpError.message };
        }

        if (data.session) {
          syncSession(data.session);
          return {};
        }

        // Email confirmation required by Supabase configuration
        return {
          message: "Account created! Please check your email to confirm your registration.",
        };
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Sign-up failed";
        setError(msg);
        return { error: msg };
      }
    },
    [supabase, syncSession]
  );

  // Log Out
  const logout = useCallback(async (): Promise<void> => {
    setError(null);
    if (supabase) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.warn("[THOZHI Auth] Sign-out warning:", err);
      }
    }
    syncSession(null);
  }, [supabase, syncSession]);

  const value: AuthContextType = {
    user,
    session,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    isConfigured,
    error,
    login,
    signUp,
    logout,
    refreshToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
