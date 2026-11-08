import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://bwzqudaaxfubtbgwmevo.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

let clientInstance: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient | null {
  if (clientInstance) {
    return clientInstance;
  }

  if (typeof window === "undefined") {
    // Server-side rendering
    if (supabaseUrl && supabaseAnonKey) {
      return createClient(supabaseUrl, supabaseAnonKey, {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      });
    }
    return null;
  }

  // Client-side browser execution
  if (supabaseUrl && supabaseAnonKey) {
    clientInstance = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: "thozhi_supabase_session",
      },
    });
    return clientInstance;
  }

  return null;
}

export const supabase = getSupabaseClient();
