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

    const handleUpdate = (e: Event) => {
      const custom = e as CustomEvent<UserProfile>;
      if (custom.detail) {
        setProfile(custom.detail);
      } else {
        fetchProfile();
      }
    };

    if (typeof window !== "undefined") {
      window.addEventListener(EVENT_NAME, handleUpdate);
    }

    return () => {
      mounted = false;
      if (typeof window !== "undefined") {
        window.removeEventListener(EVENT_NAME, handleUpdate);
      }
    };
  }, []);

  const saveProfile = useCallback(
    async (updates: { display_name?: string; email?: string; timezone?: string }) => {
      setLoading(true);
      try {
        const updated = await updateUserProfile(updates);
        setProfile(updated);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        } catch {
          // ignore
        }
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: updated }));
        }
        return updated;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    profile,
    displayName: profile.display_name || "Karthi P.",
    initials: getInitials(profile.display_name || "Karthi P."),
    saveProfile,
    loading,
  };
}
