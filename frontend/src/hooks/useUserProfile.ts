import { useState, useEffect, useCallback } from "react";
import { getUserProfile, updateUserProfile } from "@/lib/api";
import { UserProfile } from "@/types";

const STORAGE_KEY = "thozhi_user_profile";
const EVENT_NAME = "thozhi_user_profile_updated";

export function getInitials(name?: string | null): string {
  if (!name || !name.trim()) return "U";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function useUserProfile() {
  const [profile, setProfile] = useState<UserProfile>(() => {
    if (typeof window !== "undefined") {
      try {
        const cached = localStorage.getItem(STORAGE_KEY);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (parsed && typeof parsed.display_name === "string") {
            return parsed;
          }
        }
      } catch {
        // fallback
      }
    }
    return {
      id: "default-user",
      display_name: "Karthi P.",
      timezone: "Asia/Kolkata",
    };
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchProfile = async () => {
      // Do not attempt to query profile if no auth token is present
      const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY ? "thozhi_auth_token" : "") : null;
      if (!token) return;
      try {
        const data = await getUserProfile();
        if (mounted && data) {
          setProfile(data);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
          } catch {
            // ignore localStorage quota
          }
        }
      } catch {
        // preserve current profile
      }
    };

    fetchProfile();

    const handleProfileUpdate = () => {
      if (typeof window !== "undefined") {
        try {
          const cached = localStorage.getItem(STORAGE_KEY);
          if (cached) {
            const parsed = JSON.parse(cached);
            if (parsed && typeof parsed.display_name === "string") {
              setProfile(parsed);
            }
          }
        } catch {
          // ignore
        }
      }
    };

    window.addEventListener(EVENT_NAME, handleProfileUpdate);
    return () => {
      mounted = false;
      window.removeEventListener(EVENT_NAME, handleProfileUpdate);
    };
  }, []);

  const updateName = useCallback(async (newName: string) => {
    const trimmed = newName.trim();
    if (!trimmed) return;

    setLoading(true);
    try {
      const updated = await updateUserProfile({ display_name: trimmed });
      setProfile(updated);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        window.dispatchEvent(new Event(EVENT_NAME));
      } catch {
        // ignore
      }
      return updated;
    } finally {
      setLoading(false);
    }
  }, []);

  const saveProfile = useCallback(async (patch: { display_name?: string }) => {
    if (patch.display_name) {
      return updateName(patch.display_name);
    }
  }, [updateName]);

  return {
    profile,
    displayName: profile.display_name || "Karthi P.",
    initials: getInitials(profile.display_name),
    timezone: profile.timezone || "Asia/Kolkata",
    loading,
    updateName,
    saveProfile,
  };
}
