import { useEffect, useState, useCallback, useSyncExternalStore } from "react";
import { apiFetch } from "@/lib/api";
import type { UserInfo } from "@/features/auth/types";

// --- userId external store (SSR-safe) ---
let cachedUserId: number | null = null;
let listeners: Array<() => void> = [];

function getSnapshot(): number | null {
  return cachedUserId;
}

function getServerSnapshot(): number | null {
  return null;
}

function subscribe(onStoreChange: () => void): () => void {
  listeners.push(onStoreChange);
  return () => {
    listeners = listeners.filter((l) => l !== onStoreChange);
  };
}

function setStoredUserId(id: number | null) {
  cachedUserId = id;
  if (id !== null) {
    localStorage.setItem("user_id", String(id));
  } else {
    localStorage.removeItem("user_id");
  }
  listeners.forEach((l) => l());
}

// Initialize from URL params or localStorage on first load
if (typeof window !== "undefined") {
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("user_id");
  if (uid) {
    cachedUserId = Number(uid);
    localStorage.setItem("user_id", uid);
    window.history.replaceState({}, "", "/");
  } else {
    const stored = localStorage.getItem("user_id");
    cachedUserId = stored ? Number(stored) : null;
  }
}

// --- hydration external store ---
let isHydrated = false;
let hydrationListeners: Array<() => void> = [];

function getHydratedSnapshot(): boolean {
  return isHydrated;
}

function getHydratedServerSnapshot(): boolean {
  return false;
}

function subscribeHydration(onStoreChange: () => void): () => void {
  hydrationListeners.push(onStoreChange);
  // Mark hydrated on first subscribe (client-side only)
  if (!isHydrated) {
    isHydrated = true;
    // Notify on next microtask to avoid sync setState
    Promise.resolve().then(() => hydrationListeners.forEach((l) => l()));
  }
  return () => {
    hydrationListeners = hydrationListeners.filter((l) => l !== onStoreChange);
  };
}

export function useAuth() {
  const userId = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const hydrated = useSyncExternalStore(subscribeHydration, getHydratedSnapshot, getHydratedServerSnapshot);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  // Load user info + categories
  useEffect(() => {
    if (!userId) return;
    apiFetch<UserInfo>(`/auth/me?user_id=${userId}`)
      .then(setUserInfo)
      .catch(() => {
        setStoredUserId(null);
      });
    apiFetch<{ categories: string[] }>("/api/classify/categories")
      .then((data) => setCategories(data.categories))
      .catch(() => {});
  }, [userId]);

  const handleLogin = useCallback(async () => {
    const data = await apiFetch<{ auth_url: string }>("/auth/login");
    window.location.href = data.auth_url;
  }, []);

  const handleLogout = useCallback(() => {
    setStoredUserId(null);
    setUserInfo(null);
  }, []);

  return {
    userId,
    hydrated,
    userInfo,
    setUserInfo,
    categories,
    handleLogin,
    handleLogout,
  };
}
